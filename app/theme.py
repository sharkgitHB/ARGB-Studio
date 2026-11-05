"""Design system: palette, bundled Persian font (Vazirmatn) and the global QSS."""

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
)

ASSETS = Path(__file__).resolve().parent / "assets"

# ---------------------------------------------------------------- palette
BG = "#131318"        # window background
SURFACE = "#18181f"   # cards / panels
SURFACE2 = "#22222b"  # inputs
BORDER = "#26262f"
BORDER2 = "#33333f"
ACCENT = "#6d4aff"    # violet
ACCENT_HOVER = "#7d5cff"
TEXT = "#e8e8f0"
DIM = "#8f8fa3"
GREEN = "#3ecf6f"
RED = "#e05555"
AMBER = "#f0ad4e"

_FONT_FAMILY = "Segoe UI"  # fallback if bundled font fails to load


def apply_theme(app):
    """Load bundled fonts and set the global stylesheet. Call before any widget."""
    for name in ("Vazirmatn-Regular.ttf", "Vazirmatn-Bold.ttf"):
        path = ASSETS / "fonts" / name
        if path.exists():
            fid = QFontDatabase.addApplicationFont(str(path))
            families = QFontDatabase.applicationFontFamilies(fid)
            if families:
                global _FONT_FAMILY
                _FONT_FAMILY = families[0]
    app.setFont(QFont(_FONT_FAMILY, 10))
    app.setStyleSheet(build_stylesheet())
    return _FONT_FAMILY


def font_family():
    return _FONT_FAMILY


def _arrow_png(path: Path, up: bool, w=12, h=8):
    """Render a small triangle (Qt QSS can't do border-tricks for arrows)."""
    img = QImage(w * 3, h * 3, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(Qt.PenStyle.NoPen))
    p.setBrush(QColor(DIM))
    if up:
        pts = [QPointF(1.5, 6.5), QPointF(10.5, 6.5), QPointF(6.0, 1.5)]
    else:
        pts = [QPointF(1.5, 1.5), QPointF(10.5, 1.5), QPointF(6.0, 6.5)]
    p.drawPolygon(pts)
    p.end()
    img.save(str(path))


def _arrow_assets():
    """Generate arrow/checkmark PNGs once; return url()-ready posix paths."""
    gen = ASSETS / "gen"
    gen.mkdir(parents=True, exist_ok=True)
    down, up = gen / "arrow-down.png", gen / "arrow-up.png"
    if not down.exists():
        _arrow_png(down, up=False)
    if not up.exists():
        _arrow_png(up, up=True)
    check = gen / "check.png"
    if not check.exists():
        img = QImage(28, 26, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor("#ffffff"))
        pen.setWidthF(4.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        path = QPainterPath()
        path.moveTo(5, 14)
        path.lineTo(11, 20)
        path.lineTo(23, 5)
        p.drawPath(path)
        p.end()
        img.save(str(check))
    return down.as_posix(), up.as_posix(), check.as_posix()


def build_stylesheet() -> str:
    arrow_down, arrow_up, check_png = _arrow_assets()
    return f"""
    * {{ outline: none; }}
    QWidget {{ font-family: '{_FONT_FAMILY}'; font-size: 10pt; color: {TEXT}; }}
    QMainWindow, QDialog {{ background: {BG}; }}
    QToolTip {{ background: {SURFACE2}; color: {TEXT}; border: 1px solid {BORDER2};
                padding: 4px 8px; border-radius: 6px; }}

    /* ---------- header ---------- */
    #header {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1c1726, stop:1 {SURFACE});
        border-bottom: 1px solid {BORDER};
    }}
    #accentStrip {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:0.55 #8f6bff, stop:1 #22d3ee);
    }}
    #logoDot {{
        min-width: 16px; max-width: 16px; min-height: 16px; max-height: 16px;
        border-radius: 8px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8f6bff, stop:1 #22d3ee);
    }}
    #title {{ font-size: 17px; font-weight: 800; color: {ACCENT_HOVER}; }}
    #subtitle {{ color: {DIM}; font-size: 12px; }}
    QLabel#statusPill {{ border-radius: 12px; padding: 4px 14px; font-weight: 600;
                         font-size: 12px; }}

    /* ---------- context menus (tray fix: native menu is white) ---------- */
    QMenu {{
        background: {SURFACE2}; color: {TEXT};
        border: 1px solid {BORDER2}; border-radius: 10px; padding: 6px;
    }}
    QMenu::item {{ padding: 8px 26px; border-radius: 6px; background: transparent; }}
    QMenu::item:selected {{ background: {ACCENT}; color: white; }}
    QMenu::item:disabled {{ color: {DIM}; }}
    QMenu::separator {{ height: 1px; background: {BORDER2}; margin: 5px 8px; }}

    /* ---------- buttons ---------- */
    QPushButton {{
        background: {SURFACE2}; color: {TEXT};
        border: 1px solid {BORDER2}; border-radius: 8px;
        padding: 9px 16px; min-height: 22px;
    }}
    QPushButton:hover {{ background: #2b2b36; }}
    QPushButton:pressed {{ background: #1d1d25; }}
    QPushButton:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7d5cff, stop:1 #5b2ee0);
        border-color: {ACCENT}; color: white; font-weight: 700;
    }}
    QPushButton:checked:hover {{ background: {ACCENT_HOVER}; }}
    QPushButton:disabled {{ color: {DIM}; background: {SURFACE}; }}
    QPushButton#accent {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7d5cff, stop:1 #5b2ee0);
        border: none; color: white; font-weight: 700;
    }}
    QPushButton#accent:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8d6fff, stop:1 #6a3ef0);
    }}
    QPushButton#accent:pressed {{ background: #5b3ce0; }}
    QPushButton#danger {{
        background: transparent; color: {RED}; border: 1px solid #4a2a2a;
    }}
    QPushButton#danger:hover {{ background: #2a1d1d; }}
    QPushButton#swatch {{
        border: 1px solid {BORDER2}; border-radius: 10px; color: white;
        font-weight: 700; min-height: 44px;
    }}

    /* ---------- inputs ---------- */
    QComboBox {{
        background: {SURFACE2}; color: {TEXT}; border: 1px solid {BORDER2};
        border-radius: 8px; padding: 7px 12px; min-height: 22px;
    }}
    QComboBox:hover {{ border-color: #444452; }}
    QComboBox::drop-down {{ border: none; width: 28px; }}
    QComboBox::down-arrow {{ image: url('{arrow_down}'); width: 12px; height: 8px; }}
    QComboBox QAbstractItemView {{
        background: {SURFACE2}; color: {TEXT}; border: 1px solid {BORDER2};
        selection-background-color: {ACCENT}; selection-color: white; outline: none;
        padding: 4px;
    }}
    QSpinBox {{
        background: {SURFACE2}; color: {TEXT}; border: 1px solid {BORDER2};
        border-radius: 8px; padding: 6px 12px; min-height: 22px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        width: 20px; border: none; background: transparent;
    }}
    QSpinBox::up-arrow {{ image: url('{arrow_up}'); width: 10px; height: 7px; }}
    QSpinBox::down-arrow {{ image: url('{arrow_down}'); width: 10px; height: 7px; }}
    QSlider {{ min-height: 26px; }}
    QSlider::groove:horizontal {{ height: 6px; background: #2c2c38; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
    QSlider::handle:horizontal {{
        width: 16px; height: 16px; margin: -6px 0; border-radius: 8px;
        background: #f0f0f6; border: 2px solid {ACCENT};
    }}
    QSlider::handle:hover {{ background: #ffffff; }}

    QCheckBox {{ spacing: 9px; color: {TEXT}; }}
    QCheckBox::indicator {{
        width: 19px; height: 19px; border-radius: 6px;
        border: 1px solid #3a3a48; background: {SURFACE2};
    }}
    QCheckBox::indicator:hover {{ border-color: {ACCENT}; }}
    QCheckBox::indicator:checked {{
        background: {ACCENT}; border-color: {ACCENT}; image: url('{check_png}');
    }}

    /* ---------- panels / scroll ---------- */
    #panel {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
    #previewHost {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 12px; }}
    QLabel#sectionLabel {{ color: {DIM}; font-size: 11px; font-weight: 700; }}
    QLabel#valueLabel {{ color: #b9b9c9; font-size: 12px; }}
    QLabel#hint {{ color: {DIM}; font-size: 11px; }}

    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
    QScrollBar::handle:vertical {{ background: {BORDER2}; border-radius: 4px; min-height: 30px; }}
    QScrollBar::handle:vertical:hover {{ background: #44444f; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    """
