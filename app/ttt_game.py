from display import Display
import time
import random

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
RUNTIME_SECONDS = 15  # How long the TTT games run (in seconds)
# ============================================================================

#Game Board
# Usage:  game_board[col][row]
#
#  Row
#   0 |  0 1 2 
#   1 |  3 4 5 
#   2 |  6 7 8
#   --+------------
# col    0 1 2

game_board = [[None for _ in range(3)] for _ in range(3)]


center_pt = (32,26)
spacing   = 18

CC = center_pt[0]  # X
RC = center_pt[1]  # Y

# -X-
C0 = CC - spacing -1
C1 = CC
C2 = CC + spacing +1

# -Y-
R0 = RC - spacing
R1 = RC
R2 = RC + spacing +1

board_coords = [ [(C0,R0), (C1,R0), (C2,R0) ],
                 [(C0,R1), (C1,R1), (C2,R1) ],
                 [(C0,R2), (C1,R2), (C2,R2) ]
                ]


text_color = (175,175,175)

brd_color  = (125,125,125)



def ttt_RunGame( disp ):
    """
    Run multiple TicTacToe games for RUNTIME_SECONDS.
    Games get progressively faster as time goes on.
    """

    random.seed(time.time())

    sleep_time = 0.25
    game_count = 0

    print("TTT GAME")

    disp.text_loadFont('8x13B.bdf')
    #disp.text_loadFont('9x15B.bdf')

    start_time = time.time()

    while True:
        # Check if runtime limit exceeded
        elapsed = time.time() - start_time
        if elapsed >= RUNTIME_SECONDS:
            print(f"TTT runtime limit ({RUNTIME_SECONDS} seconds) reached after {game_count} games")
            time.sleep(3.0)
            return

        game_count += 1
        whos_turn = 0  #0=X, 1=O 

        Clear_Board()

        while(True):

            disp.clear()

            #Get next move
            Get_Next_Move(whos_turn)

            #Place pieces on display
            for c in range(3):
                for r in range(3):
                    if game_board[c][r] == 'X':
                        x,y = board_coords[c][r]
                        disp.draw_x( x, y, 10, 3, text_color)
                    if game_board[c][r] == 'O':
                        x,y = board_coords[c][r]
                        disp.draw_o( x, y, 7, 2, text_color)
            
            #Draw Board Lines
            Draw_Board(disp)

            #Set bottom text
            disp.text_set(17,64,text_color,  "WOPR")

            disp.show()       

            if Check_For_Winner() != None:
                print(f"WINNER (Game {game_count})")
                time.sleep(1)
                break


            if Check_for_Draw():
                #print(f"DRAW!! (Game {game_count})")
                if sleep_time > 0.005:
                    sleep_time *= 0.65
                break

            time.sleep(sleep_time)


            #setup for next turn:
            if whos_turn == 1:
                whos_turn = 0
            else:
                whos_turn = 1

    #END RunGame Loop
#END RunGame


def Clear_Board():
    for col in range(3):
        for row in range(3):
            game_board[col][row] = None

def Draw_Board(disp):
    
    #Left Vertical
    disp.draw_line( 32-(18/2),   2, 32-(18/2),   52, brd_color)
    disp.draw_line( 32-(18/2)-1, 2, 32-(18/2)-1, 52, brd_color)

    #Right Vertical
    disp.draw_line( 32+(18/2),   2, 32+(18/2),   52, brd_color)
    disp.draw_line( 32+(18/2)+1, 2, 32+(18/2)+1, 52, brd_color)

    #Upper Horizontal
    disp.draw_line( 8, 26+(18/2),   58, 26+(18/2),   brd_color)
    disp.draw_line( 8, 26+(18/2)+1, 58, 26+(18/2)+1, brd_color)

    #Lower Horizontal
    disp.draw_line( 8, 26-(18/2),   58, 26-(18/2),   brd_color)
    disp.draw_line( 8, 26-(18/2)+1, 58, 26-(18/2)+1, brd_color)

def Check_For_Winner():

    # Check rows
    for row in range(3):
        if (game_board[0][row] == game_board[1][row] == game_board[2][row] and game_board[0][row] is not None):
            return game_board[0][row]
    
    # Check columns  
    for col in range(3):
        if (game_board[col][0] == game_board[col][1] == game_board[col][2] and game_board[col][0] is not None):
            return game_board[col][0]
    
    # Check diagonals
    # Top-left to bottom-right
    if (game_board[0][0] == game_board[1][1] == game_board[2][2] and game_board[0][0] is not None):
        return game_board[0][0]
    
    # Top-right to bottom-left  
    if (game_board[2][0] == game_board[1][1] == game_board[0][2] and game_board[2][0] is not None):
        return game_board[2][0]
    
    return None


def Check_for_Draw():

    # First check if there's already a winner
    if Check_For_Winner() is not None:
        return False
    
    # Check if any spaces are empty
    for col in range(3):
        for row in range(3):
            if game_board[col][row] is None:
                return False
    
    # No winner and no empty spaces = draw
    return True
def Get_Next_Move(turn):
    """
    AI move generator that never loses!
    Uses minimax algorithm with strategic priorities and optimizations
    """
    # Special rule #1: If turn=0 and board is empty, take center
    if turn == 0 and Get_Piece_Count() == 0:
        game_board[1][1] = 'X'
        return
    
    # Early game optimization: Use strategic priorities before full minimax
    piece_count = Get_Piece_Count()
    if piece_count <= 4:
        move = get_strategic_move(turn)
        if move:
            col, row = move
            piece = 'X' if turn == 0 else 'O'
            game_board[col][row] = piece
            return
    
    # Find the best move using minimax for mid/late game
    best_move = find_best_move(turn)
    
    if best_move:
        col, row = best_move
        if turn == 0:
            game_board[col][row] = 'X'
        else:
            game_board[col][row] = 'O'


def get_strategic_move(turn):
    """
    Fast strategic move selection for early game
    Returns (col, row) or None if no strategic move found
    """
    piece = 'X' if turn == 0 else 'O'
    opponent = 'O' if turn == 0 else 'X'
    
    # Priority 1: Win immediately if possible
    for col in range(3):
        for row in range(3):
            if game_board[col][row] is None:
                game_board[col][row] = piece
                if Check_For_Winner() == piece:
                    game_board[col][row] = None
                    return (col, row)
                game_board[col][row] = None
    
    # Priority 2: Block opponent win
    for col in range(3):
        for row in range(3):
            if game_board[col][row] is None:
                game_board[col][row] = opponent
                if Check_For_Winner() == opponent:
                    game_board[col][row] = None
                    return (col, row)
                game_board[col][row] = None
    
    # Priority 3: Take corners
    corners = [(0,0), (0,2), (2,0), (2,2)]
    available_corners = [pos for pos in corners if game_board[pos[0]][pos[1]] is None]
    if available_corners:
        return random.choice(available_corners)
    
    # Priority 4: Take edges
    edges = [(0,1), (1,0), (1,2), (2,1)]
    available_edges = [pos for pos in edges if game_board[pos[0]][pos[1]] is None]
    if available_edges:
        return random.choice(available_edges)
    
    return None


def Get_Piece_Count():
    sum = 0
    for col in range(3):
        for row in range(3):
            if game_board[col][row] is not None:
                sum += 1
    return sum


def find_best_move(turn):
    """
    Find the best move using minimax algorithm with alpha-beta pruning
    Returns (col, row) tuple of best move
    """
    current_player = 'X' if turn == 0 else 'O'
    best_score = float('-inf')
    best_move = None
    
    # Try all empty squares
    for col in range(3):
        for row in range(3):
            if game_board[col][row] is None:
                # Make the move
                game_board[col][row] = current_player
                
                # Evaluate this move with alpha-beta pruning
                score = minimax_ab(current_player, False, 0, float('-inf'), float('inf'))
                
                # Undo the move
                game_board[col][row] = None
                
                # Update best move if this is better
                if score > best_score:
                    best_score = score
                    best_move = (col, row)
    
    return best_move


def minimax_ab(player, is_maximizing, depth, alpha, beta):
    """
    Minimax with alpha-beta pruning for faster evaluation
    """
    winner = Check_For_Winner()
    
    # Terminal states
    if winner == player:
        return 10 - depth
    elif winner is not None:
        return -10 + depth
    elif Check_for_Draw():
        return 0
    
    if is_maximizing:
        max_score = float('-inf')
        current_piece = player
        for col in range(3):
            for row in range(3):
                if game_board[col][row] is None:
                    game_board[col][row] = current_piece
                    score = minimax_ab(player, False, depth + 1, alpha, beta)
                    game_board[col][row] = None
                    max_score = max(score, max_score)
                    alpha = max(alpha, score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
        return max_score
    else:
        min_score = float('inf')
        opponent_piece = 'O' if player == 'X' else 'X'
        for col in range(3):
            for row in range(3):
                if game_board[col][row] is None:
                    game_board[col][row] = opponent_piece
                    score = minimax_ab(player, True, depth + 1, alpha, beta)
                    game_board[col][row] = None
                    min_score = min(score, min_score)
                    beta = min(beta, score)
                    if beta <= alpha:
                        break  # Alpha-beta pruning
        return min_score

