from display import Display
from c4_game import RunGame
from starfield import RunStarfield
from ttt_game import ttt_RunGame
from ReactionDiffusion import RunReactionDiffusion
import time

disp = Display()

disp.clear()
#disp.draw_square(5, 5, 10,   (255, 0, 0))
#disp.draw_circle(45, 30, 10, (0, 255, 0))


RunReactionDiffusion(disp)

RunGame(disp)
#RunStarfield(disp)
#ttt_RunGame(disp)



#disp.show()
#time.sleep(7)
