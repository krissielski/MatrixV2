# display.by
# Basic control functions for the display
# 
#  (0,0)
#       *-----> +X 
#       |    
#       |
#    +Y |
#
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

class Display:
    def __init__(self):
        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1

        self.matrix = RGBMatrix(options=options)
        self.canvas = self.matrix.CreateFrameCanvas()
        self.width = self.canvas.width
        self.height = self.canvas.height

        self.font = graphics.Font()
        # self.font.LoadFont("fonts/5x7.bdf")
        self.font.LoadFont("fonts/5x8.bdf")
        # self.font.LoadFont("fonts/4x6.bdf")

        #Overlay settings
        self.overlay_type  = 1          #0=subtractive, 1=additive    
        self.overlay_color = (0,0,0)
        self.overlay = [[0 for _ in range(self.width)] for _ in range(self.height)]

        #Text
        self.font_color = graphics.Color(0, 0, 0)
        self.font_pos   = (0,0)
        self.font_text  = ""


    # ---- Base drawing ----
    def background(self, color=(0, 0, 0)):
        r, g, b = color
        for x in range(self.width):
            for y in range(self.height):
                self.canvas.SetPixel(x, y, r, g, b)

    def clear(self):
        self.background( (0,0,0) )          

    def draw_square(self, x, y, size, color):
        r, g, b = color
        for yy in range(y, y + size):
            for xx in range(x, x + size):
                if 0 <= xx < self.width and 0 <= yy < self.height:
                    self.canvas.SetPixel(xx, yy, r, g, b)

    def draw_rectangle(self, x, y, width, height, color):
        r, g, b = color
        for yy in range(y, y + height):
            for xx in range(x, x + width):
                if 0 <= xx < self.width and 0 <= yy < self.height:
                    self.canvas.SetPixel(xx, yy, r, g, b)

    def draw_circle(self, cx, cy, radius, color):
        r, g, b = color
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x*x + y*y < radius*radius:
                    px, py = cx + x, cy + y
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.canvas.SetPixel(px, py, r, g, b)
    
    # ---- Text ----
    def text_set(self,x,y,color,text):
        r, g, b = color
        self.font_pos   = (x,y)
        self.font_color = graphics.Color(r,g,b)
        self.font_text  = text

    def text_render(self):
        x,y = self.font_pos
        graphics.DrawText(self.canvas, self.font, x,y, self.font_color, self.font_text)


    # ---- Overlay drawing ----
    def overlay_set_color(self, color):
        self.overlay_color = color

    def overlay_set_type(self, overlay_type):
        self.overlay_type = overlay_type
    
    def overlay_set_pixel(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.overlay[y][x] = 1

    def overlay_circle(self, cx, cy, radius):
        for y in range(-radius, radius + 1):
            for x in range(-radius, radius + 1):
                if x*x + y*y < radius*radius:
                    px, py = cx + x, cy + y
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.overlay[py][px] = 1

    def overlay_square(self, x, y, size):
        for yy in range(y, y + size):
            for xx in range(x, x + size):
                if 0 <= xx < self.width and 0 <= yy < self.height:
                    self.overlay[yy][xx] = 1

    def overlay_rectangle(self, x, y, width, height):
        for yy in range(y, y + height):
            for xx in range(x, x + width):
                if 0 <= xx < self.width and 0 <= yy < self.height:
                    self.overlay[yy][xx] = 1

    def overlay_render(self):
        r, g, b = self.overlay_color
        for y in range(self.height):
            for x in range(self.width):

                if self.overlay[y][x]:
                    if self.overlay_type == 1:
                        #Additive
                        self.canvas.SetPixel(x, y, r, g, b)
                else:
                    if self.overlay_type == 0:
                        #subtractive
                        self.canvas.SetPixel(x, y, r, g, b)         



    # Draw overlay on canvas then write to display
    def show(self):
        self.overlay_render()
        self.text_render()
        self.canvas = self.matrix.SwapOnVSync(self.canvas)
