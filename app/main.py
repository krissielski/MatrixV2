from display import Display
from c4_game import RunGame
from starfield import RunStarfield
from ttt_game import ttt_RunGame
from ReactionDiffusion import RunReactionDiffusion
import time

disp = Display()

disp.clear()

# Run games in an infinite loop
# Each game runs until it completes, then the next game starts
while True:

    print("\n" + "="*50)
    print("Starting Connect4")
    print("="*50)
    disp.reset()
    RunGame(disp)  


    print("\n" + "="*50)
    print("Starting Reaction-Diffusion")
    print("="*50)
    disp.reset()
    RunReactionDiffusion(disp)
    
    print("\n" + "="*50)
    print("Starting Starfield")
    print("="*50)
    disp.reset()
    RunStarfield(disp)
    
    print("\n" + "="*50)
    print("Starting TicTacToe")
    print("="*50)
    disp.reset()
    ttt_RunGame(disp)

