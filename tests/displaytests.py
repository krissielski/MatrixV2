import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

# Set up display options
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1


matrix = RGBMatrix(options=options)
canvas = matrix.CreateFrameCanvas()

# 
#  (0,0)
#       *-----> +X 
#       |    
#       |
#    +Y |


# Define colors
bg_color     = graphics.Color(0, 0, 60)  
square_color = graphics.Color(200, 0, 0)   
circle_color = graphics.Color(200, 200, 0) 

# Fill background
for x in range(64):
    for y in range(64):
        canvas.SetPixel(x, y, bg_color.red, bg_color.green, bg_color.blue)

# Draw filled square (top-left corner at 10,10; size 20x20)
for y in range(10, 30):
    graphics.DrawLine(canvas, 10, y, 29, y, square_color)

# Draw filled circle (center at 48, 32; radius 10)
cx, cy, r = 48, 32, 5
for y in range(-r, r + 1):
    for x in range(-r, r + 1):
        if x*x + y*y < r*r:
            canvas.SetPixel(cx + x, cy + y, circle_color.red, circle_color.green, circle_color.blue)


# Show it
matrix.SwapOnVSync(canvas)

# Keep displayed
time.sleep(5)
