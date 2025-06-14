import random
import math
import time

# Starfield class
class StarField:
    def __init__(self, width=64, height=64, num_stars=100, speed=2.0):
        self.width = width
        self.height = height
        self.num_stars = num_stars
        self.speed = speed
        self.center_x = width // 2
        self.center_y = height // 2
        
        # List to store star data: [x, y, z, r, g, b, trail_positions]
        self.stars = []
        
        # Initialize stars
        for _ in range(num_stars):
            self._create_star()
    
    def _create_star(self):
        """Create a new star at a random position"""
        # Start stars near the center so they can expand outward
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(1, 15)  # Start close to center
        x = self.center_x + distance * math.cos(angle)
        y = self.center_y + distance * math.sin(angle)
        z = random.uniform(50, 200)  # Distance from viewer
        
        # Randomize star colors - give each star a base color type
        star_type = random.choice(['white', 'blue', 'red', 'yellow', 'cyan', 'magenta'])
        if star_type == 'white':
            base_r, base_g, base_b = 255, 255, 255
        elif star_type == 'blue':
            base_r, base_g, base_b = 100, 150, 255
        elif star_type == 'red':
            base_r, base_g, base_b = 255, 100, 100
        elif star_type == 'yellow':
            base_r, base_g, base_b = 255, 255, 100
        elif star_type == 'cyan':
            base_r, base_g, base_b = 100, 255, 255
        else:  # magenta
            base_r, base_g, base_b = 255, 100, 255
        
        # Trail positions for streak effect (list of previous positions)
        trail_positions = []
        
        self.stars.append([x, y, z, base_r, base_g, base_b, trail_positions])
    
    def update(self):
        """Update all star positions and colors"""
        updated_stars = []
        
        for star in self.stars:
            x, y, z, base_r, base_g, base_b, trail_positions = star
            
            # Move star closer (decrease z)
            z -= self.speed
            
            # If star is too close, respawn it far away
            if z <= 1.0:
                # Create new star near center so it can expand outward
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(1, 15)  # Start close to center
                x = self.center_x + distance * math.cos(angle)
                y = self.center_y + distance * math.sin(angle)
                z = random.uniform(150, 200)
                trail_positions = []
                
                # Give new star a random color
                star_type = random.choice(['white', 'blue', 'red', 'yellow', 'cyan', 'magenta'])
                if star_type == 'white':
                    base_r, base_g, base_b = 255, 255, 255
                elif star_type == 'blue':
                    base_r, base_g, base_b = 100, 150, 255
                elif star_type == 'red':
                    base_r, base_g, base_b = 255, 100, 100
                elif star_type == 'yellow':
                    base_r, base_g, base_b = 255, 255, 100
                elif star_type == 'cyan':
                    base_r, base_g, base_b = 100, 255, 255
                else:  # magenta
                    base_r, base_g, base_b = 255, 100, 255
            else:
                # Calculate movement toward center (warp effect)
                # Direction vector from current position to center
                dx = x-self.center_x
                dy = y-self.center_y 
                
                # Normalize and apply perspective based on distance
                distance_to_center = math.sqrt(dx*dx + dy*dy)
                if distance_to_center > 0:
                    # Movement factor increases as star gets closer (lower z)
                    movement_factor = (200 - z) / 200.0 * 0.5
                    x += dx * movement_factor / distance_to_center
                    y += dy * movement_factor / distance_to_center
                
                # Update trail positions (add current position to trail)
                trail_positions.append((int(x), int(y)))
                # Keep only last few positions for trail
                if len(trail_positions) > 4:
                    trail_positions.pop(0)
            
            # Calculate brightness based on distance
            brightness_factor = min(1.0, max(0.2, (200 - z) / 200))
            
            # Apply brightness to base color (preserve the star's color but make it brighter/dimmer)
            r = int(base_r * brightness_factor)
            g = int(base_g * brightness_factor)
            b = int(base_b * brightness_factor)
            
            updated_stars.append([x, y, z, base_r, base_g, base_b, trail_positions])
        
        self.stars = updated_stars
    
    def get_pixels(self):
        """Return list of pixels to draw: [(x, y, r, g, b), ...]"""
        pixels = []
        
        for star in self.stars:
            x, y, z, base_r, base_g, base_b, trail_positions = star
            
            # Calculate current display color based on distance
            brightness_factor = min(1.0, max(0.2, (200 - z) / 200))
            r = int(base_r * brightness_factor)
            g = int(base_g * brightness_factor)
            b = int(base_b * brightness_factor)
            
            # Only draw stars that are on screen
            if 0 <= x < self.width and 0 <= y < self.height:
                pixels.append((int(x), int(y), r, g, b))
                
                # Draw trail/streak effect for fast-moving close stars
                if z < 80 and len(trail_positions) > 1:
                    for i, (trail_x, trail_y) in enumerate(trail_positions[:-1]):
                        if 0 <= trail_x < self.width and 0 <= trail_y < self.height:
                            # Fade trail based on position in trail
                            fade = (i + 1) / len(trail_positions) * 0.6
                            trail_r = int(r * fade)
                            trail_g = int(g * fade)
                            trail_b = int(b * fade)
                            # Only add trail if it's bright enough to be visible
                            if trail_r + trail_g + trail_b > 30:
                                pixels.append((trail_x, trail_y, trail_r, trail_g, trail_b))
        
        return pixels
    



def RunStarfield(disp):

    print("Running Starfield")

    start_time = time.time()

    starfield = StarField(disp.width, disp.height, num_stars=100, speed=2.0)

    while(1):
        starfield.update()

        pixel_list = starfield.get_pixels()

        disp.clear()

        # Draw each pixel
        for x, y, r, g, b in pixel_list:
            disp.set_pixel(x,y,r,g,b)


        disp.show()
        time.sleep(.01)

