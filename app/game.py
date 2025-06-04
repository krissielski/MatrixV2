
from display import Display
import time
import random


NUMROWS     = 6
NUMCOLS     = 7

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

    while True:

        #Check for Draw
        if CheckForDraw():
            print("   DRAW!!!!!!!!!!!")
            time.sleep(5)
            exit()            

        # Randomly pick columns until a row is found
        row = None
        while row is None:
            col = random.randint(0, 6)
            row = GetFirstOpenRow(col)


        DropChip(disp,col,row, player_color[player] )

        PlaceChip(col,row,player)

        time.sleep(2)

        winner = CheckForWinner(col,row,player)
        if winner is not None:
            print("Winner!!!", col, row)
            print(winner)

            #delay and reset
            time.sleep(5)
            player = 0
            # Clear the game board
            for col in range(NUMCOLS):
                for row in range(NUMROWS):
                    game_board[col][row] = None


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

def ReadChip( col, row ):
    if 0 <= row < NUMROWS and 0 <= col < NUMCOLS:
        return game_board[col][row]
    else:
        raise IndexError("Row or column out of range")

#return row or None if FULL
def GetFirstOpenRow( col ):
    if 0 <= col < NUMCOLS:
        for row in range(NUMROWS):
            if game_board[col][row] is None:
                return row
        return None
    else:
        raise IndexError("Column out of range")


def DrawChips(disp):
    for row in range(NUMROWS):
        for col in range(NUMCOLS):

            player = game_board[col][row]

            if ( player is not None ):

                x = STARTING_X + col * CHIP_OFFSET

                y = STARTING_Y + (NUMROWS-1 - row) * CHIP_OFFSET

                disp.draw_circle(x,y,CHIP_RADIUS, player_color[player] )

#END DrawChips

#-----------------------------------------------------------------
#

#returns a list of winning positions, or None if no winner found
def CheckForWinner(col, row, player):
    
    # Validate input parameters
    if not (0 <= col < NUMCOLS and 0 <= row < NUMROWS):
        raise IndexError("Invalid board position")
    
    # Check if the position actually contains the player's chip
    if ReadChip(col, row) != player:
        return None
    
    # Check all four directions for 4-in-a-row
    directions = [
        (0, 1),   # Horizontal
        (1, 0),   # Vertical  
        (1, 1),   # Diagonal (bottom-left to top-right)
        (1, -1)   # Diagonal (top-left to bottom-right)
    ]
    
    for dx, dy in directions:

        count = 1                   # Count the chip at the starting position
        positions = [(col,row)]     # Include the starting position
        
        # Check in positive direction
        c, r = col + dx, row + dy
        while (0 <= c < NUMCOLS and 0 <= r < NUMROWS and ReadChip(c, r) == player):
            positions.append( (c,r) )
            count += 1
            c += dx
            r += dy
        
        # Check in negative direction  
        c, r = col - dx, row - dy
        while (0 <= c < NUMCOLS and 0 <= r < NUMROWS and ReadChip(c, r) == player):
            positions.append( (c,r) )
            count += 1
            c -= dx
            r -= dy
        
        #Check for at least 4 in a row
        if len(positions) >= 4:
            return positions
    
    #Nope, none found
    return None


def CheckForDraw():
    for col in range(NUMCOLS):
        if GetFirstOpenRow(col) is not None:
            return False
    return True

