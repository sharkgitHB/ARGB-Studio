"""Main window: header (status, master power, language), live preview,
controls panel, first-run wizard and system-tray integration."""

import copy
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from . import autostart, effects, i18n, icons, theme
from .backend import OpenRGBManager, acquire_lock, surface_existing_window
from .engine import Engine
from .preview import PreviewWidget

STATE_PATH = "last_state.json"


def _label(text, object_name=None):
    lbl = QLabel(text)
    if object_name:
        lbl.setObjectName(object_name)
    return lbl


def _section(text):
    lbl = QLabel(text)
    lbl.setObjectName("sectionLabel")
    return lbl


def _effect_label(eff):
    table = (
        effects.EFFECT_LABELS_FA if i18n.current() == "fa" else effects.EFFECT_LABELS_EN
    )
    return table[eff]


class EffectPicker(QWidget):
    """All effects at once as exclusive toggle buttons (clearer than a combo)."""

    changed = Signal(str)

    def __init__(self):
        super().__init__()
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)
        self.buttons = {}
        group = QButtonGroup(self)
        group.setExclusive(True)
        for i, eff in enumerate(effects.EFFECTS):
            btn = QPushButton(_effect_label(eff))
            btn.setCheckable(True)
            btn.setMinimumHeight(36)
            btn.clicked.connect(lambda _=False, e=eff: self.changed.emit(e))
            group.addButton(btn)
            self.buttons[eff] = btn
            grid.addWidget(btn, i // 3, i % 3)

    def set_effect(self, eff):
        for e, btn in self.buttons.items():
            btn.setChecked(e == eff)

    def refresh_texts(self):
        for e, btn in self.buttons.items():
            btn.setText(_effect_label(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ARGB Studio")
        self.resize(1150, 760)
        self.setMinimumSize(940, 620)

        self.engine = Engine()
        self.selected = (0, 0)
        self._connect_retries = 0
        self._really_quit = False
        self._tray_notified = False

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())
        strip = QWidget()
        strip.setObjectName("accentStrip")
        strip.setFixedHeight(2)
        layout.addWidget(strip)

        body = QHBoxLayout()
        body.setContentsMargins(14, 14, 14, 14)
        body.setSpacing(14)
        layout.addLayout(body, stretch=1)

        self.preview = PreviewWidget(self.engine)
        self.preview.zone_clicked.connect(self.on_zone_clicked)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.preview)
        scroll.setObjectName("previewHost")
        body.addWidget(scroll, stretch=1)

        body.addWidget(self._build_controls())

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(33)

        self.engine.bridge.status.connect(self.on_status)
        self.engine.bridge.devices_loaded.connect(self.on_devices_loaded)

        self._setup_tray()

        # IPC: a second instance asks this one to pop its window up.
        from PySide6.QtNetwork import QLocalServer
        QLocalServer.removeServer("ARGBStudio")
        self._ipc_server = QLocalServer()
        self._ipc_server.newConnection.connect(self._on_ipc_connection)
        self._ipc_server.listen("ARGBStudio")

        self.engine.load_state(STATE_PATH)
        self.backend = OpenRGBManager()
        self.backend.stateChanged.connect(self.on_backend_state)
        self.backend.ensure_running_async()

    # ---------------------------------------------------------------- header

    def _build_header(self):
        header = QWidget()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(18, 12, 18, 12)
        h.setSpacing(10)

        logo = QLabel()
        logo.setObjectName("logoDot")
        h.addWidget(logo)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self._title_lbl = _label("ARGB Studio", "title")
        self._subtitle_lbl = _label(i18n.tr("app_subtitle"), "subtitle")
        title_box.addWidget(self._title_lbl)
        title_box.addWidget(self._subtitle_lbl)
        h.addLayout(title_box)

        h.addStretch(1)

        self.lang_btn = QPushButton("EN" if i18n.current() == "fa" else "فا")
        self.lang_btn.setToolTip("English / فارسی")
        self.lang_btn.setFixedWidth(64)
        self.lang_btn.setIcon(icons.icon("globe"))
        self.lang_btn.clicked.connect(
            lambda: self.apply_language("en" if i18n.current() == "fa" else "fa")
        )
        h.addWidget(self.lang_btn)

        self.master_on_btn = QPushButton(i18n.tr("master_on"))
        self.master_on_btn.setObjectName("accent")
        self.master_on_btn.setIcon(icons.icon("bolt"))
        self.master_on_btn.clicked.connect(self.on_master_on)
        h.addWidget(self.master_on_btn)

        self.master_off_btn = QPushButton(i18n.tr("master_off"))
        self.master_off_btn.setObjectName("danger")
        self.master_off_btn.setIcon(icons.icon("power"))
        self.master_off_btn.clicked.connect(self.on_master_off)
        h.addWidget(self.master_off_btn)

        self.status_pill = QLabel()
        self.status_pill.setObjectName("statusPill")
        self._set_pill("warn", i18n.tr("status_preparing"))
        h.addWidget(self.status_pill)

        self.reconnect_btn = QPushButton(i18n.tr("reconnect"))
        self.reconnect_btn.setIcon(icons.icon("refresh"))
        self.reconnect_btn.clicked.connect(lambda: self.engine.connect_async())
        h.addWidget(self.reconnect_btn)
        return header

    def _set_pill(self, kind, text):
        bg = {"ok": theme.GREEN, "warn": theme.AMBER, "err": theme.RED}[kind]
        self.status_pill.setText(text)
        self.status_pill.setStyleSheet(
            f"background: {bg}; color: #101014; border-radius: 12px;"
            "padding: 4px 14px; font-weight: 700; font-size: 12px;"
        )

    def _section_row(self, icon_name, text):
        """Section caption with a small accent icon."""
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(7)
        ic = QLabel()
        ic.setPixmap(icons.pixmap(icon_name, color="#b9a8ff", size=14))
        ic.setStyleSheet("background: transparent;")
        h.addWidget(ic)
        lbl = _section(text)
        h.addWidget(lbl)
        h.addStretch(1)
        return row, lbl

    # ---------------------------------------------------------------- controls

    def _build_controls(self):
        panel = QWidget()
        panel.setObjectName("panel")
        panel.setFixedWidth(340)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        # Scrollable inner content: nothing gets clipped in any language/DPI.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("panelScroll")
        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        v = QVBoxLayout(inner)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(10)

        self.sel_dev = _label("")
        self.sel_dev.setObjectName("sectionLabel")
        v.addWidget(self.sel_dev)
        self.sel_zone = _label(i18n.tr("sel_none"))
        self.sel_zone.setStyleSheet("font-weight: 700; font-size: 14px; color: #b9a8ff;")
        v.addWidget(self.sel_zone)

        self.wizard_btn = QPushButton(i18n.tr("wizard_btn"))
        self.wizard_btn.setToolTip(i18n.tr("wizard_tip"))
        self.wizard_btn.setIcon(icons.icon("wand"))
        self.wizard_btn.clicked.connect(self.on_setup_wizard)
        v.addWidget(self.wizard_btn)

        v.addSpacing(4)
        effect_row, self._sec_effect = self._section_row("wave", i18n.tr("effect"))
        v.addWidget(effect_row)
        self.effect_picker = EffectPicker()
        self.effect_picker.changed.connect(self.on_effect_changed)
        v.addWidget(self.effect_picker)

        v.addSpacing(4)
        color_row, self._sec_color = self._section_row("droplet", i18n.tr("color"))
        v.addWidget(color_row)
        self.color_btn = QPushButton(i18n.tr("choose_color"))
        self.color_btn.setObjectName("swatch")
        self.color_btn.clicked.connect(self.on_pick_color)
        v.addWidget(self.color_btn)

        v.addSpacing(4)
        speed_row = QHBoxLayout()
        speed_ic = QLabel()
        speed_ic.setPixmap(icons.pixmap("gauge", color="#b9a8ff", size=14))
        speed_ic.setStyleSheet("background: transparent;")
        speed_row.addWidget(speed_ic)
        self._sec_speed = _section(i18n.tr("effect_speed"))
        self._sec_speed.setToolTip(i18n.tr("effect_speed_tip"))
        speed_row.addWidget(self._sec_speed)
        speed_row.addStretch(1)
        self.speed_value = _label("4", "valueLabel")
        speed_row.addWidget(self.speed_value)
        v.addLayout(speed_row)
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        v.addWidget(self.speed_slider)

        bright_row = QHBoxLayout()
        bright_ic = QLabel()
        bright_ic.setPixmap(icons.pixmap("sun", color="#b9a8ff", size=14))
        bright_ic.setStyleSheet("background: transparent;")
        bright_row.addWidget(bright_ic)
        self._sec_bright = _section(i18n.tr("brightness"))
        bright_row.addWidget(self._sec_bright)
        bright_row.addStretch(1)
        self.bright_value = _label("80" + i18n.tr("percent"), "valueLabel")
        bright_row.addWidget(self.bright_value)
        v.addLayout(bright_row)
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(5, 100)
        self.bright_slider.valueChanged.connect(self.on_brightness_changed)
        v.addWidget(self.bright_slider)

        self.enabled_check = QCheckBox(i18n.tr("enabled"))
        self.enabled_check.toggled.connect(self.on_enabled_toggled)
        v.addWidget(self.enabled_check)

        v.addSpacing(4)
        led_row_w, self._sec_led = self._section_row("mixer", i18n.tr("led_layout"))
        v.addWidget(led_row_w)
        led_row = QHBoxLayout()
        self.led_spin = QSpinBox()
        self.led_spin.setRange(1, 500)
        led_row.addWidget(self.led_spin, stretch=1)
        self.led_btn = QPushButton(i18n.tr("set_count"))
        self.led_btn.setIcon(icons.icon("check"))
        self.led_btn.clicked.connect(self.on_set_leds)
        led_row.addWidget(self.led_btn)
        v.addLayout(led_row)

        v.addStretch(1)

        self.apply_all_btn = QPushButton(i18n.tr("apply_all"))
        self.apply_all_btn.setObjectName("accent")
        self.apply_all_btn.setIcon(icons.icon("layers"))
        self.apply_all_btn.clicked.connect(self.on_apply_all)
        v.addWidget(self.apply_all_btn)

        self.autostart_check = QCheckBox(i18n.tr("autostart"))
        self.autostart_check.setChecked(autostart.is_enabled())
        self.autostart_check.toggled.connect(self.on_autostart_toggled)
        v.addWidget(self.autostart_check)

        self.shortcut_btn = QPushButton(i18n.tr("shortcut_btn"))
        self.shortcut_btn.clicked.connect(self.on_create_shortcut)
        v.addWidget(self.shortcut_btn)

        self.hint_lbl = _label(i18n.tr("hint"), "hint")
        self.hint_lbl.setWordWrap(True)
        v.addWidget(self.hint_lbl)
        v.addStretch(1)
        scroll.setWidget(inner)
        outer.addWidget(scroll)
        return panel

    # ---------------------------------------------------------------- language

    def apply_language(self, lang):
        i18n.set_lang(lang)
        app = QApplication.instance()
        app.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if i18n.is_rtl()
            else Qt.LayoutDirection.LeftToRight
        )
        self.lang_btn.setText("EN" if i18n.is_rtl() else "فا")
        self._subtitle_lbl.setText(i18n.tr("app_subtitle"))
        self.master_on_btn.setText(i18n.tr("master_on"))
        self.master_off_btn.setText(i18n.tr("master_off"))
        self.reconnect_btn.setText(i18n.tr("reconnect"))
        self.wizard_btn.setText(i18n.tr("wizard_btn"))
        self.wizard_btn.setToolTip(i18n.tr("wizard_tip"))
        self._sec_effect.setText(i18n.tr("effect"))
        self._sec_color.setText(i18n.tr("color"))
        self._sec_speed.setText(i18n.tr("effect_speed"))
        self._sec_speed.setToolTip(i18n.tr("effect_speed_tip"))
        self._sec_bright.setText(i18n.tr("brightness"))
        self._sec_led.setText(i18n.tr("led_layout"))
        self.color_btn.setText(i18n.tr("choose_color"))
        self.led_btn.setText(i18n.tr("set_count"))
        self.apply_all_btn.setText(i18n.tr("apply_all"))
        self.autostart_check.setText(i18n.tr("autostart"))
        self.shortcut_btn.setText(i18n.tr("shortcut_btn"))
        self.enabled_check.setText(i18n.tr("enabled"))
        self.hint_lbl.setText(i18n.tr("hint"))
        self.effect_picker.refresh_texts()
        if self._current_cfg():
            self.speed_value.setText(str(int(self._current_cfg().speed)))
            self.bright_value.setText(
                f"{int(self._current_cfg().brightness * 100)}{i18n.tr('percent')}"
            )
        else:
            self.sel_zone.setText(i18n.tr("sel_none"))
        self._refresh_pill_after_lang()
        self._build_tray_menu()
        self.preview.update()

    def _refresh_pill_after_lang(self):
        if self.engine.connected:
            self._set_pill("ok", i18n.tr("connected_n", n=len(self.engine.devices_meta)))
        else:
            self._set_pill("warn", i18n.tr("status_connecting"))

    # ---------------------------------------------------------------- tray

    def _setup_tray(self):
        from PySide6.QtWidgets import QSystemTrayIcon
        self._tray_available = QSystemTrayIcon.isSystemTrayAvailable()
        self.tray = None
        if not self._tray_available:
            return
        self.tray = QSystemTrayIcon(icons.app_icon(), self)
        self.tray.setToolTip("ARGB Studio")
        self.tray.activated.connect(self._on_tray_activated)
        self._build_tray_menu()
        self.tray.show()

    def _build_tray_menu(self):
        if self.tray is None:
            return
        from PySide6.QtWidgets import QMenu
        menu = QMenu()
        show_act = QAction(i18n.tr("tray_show"), menu)
        show_act.triggered.connect(self._show_from_tray)
        on_act = QAction(i18n.tr("master_on"), menu)
        on_act.triggered.connect(self.on_master_on)
        off_act = QAction(i18n.tr("master_off"), menu)
        off_act.triggered.connect(self.on_master_off)
        exit_act = QAction(i18n.tr("tray_exit"), menu)
        exit_act.triggered.connect(self._exit_for_real)
        menu.addAction(show_act)
        menu.addSeparator()
        menu.addAction(on_act)
        menu.addAction(off_act)
        menu.addSeparator()
        menu.addAction(exit_act)
        self.tray.setContextMenu(menu)
        self._tray_menu = menu  # keep alive

    def _on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_ipc_connection(self):
        from PySide6.QtNetwork import QLocalSocket
        while self._ipc_server.hasPendingConnections():
            sock = self._ipc_server.nextPendingConnection()
            if sock is None:
                continue
            sock.readAll()
            sock.disconnectFromServer()
            self._show_from_tray()

    def _exit_for_real(self):
        self._really_quit = True
        self.close()

    # ---------------------------------------------------------------- slots

    def on_status(self, connected, message):
        self._set_pill("ok" if connected else "err", message)

    def on_backend_state(self, state):
        if state in ("already-running", "launched"):
            self._set_pill("warn", i18n.tr("status_connecting"))
            self.engine.connect_async()
        elif state == "notfound":
            self._set_pill("err", i18n.tr("status_notfound"))
        else:
            self._set_pill("err", i18n.tr("status_launch_failed"))

    def on_devices_loaded(self):
        if self.engine.devices_meta:
            self._connect_retries = 0
            if self.selected not in self.engine.config:
                self.selected = (0, 0)
        elif self._connect_retries < 6:
            self._connect_retries += 1
            self._set_pill("warn", i18n.tr("status_detecting"))
            QTimer.singleShot(3500, self.engine.connect_async)
            return
        self.sync_controls()
        self.preview.update()

    def on_zone_clicked(self, d, z):
        self.selected = (d, z)
        self.sync_controls()

    def on_effect_changed(self, eff):
        self._edit(effect=eff)

    def on_pick_color(self):
        cfg = self._current_cfg()
        start = QColor(*cfg.color) if cfg else QColor(138, 43, 226)
        color = QColorDialog.getColor(start, self, i18n.tr("color_dialog"))
        if color.isValid():
            self._set_swatch(color)
            self._edit(color=(color.red(), color.green(), color.blue()))

    def on_speed_changed(self, value):
        self.speed_value.setText(str(value))
        self._edit(speed=value)

    def on_brightness_changed(self, value):
        self.bright_value.setText(f"{value}{i18n.tr('percent')}")
        self._edit(brightness=value / 100.0)

    def on_enabled_toggled(self, checked):
        self._edit(enabled=checked)

    def on_set_leds(self):
        d, z = self.selected
        size = self.led_spin.value()
        self._set_pill("warn", i18n.tr("resizing"))
        self.engine.resize_zone(d, z, size)

    def on_apply_all(self):
        cfg = self._current_cfg()
        if not cfg:
            return
        for key in self.engine.config:
            self.engine.config[key] = copy.deepcopy(cfg)
        self.engine.save_state(STATE_PATH)

    def on_master_on(self):
        for cfg in self.engine.config.values():
            cfg.enabled = True
            if cfg.effect == effects.EFFECT_OFF:
                cfg.effect = effects.EFFECT_STATIC
                if cfg.color == (0, 0, 0):
                    cfg.color = (255, 255, 255)
        self.engine.save_state(STATE_PATH)
        self.sync_controls()

    def on_master_off(self):
        for cfg in self.engine.config.values():
            cfg.effect = effects.EFFECT_OFF
        self.engine.save_state(STATE_PATH)

    def on_autostart_toggled(self, checked):
        if checked:
            ok, msg = autostart.enable()
            if not ok:
                self.autostart_check.blockSignals(True)
                self.autostart_check.setChecked(False)
                self.autostart_check.blockSignals(False)
                self._set_pill("err", i18n.tr("autostart_failed", msg=msg))
        else:
            autostart.disable()

    def on_create_shortcut(self):
        """Create a desktop shortcut with the app icon (premium double-click)."""
        app_dir = Path(__file__).resolve().parent.parent
        try:
            ico_path = app_dir / "runtime" / "app.ico"
            ico_path.parent.mkdir(parents=True, exist_ok=True)
            if not icons.export_ico(ico_path):
                raise RuntimeError("ICO export failed")
            script_path = app_dir / "runtime" / "create_shortcut.ps1"
            script = (
                "$desktop = [Environment]::GetFolderPath('Desktop')\n"
                "$lnkPath = Join-Path $desktop 'ARGB Studio.lnk'\n"
                "$ws = New-Object -ComObject WScript.Shell\n"
                "$lnk = $ws.CreateShortcut($lnkPath)\n"
                f'$lnk.TargetPath = "{app_dir / "run.bat"}"\n'
                f'$lnk.WorkingDirectory = "{app_dir}"\n'
                f'$lnk.IconLocation = "{ico_path},0"\n'
                "$lnk.WindowStyle = 7\n"
                "$lnk.Save()\n"
                "Write-Output $lnkPath\n"
            )
            script_path.write_text(script, encoding="utf-8-sig")
            r = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-File", str(script_path)],
                capture_output=True, timeout=30, creationflags=0x08000000,
            )
            lnk = r.stdout.decode("utf-8", "ignore").strip() if r.stdout else ""
            if r.returncode == 0 and lnk and Path(lnk).exists():
                self._set_pill("ok", i18n.tr("shortcut_ok"))
            else:
                err = (r.stderr or b"?").decode("utf-8", "ignore").strip()[:120]
                self._set_pill("err", i18n.tr("shortcut_failed", err=err))
        except Exception as exc:  # noqa: BLE001
            self._set_pill("err", i18n.tr("shortcut_failed", err=exc))

    # ---------------------------------------------------------------- wizard

    def on_setup_wizard(self):
        targets = []
        for di, dev in enumerate(self.engine.devices_meta):
            for zi, zone in enumerate(dev["zones"]):
                if zone["leds"] == 0:
                    targets.append((di, zi))
        if not targets:
            QMessageBox.information(self, i18n.tr("wiz_ask_title"), i18n.tr("wiz_all_done"))
            return
        self._wizard_targets = targets
        self._wizard_idx = 0
        self._wizard_next()

    def _wizard_next(self):
        if self._wizard_idx >= len(self._wizard_targets):
            self.engine.save_state(STATE_PATH)
            self.sync_controls()
            self.preview.update()
            QMessageBox.information(
                self, i18n.tr("wiz_ask_title"), i18n.tr("wiz_done")
            )
            return
        di, zi = self._wizard_targets[self._wizard_idx]
        name = f"{self.engine.devices_meta[di]['name']} › {self.engine.devices_meta[di]['zones'][zi]['name']}"
        cfg = self.engine.config[(di, zi)]
        cfg.enabled = True
        cfg.effect = effects.EFFECT_STATIC
        cfg.color = (255, 170, 0)
        cfg.brightness = 0.9
        self.engine.resize_zone(di, zi, 16)
        self.preview.set_selected((di, zi))
        QTimer.singleShot(1500, lambda: self._wizard_ask(di, zi, name))

    def _wizard_ask(self, di, zi, name):
        n = self.engine.devices_meta[di]["zones"][zi]["leds"]
        msg = QMessageBox(self)
        msg.setWindowTitle(i18n.tr("wiz_ask_title"))
        msg.setText(i18n.tr("wiz_ask", name=name, n=n))
        yes = msg.addButton(i18n.tr("wiz_yes"), QMessageBox.ButtonRole.YesRole)
        msg.addButton(i18n.tr("wiz_no"), QMessageBox.ButtonRole.NoRole)
        msg.exec()
        cfg = self.engine.config[(di, zi)]
        if msg.clickedButton() is yes:
            cfg.effect = effects.EFFECT_RAINBOW
            cfg.color = (138, 43, 226)
        else:
            self.engine.resize_zone(di, zi, 0)
            cfg.enabled = False
            cfg.effect = effects.EFFECT_OFF
        self._wizard_idx += 1
        QTimer.singleShot(700, self._wizard_next)

    # ---------------------------------------------------------------- helpers

    def _current_cfg(self):
        return self.engine.config.get(self.selected)

    def _edit(self, **changes):
        cfg = self._current_cfg()
        if not cfg:
            return
        for name, value in changes.items():
            setattr(cfg, name, value)
        self.engine.save_state(STATE_PATH)

    def _set_swatch(self, color: QColor):
        self.color_btn.setStyleSheet(
            f"background: {color.name()}; border: 1px solid {theme.BORDER2};"
            "border-radius: 10px; color: white; font-weight: 700; min-height: 44px;"
        )

    def sync_controls(self):
        cfg = self._current_cfg()
        if not cfg:
            self.sel_dev.setText("")
            self.sel_zone.setText(i18n.tr("sel_none"))
            return
        d, z = self.selected
        meta = self.engine.devices_meta[d]["zones"][z]
        self.sel_dev.setText(self.engine.devices_meta[d]["name"])
        self.sel_zone.setText(meta["name"])
        self.preview.set_selected(self.selected)

        self.effect_picker.set_effect(cfg.effect)
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(int(cfg.speed))
        self.speed_slider.blockSignals(False)
        self.speed_value.setText(str(int(cfg.speed)))
        self.bright_slider.blockSignals(True)
        self.bright_slider.setValue(int(cfg.brightness * 100))
        self.bright_slider.blockSignals(False)
        self.bright_value.setText(f"{int(cfg.brightness * 100)}{i18n.tr('percent')}")
        self.enabled_check.blockSignals(True)
        self.enabled_check.setChecked(cfg.enabled)
        self.enabled_check.blockSignals(False)
        self.led_spin.blockSignals(True)
        self.led_spin.setValue(meta["leds"] if meta["leds"] > 0 else 12)
        self.led_spin.blockSignals(False)
        self._set_swatch(QColor(*cfg.color))

    def _on_tick(self):
        self.engine.tick()
        self.preview.update()

    def closeEvent(self, event):
        # Close-to-tray: keep running next to the clock like other RGB apps.
        if not self._really_quit and self._tray_available:
            event.ignore()
            self.hide()
            if not self._tray_notified:
                self.tray.showMessage(
                    "ARGB Studio",
                    i18n.tr("tray_hidden"),
                    QSystemTrayIcon.MessageIcon.Information,
                    3000,
                )
                self._tray_notified = True
            return
        self.engine.sender.close()
        self.backend.shutdown()
        if self.tray is not None:
            self.tray.hide()
        try:
            self.engine.save_state(STATE_PATH)
        except OSError:
            pass
        super().closeEvent(event)


def _enable_dark_titlebar(win):
    """Windows: match the OS title bar to the dark theme."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = int(win.winId())
        value = ctypes.c_int(1)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (19 on older builds)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(value), ctypes.sizeof(value)
            ) == 0:
                break
    except Exception:
        pass


def _poke_running_instance() -> bool:
    """Ask the already-running instance (over a named pipe) to show itself."""
    from PySide6.QtNetwork import QLocalSocket
    sock = QLocalSocket()
    sock.connectToServer("ARGBStudio")
    if not sock.waitForConnected(500):
        return False
    sock.write(b"show")
    sock.flush()
    sock.waitForBytesWritten(500)
    sock.disconnectFromServer()
    return True


def launch():
    lock = acquire_lock()
    if lock is None:
        # Another instance runs: pop its window up via IPC.
        if not _poke_running_instance() and not surface_existing_window():
            app = QApplication(sys.argv)
            QMessageBox.information(None, "ARGB Studio", i18n.tr("single_instance"))
        return
    i18n.load_lang()
    app = QApplication(sys.argv)
    app._lock = lock  # keep the single-instance lock alive
    app.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if i18n.is_rtl()
        else Qt.LayoutDirection.LeftToRight
    )
    theme.apply_theme(app)
    app.setWindowIcon(icons.app_icon())
    window = MainWindow()
    window.show()
    _enable_dark_titlebar(window)
    sys.exit(app.exec())
