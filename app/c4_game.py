
from display import Display
import time
import random

from c4_common import NUMROWS,NUMCOLS,GetFirstOpenRow,CheckForWinner,CheckForDraw,CheckForValidMove

CHIP_RADIUS = 4
STARTING_X  = 4
STARTING_Y  = 5
CHIP_OFFSET = 9
FALL_DELAY  = 0.005


#Game Board
# Usage:  game_board[col][row]
#
#  Row
#   5 |  * * * *
#   . |  * * * *
#   . |  * * * *
#   0 |  * * * *
#   --+------------
# col    0 . . 6
#
game_board = [[None for _ in range(NUMROWS)] for _ in range(NUMCOLS)]


#player colors    RED        YELLOW
player_color = [(175,0,0), (175,175,0)]

def RunGame( disp ):

    disp.overlay_set_color((0,0,100))
    disp.overlay_set_type(0)

    random.seed(time.time())

    #Generate overlay:
    for c in range (NUMCOLS):
        for r in range (NUMROWS):

            x = STARTING_X + c * CHIP_OFFSET
            y = STARTING_Y + r * CHIP_OFFSET

            disp.overlay_circle(x, y, CHIP_RADIUS)

    #Player 0 (RED), player 1 (Yellow)
    player = 0

    select_mode = [0,0]

    while True:

        # Get Next move
        col,row = GetNextMove( select_mode[player], player )

        #verify valid move
        if not CheckForValidMove( game_board, col, row ):
            print("  INVALID MOVE:", col, row, player)
            time.sleep(5)
            exit() 

        DropChip(disp,col,row, player_color[player] )

        PlaceChip(col,row,player)

        time.sleep(2)


        # Check for Draw
        if CheckForDraw():
            print("   DRAW!!!!!!!!!!!")
            time.sleep(5)
            exit()   


        # Check for Winner
        winner = CheckForWinner(col,row,player)
        if winner is not None:
            print("Winner!!!", col, row)
            print(winner)

            BlinkWinningChips(disp,winner,player)

            # Hold winning chips for a bit
            time.sleep(5)

            # Reset for next game
            player = 0
            # Clear the game board
            for col in range(NUMCOLS):
                for row in range(NUMROWS):
                    game_board[col][row] = None

            continue


        #Prepare for NEXT turn

        if player == 0:
            player = 1
        else:
            player = 0

# End RunGame


def DropChip( disp, final_col, final_row, color ):

    #sanity check
    if final_col < 0 or final_col >= NUMCOLS:
        raise ValueError("final_col range = [0,6]")
    if final_row < 0 or final_row >= NUMROWS:
        raise ValueError("final_row range [0,5]")


    y = STARTING_Y - (2*CHIP_RADIUS)

    x = STARTING_X + final_col * CHIP_OFFSET

    final_y = STARTING_Y + (NUMROWS-1 - final_row) * CHIP_OFFSET

    while (y <= final_y ):

        disp.clear()

        disp.draw_circle(x,y,CHIP_RADIUS, color )

        y = y+1

        DrawChips(disp)
        disp.show()
        time.sleep(FALL_DELAY)
#end DropChip


def PlaceChip( col, row, player ):
    if 0 <= row < NUMROWS and 0 <= col < NUMCOLS:
        game_board[col][row] = player
    else:
        raise IndexError("Row or column out of range")


def DrawChips(disp):
    for row in range(NUMROWS):
        for col in range(NUMCOLS):

            player = game_board[col][row]

            if ( player is not None ):

                x = STARTING_X + col * CHIP_OFFSET

                y = STARTING_Y + (NUMROWS-1 - row) * CHIP_OFFSET

                disp.draw_circle(x,y,CHIP_RADIUS, player_color[player] )

#END DrawChips



def BlinkWinningChips(disp, winning_positions, player):
    
    BLINK_COUNT = 3
    BLINK_DELAY = 0.3

    BRIGHT_GAIN = 1.4    
    DIM_GAIN    = 0.6  


    if not winning_positions:
        return
    
    # Get the base color for this player
    base_color = player_color[player]
    
    for blink in range(BLINK_COUNT):
        
        # Flash bright, then dim
        for gain in [DIM_GAIN, BRIGHT_GAIN ]:
            
            # Calculate adjusted color with gain multiplier
            adjusted_color = tuple(min(255, int(c * gain)) for c in base_color)
            
            disp.clear()
            
            DrawChips(disp)
            
            # Draw winning chips with adjusted color
            for col, row in winning_positions:
                x = STARTING_X + col * CHIP_OFFSET
                y = STARTING_Y + (NUMROWS-1 - row) * CHIP_OFFSET
                disp.draw_circle(x, y, CHIP_RADIUS, adjusted_color)
            
            disp.show()
            time.sleep(BLINK_DELAY)
#End BlinkWinningChips   



def GetNextMove(mode, player):


    player_name = "Red" if player == 0 else "Yellow"


    #--------------------------------------------------------------------
    # Random selection mode - keep trying until valid column found
    if mode == 0:

        while True:
            col = random.randint(0, 6)
            row = GetFirstOpenRow(col)
            if row is not None:
                return (col,row)

    #--------------------------------------------------------------------
    # User input mode                
    elif mode == 1:

        while True:
            try:
                # Get user input (1-7, convert to 0-6)
                user_input = input(f"{player_name} player, enter column (1-7): ")
                
                # Convert to integer
                col_input = int(user_input)
                
                # Validate range (user enters 1-7, we use 0-6)
                if col_input < 1 or col_input > 7:
                    print("Invalid column! Please enter a number between 1 and 7.")
                    continue
                
                # Convert to 0-based index
                col = col_input - 1
                
                # Check if column has space
                row = GetFirstOpenRow(col)
                if row is None:
                    print(f"Column {col_input} is full! Please choose another column.")
                    continue
                
                # Valid move found
                return  (col,row)
                
            except ValueError:
                print("Invalid input! Please enter a number between 1 and 7.")
                continue
    
    else:
        raise ValueError(f"Invalid mode: {mode}. Use 0 for random, 1 for user input.")
#GetNextMove


