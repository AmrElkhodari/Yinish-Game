# In ui/node_item.py
from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QColor, QPen, QBrush
from PySide6.QtCore import Qt


class NodeItem(QGraphicsEllipseItem):
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

        # --- NEW: Highlight Dot ---
        self.highlight_brush = QBrush(QColor("#FFD54F"))  # Golden dot for valid move

        self.setPen(self.default_pen)
        self.setBrush(self.default_brush)
        self.setAcceptHoverEvents(True)

    # --- NEW: Toggles the valid move indicator ---
    def set_highlight(self, active):
        if active:
            # Draw a solid center dot
            self.setPen(self.default_pen)
            self.setBrush(self.highlight_brush)
        else:
            self.setPen(self.default_pen)
            self.setBrush(self.default_brush)

    def hoverEnterEvent(self, event):
        # Only apply hover effect if it's not currently highlighted as a valid move
        if self.brush() != self.highlight_brush:
            self.setPen(self.hover_pen)
            self.setBrush(self.hover_brush)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if self.brush() != self.highlight_brush:
            self.setPen(self.default_pen)
            self.setBrush(self.default_brush)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        self.click_callback(self)
        event.accept()