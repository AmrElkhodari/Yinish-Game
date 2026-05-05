import copy


class ImpossibleEngine:
    def __init__(self, ai_color):
        self.ai_color = ai_color
        self.opponent_color = 'blue' if ai_color == 'red' else 'red'
        # NO DEPTH LIMIT! The AI will attempt to search to the end of the game.

    def get_best_move(self, engine):
        best_move = None
        best_score = float('-inf')

        valid_moves = self.get_all_legal_moves(engine, self.ai_color)

        # If there are no moves (shouldn't happen unless game is broken), return None
        if not valid_moves: return None

        for move in valid_moves:
            simulated_engine = self.simulate_move(engine, move)
            # Run minimax with NO DEPTH
            score = self.minimax(simulated_engine, False)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, engine, is_maximizing):
        # 1. Base Case: The game is LITERALLY OVER. No depth checking.
        if engine.scores['red'] >= 3 or engine.scores['blue'] >= 3:
            if engine.scores[self.ai_color] >= 3:
                return 1  # AI Wins in this timeline
            else:
                return -1  # Human Wins in this timeline

        # 2. Recursive Step
        if is_maximizing:
            max_eval = float('-inf')
            moves = self.get_all_legal_moves(engine, self.ai_color)

            # Tie/Trap handler: if no moves available, it's a draw/loss
            if not moves: return 0

            for move in moves:
                simulated_engine = self.simulate_move(engine, move)
                eval_score = self.minimax(simulated_engine, False)
                max_eval = max(max_eval, eval_score)

            return max_eval

        else:
            min_eval = float('inf')
            moves = self.get_all_legal_moves(engine, self.opponent_color)

            if not moves: return 0

            for move in moves:
                simulated_engine = self.simulate_move(engine, move)
                eval_score = self.minimax(simulated_engine, True)
                min_eval = min(min_eval, eval_score)

            return min_eval

    # --- Game Logic Helpers (Same as before) ---
    def simulate_move(self, engine, move):
        new_engine = copy.deepcopy(engine)
        start_q, start_r, end_q, end_r = move
        new_engine.update_ring_position(start_q, start_r, end_q, end_r)

        sequence, color = new_engine.check_for_sequence()
        if sequence:
            for q, r in sequence[:5]:
                if (q, r) in new_engine.markers:
                    del new_engine.markers[(q, r)]
            rings_to_remove = [(q, r) for (q, r), c in new_engine.rings.items() if c == color]
            if rings_to_remove:
                del new_engine.rings[rings_to_remove[0]]
            new_engine.scores[color] += 1

        new_engine.switch_turn()
        return new_engine

    def get_all_legal_moves(self, engine, color):
        moves = []
        my_rings = [(q, r) for (q, r), c in engine.rings.items() if c == color]
        directions = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]
        board_radius = 5

        def is_valid_board_node(q, r):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) > board_radius: return False
            if max(abs(q), abs(r), abs(s)) == board_radius and (q == 0 or r == 0 or s == 0): return False
            return True

        for start_q, start_r in my_rings:
            for dq, dr in directions:
                current_q, current_r = start_q + dq, start_r + dr
                while is_valid_board_node(current_q, current_r):
                    if engine.is_valid_move(start_q, start_r, current_q, current_r, silent=True):
                        moves.append((start_q, start_r, current_q, current_r))
                    current_q += dq
                    current_r += dr
        return moves