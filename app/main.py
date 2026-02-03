from display import Display
from c4_game import RunGame
from starfield import RunStarfield
from ttt_game import ttt_RunGame
from ReactionDiffusion import RunReactionDiffusion
from gameoflife import RunGameOfLife
from snake import RunSnakeGame
from matrix import RunMatrix
from pong import RunPongGame
import time

disp = Display()

disp.clear()

# Run games in an infinite loop
# Each game runs until it completes, then the next game starts
while True:

    print("="*50)
    disp.reset()
    RunPongGame(disp)

    print("="*50)
    disp.reset()
    RunMatrix(disp)

    print("="*50)
    disp.reset()
    RunSnakeGame(disp)

    print("="*50)
    disp.reset()
    RunGameOfLife(disp)

    print("="*50)
    disp.reset()
    RunGame(disp)  

    print("="*50)
    disp.reset()
    RunReactionDiffusion(disp)
    
    print("="*50)
    disp.reset()
    RunStarfield(disp)
    
    print("="*50)
    disp.reset()
    ttt_RunGame(disp)

