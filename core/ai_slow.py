import copy


class SlowEngine:
    def __init__(self, ai_color, max_depth=4):
        self.ai_color = ai_color
        self.opponent_color = 'blue' if ai_color == 'red' else 'red'
        self.max_depth = max_depth

    def get_best_move(self, engine):
        best_move = None
        best_score = float('-inf')

        valid_moves = self.get_all_legal_moves(engine, self.ai_color)

        for move in valid_moves:
            simulated_engine = self.simulate_move(engine, move)
            # Notice: No alpha/beta passed down
            score = self.minimax(simulated_engine, self.max_depth - 1, False)

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def minimax(self, engine, depth, is_maximizing):
        if depth == 0 or engine.scores['red'] >= 3 or engine.scores['blue'] >= 3:
            return self.evaluate_board(engine)

        if is_maximizing:
            max_eval = float('-inf')
            moves = self.get_all_legal_moves(engine, self.ai_color)

            for move in moves:
                simulated_engine = self.simulate_move(engine, move)
                eval_score = self.minimax(simulated_engine, depth - 1, False)
                max_eval = max(max_eval, eval_score)
                # Notice: No pruning (break) statement here!

            return max_eval

        else:
            min_eval = float('inf')
            moves = self.get_all_legal_moves(engine, self.opponent_color)

            for move in moves:
                simulated_engine = self.simulate_move(engine, move)
                eval_score = self.minimax(simulated_engine, depth - 1, True)
                min_eval = min(min_eval, eval_score)
                # Notice: No pruning (break) statement here!

            return min_eval

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

    def evaluate_board(self, engine):
        if engine.scores[self.ai_color] >= 3: return float('inf')
        if engine.scores[self.opponent_color] >= 3: return float('-inf')

        score = 0
        score += engine.scores[self.ai_color] * 1000
        score -= engine.scores[self.opponent_color] * 1000

        my_markers = sum(1 for c in engine.markers.values() if c == self.ai_color)
        opp_markers = sum(1 for c in engine.markers.values() if c == self.opponent_color)
        score += my_markers * 10
        score -= opp_markers * 10

        for (q, r), c in engine.rings.items():
            distance_to_center = max(abs(q), abs(r), abs(-q - r))
            position_bonus = (5 - distance_to_center) * 5
            if c == self.ai_color:
                score += position_bonus
            else:
                score -= position_bonus

        return score