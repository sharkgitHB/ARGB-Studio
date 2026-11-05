"""Live LED preview: every device/zone is a card with a row of LED dots.

Click a card to select that zone for editing. Frame colors come straight from
Engine.frames (computed by the 30 fps tick), so the preview stays in sync with
what is actually being sent to the hardware.
"""

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from . import i18n, theme

PAD = 12.0
DEV_H = 17.0     # small dim device-name line
ZONE_H = 23.0    # bold zone-name line
DOT_MIN = 7.0
DOT_MAX = 20.0
GAP = 10.0


class PreviewWidget(QWidget):
    zone_clicked = Signal(int, int)  # device_idx, zone_idx

    def __init__(self, engine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.selected = (0, 0)
        self._hover = None
        self._row_rects = {}  # (d, z) -> QRectF
        self.setMinimumHeight(160)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # ---------------------------------------------------------------- selection

    def set_selected(self, key):
        self.selected = key
        self.update()

    def mousePressEvent(self, event):
        pos = event.position()
        for key, rect in self._row_rects.items():
            if rect.contains(pos):
                self.selected = key
                self.zone_clicked.emit(*key)
                self.update()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position()
        hover = None
        for key, rect in self._row_rects.items():
            if rect.contains(pos):
                hover = key
                break
        if hover != self._hover:
            self._hover = hover
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover = None
        self.update()
        super().leaveEvent(event)

    # ---------------------------------------------------------------- painting

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Stage-like backdrop: subtle glow from the top center.
        grad = QRadialGradient(self.width() * 0.5, -self.height() * 0.3, self.width() * 1.4)
        grad.setColorAt(0.0, QColor("#1d1a30"))
        grad.setColorAt(1.0, QColor(theme.BG))
        painter.fillRect(self.rect(), grad)

        self._row_rects = {}
        meta = self.engine.devices_meta
        if not meta:
            self._paint_empty(painter)
            return

        width = float(self.width())
        y = PAD
        for di, dev in enumerate(meta):
            for zi, zone in enumerate(dev["zones"]):
                n = zone["leds"]
                key = (di, zi)
                row_h = DEV_H + ZONE_H + (DOT_MAX + 12.0 if n else 10.0) + PAD
                rect = QRectF(PAD, y, width - 2 * PAD, row_h)
                self._row_rects[key] = rect
                self._paint_card(painter, key, dev, zone, rect)
                y += row_h + GAP

        self.setMinimumHeight(int(y + PAD))

    def _paint_empty(self, painter):
        painter.setPen(QColor(theme.ACCENT_HOVER))
        f = QFont(theme.font_family(), 13)
        f.setBold(True)
        painter.setFont(f)
        painter.drawText(
            self.rect().adjusted(0, -40, 0, -40),
            Qt.AlignmentFlag.AlignCenter,
            i18n.tr("empty_title"),
        )
        painter.setPen(QColor(theme.DIM))
        f2 = QFont(theme.font_family(), 10)
        painter.setFont(f2)
        painter.drawText(
            self.rect().adjusted(0, 10, 0, 10),
            Qt.AlignmentFlag.AlignCenter,
            i18n.tr("empty_body"),
        )

    def _paint_card(self, painter, key, dev, zone, rect):
        selected = key == self.selected
        hovered = key == self._hover
        if selected:
            # Soft glow around the selected card.
            glow = QPainterPath()
            glow.addRoundedRect(rect.adjusted(-2.5, -2.5, 2.5, 2.5), 12, 12)
            painter.setPen(QPen(QColor(109, 74, 255, 70), 6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(glow)
            painter.setPen(QPen(QColor(theme.ACCENT), 2))
            painter.setBrush(QColor("#231c36"))
        elif hovered:
            painter.setPen(QPen(QColor("#3d3d4d"), 1))
            painter.setBrush(QColor("#20202a"))
        else:
            painter.setPen(QPen(QColor(theme.BORDER), 1))
            painter.setBrush(QColor("#1b1b23"))
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)
        painter.drawPath(path)

        n = zone["leds"]
        title_w = rect.width() - 28 - 80  # leave room for the LED-count chip

        # Line 1: device name (small, dim).
        painter.setPen(QColor(theme.DIM))
        painter.setFont(QFont(theme.font_family(), 8))
        dev_name = QFontMetrics(painter.font()).elidedText(
            dev["name"], Qt.TextElideMode.ElideLeft, title_w
        )
        painter.drawText(
            QRectF(rect.left() + 14, rect.top() + 6, title_w, DEV_H),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            dev_name,
        )

        # Line 2: zone name (bold).
        painter.setPen(QColor("#e0e0ea") if selected else QColor("#c5c5d2"))
        f = QFont(theme.font_family(), 11)
        f.setBold(True)
        painter.setFont(f)
        zone_name = QFontMetrics(painter.font()).elidedText(
            zone["name"], Qt.TextElideMode.ElideRight, title_w
        )
        painter.drawText(
            QRectF(rect.left() + 14, rect.top() + 6 + DEV_H, title_w, ZONE_H),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            zone_name,
        )

        # LED count chip on the opposite side.
        painter.setFont(QFont(theme.font_family(), 9))
        if n:
            painter.setPen(QColor(theme.DIM))
            painter.drawText(
                rect.adjusted(14, 0, -14, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                f"{n} LED",
            )
        else:
            painter.setPen(QColor(theme.AMBER))
            painter.drawText(
                rect.adjusted(14, 0, -14, 0),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                i18n.tr("not_configured"),
            )

        if n:
            self._paint_dots(painter, key, n, rect)

    def _paint_dots(self, painter, key, n, rect):
        area_w = rect.width() - 28
        dot = max(DOT_MIN, min(DOT_MAX, area_w / max(n, 1) - 2.0))
        spacing = area_w / max(n, 1)
        x0 = rect.left() + 14
        y_center = rect.top() + DEV_H + ZONE_H + (rect.height() - DEV_H - ZONE_H) / 2

        frame = self.engine.frames.get(key)
        cfg = self.engine.config.get(key)
        for i in range(n):
            if frame and i < len(frame):
                r, g, b = frame[i]
            else:
                r, g, b = (0, 0, 0)
            x = x0 + i * spacing + (spacing - dot) / 2
            if (r, g, b) == (0, 0, 0) and cfg is not None and cfg.enabled:
                color = QColor("#2b2b34")  # keep off LEDs visible
                painter.setPen(QPen(QColor("#3a3a45"), 1))
                painter.setBrush(color)
                painter.drawEllipse(x, y_center - dot / 2, dot, dot)
                continue
            color = QColor(r, g, b)
            # Light bloom behind lit LEDs (skipped for very long strips).
            if n <= 64:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(r, g, b, 75))
                painter.drawEllipse(
                    x - dot * 0.35, y_center - dot * 0.85, dot * 1.7, dot * 1.7
                )
            painter.setPen(QPen(color.darker(160), 1))
            painter.setBrush(color)
            painter.drawEllipse(x, y_center - dot / 2, dot, dot)
            # Specular highlight -> reads as a physical LED.
            painter.setBrush(QColor(255, 255, 255, 60))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                x + dot * 0.18, y_center - dot * 0.32, dot * 0.3, dot * 0.3
            )
