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

        #No need for a high refresh rate 
        options.pwm_lsb_nanoseconds = 200
        #options.pwm_dither_bits = 0
        #options.pwm_bits = 7


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

    def set_pixel(self, x, y, r, g, b):
        self.canvas.SetPixel(x, y, r, g, b)


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
    

    def draw_o(self, cx, cy, outer_radius, width, color):
        """
        Draw an 'O' shape - a circle with a hollow center
        
        Args:
            cx, cy: Center coordinates
            outer_radius: Outer radius of the O
            width: Width of the ring/stroke
            color: RGB color tuple
        """
        inner_radius = outer_radius - width
        r, g, b = color
        for y in range(-outer_radius, outer_radius + 1):
            for x in range(-outer_radius, outer_radius + 1):
                distance_squared = x*x + y*y
                # Check if point is within outer circle but outside inner circle
                if (distance_squared < outer_radius*outer_radius and 
                    distance_squared >= inner_radius*inner_radius):
                    px, py = cx + x, cy + y
                    if 0 <= px < self.width and 0 <= py < self.height:
                        self.canvas.SetPixel(px, py, r, g, b)

    def draw_line(self, x1, y1, x2, y2, color):
        """
        Draw a line between two points using Bresenham's line algorithm
        
        Args:
            x1, y1: Starting point coordinates
            x2, y2: Ending point coordinates
            color: RGB color tuple
        """
        r, g, b = color
        
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        x, y = x1, y1
        
        # Determine direction of line
        x_inc = 1 if x1 < x2 else -1
        y_inc = 1 if y1 < y2 else -1
        
        # Bresenham's algorithm
        if dx > dy:
            # Line is more horizontal than vertical
            error = dx / 2
            while x != x2:
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.canvas.SetPixel(x, y, r, g, b)
                error -= dy
                if error < 0:
                    y += y_inc
                    error += dx
                x += x_inc
        else:
            # Line is more vertical than horizontal
            error = dy / 2
            while y != y2:
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.canvas.SetPixel(x, y, r, g, b)
                error -= dx
                if error < 0:
                    x += x_inc
                    error += dy
                y += y_inc
        
    def draw_x(self, center_x, center_y, height, line_width, color):
        """
        Draw an 'X' shape using two diagonal lines
        
        Args:
            center_x, center_y: Center coordinates of the X
            height: Height (and width) of the X
            line_width: Width of each line stroke
            color: RGB color tuple
        """
        half_up = height // 2
        half_down = height - half_up + 1  # Add 1 to account for center pixel
        
        # Calculate the four corner points
        x1, y1 = center_x - half_up, center_y - half_up      # Top-left
        x2, y2 = center_x + half_down, center_y + half_down  # Bottom-right
        x3, y3 = center_x + half_down, center_y - half_up    # Top-right
        x4, y4 = center_x - half_up, center_y + half_down    # Bottom-left
    
        
        # Draw multiple parallel lines to create line width
        for i in range(line_width):
            offset = i - line_width // 2
            
            # First diagonal: top-left to bottom-right
            self.draw_line(x1 + offset, y1, x2 + offset, y2, color)
            self.draw_line(x1, y1 + offset, x2, y2 + offset, color)
            
            # Second diagonal: top-right to bottom-left  
            self.draw_line(x3 - offset, y3, x4 - offset, y4, color)
            self.draw_line(x3, y3 + offset, x4, y4 + offset, color)





    # ---- Text ----
    def text_set(self,x,y,color,text):
        r, g, b = color
        self.font_pos   = (x,y)
        self.font_color = graphics.Color(r,g,b)
        self.font_text  = text

    def text_render(self):
        x,y = self.font_pos
        graphics.DrawText(self.canvas, self.font, x,y, self.font_color, self.font_text)

    def text_loadFont(self,fontname):
        self.font.LoadFont("fonts/"+fontname)


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
