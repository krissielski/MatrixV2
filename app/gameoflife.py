import random
import time

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
RUNTIME_SECONDS = 200  # How long the game runs (in seconds). Default 300s
FRAME_TIME_MS = 500    # Time between each generation update (in milliseconds). Default 500ms
STARTING_DENSITY = 0.2 # Initial population density (0.0 to 1.0). Default 0.3
COLOR_CYCLE_SPEED = 0.005  # Speed of color hue rotation (0.001-0.01)
# ============================================================================

class GameOfLife:
    def __init__(self, width=64, height=64, density=STARTING_DENSITY):
        """
        Initialize Conway's Game of Life
        
        Args:
            width: Width of the game board (default 64)
            height: Height of the game board (default 64)
            density: Initial population density (0.0 to 1.0, default STARTING_DENSITY)
        """
        self.width = width
        self.height = height
        
        # Create the game board: True = alive, False = dead
        self.board = [[random.random() < density for _ in range(width)] for _ in range(height)]
        
        self.generation = 0
        
        # Color hue offset (cycles through spectrum)
        self.hue_offset = 0.0
    
    def _count_neighbors(self, x, y):
        """Count live neighbors around cell (x, y)"""
        count = 0
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                
                nx = x + dx
                ny = y + dy
                
                # Check bounds (edges are dead)
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.board[ny][nx]:
                        count += 1
        
        return count
    
    def update(self):
        """Apply Conway's Game of Life rules and update the board"""
        new_board = [[False for _ in range(self.width)] for _ in range(self.height)]
        
        for y in range(self.height):
            for x in range(self.width):
                neighbors = self._count_neighbors(x, y)
                is_alive = self.board[y][x]
                
                # Apply Conway's Game of Life rules
                if is_alive:
                    # A live cell with 2-3 live neighbors survives
                    if neighbors in [2, 3]:
                        new_board[y][x] = True
                    # Otherwise it dies (overpopulation or underpopulation)
                else:
                    # A dead cell with exactly 3 live neighbors becomes alive
                    if neighbors == 3:
                        new_board[y][x] = True
        
        self.board = new_board
        self.generation += 1
        
        # Update color hue
        self.hue_offset += COLOR_CYCLE_SPEED
        if self.hue_offset >= 1.0:
            self.hue_offset -= 1.0
    
    def get_pixels(self):
        """Return list of pixels to draw: [(x, y, r, g, b), ...]"""
        pixels = []
        
        # Convert hue offset to current hue (0-359)
        current_hue = int(self.hue_offset * 359)
        
        for y in range(self.height):
            for x in range(self.width):
                if self.board[y][x]:
                    # Live cells cycle through rainbow colors
                    r, g, b = self._hsv_to_rgb(current_hue, 255, 255)
                    pixels.append((x, y, r, g, b))
        
        return pixels
    
    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB. h=0-359, s=0-255, v=0-255"""
        h = h % 360
        s = s / 255.0
        v = v / 255.0
        
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))
    
    def count_population(self):
        """Return the number of live cells"""
        return sum(sum(row) for row in self.board)


def RunGameOfLife(disp, runtime_seconds=RUNTIME_SECONDS, frame_time_ms=FRAME_TIME_MS):
    """
    Run Conway's Game of Life

    """
    
    start_time = time.time()
    last_update_time = start_time
    
    game = GameOfLife(disp.width, disp.height, density=STARTING_DENSITY)
    
    while True:
        current_time = time.time()
        
        # Update game state based on frame time
        if (current_time - last_update_time) >= (frame_time_ms / 1000.0):
            game.update()
            last_update_time = current_time
            
            # Get pixels and draw only after update
            pixel_list = game.get_pixels()
            
            disp.clear()
            
            # Draw each pixel
            for x, y, r, g, b in pixel_list:
                disp.set_pixel(x, y, r, g, b)
            
            disp.show()
            
            #population = game.count_population()
            #print(f"Generation {game.generation}: {population} cells alive")
        else:
            # Small sleep to prevent busy-waiting when waiting for next frame
            time.sleep(0.1)
        
        # Check if runtime limit exceeded
        if current_time >= start_time + runtime_seconds:
            population = game.count_population()
            print(f"Game of Life runtime limit ({runtime_seconds} seconds) reached")
            print(f"   Final generation: {game.generation}: {population} cells alive")
            time.sleep(3.0)
            return
