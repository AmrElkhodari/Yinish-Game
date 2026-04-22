# In core/rules.py
import copy


class YinshEngine:
    def __init__(self):
        self.rings = {}
        self.markers = {}
        self.current_turn = 'red'
        self.scores = {'red': 0, 'blue': 0}

        # --- NEW: Time Travel Memory ---
        self.history = []
        self.history_index = -1
        self.save_history_state()  # Save the initial board state

    def save_history_state(self):
        """Takes a snapshot of the board."""
        # If we go back in time and change the future, erase the old future
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]

        state = {
            'rings': copy.deepcopy(self.rings),
            'markers': copy.deepcopy(self.markers),
            'scores': copy.deepcopy(self.scores),
            'current_turn': self.current_turn
        }
        self.history.append(state)
        self.history_index = len(self.history) - 1

    def load_history_state(self, index):
        """Loads a snapshot from the past or future."""
        if 0 <= index < len(self.history):
            state = self.history[index]
            self.rings = copy.deepcopy(state['rings'])
            self.markers = copy.deepcopy(state['markers'])
            self.scores = copy.deepcopy(state['scores'])
            self.current_turn = state['current_turn']
            self.history_index = index

    def is_correct_turn(self, ring_color):
        if ring_color != self.current_turn:
            print(f"❌ Invalid Selection: It is currently {self.current_turn.upper()}'s turn!")
            return False
        return True

    def switch_turn(self):
        self.current_turn = 'blue' if self.current_turn == 'red' else 'red'
        print(f"\n--- 🎮 {self.current_turn.upper()}'S TURN ---")

    def add_ring(self, q, r, color):
        self.rings[(q, r)] = color

    def add_marker(self, q, r, color):
        self.markers[(q, r)] = color

    def update_ring_position(self, start_q, start_r, end_q, end_r):
        flipped_coords = []
        if (start_q, start_r) in self.rings:
            color = self.rings.pop((start_q, start_r))
            self.markers[(start_q, start_r)] = color
            self.rings[(end_q, end_r)] = color

        path = self.get_path_coordinates(start_q, start_r, end_q, end_r)
        for q, r in path:
            if (q, r) in self.markers:
                current_color = self.markers[(q, r)]
                new_color = 'blue' if current_color == 'red' else 'red'
                self.markers[(q, r)] = new_color
                flipped_coords.append((q, r))

        return flipped_coords

    def is_straight_line(self, q1, r1, q2, r2):
        if q1 == q2 and r1 == r2:
            return False
        return (q1 == q2) or (r1 == r2) or (q1 + r1 == q2 + r2)

    def is_occupied(self, q, r):
        return (q, r) in self.rings or (q, r) in self.markers

    def is_valid_move(self, start_q, start_r, end_q, end_r, silent=False):
        if not self.is_straight_line(start_q, start_r, end_q, end_r):
            if not silent: print("❌ Invalid Move: Rings must slide in a straight line.")
            return False

        if self.is_occupied(end_q, end_r):
            if not silent: print(f"❌ Invalid Move: Space ({end_q}, {end_r}) is already occupied!")
            return False

        path = self.get_path_coordinates(start_q, start_r, end_q, end_r)
        jumped_over_marker = False

        for q, r in path:
            if (q, r) in self.rings:
                if not silent: print(f"❌ Invalid Move: Cannot jump over the ring at ({q}, {r}).")
                return False

            if (q, r) in self.markers:
                jumped_over_marker = True
            elif jumped_over_marker:
                if not silent: print("❌ Invalid Move: Must land in the first empty space after jumping a marker.")
                return False

        return True

    def get_path_coordinates(self, q1, r1, q2, r2):
        path = []
        s1 = -q1 - r1
        s2 = -q2 - r2
        distance = max(abs(q1 - q2), abs(r1 - r2), abs(s1 - s2))
        if distance <= 1: return path
        dq = (q2 - q1) // distance
        dr = (r2 - r1) // distance
        current_q = q1 + dq
        current_r = r1 + dr
        while (current_q, current_r) != (q2, r2):
            path.append((current_q, current_r))
            current_q += dq
            current_r += dr
        return path

    def check_for_sequence(self):
        """Finds the longest contiguous line of markers of the same color (can be > 5)"""
        directions = [(1, 0), (0, 1), (-1, 1)]

        for (q, r), color in self.markers.items():
            for dq, dr in directions:
                # Make sure we only check from the very START of a sequence to avoid duplicates
                prev_q, prev_r = q - dq, r - dr
                if self.markers.get((prev_q, prev_r)) == color:
                    continue

                sequence = [(q, r)]
                current_q, current_r = q + dq, r + dr

                # Keep walking the line as long as the color matches
                while self.markers.get((current_q, current_r)) == color:
                    sequence.append((current_q, current_r))
                    current_q += dq
                    current_r += dr

                if len(sequence) >= 5:
                    return sequence, color

        return None, None