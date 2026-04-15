# In core/rules.py

class YinshEngine:
    def __init__(self):
        self.rings = {}
        self.markers = {}
        # --- NEW: Track whose turn it is ---
        self.current_turn = 'red'

    # --- NEW: Turn Management ---
    def is_correct_turn(self, ring_color):
        """Checks if the clicked ring belongs to the current player."""
        if ring_color != self.current_turn:
            print(f"❌ Invalid Selection: It is currently {self.current_turn.upper()}'s turn!")
            return False
        return True

    def switch_turn(self):
        """Passes the turn to the other player."""
        self.current_turn = 'blue' if self.current_turn == 'red' else 'red'
        print(f"\n--- 🎮 {self.current_turn.upper()}'S TURN ---")

    # --- Memory Management ---
    def add_ring(self, q, r, color):
        """Registers a ring in the engine's memory."""
        self.rings[(q, r)] = color

    def add_marker(self, q, r, color):
        """Registers a marker in the engine's memory."""
        self.markers[(q, r)] = color

    def update_ring_position(self, start_q, start_r, end_q, end_r):
        """
        Moves a ring in the engine's memory, flips any jumped markers,
        and returns a list of the coordinates that were flipped.
        """
        flipped_coords = []

        # 1. Move the Ring
        if (start_q, start_r) in self.rings:
            color = self.rings.pop((start_q, start_r))
            self.markers[(start_q, start_r)] = color
            self.rings[(end_q, end_r)] = color

        # 2. Check the path and flip markers
        path = self.get_path_coordinates(start_q, start_r, end_q, end_r)
        for q, r in path:
            if (q, r) in self.markers:
                # Flip the color in memory
                current_color = self.markers[(q, r)]
                new_color = 'blue' if current_color == 'red' else 'red'
                self.markers[(q, r)] = new_color

                # Remember that we flipped this one
                flipped_coords.append((q, r))
                print(f"🔄 Flipped marker at ({q}, {r}) to {new_color.upper()}")

        return flipped_coords

    # --- Math & Logic ---
    def is_straight_line(self, q1, r1, q2, r2):
        if q1 == q2 and r1 == r2:
            return False
        return (q1 == q2) or (r1 == r2) or (q1 + r1 == q2 + r2)

    def is_occupied(self, q, r):
        """Checks if a space has a ring OR a marker on it."""
        return (q, r) in self.rings or (q, r) in self.markers

    # --- The Master Rule Checker ---
    def is_valid_move(self, start_q, start_r, end_q, end_r):
        # 1. Must be a straight line
        if not self.is_straight_line(start_q, start_r, end_q, end_r):
            print("❌ Invalid Move: Rings must slide in a straight line.")
            return False

        # 2. Cannot land on an occupied space
        if self.is_occupied(end_q, end_r):
            print(f"❌ Invalid Move: Space ({end_q}, {end_r}) is already occupied!")
            return False

        # 3. Analyze the path between start and end
        path = self.get_path_coordinates(start_q, start_r, end_q, end_r)
        jumped_over_marker = False

        for q, r in path:
            # Rule A: Cannot jump over other rings!
            if (q, r) in self.rings:
                print(f"❌ Invalid Move: Cannot jump over the ring at ({q}, {r}).")
                return False

            # Rule B: Track if we are jumping over markers
            if (q, r) in self.markers:
                jumped_over_marker = True
            elif jumped_over_marker:
                # Rule C: If we jumped a marker, we CANNOT pass over an empty space.
                # We must land in the very first empty space available.
                print("❌ Invalid Move: Must land in the first empty space after jumping a marker.")
                return False

        print("✅ Valid Move!")
        return True

    def get_path_coordinates(self, q1, r1, q2, r2):
        """
        Returns a list of all (q, r) coordinates strictly between the start and end point.
        Does not include the start or end points themselves.
        """
        path = []

        # 1. Calculate the 'distance' in hex spaces
        s1 = -q1 - r1
        s2 = -q2 - r2
        distance = max(abs(q1 - q2), abs(r1 - r2), abs(s1 - s2))

        if distance <= 1:
            return path  # There are no spaces between adjacent nodes

        # 2. Determine the single step direction
        dq = (q2 - q1) // distance
        dr = (r2 - r1) // distance

        # 3. Walk the path one step at a time
        current_q = q1 + dq
        current_r = r1 + dr

        while (current_q, current_r) != (q2, r2):
            path.append((current_q, current_r))
            current_q += dq
            current_r += dr

        return path