
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


    turn = 0

    while True:
        col = random.randint(0, 6)

        if turn == 0:
            chip_color = (150,0,0)
        else:
            chip_color = (150,150,0)
        
        row = GetFirstOpenRow(col)
        if( row == None ):
            exit()

 
        DropChip(disp,col,row,chip_color)

        PlaceChip(col,row,turn)


        print()
        print("> ",col,row)
        print(game_board)


        time.sleep(1)


        #Prepare for NEXT turn

        if turn == 0:
            turn = 1
        else:
            turn = 0

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


def PlaceChip( col, row, value ):
    if 0 <= row < NUMROWS and 0 <= col < NUMCOLS:
        game_board[col][row] = value
    else:
        raise IndexError("Row or column out of range")

def ReadChip( col, row ):
    if 0 <= row < NUMROWS and 0 <= col < NUMCOLS:
        return game_board[col][row]
    else:
        raise IndexError("Row or column out of range")

#return (row,value) or None if FULL
def GetFirstOpenRow( col ):
    if 0 <= col < NUMCOLS:
        for row in range(NUMROWS):
            value = game_board[col][row]
            if value is None:
                return row
        return None
    else:
        raise IndexError("Column out of range")

def DrawChips(disp):
    for row in range(NUMROWS):
        for col in range(NUMCOLS):

            value = game_board[col][row]

            if ( value is not None ):

                if value == 0:
                    color = (200,0,0)
                if value == 1:
                    color = (200,200,0)

                x = STARTING_X + col * CHIP_OFFSET

                y = STARTING_Y + (NUMROWS-1 - row) * CHIP_OFFSET

                disp.draw_circle(x,y,CHIP_RADIUS, color )

#END DrawChips
