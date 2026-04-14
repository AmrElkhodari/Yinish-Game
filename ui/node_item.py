# In ui/node_item.py
from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtCore import Qt


class NodeItem(QGraphicsEllipseItem):
    # Added 'click_callback'
    def __init__(self, q, r, click_callback, size=15):
        super().__init__()
        self.q = q
        self.r = r
        self.size = size
        self.click_callback = click_callback

        self.setRect(-self.size / 2, -self.size / 2, self.size, self.size)

        self.default_pen = QPen(Qt.GlobalColor.transparent)
        self.default_brush = QBrush(Qt.GlobalColor.transparent)

        self.hover_pen = QPen(QColor("#80CBC4"), 2)
        self.hover_brush = QBrush(Qt.GlobalColor.transparent)

        self.setPen(self.default_pen)
        self.setBrush(self.default_brush)
        self.setAcceptHoverEvents(True)

    def hoverEnterEvent(self, event):
        self.setPen(self.hover_pen)
        self.setBrush(self.hover_brush)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(self.default_pen)
        self.setBrush(self.default_brush)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        # Tell the board this node was clicked
        self.click_callback(self)

        # Stop the click from passing through the board
        event.accept()