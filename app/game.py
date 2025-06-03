
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


def RunGame( disp ):

    disp.overlay_set_color((0,0,110))
    disp.overlay_set_type(0)

    #Generate overlay:
    for c in range (NUMCOLS):
        for r in range (NUMROWS):

            x = STARTING_X + c * CHIP_OFFSET
            y = STARTING_Y + r * CHIP_OFFSET

            disp.overlay_circle(x, y, CHIP_RADIUS)


    while True:
        col = random.randint(0, 6)
        print("Col= ",col)
        DropChip(disp,col,5)
        time.sleep(1)

# End RunGame


def DropChip( disp, final_col, final_row ):

    #sanity check
    if final_col < 0 or final_col >= NUMCOLS:
        raise ValueError("final_col range = [0,6]")
    if final_row < 0 or final_row >= NUMROWS:
        raise ValueError("final_row range [0,5]")


    y = STARTING_Y - (2*CHIP_RADIUS)

    x = STARTING_X + final_col * CHIP_OFFSET

    final_y = STARTING_Y + final_row * CHIP_OFFSET

    while (y <= final_y ):

        disp.clear()

        disp.draw_circle(x,y,CHIP_RADIUS, (150,0,0) )

        y = y+1
        disp.show()
        time.sleep(FALL_DELAY)
#end DropChip
