from PySide6.QtWidgets import QGraphicsEllipseItem
from PySide6.QtGui import QColor, QPen, QBrush, QPainterPath
from PySide6.QtCore import Qt


class MarkerItem(QGraphicsEllipseItem):
    def __init__(self, color_str, size=20):
        super().__init__()
        self.size = size
        self.current_color = color_str  # 'white' or 'black'

        # Center the marker on the coordinate
        self.setRect(-self.size / 2, -self.size / 2, self.size, self.size)
        self.setZValue(1)  # Sits above the board, below the rings

        self._update_visuals()

    def _update_visuals(self):
        """Changes the marker's color to simulate flipping it."""
        if self.current_color == 'red':
            base_color = QColor("#EF5350") # Soft bright red
            border_color = QColor("#B71C1C") # Dark red border
        else:
            # Blue piece
            base_color = QColor("#29B6F6") # Light crisp blue
            border_color = QColor("#01579B") # Dark blue border

        self.setBrush(QBrush(base_color))
        self.setPen(QPen(border_color, 2))

    def flip(self):
        """Toggles the color between white and black."""
        self.current_color = 'black' if self.current_color == 'white' else 'white'
        self._update_visuals()


# In ui/piece_item.py (Update the RingItem class)

class RingItem(QGraphicsEllipseItem):
    # Added 'click_callback' to the arguments
    def __init__(self, q, r, color_str, click_callback, size=36):
        super().__init__()
        self.q = q
        self.r = r
        self.size = size
        self.color_str = color_str
        self.click_callback = click_callback  # Remembers the function to call
        self.is_selected = False  # NEW: Tracks selection state

        self.setRect(-self.size / 2, -self.size / 2, self.size, self.size)
        self.setZValue(2)

        if self.color_str == 'red':
            self.base_color = QColor("#EF5350")
        else:
            self.base_color = QColor("#29B6F6")

        self.base_pen = QPen(self.base_color, 6)
        self.selected_pen = QPen(QColor("#FFD54F"), 8)  # Golden yellow when selected

        self.setPen(self.base_pen)
        self.setBrush(QBrush(Qt.GlobalColor.transparent))
        self.setAcceptHoverEvents(True)

    # --- NEW: Toggle visual selection ---
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
        """Forces the clickable hitbox to be the entire solid circle, ignoring transparency."""
        path = QPainterPath()

        # FIX: Use self.rect() instead of self.boundingRect() to avoid infinite recursion!
        path.addEllipse(self.rect())

        return path

    def boundingRect(self):
        """
        Pads the exact bounding box so Qt knows to erase the thick pen strokes
        when the piece moves, preventing visual ghosting artifacts.
        """
        # Our thickest pen is 8px. Half of that bleeds outward (4px).
        # We add 6px of padding to all sides just to be completely safe.
        padding = 6
        return self.rect().adjusted(-padding, -padding, padding, padding)

    def mousePressEvent(self, event):
        # 1. Tell the board to select this ring
        self.click_callback(self)

        # 2. Tell Qt: "I handled this click! Do not pass it to anything underneath me!"
        event.accept()