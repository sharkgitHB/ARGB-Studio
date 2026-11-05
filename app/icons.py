"""Programmatically drawn vector-style icons (24x24 design grid, QPainter).

No external assets or dependencies: every icon is crisp at any DPI because it
is rendered from geometry at the requested size.
"""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)

_CACHE = {}

DEFAULT_COLOR = "#e8e8f0"


def _pen(color, width=2.0):
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def _line(p, x1, y1, x2, y2):
    p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _bolt(p, color):
    p.setPen(_pen(color, 1.2))
    p.setBrush(QColor(color))
    p.drawPolygon(QPolygonF([
        QPointF(13.5, 1.5), QPointF(4.5, 13.5), QPointF(11, 13.5),
        QPointF(10, 22.5), QPointF(19.5, 10), QPointF(12.8, 10),
    ]))


def _power(p, color):
    p.setPen(_pen(color))
    p.drawArc(QRectF(5, 5.5, 14, 14), 115 * 16, 310 * 16)
    _line(p, 12, 2.5, 12, 10.5)


def _refresh(p, color):
    p.setPen(_pen(color))
    r = QRectF(4.5, 4.5, 15, 15)
    p.drawArc(r, 105 * 16, 310 * 16)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(13.2, 0.9), QPointF(20.3, 3.1), QPointF(15.2, 8.2),
    ]))


def _globe(p, color):
    p.setPen(_pen(color))
    p.drawEllipse(QRectF(4, 4, 16, 16))
    p.drawEllipse(QRectF(9.2, 4, 5.6, 16))
    _line(p, 4, 12, 20, 12)


def _wave(p, color):
    p.setPen(_pen(color))
    path = QPainterPath()
    path.moveTo(2, 12)
    path.cubicTo(5.5, 2, 8.5, 22, 12, 12)
    path.cubicTo(15.5, 2, 18.5, 22, 22, 12)
    p.drawPath(path)


def _droplet(p, color):
    p.setPen(_pen(color))
    path = QPainterPath()
    path.moveTo(12, 2.8)
    path.cubicTo(15.5, 8.5, 18.8, 11.2, 18.8, 14.6)
    path.cubicTo(18.8, 18.6, 15.8, 21.3, 12, 21.3)
    path.cubicTo(8.2, 21.3, 5.2, 18.6, 5.2, 14.6)
    path.cubicTo(5.2, 11.2, 8.5, 8.5, 12, 2.8)
    p.drawPath(path)


def _gauge(p, color):
    p.setPen(_pen(color))
    p.drawArc(QRectF(4, 4.5, 16, 16), 0, 180 * 16)
    _line(p, 12, 12.5, 17, 7.5)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(QRectF(10.9, 11.4, 2.2, 2.2))


def _sun(p, color):
    p.setPen(_pen(color))
    p.drawEllipse(QRectF(9, 9, 6, 6))
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0),
                   (-0.707, -0.707), (0.707, -0.707),
                   (-0.707, 0.707), (0.707, 0.707)):
        _line(p, 12 + dx * 8.6, 12 + dy * 8.6, 12 + dx * 11.2, 12 + dy * 11.2)


def _mixer(p, color):
    p.setPen(_pen(color))
    _line(p, 4, 6, 20, 6)
    _line(p, 4, 12, 20, 12)
    _line(p, 4, 18, 20, 18)
    p.setBrush(QColor("#18181f"))
    for cx, cy in ((9, 6), (15.5, 12), (7, 18)):
        p.drawEllipse(QRectF(cx - 2.4, cy - 2.4, 4.8, 4.8))


def _check(p, color):
    p.setPen(_pen(color, 2.6))
    path = QPainterPath()
    path.moveTo(4.5, 12.5)
    path.lineTo(10, 18)
    path.lineTo(19.5, 6)
    p.drawPath(path)


def _layers(p, color):
    p.setPen(_pen(color))
    p.setBrush(Qt.BrushStyle.NoBrush)
    poly = QPolygonF([
        QPointF(12, 2.5), QPointF(21, 7.5), QPointF(12, 12.5), QPointF(3, 7.5),
    ])
    p.drawPolygon(poly)
    _line(p, 3, 12, 12, 17)
    _line(p, 21, 12, 12, 17)
    _line(p, 3, 16.5, 12, 21.5)
    _line(p, 21, 16.5, 12, 21.5)


def _wand(p, color):
    p.setPen(_pen(color))
    _line(p, 4, 20.5, 14.5, 10)
    _line(p, 17.5, 1.8, 17.5, 6.8)
    _line(p, 15, 4.3, 20, 4.3)
    _line(p, 6.5, 3.5, 6.5, 7)
    _line(p, 4.75, 5.25, 8.25, 5.25)
    _line(p, 20.5, 10.5, 20.5, 13)
    _line(p, 19.25, 11.75, 21.75, 11.75)


def _monitor_bolt(p, color):
    p.setPen(_pen(color))
    p.drawRoundedRect(QRectF(3, 4, 18, 12.5), 2, 2)
    _line(p, 9, 21, 15, 21)
    _line(p, 12, 16.5, 12, 21)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawPolygon(QPolygonF([
        QPointF(12.6, 6), QPointF(9.6, 11), QPointF(11.6, 11),
        QPointF(11, 14.5), QPointF(14.6, 9.4), QPointF(12.5, 9.4),
        QPointF(13.4, 6),
    ]))


_DRAWERS = {
    "bolt": _bolt,
    "power": _power,
    "refresh": _refresh,
    "globe": _globe,
    "wave": _wave,
    "droplet": _droplet,
    "gauge": _gauge,
    "sun": _sun,
    "mixer": _mixer,
    "check": _check,
    "layers": _layers,
    "wand": _wand,
    "monitor_bolt": _monitor_bolt,
}


def pixmap(name, color=DEFAULT_COLOR, size=16):
    """Render one icon as a crisp QPixmap at the requested logical size."""
    key = (name, color, size)
    if key in _CACHE:
        return _CACHE[key]
    dpr = 3.0
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.scale(size * dpr / 24.0, size * dpr / 24.0)
    p.setBrush(Qt.BrushStyle.NoBrush)
    _DRAWERS[name](p, color)
    p.end()
    pm.setDevicePixelRatio(dpr)
    _CACHE[key] = pm
    return pm


def icon(name, color=DEFAULT_COLOR, size=16):
    return QIcon(pixmap(name, color, size))


def app_icon():
    """Rounded-square gradient app/tray icon with a bolt."""
    pm = QPixmap(256, 256)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    grad = QLinearGradient(0, 0, 256, 256)
    grad.setColorAt(0.0, QColor("#8f6bff"))
    grad.setColorAt(1.0, QColor("#4b23c8"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(grad)
    p.drawRoundedRect(QRectF(16, 16, 224, 224), 56, 56)
    p.setBrush(QColor("#ffffff"))
    bolt = QPolygonF([
        QPointF(148, 44), QPointF(76, 148), QPointF(122, 148),
        QPointF(110, 216), QPointF(184, 112), QPointF(134, 112),
    ])
    p.drawPolygon(bolt)
    p.end()
    return QIcon(pm)


def export_ico(path) -> bool:
    """Save the app icon as a Windows .ico (for shortcuts)."""
    return app_icon().pixmap(256, 256).save(str(path), "ICO")
