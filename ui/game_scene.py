import math
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem
from PySide6.QtGui import QPainter, QPen, QColor, QBrush
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve

from ui.node_item import NodeItem
from ui.piece_item import RingItem, MarkerItem


class GameView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark mode background
        self.setBackgroundBrush(QBrush(QColor("#303030")))

        self.node_size = 15
        self.board_scale = 50
        self.board_radius = 5

        # State Tracking
        self.selected_ring = None

        self._generate_lattice_lines()
        self._generate_board_nodes()
        self._spawn_test_pieces()

    def is_valid_node(self, q, r):
        """Defines the exact shape of the YINSH board (removes the 6 corners)."""
        s = -q - r
        if max(abs(q), abs(r), abs(s)) > self.board_radius:
            return False
        if max(abs(q), abs(r), abs(s)) == self.board_radius and (q == 0 or r == 0 or s == 0):
            return False
        return True

    def _generate_lattice_lines(self):
        """Draws the teal lines connecting the valid nodes."""
        line_pen = QPen(QColor("#B2DFDB"))
        line_pen.setWidth(2)

        def hex_to_pixel(q, r):
            x = self.board_scale * math.sqrt(3) * (q + r / 2)
            y = self.board_scale * 3 / 2 * r
            return x, y

        directions = [(1, 0), (0, 1), (-1, 1)]

        for q in range(-self.board_radius, self.board_radius + 1):
            for r in range(-self.board_radius, self.board_radius + 1):
                if self.is_valid_node(q, r):
                    x1, y1 = hex_to_pixel(q, r)
                    for dq, dr in directions:
                        nq, nr = q + dq, r + dr
                        if self.is_valid_node(nq, nr):
                            x2, y2 = hex_to_pixel(nq, nr)
                            line = QGraphicsLineItem(x1, y1, x2, y2)
                            line.setPen(line_pen)
                            line.setZValue(-1)
                            self.scene.addItem(line)

    def _generate_board_nodes(self):
        """Spawns the invisible hitboxes for clicking."""
        for q in range(-self.board_radius, self.board_radius + 1):
            for r in range(-self.board_radius, self.board_radius + 1):
                if self.is_valid_node(q, r):
                    # Passing self.handle_node_click so the node can talk back
                    node_item = NodeItem(q, r, self.handle_node_click, size=self.node_size)
                    x = self.board_scale * math.sqrt(3) * (q + r / 2)
                    y = self.board_scale * 3 / 2 * r
                    node_item.setPos(x, y)
                    self.scene.addItem(node_item)

    def _spawn_test_pieces(self):
        """Temporary function to put some pieces on the board."""

        def get_pixel_pos(q, r):
            x = self.board_scale * math.sqrt(3) * (q + r / 2)
            y = self.board_scale * 3 / 2 * r
            return x, y

        # 1. Center Red Ring with Blue Marker
        x, y = get_pixel_pos(0, 0)
        marker = MarkerItem('blue')
        marker.setPos(x, y)
        self.scene.addItem(marker)

        ring = RingItem(0, 0, 'red', self.handle_ring_click)
        ring.setPos(x, y)
        self.scene.addItem(ring)

        # 2. Empty Red Ring
        x2, y2 = get_pixel_pos(0, -2)
        ring2 = RingItem(0, -2, 'red', self.handle_ring_click)
        ring2.setPos(x2, y2)
        self.scene.addItem(ring2)

        # 3. Empty Blue Ring
        x3, y3 = get_pixel_pos(2, 0)
        ring3 = RingItem(2, 0, 'blue', self.handle_ring_click)
        ring3.setPos(x3, y3)
        self.scene.addItem(ring3)

    # --- LOGIC HANDLERS ---
    def handle_ring_click(self, ring_item):
        """Triggered when a player clicks a ring."""
        # Deselect old
        if self.selected_ring:
            self.selected_ring.set_selected(False)

        # Select new
        self.selected_ring = ring_item
        self.selected_ring.set_selected(True)
        print(f"Selected {ring_item.color_str} ring at ({ring_item.q}, {ring_item.r})")

    def handle_node_click(self, node_item):
        """Triggered when a player clicks an empty node."""
        if self.selected_ring:
            print(f"Sliding ring to ({node_item.q}, {node_item.r})")

            # 1. Capture the start and end pixel coordinates
            start_pos = self.selected_ring.pos()
            end_pos = node_item.pos()

            # 2. Create the Animation Engine
            # We attach it to 'self' so Python's garbage collector doesn't delete it mid-animation
            self.move_anim = QVariantAnimation(self)
            self.move_anim.setDuration(350)  # 350 milliseconds is a great, snappy speed
            self.move_anim.setStartValue(start_pos)
            self.move_anim.setEndValue(end_pos)

            # This makes the ring accelerate at the start and slow down at the end
            self.move_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

            # 3. Connect the engine to the ring
            # Every frame, the engine emits a new position. We tell the ring to move there.
            ring_to_animate = self.selected_ring
            self.move_anim.valueChanged.connect(ring_to_animate.setPos)

            # 4. Press Play
            self.move_anim.start()

            # 5. Instantly update the pure math/logic behind the scenes
            self.selected_ring.q = node_item.q
            self.selected_ring.r = node_item.r

            # 6. Deselect the ring so the player can click something else
            self.selected_ring.set_selected(False)
            self.selected_ring = None