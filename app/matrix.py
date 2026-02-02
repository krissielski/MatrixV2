import random
import time

RUNTIME_SECONDS = 60
DEFAULT_NUM_COLUMNS = 15

class MatrixRain:
    def __init__(self, width=64, height=64, num_columns=15):
        self.width = width
        self.height = height
        self.num_columns = num_columns
        
        self.speed_min = 20
        self.speed_max = 40
        self.trail_min = 8
        self.trail_max = 16
        
        self.columns = []
        
        for i in range(min(num_columns, width)):
            x_pos = int(i * width / num_columns)
            
            speed = random.uniform(self.speed_min, self.speed_max)
            trail_length = random.randint(self.trail_min, self.trail_max)
            delay = random.uniform(0, 3)
            
            start_y = -trail_length - random.uniform(0, 20)
            
            column = {
                'x': x_pos,
                'y': start_y,
                'speed': speed,
                'trail_length': trail_length,
                'delay': delay,
                'delay_remaining': delay,
                'active': False
            }
            self.columns.append(column)
    
    def update(self, delta_time):
        for column in self.columns:
            if column['delay_remaining'] > 0:
                column['delay_remaining'] -= delta_time
                if column['delay_remaining'] <= 0:
                    column['active'] = True
                continue
            
            if column['active']:
                column['y'] += column['speed'] * delta_time
                
                if column['y'] >= self.height + column['trail_length']:
                    column['y'] = -column['trail_length'] - random.uniform(0, 20)
                    column['speed'] = random.uniform(self.speed_min, self.speed_max)
                    column['trail_length'] = random.randint(self.trail_min, self.trail_max)
    
    def get_pixels(self):
        pixels = []
        
        for column in self.columns:
            if not column['active']:
                continue
            
            x = column['x']
            y = column['y']
            trail_length = column['trail_length']
            
            for i in range(trail_length):
                current_y = int(y - i)
                
                if 0 <= current_y < self.height:
                    ratio = i / trail_length
                    
                    if i == 0 or i == 1:
                        r, g, b = 0, 255, 0
                    else:
                        r = 0
                        g = int(255 * (1 - ratio))
                        b = 0
                        g = max(g, 30)
                    
                    if g > 0:
                        pixels.append((x, current_y, r, g, b))
        
        return pixels


def RunMatrix(disp):
    print("Running Matrix Rain")
    
    start_time = time.time()
    last_update = time.time()
    
    matrix_rain = MatrixRain(disp.width, disp.height, num_columns=DEFAULT_NUM_COLUMNS)
    
    while True:
        current_time = time.time()
        delta_time = current_time - last_update
        last_update = current_time
        
        matrix_rain.update(delta_time)
        
        pixel_list = matrix_rain.get_pixels()
        
        disp.clear()
        
        for x, y, r, g, b in pixel_list:
            disp.set_pixel(x, y, r, g, b)
        
        disp.show()
        time.sleep(0.01)
        
        elapsed = current_time - start_time
        if elapsed >= RUNTIME_SECONDS:
            print(f"Matrix runtime limit ({RUNTIME_SECONDS} seconds) reached")
            return