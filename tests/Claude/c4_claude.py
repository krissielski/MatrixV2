import random
from c4_common import NUMROWS, NUMCOLS, GetFirstOpenRow, CheckForWinner, CheckForDraw

def GetAIMove(board, player, level):
    """
    Intelligent Connect-4 move generator using minimax with alpha-beta pruning.
    
    Args:
        board: Current game board state
        player: Current player (0 or 1)
        level: Search depth (intelligence level)
    
    Returns:
        (col, row) tuple for the best move
    """
    if level <= 0:
        level = 1  # Minimum depth
    
    best_moves = []
    best_score = float('-inf')
    
    # Try each possible column
    for col in range(NUMCOLS):
        row = GetFirstOpenRow(board, col)
        if row is not None:  # Valid move
            # Make the move
            board[col][row] = player
            
            # Evaluate this move using minimax
            score = minimax(board, level - 1, float('-inf'), float('-inf'), False, player, 1 - player)
            
            # Undo the move
            board[col][row] = None
            
            # Track best moves
            if score > best_score:
                best_score = score
                best_moves = [(col, row)]
            elif score == best_score:
                best_moves.append((col, row))
    
    # Return best move (random selection if tie)
    if best_moves:
        return random.choice(best_moves)
    else:
        # Fallback - should not happen in normal game
        col = random.randint(0, NUMCOLS - 1)
        row = GetFirstOpenRow(board, col)
        return (col, row) if row is not None else (0, 0)


def minimax(board, depth, alpha, beta, is_maximizing, ai_player, current_player):
    """
    Minimax algorithm with alpha-beta pruning.
    
    Args:
        board: Current board state
        depth: Remaining search depth
        alpha: Alpha value for pruning
        beta: Beta value for pruning
        is_maximizing: True if maximizing player's turn
        ai_player: The AI player number (0 or 1)
        current_player: Current player making the move
    
    Returns:
        Score for this board position
    """
    # Base case: Check for terminal states
    winner_found = False
    for col in range(NUMCOLS):
        for row in range(NUMROWS):
            if board[col][row] is not None:
                winner = CheckForWinner(board, col, row, board[col][row])
                if winner is not None:
                    winner_found = True
                    if board[col][row] == ai_player:
                        return 1000 + depth  # Win bonus + depth bonus
                    else:
                        return -1000 - depth  # Loss penalty
    
    # Check for draw
    if CheckForDraw(board):
        return 0
    
    # Depth limit reached
    if depth <= 0:
        return evaluate_board(board, ai_player)
    
    if is_maximizing:
        max_score = float('-inf')
        for col in range(NUMCOLS):
            row = GetFirstOpenRow(board, col)
            if row is not None:
                # Make move
                board[col][row] = current_player
                
                # Recursive call
                score = minimax(board, depth - 1, alpha, beta, False, ai_player, 1 - current_player)
                
                # Undo move
                board[col][row] = None
                
                max_score = max(max_score, score)
                alpha = max(alpha, score)
                
                # Alpha-beta pruning
                if beta <= alpha:
                    break
        return max_score
    else:
        min_score = float('inf')
        for col in range(NUMCOLS):
            row = GetFirstOpenRow(board, col)
            if row is not None:
                # Make move
                board[col][row] = current_player
                
                # Recursive call
                score = minimax(board, depth - 1, alpha, beta, True, ai_player, 1 - current_player)
                
                # Undo move
                board[col][row] = None
                
                min_score = min(min_score, score)
                beta = min(beta, score)
                
                # Alpha-beta pruning
                if beta <= alpha:
                    break
        return min_score


def evaluate_board(board, ai_player):
    """
    Evaluate the current board position for the AI player.
    
    Args:
        board: Current board state
        ai_player: The AI player number
    
    Returns:
        Score representing how good the position is for the AI
    """
    score = 0
    opponent = 1 - ai_player
    
    # Evaluate all possible 4-in-a-row windows
    # Check horizontal, vertical, and both diagonals
    
    # Horizontal windows
    for row in range(NUMROWS):
        for col in range(NUMCOLS - 3):
            window = [board[col + i][row] for i in range(4)]
            score += evaluate_window(window, ai_player)
    
    # Vertical windows
    for col in range(NUMCOLS):
        for row in range(NUMROWS - 3):
            window = [board[col][row + i] for i in range(4)]
            score += evaluate_window(window, ai_player)
    
    # Diagonal windows (positive slope)
    for row in range(NUMROWS - 3):
        for col in range(NUMCOLS - 3):
            window = [board[col + i][row + i] for i in range(4)]
            score += evaluate_window(window, ai_player)
    
    # Diagonal windows (negative slope)
    for row in range(3, NUMROWS):
        for col in range(NUMCOLS - 3):
            window = [board[col + i][row - i] for i in range(4)]
            score += evaluate_window(window, ai_player)
    
    # Bonus for center column control
    center_col = NUMCOLS // 2
    center_count = sum(1 for row in range(NUMROWS) if board[center_col][row] == ai_player)
    score += center_count * 3
    
    return score


def evaluate_window(window, ai_player):
    """
    Evaluate a 4-position window for scoring potential.
    
    Args:
        window: List of 4 board positions
        ai_player: The AI player number
    
    Returns:
        Score for this window
    """
    score = 0
    opponent = 1 - ai_player
    
    ai_count = window.count(ai_player)
    opp_count = window.count(opponent)
    empty_count = window.count(None)
    
    # Score based on piece counts
    if ai_count == 4:
        score += 100
    elif ai_count == 3 and empty_count == 1:
        score += 10
    elif ai_count == 2 and empty_count == 2:
        score += 2
    
    # Penalize opponent opportunities
    if opp_count == 3 and empty_count == 1:
        score -= 80
    elif opp_count == 2 and empty_count == 2:
        score -= 2
    
    return score