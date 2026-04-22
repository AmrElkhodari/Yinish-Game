# In ui/piece_item.py
from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QColor, QPen, QBrush, QPainterPath
from PySide6.QtCore import Qt


class MarkerItem(QGraphicsEllipseItem):
    # --- NEW: Added q, r, and callback so they can be clicked! ---
    def __init__(self, q, r, color_str, click_callback, size=20):
        super().__init__()
        self.q = q
        self.r = r
        self.size = size
        self.current_color = color_str
        self.click_callback = click_callback

        self.setRect(-self.size / 2, -self.size / 2, self.size, self.size)
        self.setZValue(1)
        self._update_visuals()

        # Make it clickable
        self.setAcceptHoverEvents(True)

    def _update_visuals(self):
        if self.current_color == 'red':
            base_color = QColor("#EF5350")
            border_color = QColor("#B71C1C")
        else:
            base_color = QColor("#29B6F6")
            border_color = QColor("#01579B")

        self.setBrush(QBrush(base_color))
        self.setPen(QPen(border_color, 2))

    def flip(self):
        self.current_color = 'blue' if self.current_color == 'red' else 'red'
        self._update_visuals()
        self.update()

    def mousePressEvent(self, event):
        if self.click_callback:
            self.click_callback(self)
        event.accept()


class RingItem(QGraphicsEllipseItem):
    def __init__(self, q, r, color_str, click_callback, size=36):
        super().__init__()
        self.q = q
        self.r = r
        self.size = size
        self.color_str = color_str
        self.click_callback = click_callback
        self.is_selected = False

        self.setRect(-self.size / 2, -self.size / 2, self.size, self.size)
        self.setZValue(2)

        if self.color_str == 'red':
            self.base_color = QColor("#EF5350")
        else:
            self.base_color = QColor("#29B6F6")

        self.base_pen = QPen(self.base_color, 6)
        self.selected_pen = QPen(QColor("#FFD54F"), 8)

        self.setPen(self.base_pen)
        self.setBrush(QBrush(Qt.GlobalColor.transparent))
        self.setAcceptHoverEvents(True)

    def set_selected(self, selected):
        self.is_selected = selected
        if self.is_selected:
            self.setPen(self.selected_pen)
        else:
            self.setPen(self.base_pen)

    def hoverEnterEvent(self, event):
        if not self.is_selected:
            self.setPen(QPen(self.base_color, 8))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.is_selected:
            self.setPen(self.base_pen)
        super().hoverLeaveEvent(event)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.rect())
        return path

    def boundingRect(self):
        padding = 6
        return self.rect().adjusted(-padding, -padding, padding, padding)

    def mousePressEvent(self, event):
        self.click_callback(self)
        event.accept()