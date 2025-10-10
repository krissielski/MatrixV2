"""
Reaction-Diffusion Pattern Generator for 64x64 RGB LED Matrix

Implements the Gray-Scott reaction-diffusion algorithm to generate continuously
evolving organic patterns. Optimized for Raspberry Pi with vectorized NumPy operations.

Algorithm: Gray-Scott model simulates two chemicals (A and B) that react and diffuse:
- A is consumed and converted to B in the reaction
- B decays back to an inert product
- Both chemicals diffuse at different rates

Limitations:
- Fixed boundaries (no wrapping) to improve cache performance
- Requires NumPy for vectorization
"""

import numpy as np
import time
import random

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================

# Diffusion rates (higher = faster spreading)
DIFFUSION_A = 1.0      # Diffusion rate for chemical A (typically 1.0)
DIFFUSION_B = 0.5      # Diffusion rate for chemical B (typically 0.5)

# Gray-Scott reaction parameters (these create different pattern types)
FEED_RATE = 0.055      # Feed rate: how fast A is added (0.01-0.1)
KILL_RATE = 0.062      # Kill rate: how fast B is removed (0.045-0.07)
                       # Try: (0.055, 0.062) for spots/stripes
                       #      (0.039, 0.058) for worms
                       #      (0.035, 0.065) for waves

# Simulation speed
TIME_STEP = 1.05      # Time step per frame (0.5-2.0, higher = faster evolution)

# Color settings
BACKGROUND_COLOR = (0, 0, 0)      # RGB for background (low B concentration)
COLOR_CYCLE_SPEED = 0.005           # Speed of color hue rotation (0.001-0.01)
BRIGHTNESS = 200                    # Max brightness for patterns (0-255)

# Pattern change settings
FRAMES_PER_PATTERN = 1500  # Frames before switching to new seed pattern

# ============================================================================


class ReactionDiffusion:
    def __init__(self, width=64, height=64):
        """
        Initialize the Reaction-Diffusion system.
        
        Args:
            width: Grid width (default 64)
            height: Grid height (default 64)
        """
        self.width = width
        self.height = height
        
        # Chemical concentration grids (single precision for speed)
        self.A = np.ones((height, width), dtype=np.float32)
        self.B = np.zeros((height, width), dtype=np.float32)
        
        # Color hue offset (cycles through spectrum)
        self.hue_offset = 0.0
        
        # Precompute Laplacian weights for manual convolution
        # Using 3x3 kernel with center weight = -1, neighbors sum to 1
        self.w_center = -1.0
        self.w_adjacent = 0.2
        self.w_diagonal = 0.05
        
        # Precompute RGB lookup table for faster HSV->RGB conversion
        # This eliminates expensive trig and conditional operations per pixel
        self._build_color_lut()
        
        # Frame counter and pattern list
        self.frame_count = 0
        self.current_pattern = 0
        self.pattern_types = [
#           'random_noise',
            'central_spot',
            'multiple_dots',
            'stripes_horizontal',
            'stripes_vertical',
            'diagonal',
            'worms',
            'ring',
            'corners'
        ]
        
        # Initialize with first pattern
        self._seed_pattern(self.pattern_types[0])
    
    def _build_color_lut(self):
        """
        Precompute color lookup table for HSV to RGB conversion.
        Creates 256 hues x 256 intensities for instant lookup.
        This is a major optimization - converts O(n) trig operations to O(1) lookup.
        """
        # Create smaller LUT: 360 hues x 64 intensity levels
        # We'll interpolate for sub-pixel accuracy if needed
        self.color_lut = np.zeros((360, 64, 3), dtype=np.uint8)
        
        for h in range(360):
            hue = h / 360.0
            for v_idx in range(64):
                v = v_idx / 63.0
                
                # HSV to RGB conversion
                # S=1 (full saturation), V varies with intensity
                hi = int(hue * 6)
                f = (hue * 6) - hi
                p = 0
                q = v * (1 - f)
                t = v * f
                
                if hi == 0:
                    r, g, b = v, t, p
                elif hi == 1:
                    r, g, b = q, v, p
                elif hi == 2:
                    r, g, b = p, v, t
                elif hi == 3:
                    r, g, b = p, q, v
                elif hi == 4:
                    r, g, b = t, p, v
                else:
                    r, g, b = v, p, q
                
                self.color_lut[h, v_idx] = [
                    int(r * BRIGHTNESS),
                    int(g * BRIGHTNESS),
                    int(b * BRIGHTNESS)
                ]
    
    def _seed_pattern(self, pattern_type):
        """
        Initialize the grid with a specific seed pattern.
        
        Args:
            pattern_type: String identifying the pattern type
        """
        # Reset to base state
        self.A.fill(1.0)
        self.B.fill(0.0)
        
        h, w = self.height, self.width
        cx, cy = w // 2, h // 2
        
        if pattern_type == 'random_noise':
            # Random scattered points
            noise_mask = np.random.rand(h, w) > 0.90
            self.B[noise_mask] = 1.0
            
        elif pattern_type == 'central_spot':
            # Single large spot in center
            y, x = np.ogrid[:h, :w]
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            self.B[dist < 8] = 1.0
            
        elif pattern_type == 'multiple_dots':
            # Several random spots
            for _ in range(random.randint(5, 12)):
                dx = random.randint(-w//3, w//3)
                dy = random.randint(-h//3, h//3)
                y, x = np.ogrid[:h, :w]
                dist = np.sqrt((x - cx - dx)**2 + (y - cy - dy)**2)
                self.B[dist < random.randint(2, 5)] = 1.0
                
        elif pattern_type == 'stripes_horizontal':
            # Horizontal stripes
            for y in range(0, h, 8):
                if y < h:
                    self.B[y:min(y+3, h), :] = 1.0
                    
        elif pattern_type == 'stripes_vertical':
            # Vertical stripes
            for x in range(0, w, 8):
                if x < w:
                    self.B[:, x:min(x+3, w)] = 1.0
                    
        elif pattern_type == 'diagonal':
            # Diagonal stripes
            for i in range(-h, w, 10):
                for offset in range(3):
                    for y in range(h):
                        x = i + y + offset
                        if 0 <= x < w:
                            self.B[y, x] = 1.0
                            
        elif pattern_type == 'worms':
            # Random "worm" lines
            for _ in range(random.randint(3, 6)):
                x = random.randint(5, w-5)
                y = random.randint(5, h-5)
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                for step in range(random.randint(10, 25)):
                    if 0 <= x < w and 0 <= y < h:
                        self.B[max(0, y-1):min(h, y+2), max(0, x-1):min(w, x+2)] = 1.0
                    x += dx
                    y += dy
                    if random.random() < 0.2:
                        dx = random.choice([-1, 0, 1])
                        dy = random.choice([-1, 0, 1])
                        
        elif pattern_type == 'ring':
            # Ring pattern
            y, x = np.ogrid[:h, :w]
            dist = np.sqrt((x - cx)**2 + (y - cy)**2)
            self.B[(dist > 12) & (dist < 18)] = 1.0
            
        elif pattern_type == 'corners':
            # Spots in corners
            corner_size = 6
            self.B[0:corner_size, 0:corner_size] = 1.0
            self.B[0:corner_size, -corner_size:] = 1.0
            self.B[-corner_size:, 0:corner_size] = 1.0
            self.B[-corner_size:, -corner_size:] = 1.0
    
    def _laplacian_fast(self, grid):
        """
        Optimized Laplacian using direct array slicing.
        This is faster than generic convolution.
        
        Args:
            grid: 2D numpy array
            
        Returns:
            Laplacian of the grid
        """
        # Pad once with edge values (reflection)
        padded = np.pad(grid, pad_width=1, mode='edge')
        
        # Manual 3x3 convolution using slicing - much faster than loops
        result = (
            self.w_center * padded[1:-1, 1:-1] +
            self.w_adjacent * (padded[0:-2, 1:-1] + padded[2:, 1:-1] + 
                              padded[1:-1, 0:-2] + padded[1:-1, 2:]) +
            self.w_diagonal * (padded[0:-2, 0:-2] + padded[0:-2, 2:] + 
                              padded[2:, 0:-2] + padded[2:, 2:])
        )
        
        return result
    
    def update(self):
        """
        Update the reaction-diffusion system for one time step.
        Uses vectorized operations for performance.
        """
        # Check if it's time to change pattern
        self.frame_count += 1
        if self.frame_count >= FRAMES_PER_PATTERN:
            self.frame_count = 0
            self.current_pattern = (self.current_pattern + 1) % len(self.pattern_types)
            self._seed_pattern(self.pattern_types[self.current_pattern])
            print(f"Switching to pattern: {self.pattern_types[self.current_pattern]}")
        
        # Compute Laplacians (diffusion)
        laplacian_A = self._laplacian_fast(self.A)
        laplacian_B = self._laplacian_fast(self.B)
        
        # Gray-Scott reaction-diffusion equations (vectorized)
        # Compute reaction term once
        AB2 = self.A * self.B * self.B
        
        # Update in-place for memory efficiency
        self.A += (DIFFUSION_A * laplacian_A - AB2 + 
                   FEED_RATE * (1 - self.A)) * TIME_STEP
        self.B += (DIFFUSION_B * laplacian_B + AB2 - 
                   (KILL_RATE + FEED_RATE) * self.B) * TIME_STEP
        
        # Clamp values (in-place)
        np.clip(self.A, 0, 1, out=self.A)
        np.clip(self.B, 0, 1, out=self.B)
        
        # Update color hue
        self.hue_offset += COLOR_CYCLE_SPEED
        if self.hue_offset >= 1.0:
            self.hue_offset -= 1.0
    
    def get_pixels(self):
        """
        Convert current state to RGB pixel list.
        Background = BACKGROUND_COLOR, patterns cycle through rainbow.
        
        Returns:
            List of tuples: [(x, y, r, g, b), ...]
        """
        pixels = []
        
        # Current hue (0-359)
        current_hue = int(self.hue_offset * 359)
        
        # Convert B concentration to intensity (0-63 for LUT)
        # Use fast numpy operations
        intensity_raw = (self.B * 63).astype(np.int32)
        np.clip(intensity_raw, 0, 63, out=intensity_raw)
        
        # Process all pixels at once using vectorization
        for y in range(self.height):
            for x in range(self.width):
                b_val = self.B[y, x]
                
                if b_val < 0.1:
                    # Background color
                    pixels.append((x, y, BACKGROUND_COLOR[0], 
                                 BACKGROUND_COLOR[1], BACKGROUND_COLOR[2]))
                else:
                    # Get color from LUT
                    intensity_idx = intensity_raw[y, x]
                    r, g, b = self.color_lut[current_hue, intensity_idx]
                    pixels.append((x, y, int(r), int(g), int(b)))
        
        return pixels


def RunReactionDiffusion(disp):
    """
    Main loop for running the reaction-diffusion visualization.
    
    Args:
        disp: Display object with clear(), set_pixel(), and show() methods
    """
    print("Running Reaction-Diffusion")
    
    rd = ReactionDiffusion(disp.width, disp.height)
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        # Update simulation
        rd.update()
        
        # Get pixel data
        pixel_list = rd.get_pixels()
        
        # Clear display
        disp.clear()
        
        # Draw each pixel
        for x, y, r, g, b in pixel_list:
            disp.set_pixel(x, y, r, g, b)
        
        # Show frame
        disp.show()
        
        # Performance monitoring (every 100 frames)
        frame_count += 1
        if frame_count % 100 == 0:
            elapsed = time.time() - start_time
            fps = 100 / elapsed
            print(f"FPS: {fps:.2f}")
            start_time = time.time()
        
        # Small delay to prevent maxing out CPU
        time.sleep(0.001)