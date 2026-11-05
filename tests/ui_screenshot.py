"""Render the UI offscreen with fake data in BOTH languages for design QA.

Run from argb-studio/:  .venv/Scripts/python tests/ui_screenshot.py
"""

import os
import sys
from pathlib import Path

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app import effects, i18n, theme  # noqa: E402
from app.engine import ZoneConfig  # noqa: E402
from app.main_window import MainWindow, OpenRGBManager  # noqa: E402


def fake_data(w):
    w.engine.devices_meta = [
        {
            "name": "ASUS TUF GAMING A620M-PLUS WIFI",
            "type": "MOTHERBOARD",
            "zones": [
                {"name": "Aura Mainboard", "leds": 1},
                {"name": "Addressable RGB Header 1", "leds": 24},
                {"name": "Addressable RGB Header 2", "leds": 16},
                {"name": "Addressable RGB Header 3", "leds": 0},
            ],
        },
        {
            "name": "Mock USB Controller",
            "type": "LEDSTRIP",
            "zones": [{"name": "Strip", "leds": 30}],
        },
    ]
    cfgs = {
        (0, 0): ZoneConfig(effect=effects.EFFECT_STATIC, color=(138, 43, 226)),
        (0, 1): ZoneConfig(effect=effects.EFFECT_RAINBOW, speed=4, brightness=0.85),
        (0, 2): ZoneConfig(effect=effects.EFFECT_BREATHING, color=(0, 120, 255)),
        (0, 3): ZoneConfig(effect=effects.EFFECT_OFF),
        (1, 0): ZoneConfig(effect=effects.EFFECT_WAVE, color=(255, 60, 0)),
    }
    led_counts = {(0, 0): 1, (0, 1): 24, (0, 2): 16, (0, 3): 0, (1, 0): 30}
    w.engine.config = cfgs
    for key, cfg in cfgs.items():
        n = led_counts[key]
        w.engine.frames[key] = (
            effects.compute_frame(
                cfg.effect, cfg.color, cfg.speed, cfg.brightness, n, 1.3, key[0] * 7
            )
            if n
            else []
        )
    w.on_devices_loaded()
    w.on_status(True, i18n.tr("connected_n", n=2))
    w.selected = (0, 1)
    w.sync_controls()


def main():
    OpenRGBManager.ensure_running_async = lambda self, wait_for_port=30.0: None

    settings_backup = None
    if i18n.SETTINGS_PATH.exists():
        settings_backup = i18n.SETTINGS_PATH.read_text(encoding="utf-8")

    app = QApplication([])
    theme.apply_theme(app)

    w = MainWindow()
    fake_data(w)
    w.resize(1150, 780)
    w.show()
    app.processEvents()

    out_dir = Path(__file__).resolve().parent

    for lang in ("fa", "en"):
        i18n.set_lang(lang)
        app.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft if lang == "fa"
            else Qt.LayoutDirection.LeftToRight
        )
        w.apply_language(lang)
        app.processEvents()
        out = out_dir / f"ui_preview_{lang}.png"
        w.grab().save(str(out))
        print("saved:", out)

    if settings_backup is not None:
        i18n.SETTINGS_PATH.write_text(settings_backup, encoding="utf-8")
    elif i18n.SETTINGS_PATH.exists():
        i18n.SETTINGS_PATH.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
