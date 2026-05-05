import math
import random
import copy
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QLabel
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap, QFont
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QUrl, QObject, Signal, QTimer, QPointF, QThread
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from ui.node_item import NodeItem
from ui.piece_item import RingItem, MarkerItem
from core.rules import YinshEngine
from core.ai_fast import FastEngine
from core.ai_slow import SlowEngine
from core.ai_impossible import ImpossibleEngine

# --- NEW: BACKGROUND THREAD FOR AI ---
class AIWorker(QThread):
    move_calculated = Signal(tuple)

    def __init__(self, engine_snapshot, ai_color):
        super().__init__()
        self.engine_snapshot = engine_snapshot

        # --- EASILY SWITCH ENGINES HERE ---
        # Change this string to 'fast', 'slow', or 'impossible' to test them
        self.engine_type = 'fast'

        if self.engine_type == 'fast':
            self.ai = FastEngine(ai_color, max_depth=3)
        elif self.engine_type == 'slow':
            self.ai = SlowEngine(ai_color, max_depth=3)
        elif self.engine_type == 'impossible':
            self.ai = ImpossibleEngine(ai_color)  # No depth passed here!

    def run(self):
        # This runs invisibly in the background so the UI doesn't freeze
        print(f"🤖 AI Thinking using {self.engine_type.upper()} ENGINE...")

        best_move = self.ai.get_best_move(self.engine_snapshot)
        self.move_calculated.emit(best_move)


# --- NETWORK SIGNALS (Kept for your online mode later) ---
class NetworkSignals(QObject):
    data_received = Signal(dict)


class GameView(QGraphicsView):
    def __init__(self, p1_name="Player 1", p2_name="Player 2", db=None, room_code=None, local_color=None,
                 ai_mode=False):
        super().__init__()

        self.p1_name = p1_name
        self.p2_name = p2_name
        self.db = db
        self.room_code = room_code
        self.local_color = local_color

        # --- NEW: AI Variables ---
        self.ai_mode = ai_mode
        self.ai_color = 'blue' if ai_mode else None  # AI is always blue right now
        self.ai_is_thinking = False

        self.network_signals = NetworkSignals()
        self.network_signals.data_received.connect(self._on_remote_update)

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

        self._setup_audio()
        self._generate_lattice_lines()
        self._generate_board_nodes()
        self._setup_ui_overlays()

        if self.db and self.room_code:
            self.db_stream = self.db.child("rooms").child(self.room_code).stream(self._db_listener)
            if self.local_color == 'red':
                self._spawn_random_rings()
                self._push_state_to_db()
        else:
            self._spawn_random_rings()

    # --- [ONLINE SYNC LOGIC KEPT EXACTLY THE SAME] ---
    def _db_listener(self, message):
        if self.db and self.room_code:
            full_data = self.db.child("rooms").child(self.room_code).get().val()
            if full_data: self.network_signals.data_received.emit(full_data)

    def _on_remote_update(self, data):
        if self.local_color == 'red':
            new_joiner = data.get('joiner')
            if new_joiner and new_joiner != 'Waiting...' and self.p2_name != new_joiner:
                self.p2_name = new_joiner
                self.play_sound('score')
                self._update_ui_state()
                self._show_instruction(f"✨ {new_joiner} has joined the game!", timeout=3000)

        if data.get('last_mover') == self.local_color: return

        if 'rings' in data and data.get('last_mover') != 'none':
            current_rings = set(self.engine.rings.keys())
            new_rings_data = data.get('rings', {})
            new_rings = {tuple(map(int, k.split(','))) for k in new_rings_data.keys()}

            start_pos = list(current_rings - new_rings)
            end_pos = list(new_rings - current_rings)

            if len(start_pos) == 1 and len(end_pos) == 1:
                sq, sr = start_pos[0]
                eq, er = end_pos[0]
                ring_visual = self.visual_rings.get((sq, sr))

                if ring_visual:
                    start_pixel = ring_visual.pos()
                    end_pixel = QPointF(self.board_scale * math.sqrt(3) * (eq + er / 2), self.board_scale * 3 / 2 * er)

                    self.remote_anim = QVariantAnimation(self)
                    self.remote_anim.setDuration(350)
                    self.remote_anim.setStartValue(start_pixel)
                    self.remote_anim.setEndValue(end_pixel)
                    self.remote_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
                    self.remote_anim.valueChanged.connect(ring_visual.setPos)
                    self.remote_anim.finished.connect(lambda: self._apply_remote_update(data))
                    self.remote_anim.start()
                    self.play_sound('move')
                    return
            self._apply_remote_update(data)

    def _apply_remote_update(self, data):
        if self.engine.history_index < len(self.engine.history) - 1: self.instruction_label.hide()
        self.engine.from_dict(data)
        self.engine.save_history_state()
        self._sync_pieces_from_engine()
        self._update_ui_state()

    def _push_state_to_db(self):
        if self.db and self.room_code:
            state = self.engine.to_dict()
            state['last_mover'] = self.local_color
            self.db.child("rooms").child(self.room_code).update(state)

    # ---------------------------------------------------

    def _setup_audio(self):
        self.sounds = {}
        self.audio_outputs = {}
        sound_files = {'move': 'piece_move.mp3', 'error': 'wrong_move.mp3', 'mark_remove': 'mark_remove.mp3',
                       'ring_remove': 'ring_remove.mp3', 'game_over': 'game_over.mp3', 'score': 'score.wav'}
        for key, filename in sound_files.items():
            player = QMediaPlayer(self)
            audio = QAudioOutput(self)
            player.setAudioOutput(audio)
            player.setSource(QUrl.fromLocalFile(f"sounds/{filename}"))
            self.sounds[key] = player
            self.audio_outputs[key] = audio

    def play_sound(self, key):
        if key in self.sounds:
            self.sounds[key].setPosition(0)
            self.sounds[key].play()

    def go_back_in_time(self):
        # Block time travel if AI is thinking
        if self.ai_is_thinking: return
        if self.engine.history_index > 0:
            self.engine.load_history_state(self.engine.history_index - 1)
            self._sync_pieces_from_engine()
            self._update_ui_state()
            self._show_instruction("⏪ VIEWING PAST (Press Right Arrow to go forward)")

    def go_forward_in_time(self):
        if self.ai_is_thinking: return
        if self.engine.history_index < len(self.engine.history) - 1:
            self.engine.load_history_state(self.engine.history_index + 1)
            self._sync_pieces_from_engine()
            self._update_ui_state()
            if self.engine.history_index == len(self.engine.history) - 1:
                self.instruction_label.hide()
            else:
                self._show_instruction("⏪ VIEWING PAST (Press Right Arrow to go forward)")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.go_back_in_time()
        elif event.key() == Qt.Key_Right:
            self.go_forward_in_time()
        super().keyPressEvent(event)

    def _setup_ui_overlays(self):
        base_font = QFont("Segoe UI", 16, QFont.Weight.Bold)
        self.red_bar = QLabel(f"🔴 {self.p1_name.upper()}: 0", self)
        self.red_bar.setFont(base_font)
        self.red_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.blue_bar = QLabel(f"🔵 {self.p2_name.upper()}: 0", self)
        self.blue_bar.setFont(base_font)
        self.blue_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.game_over_label = QLabel("GAME OVER", self)
        self.game_over_label.setFont(QFont("Segoe UI", 56, QFont.Weight.Black))
        self.game_over_label.setStyleSheet(
            "background-color: rgba(10, 10, 15, 0.9); color: #FFD700; padding: 60px 120px; border-radius: 30px; border: 4px solid #FFD700;")
        self.game_over_label.hide()

        self.instruction_label = QLabel("", self)
        self.instruction_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self.instruction_label.setStyleSheet(
            "background-color: #FFD54F; color: #111; padding: 15px 40px; border-radius: 15px; border: 2px solid #FFF;")
        self.instruction_label.hide()
        self._update_ui_state()

    def _show_instruction(self, text, timeout=None):
        self.instruction_label.setText(text)
        self.instruction_label.adjustSize()
        self.instruction_label.move((self.viewport().width() - self.instruction_label.width()) // 2, 80)
        self.instruction_label.show()
        if timeout: QTimer.singleShot(timeout, self.instruction_label.hide)

    def _update_ui_state(self):
        self.red_bar.setText(f"🔴 {self.p1_name.upper()}: {self.engine.scores['red']}")

        # If AI is thinking, show a loading status on their bar
        blue_text = "🔵 AI IS THINKING..." if self.ai_is_thinking else f"🔵 {self.p2_name.upper()}: {self.engine.scores['blue']}"
        self.blue_bar.setText(blue_text)

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
        rect = self.scene.itemsBoundingRect()
        rect.adjust(-20, -20, 20, 60)
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

        w, h = self.viewport().width(), self.viewport().height()
        self.red_bar.move(20, 20)
        self.blue_bar.move(w - self.blue_bar.width() - 20, h - self.blue_bar.height() - 20)
        self.game_over_label.move((w - self.game_over_label.width()) // 2, (h - self.game_over_label.height()) // 2)
        if hasattr(self, 'instruction_label'): self.instruction_label.move((w - self.instruction_label.width()) // 2,
                                                                           80)

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
            if isinstance(item, NodeItem): item.set_highlight(False)

        if not self.selected_ring: return

        start_q, start_r = self.selected_ring.q, self.selected_ring.r
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

        for q in range(-self.board_radius, self.board_radius + 1):
            for r in range(-self.board_radius, self.board_radius + 1):
                if self.is_valid_node(q, r):
                    x1, y1 = hex_to_pixel(q, r)
                    for dq, dr in [(1, 0), (0, 1), (-1, 1)]:
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
        valid_nodes = [(q, r) for q in range(-self.board_radius, self.board_radius + 1) for r in
                       range(-self.board_radius, self.board_radius + 1) if self.is_valid_node(q, r)]
        random.shuffle(valid_nodes)
        red_starts, blue_starts = valid_nodes[:5], valid_nodes[5:10]

        def get_pixel_pos(q, r):
            return self.board_scale * math.sqrt(3) * (q + r / 2), self.board_scale * 3 / 2 * r

        for q, r in red_starts:
            ring = RingItem(q, r, 'red', self.handle_ring_click)
            ring.setPos(*get_pixel_pos(q, r))
            self.scene.addItem(ring)
            self.engine.add_ring(q, r, 'red')
            self.visual_rings[(q, r)] = ring

        for q, r in blue_starts:
            ring = RingItem(q, r, 'blue', self.handle_ring_click)
            ring.setPos(*get_pixel_pos(q, r))
            self.scene.addItem(ring)
            self.engine.add_ring(q, r, 'blue')
            self.visual_rings[(q, r)] = ring

    # --- LOGIC HANDLERS ---
    def handle_marker_click(self, marker_item):
        # AI LOCK
        if self.ai_is_thinking or (self.ai_mode and self.engine.current_turn == self.ai_color): return
        if self.game_is_over or self.engine.history_index < len(self.engine.history) - 1: return
        if self.local_color and self.engine.current_turn != self.local_color: return

        if self.app_state == 'SELECT_MARKERS':
            if (marker_item.q, marker_item.r) in self.pending_sequence:
                idx = self.pending_sequence.index((marker_item.q, marker_item.r))
                to_remove = self.pending_sequence[idx:idx + 5] if idx + 5 <= len(
                    self.pending_sequence) else self.pending_sequence[-5:]

                for q, r in to_remove:
                    del self.engine.markers[(q, r)]
                    self.scene.removeItem(self.visual_markers.pop((q, r)))

                self.play_sound('mark_remove')
                self.app_state = 'SELECT_RING'
                self._show_instruction(f"✨ {self.scoring_color.upper()}: Now click one of your rings to remove it.")
            else:
                self.play_sound('error')

    def handle_ring_click(self, ring_item):
        # AI LOCK
        if self.ai_is_thinking or (self.ai_mode and self.engine.current_turn == self.ai_color): return
        if self.game_is_over or self.engine.history_index < len(self.engine.history) - 1: return
        if self.local_color and self.engine.current_turn != self.local_color: return

        if self.app_state == 'SELECT_RING':
            if ring_item.color_str == self.scoring_color:
                del self.engine.rings[(ring_item.q, ring_item.r)]
                self.scene.removeItem(self.visual_rings.pop((ring_item.q, ring_item.r)))

                self.engine.scores[self.scoring_color] += 1
                self.play_sound('ring_remove')
                self.instruction_label.hide()
                self._update_ui_state()

                if self.engine.scores[self.scoring_color] >= 3:
                    self.game_is_over = True
                    self.play_sound('game_over')
                    self.game_over_label.setText(f"✨ {self.scoring_color.upper()} WINS! ✨")
                    self.game_over_label.show()
                    self.game_over_label.raise_()
                    self._push_state_to_db()
                else:
                    self.app_state = 'PLAYING'
                    self.process_scoring()
            else:
                self.play_sound('error')
            return

        if self.app_state != 'PLAYING': return
        if not self.engine.is_correct_turn(ring_item.color_str):
            self.play_sound('error')
            return

        if self.selected_ring: self.selected_ring.set_selected(False)
        self.selected_ring = ring_item
        self.selected_ring.set_selected(True)
        self._update_valid_move_indicators()

    def handle_node_click(self, node_item):
        # AI LOCK
        if self.ai_is_thinking or (self.ai_mode and self.engine.current_turn == self.ai_color): return
        if self.game_is_over or self.app_state != 'PLAYING' or self.engine.history_index < len(
            self.engine.history) - 1: return
        if self.local_color and self.engine.current_turn != self.local_color: return

        if self.selected_ring:
            start_q, start_r = self.selected_ring.q, self.selected_ring.r
            end_q, end_r = node_item.q, node_item.r

            if self.engine.is_valid_move(start_q, start_r, end_q, end_r):
                self._execute_physical_move(start_q, start_r, end_q, end_r)
            else:
                self.play_sound('error')

            self.selected_ring.set_selected(False)
            self.selected_ring = None
            self._update_valid_move_indicators()

    def _execute_physical_move(self, start_q, start_r, end_q, end_r):
        """Unified method for both human and AI to physically move a ring."""
        self.play_sound('move')
        ring_color = self.engine.rings[(start_q, start_r)]

        new_marker = MarkerItem(start_q, start_r, ring_color, self.handle_marker_click)
        ring_visual = self.visual_rings[(start_q, start_r)]
        new_marker.setPos(ring_visual.pos())
        self.scene.addItem(new_marker)
        self.visual_markers[(start_q, start_r)] = new_marker

        flipped_coords = self.engine.update_ring_position(start_q, start_r, end_q, end_r)
        for fq, fr in flipped_coords:
            if (fq, fr) in self.visual_markers: self.visual_markers[(fq, fr)].flip()

        start_pos = ring_visual.pos()
        end_x = self.board_scale * math.sqrt(3) * (end_q + end_r / 2)
        end_y = self.board_scale * 3 / 2 * end_r
        end_pos = QPointF(end_x, end_y)

        self.move_anim = QVariantAnimation(self)
        self.move_anim.setDuration(350)
        self.move_anim.setStartValue(start_pos)
        self.move_anim.setEndValue(end_pos)
        self.move_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.move_anim.valueChanged.connect(ring_visual.setPos)

        ring_visual.q, ring_visual.r = end_q, end_r
        self.visual_rings[(end_q, end_r)] = self.visual_rings.pop((start_q, start_r))

        # When animation finishes, check for points
        self.move_anim.finished.connect(self.process_scoring)
        self.move_anim.start()

    def process_scoring(self):
        sequence, color = self.engine.check_for_sequence()

        if sequence:
            self.scoring_color = color

            # --- NEW: AI AUTO-SCORER ---
            if self.ai_mode and color == self.ai_color:
                # 1. AI Auto-removes markers
                for q, r in sequence[:5]:
                    del self.engine.markers[(q, r)]
                    self.scene.removeItem(self.visual_markers.pop((q, r)))
                self.play_sound('mark_remove')

                # 2. AI Auto-removes its first available ring
                ai_rings = [(q, r) for (q, r), c in self.engine.rings.items() if c == self.ai_color]
                if ai_rings:
                    r_q, r_r = ai_rings[0]
                    del self.engine.rings[(r_q, r_r)]
                    self.scene.removeItem(self.visual_rings.pop((r_q, r_r)))

                self.engine.scores[self.ai_color] += 1
                self.play_sound('ring_remove')
                self._update_ui_state()

                if self.engine.scores[self.ai_color] >= 3:
                    self.game_is_over = True
                    self.play_sound('game_over')
                    self.game_over_label.setText(f"✨ {self.ai_color.upper()} WINS! ✨")
                    self.game_over_label.show()
                else:
                    self.process_scoring()  # Check if AI got a double score!
                return
            # ---------------------------

            if len(sequence) == 5:
                self.play_sound('mark_remove')
                for q, r in sequence:
                    del self.engine.markers[(q, r)]
                    self.scene.removeItem(self.visual_markers.pop((q, r)))
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
            self._push_state_to_db()

            # --- NEW: TRIGGER AI TURN ---
            if self.ai_mode and self.engine.current_turn == self.ai_color and not self.game_is_over:
                self._trigger_ai_turn()

    # --- NEW: AI THREAD MANAGEMENT ---
    def _trigger_ai_turn(self):
        self.ai_is_thinking = True
        self._update_ui_state()  # Show the "thinking" label

        # Deepcopy the engine so the background thread doesn't touch active UI memory
        engine_snapshot = copy.deepcopy(self.engine)

        self.worker = AIWorker(engine_snapshot, self.ai_color)
        self.worker.move_calculated.connect(self._on_ai_move_calculated)
        self.worker.start()

    def _on_ai_move_calculated(self, move):
        self.ai_is_thinking = False
        self._update_ui_state()

        if move:
            start_q, start_r, end_q, end_r = move
            self._execute_physical_move(start_q, start_r, end_q, end_r)
        else:
            print("AI could not find a valid move.")