# In ui/game_scene.py
import math
import random
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QLabel
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QFont
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QUrl
# --- NEW: Upgraded to QMediaPlayer to support .mp3 files ---
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from ui.node_item import NodeItem
from ui.piece_item import RingItem, MarkerItem
from core.rules import YinshEngine


class GameView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.engine = YinshEngine()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        bg_pixmap = QPixmap("bg.png")
        if not bg_pixmap.isNull():
            self.setBackgroundBrush(QBrush(bg_pixmap))
        else:
            self.setBackgroundBrush(QBrush(QColor("#242526")))

        self.node_size = 15
        self.board_scale = 35
        self.board_radius = 5

        self.selected_ring = None
        self.visual_markers = {}
        self.visual_rings = {}

        self.game_is_over = False
        self.app_state = 'PLAYING'

        self._setup_audio()  # Initialize the new MP3 audio engine
        self._generate_lattice_lines()
        self._generate_board_nodes()
        self._spawn_random_rings()
        self._setup_ui_overlays()

    # --- NEW: MP3 Audio Manager ---
    def _setup_audio(self):
        self.sounds = {}
        self.audio_outputs = {}  # We must keep a reference to outputs so they aren't deleted

        # Mapping your specific .mp3 files to action keys
        sound_files = {
            'move': 'piece_move.mp3',
            'error': 'wrong_move.mp3',
            'mark_remove': 'mark_remove.mp3',
            'ring_remove': 'ring_remove.mp3',
            'game_over': 'game_over.mp3'
        }

        for key, filename in sound_files.items():
            player = QMediaPlayer(self)
            audio = QAudioOutput(self)
            player.setAudioOutput(audio)
            player.setSource(QUrl.fromLocalFile(f"sounds/{filename}"))

            self.sounds[key] = player
            self.audio_outputs[key] = audio

    def play_sound(self, key):
        """Helper to instantly rewind and play an MP3."""
        if key in self.sounds:
            self.sounds[key].setPosition(0)
            self.sounds[key].play()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            if self.engine.history_index > 0:
                self.engine.load_history_state(self.engine.history_index - 1)
                self._sync_pieces_from_engine()
                self._update_ui_state()
                self._show_instruction("⏪ VIEWING PAST MOVE (Press Right Arrow to go forward)")
        elif event.key() == Qt.Key_Right:
            if self.engine.history_index < len(self.engine.history) - 1:
                self.engine.load_history_state(self.engine.history_index + 1)
                self._sync_pieces_from_engine()
                self._update_ui_state()
                if self.engine.history_index == len(self.engine.history) - 1:
                    self.instruction_label.hide()
                else:
                    self._show_instruction("⏪ VIEWING PAST MOVE (Press Right Arrow to go forward)")
        super().keyPressEvent(event)

    def _setup_ui_overlays(self):
        base_font = QFont("Segoe UI", 16, QFont.Weight.Bold)

        self.red_bar = QLabel("🔴 RED SCORE: 0", self)
        self.red_bar.setFont(base_font)
        self.red_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.blue_bar = QLabel("🔵 BLUE SCORE: 0", self)
        self.blue_bar.setFont(base_font)
        self.blue_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.game_over_label = QLabel("GAME OVER", self)
        self.game_over_label.setFont(QFont("Segoe UI", 56, QFont.Weight.Black))
        self.game_over_label.setStyleSheet("""
            background-color: rgba(10, 10, 15, 0.9); 
            color: #FFD700; padding: 60px 120px; border-radius: 30px; border: 4px solid #FFD700;
        """)
        self.game_over_label.hide()

        self.instruction_label = QLabel("", self)
        self.instruction_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.instruction_label.setStyleSheet(
            "background-color: #FFD54F; color: #111; padding: 15px 40px; border-radius: 15px; border: 2px solid #FFF;")
        self.instruction_label.hide()

        self._update_ui_state()

    def _show_instruction(self, text):
        self.instruction_label.setText(text)
        self.instruction_label.adjustSize()
        self.instruction_label.move((self.viewport().width() - self.instruction_label.width()) // 2, 80)
        self.instruction_label.show()

    def _update_ui_state(self):
        self.red_bar.setText(f"🔴 RED SCORE: {self.engine.scores['red']}")
        self.blue_bar.setText(f"🔵 BLUE SCORE: {self.engine.scores['blue']}")

        active_red = "background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff4b4b, stop:1 #c62828); color: white; padding: 12px 30px; border-radius: 20px; border: 3px solid #ffcccc;"
        active_blue = "background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #29b6f6, stop:1 #0277bd); color: white; padding: 12px 30px; border-radius: 20px; border: 3px solid #b3e5fc;"
        inactive_red = "background-color: rgba(60, 10, 10, 0.7); color: #884444; padding: 12px 30px; border-radius: 20px; border: 3px solid transparent;"
        inactive_blue = "background-color: rgba(10, 30, 60, 0.7); color: #446688; padding: 12px 30px; border-radius: 20px; border: 3px solid transparent;"

        if self.engine.current_turn == 'red':
            self.red_bar.setStyleSheet(active_red)
            self.blue_bar.setStyleSheet(inactive_blue)
        else:
            self.red_bar.setStyleSheet(inactive_red)
            self.blue_bar.setStyleSheet(active_blue)

        self.red_bar.adjustSize()
        self.blue_bar.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

        w = self.viewport().width()
        h = self.viewport().height()

        self.red_bar.move(20, 20)
        self.blue_bar.move(w - self.blue_bar.width() - 20, h - self.blue_bar.height() - 20)

        self.game_over_label.move((w - self.game_over_label.width()) // 2, (h - self.game_over_label.height()) // 2)
        if hasattr(self, 'instruction_label'):
            self.instruction_label.move((w - self.instruction_label.width()) // 2, 80)

    def _sync_pieces_from_engine(self):
        for item in self.visual_rings.values(): self.scene.removeItem(item)
        for item in self.visual_markers.values(): self.scene.removeItem(item)
        self.visual_rings.clear()
        self.visual_markers.clear()

        def get_pixel_pos(q, r):
            return self.board_scale * math.sqrt(3) * (q + r / 2), self.board_scale * 3 / 2 * r

        for (q, r), color in self.engine.markers.items():
            x, y = get_pixel_pos(q, r)
            marker = MarkerItem(q, r, color, self.handle_marker_click)
            marker.setPos(x, y)
            self.scene.addItem(marker)
            self.visual_markers[(q, r)] = marker

        for (q, r), color in self.engine.rings.items():
            x, y = get_pixel_pos(q, r)
            ring = RingItem(q, r, color, self.handle_ring_click)
            ring.setPos(x, y)
            self.scene.addItem(ring)
            self.visual_rings[(q, r)] = ring

    def _update_valid_move_indicators(self):
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                item.set_highlight(False)

        if not self.selected_ring: return

        start_q = self.selected_ring.q
        start_r = self.selected_ring.r
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                if self.engine.is_valid_move(start_q, start_r, item.q, item.r, silent=True):
                    item.set_highlight(True)

    def is_valid_node(self, q, r):
        s = -q - r
        if max(abs(q), abs(r), abs(s)) > self.board_radius: return False
        if max(abs(q), abs(r), abs(s)) == self.board_radius and (q == 0 or r == 0 or s == 0): return False
        return True

    def _generate_lattice_lines(self):
        line_pen = QPen(QColor("#B2DFDB"))
        line_pen.setWidth(2)

        def hex_to_pixel(q, r):
            return self.board_scale * math.sqrt(3) * (q + r / 2), self.board_scale * 3 / 2 * r

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
        for q in range(-self.board_radius, self.board_radius + 1):
            for r in range(-self.board_radius, self.board_radius + 1):
                if self.is_valid_node(q, r):
                    node_item = NodeItem(q, r, self.handle_node_click, size=self.node_size)
                    x = self.board_scale * math.sqrt(3) * (q + r / 2)
                    y = self.board_scale * 3 / 2 * r
                    node_item.setPos(x, y)
                    self.scene.addItem(node_item)

    def _spawn_random_rings(self):
        valid_nodes = []
        for q in range(-self.board_radius, self.board_radius + 1):
            for r in range(-self.board_radius, self.board_radius + 1):
                if self.is_valid_node(q, r):
                    valid_nodes.append((q, r))

        random.shuffle(valid_nodes)
        red_starts = valid_nodes[:5]
        blue_starts = valid_nodes[5:10]

        def get_pixel_pos(q, r):
            return self.board_scale * math.sqrt(3) * (q + r / 2), self.board_scale * 3 / 2 * r

        for q, r in red_starts:
            x, y = get_pixel_pos(q, r)
            ring = RingItem(q, r, 'red', self.handle_ring_click)
            ring.setPos(x, y)
            self.scene.addItem(ring)
            self.engine.add_ring(q, r, 'red')
            self.visual_rings[(q, r)] = ring

        for q, r in blue_starts:
            x, y = get_pixel_pos(q, r)
            ring = RingItem(q, r, 'blue', self.handle_ring_click)
            ring.setPos(x, y)
            self.scene.addItem(ring)
            self.engine.add_ring(q, r, 'blue')
            self.visual_rings[(q, r)] = ring

    # --- LOGIC HANDLERS ---

    def handle_marker_click(self, marker_item):
        if self.game_is_over or self.engine.history_index < len(self.engine.history) - 1: return

        if self.app_state == 'SELECT_MARKERS':
            if (marker_item.q, marker_item.r) in self.pending_sequence:
                idx = self.pending_sequence.index((marker_item.q, marker_item.r))

                if idx + 5 <= len(self.pending_sequence):
                    to_remove = self.pending_sequence[idx:idx + 5]
                else:
                    to_remove = self.pending_sequence[-5:]

                for q, r in to_remove:
                    del self.engine.markers[(q, r)]
                    marker_visual = self.visual_markers.pop((q, r))
                    self.scene.removeItem(marker_visual)

                self.play_sound('mark_remove')  # SOUND: Markers removed
                self.app_state = 'SELECT_RING'
                self._show_instruction(f"✨ {self.scoring_color.upper()}: Now click one of your rings to remove it.")
            else:
                self.play_sound('error')  # SOUND: Wrong marker clicked

    def handle_ring_click(self, ring_item):
        if self.game_is_over or self.engine.history_index < len(self.engine.history) - 1: return

        if self.app_state == 'SELECT_RING':
            if ring_item.color_str == self.scoring_color:
                del self.engine.rings[(ring_item.q, ring_item.r)]
                ring_visual = self.visual_rings.pop((ring_item.q, ring_item.r))
                self.scene.removeItem(ring_visual)

                self.engine.scores[self.scoring_color] += 1
                self.play_sound('ring_remove')  # SOUND: Ring removed
                self.instruction_label.hide()
                self._update_ui_state()

                if self.engine.scores[self.scoring_color] >= 3:
                    self.game_is_over = True
                    self.play_sound('game_over')  # SOUND: Game Over!
                    self.game_over_label.setText(f"✨ {self.scoring_color.upper()} WINS! ✨")
                    self.game_over_label.show()
                    self.game_over_label.raise_()
                else:
                    self.app_state = 'PLAYING'
                    self.process_scoring()
            else:
                self.play_sound('error')  # SOUND: Wrong ring clicked
            return

        if self.app_state != 'PLAYING': return

        if not self.engine.is_correct_turn(ring_item.color_str):
            self.play_sound('error')  # SOUND: Wrong turn
            return

        if self.selected_ring:
            self.selected_ring.set_selected(False)

        self.selected_ring = ring_item
        self.selected_ring.set_selected(True)
        self._update_valid_move_indicators()

    def handle_node_click(self, node_item):
        if self.game_is_over or self.app_state != 'PLAYING' or self.engine.history_index < len(
            self.engine.history) - 1: return

        if self.selected_ring:
            start_q = self.selected_ring.q
            start_r = self.selected_ring.r
            end_q = node_item.q
            end_r = node_item.r

            if self.engine.is_valid_move(start_q, start_r, end_q, end_r):
                self.play_sound('move')  # SOUND: Valid move sliding

                ring_color = self.selected_ring.color_str
                new_marker = MarkerItem(start_q, start_r, ring_color, self.handle_marker_click)
                new_marker.setPos(self.selected_ring.pos())
                self.scene.addItem(new_marker)
                self.visual_markers[(start_q, start_r)] = new_marker

                flipped_coords = self.engine.update_ring_position(start_q, start_r, end_q, end_r)
                for fq, fr in flipped_coords:
                    if (fq, fr) in self.visual_markers:
                        self.visual_markers[(fq, fr)].flip()

                start_pos = self.selected_ring.pos()
                end_pos = node_item.pos()

                self.move_anim = QVariantAnimation(self)
                self.move_anim.setDuration(350)
                self.move_anim.setStartValue(start_pos)
                self.move_anim.setEndValue(end_pos)
                self.move_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

                ring_to_animate = self.selected_ring
                self.move_anim.valueChanged.connect(ring_to_animate.setPos)
                self.move_anim.start()

                self.selected_ring.q = node_item.q
                self.selected_ring.r = node_item.r

                self.visual_rings[(end_q, end_r)] = self.visual_rings.pop((start_q, start_r))
                self.process_scoring()
            else:
                self.play_sound('error')  # SOUND: Invalid destination clicked

            self.selected_ring.set_selected(False)
            self.selected_ring = None
            self._update_valid_move_indicators()

    def process_scoring(self):
        sequence, color = self.engine.check_for_sequence()

        if sequence:
            self.scoring_color = color
            if len(sequence) == 5:
                self.play_sound('mark_remove')  # SOUND: 5 in a row instantly removed
                for q, r in sequence:
                    del self.engine.markers[(q, r)]
                    marker_visual = self.visual_markers.pop((q, r))
                    self.scene.removeItem(marker_visual)

                self.app_state = 'SELECT_RING'
                self._show_instruction(f"✨ {color.upper()} got 5! Click one of your rings to remove it.")
            else:
                self.app_state = 'SELECT_MARKERS'
                self.pending_sequence = sequence
                self._show_instruction(
                    f"✨ {color.upper()}: You have {len(sequence)} in a row! Click a marker to select 5 to remove.")
        else:
            self.engine.switch_turn()
            self.engine.save_history_state()
            self._update_ui_state()