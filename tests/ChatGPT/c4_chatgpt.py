import random
from copy import deepcopy
from c4_common import NUMROWS, NUMCOLS, GetFirstOpenRow, CheckForWinner

def GetAIMove(board, player, level):
    def evaluate_window(window, player):
        opponent = 1 - player
        score = 0
        count = window.count(player)
        empty = window.count(None)
        if count == 4:
            score += 1000
        elif count == 3 and empty == 1:
            score += 10
        elif count == 2 and empty == 2:
            score += 1
        if window.count(opponent) == 3 and empty == 1:
            score -= 50
        return score

    def score_position(board, player):
        score = 0
        # Score horizontal
        for row in range(NUMROWS):
            for col in range(NUMCOLS - 3):
                window = [board[col+i][row] for i in range(4)]
                score += evaluate_window(window, player)
        # Score vertical
        for col in range(NUMCOLS):
            for row in range(NUMROWS - 3):
                window = [board[col][row+i] for i in range(4)]
                score += evaluate_window(window, player)
        # Score positive diagonal
        for col in range(NUMCOLS - 3):
            for row in range(NUMROWS - 3):
                window = [board[col+i][row+i] for i in range(4)]
                score += evaluate_window(window, player)
        # Score negative diagonal
        for col in range(NUMCOLS - 3):
            for row in range(3, NUMROWS):
                window = [board[col+i][row-i] for i in range(4)]
                score += evaluate_window(window, player)
        return score

    def simulate_move(board, col, player):
        row = GetFirstOpenRow(board, col)
        if row is None:
            return None, None
        board[col][row] = player
        return row, board

    def minimax(board, depth, current_player):
        valid_moves = [c for c in range(NUMCOLS) if GetFirstOpenRow(board, c) is not None]

        # Fixed: only call CheckForWinner if we have a valid row
        is_terminal = False
        for c in valid_moves:
            row = GetFirstOpenRow(board, c)
            if row is not None:
                # Important: we place the chip first, because CheckForWinner looks for an existing chip
                temp_board = deepcopy(board)
                temp_board[c][row] = current_player
                if CheckForWinner(temp_board, c, row, current_player):
                    is_terminal = True
                    break

        if depth == 0 or is_terminal or not valid_moves:
            return score_position(board, player)

        scores = []
        for col in valid_moves:
            b_copy = deepcopy(board)
            row = GetFirstOpenRow(b_copy, col)
            b_copy[col][row] = current_player
            score = minimax(b_copy, depth - 1, 1 - current_player)
            scores.append(score if current_player == player else -score)

        return max(scores) if current_player == player else min(scores)


    best_score = float('-inf')
    best_moves = []

    for col in range(NUMCOLS):
        row = GetFirstOpenRow(board, col)
        if row is not None:
            temp_board = deepcopy(board)
            temp_board[col][row] = player

            if CheckForWinner(temp_board, col, row, player):
                return col, row  # Immediate win

            score = minimax(temp_board, level - 1, 1 - player)

            if score > best_score:
                best_score = score
                best_moves = [(col, row)]
            elif score == best_score:
                best_moves.append((col, row))

    if best_moves:
        return random.choice(best_moves)
    for c in range(NUMCOLS):
        row = GetFirstOpenRow(board, c)
        if row is not None:
            return c, row
    return None, None  # No valid moves left