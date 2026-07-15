import random
import time
import math

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
BALL_SPEED = 1.5          # Initial ball speed (pixels per frame)
MAX_BALL_SPEED = 3.5      # Maximum ball speed (speeds up after hits)
PADDLE_HEIGHT = 3         # Height of paddle in pixels
PADDLE_WIDTH = 10         # Width of paddle in pixels
PADDLE_SPEED = 2.0        # Paddle movement speed (pixels per frame)
PADDLE_Y = 60             # Y position of paddle from top
GAME_TIME_SECONDS = 180   # How long the game runs (in seconds)
FRAME_TIME_MS = 50        # Time between frames (in milliseconds)
BRICK_ROWS = 5            # Number of brick rows
BRICK_COLS = 7            # Number of brick columns
BRICK_WIDTH = 8           # Width of each brick (the rightmost column may be different — see below)
BRICK_HEIGHT = 3          # Height of each brick
BRICK_START_Y = 2         # Y position where bricks start
BRICK_START_X = 1         # X position of the leftmost brick. With the default
                           # parameters and a 64-wide screen, the layout is:
                           # 1 empty column + 7 full bricks + 6 gaps + 1 empty column.
BRICK_GAP = 1             # Pixels between adjacent bricks.
BRICK_END_MARGIN = 1      # Pixels of empty space on the right side of the screen
                           # after the rightmost brick. Mirrors BRICK_START_X for
                           # symmetric margins. Set to 0 to fill the right edge.
                           # The rightmost brick's width is computed to make the
                           # math work out:
                           #   rightmost_w = self.width - BRICK_END_MARGIN - x
                           # With defaults (BRICK_COLS=7, BRICK_WIDTH=8, BRICK_GAP=1,
                           # BRICK_START_X=1, BRICK_END_MARGIN=1) all 7 bricks are
                           # exactly 8 px wide — no half-bricks on either side.
# ============================================================================

class BreakoutGame:
    def __init__(self, width=64, height=64):
        self.width = width
        self.height = height
        
        # Paddle position (x, y) - centered
        self.paddle_x = (width - PADDLE_WIDTH) // 2
        self.paddle_y = PADDLE_Y
        
        # Ball state
        self.ball_x = width / 2.0
        self.ball_y = height / 2.0
        self.ball_vx = random.choice([-BALL_SPEED, BALL_SPEED])
        self.ball_vy = -BALL_SPEED * 0.7  # Start moving upward
        
        # Bricks grid - True = exists, False = destroyed
        self.bricks = self._create_bricks()
        
        # Game state
        self.score = 0
        self.game_over = False
        self.winner = False
        self.reason = ""
        
        # AI state
        self.paddle_target_x = self.paddle_x
        self.last_target_update = time.time()
        
        # Ball just lost (for reset)
        self.ball_lost = False
    
    def _create_bricks(self):
        """
        Build the brick grid. The rightmost column has a variable width so
        the layout can leave a configurable right margin (BRICK_END_MARGIN).

        Math: starting at BRICK_START_X, lay down (BRICK_COLS - 1) full-width
        bricks with BRICK_GAP between them. The rightmost brick's width is
        whatever's left between its starting column and the right margin.

        With default params (BRICK_COLS=7, BRICK_WIDTH=8, BRICK_GAP=1,
        BRICK_START_X=1, BRICK_END_MARGIN=1) the rightmost column is also
        8 px wide — a clean 7-brick grid with 1 empty column on each side.
        """
        bricks = []
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = BRICK_START_X + col * (BRICK_WIDTH + BRICK_GAP)
                if col < BRICK_COLS - 1:
                    # Normal-width brick.
                    w = BRICK_WIDTH
                else:
                    # Rightmost column: extend to fill the space between
                    # its starting column and the right margin (BRICK_END_MARGIN).
                    # The math:
                    #   rightmost_w = (self.width - BRICK_END_MARGIN) - x
                    # If that comes out <= 0 the params are over-constrained;
                    # fall back to BRICK_WIDTH so the rightmost is at least
                    # visible (it'll be truncated, but not invisible).
                    w = (self.width - BRICK_END_MARGIN) - x
                    if w <= 0:
                        w = BRICK_WIDTH
                y = BRICK_START_Y + row * (BRICK_HEIGHT + 1)
                bricks.append({'x': x, 'y': y, 'w': w, 'alive': True})
        return bricks
    
    def _clamp(self, value, min_val, max_val):
        """Clamp value to range"""
        return max(min_val, min(max_val, value))
    
    def _predict_ball_at_paddle(self):
        """
        Predict where the ball will be when it reaches paddle height.
        Returns x coordinate, or None if ball is moving away.
        """
        # Check if ball is moving downward
        if self.ball_vy <= 0:
            return None  # Ball moving up, away from paddle
        
        # Calculate frames until ball reaches paddle
        dy = self.paddle_y - self.ball_y
        frames_to_paddle = dy / self.ball_vy if self.ball_vy > 0 else 0
        
        # Predict ball x position at that time
        predicted_x = self.ball_x + self.ball_vx * frames_to_paddle
        
        # Handle wall bounces
        while predicted_x < 0 or predicted_x >= self.width:
            if predicted_x < 0:
                predicted_x = -predicted_x
            elif predicted_x >= self.width:
                predicted_x = 2 * self.width - predicted_x
        
        return predicted_x
    
    def _move_paddle(self):
        """Move paddle toward predicted ball position"""
        predicted_x = self._predict_ball_at_paddle()
        
        # Only move if ball is approaching
        if predicted_x is None:
            return
        
        # Update target occasionally to prevent jiggling
        current_time = time.time()
        if current_time - self.last_target_update > 0.1:
            self.last_target_update = current_time
            
            # Aim for center of paddle on predicted ball
            new_target = predicted_x - PADDLE_WIDTH / 2.0
            new_target = self._clamp(new_target, 0, self.width - PADDLE_WIDTH)
            self.paddle_target_x = new_target
        
        # Move toward target
        if self.paddle_x < self.paddle_target_x:
            new_x = self.paddle_x + PADDLE_SPEED
            new_x = min(new_x, self.paddle_target_x)
        elif self.paddle_x > self.paddle_target_x:
            new_x = self.paddle_x - PADDLE_SPEED
            new_x = max(new_x, self.paddle_target_x)
        else:
            new_x = self.paddle_x
        
        # Clamp to bounds
        self.paddle_x = self._clamp(new_x, 0, self.width - PADDLE_WIDTH)
    
    def _check_paddle_collision(self):
        """Check if ball collides with paddle"""
        prev_ball_y = self.ball_y - self.ball_vy
        
        # Check if ball crossed from above paddle to below it
        if self.ball_vy > 0 and prev_ball_y <= self.paddle_y and self.ball_y >= self.paddle_y:
            # Check if ball is within paddle width
            if self.paddle_x <= self.ball_x < self.paddle_x + PADDLE_WIDTH:
                # Reflect ball
                self.ball_vy = -abs(self.ball_vy)
                
                # Add spin based on where ball hit paddle
                hit_pos = (self.ball_x - self.paddle_x) / PADDLE_WIDTH
                hit_pos = self._clamp(hit_pos, 0, 1)
                
                # Ball hits left side = leftward angle, right side = rightward
                angle_factor = (hit_pos - 0.5) * 1.2
                self.ball_vx = self.ball_vx * 0.8 + angle_factor * BALL_SPEED
                
                # Speed up ball (up to max)
                speed = math.sqrt(self.ball_vx ** 2 + self.ball_vy ** 2)
                if speed < MAX_BALL_SPEED:
                    scale = (speed + 0.3) / speed
                    self.ball_vx *= scale
                    self.ball_vy *= scale
                
                # Push ball above paddle
                self.ball_y = self.paddle_y - 0.5
    
    def _check_brick_collision(self):
        """Check if ball collides with bricks using trajectory-based detection"""
        prev_ball_x = self.ball_x - self.ball_vx
        prev_ball_y = self.ball_y - self.ball_vy
        
        for brick in self.bricks:
            if not brick['alive']:
                continue
            
            # Brick bounds
            brick_left = brick['x']
            brick_right = brick['x'] + brick['w']
            brick_top = brick['y']
            brick_bottom = brick['y'] + BRICK_HEIGHT
            
            # Check if ball trajectory crossed into brick area
            # We need to check if the ball crossed any of the four sides
            
            # Check top side collision (ball coming from above)
            if (prev_ball_y < brick_top and self.ball_y >= brick_top and
                brick_left <= self.ball_x < brick_right):
                brick['alive'] = False
                self.score += 10
                self.ball_vy = -abs(self.ball_vy)
                self.ball_y = brick_top - 0.1
                return
            
            # Check bottom side collision (ball coming from below)
            if (prev_ball_y >= brick_bottom and self.ball_y < brick_bottom and
                brick_left <= self.ball_x < brick_right):
                brick['alive'] = False
                self.score += 10
                self.ball_vy = abs(self.ball_vy)
                self.ball_y = brick_bottom + 0.1
                return
            
            # Check left side collision (ball coming from left)
            if (prev_ball_x < brick_left and self.ball_x >= brick_left and
                brick_top <= self.ball_y < brick_bottom):
                brick['alive'] = False
                self.score += 10
                self.ball_vx = -abs(self.ball_vx)
                self.ball_x = brick_left - 0.1
                return
            
            # Check right side collision (ball coming from right)
            if (prev_ball_x >= brick_right and self.ball_x < brick_right and
                brick_top <= self.ball_y < brick_bottom):
                brick['alive'] = False
                self.score += 10
                self.ball_vx = abs(self.ball_vx)
                self.ball_x = brick_right + 0.1
                return
    
    def _check_wall_collision(self):
        """Check if ball collides with left/right walls and top"""
        if self.ball_x < 0:
            self.ball_x = -self.ball_x
            self.ball_vx = abs(self.ball_vx)
        elif self.ball_x >= self.width:
            self.ball_x = 2 * self.width - self.ball_x
            self.ball_vx = -abs(self.ball_vx)
        
        if self.ball_y < 0:
            self.ball_y = -self.ball_y
            self.ball_vy = abs(self.ball_vy)
    
    def _check_loss(self):
        """Check if ball fell below paddle (loss condition)"""
        if self.ball_y >= self.height:
            return True
        return False
    
    def _check_win(self):
        """Check if all bricks are destroyed"""
        return all(not brick['alive'] for brick in self.bricks)
    
    def _reset_ball(self):
        """Reset ball to center with random direction"""
        self.ball_x = self.width / 2.0
        self.ball_y = self.height / 2.0
        self.ball_vx = random.choice([-BALL_SPEED, BALL_SPEED])
        self.ball_vy = -BALL_SPEED * 0.7
        self.ball_lost = False
    
    def update(self):
        """Update game state"""
        if self.game_over or self.winner:
            return
        
        # Move paddle
        self._move_paddle()
        
        # Update ball position
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy
        
        # Check collisions
        self._check_wall_collision()
        self._check_brick_collision()
        self._check_paddle_collision()
        
        # Check loss condition
        if self._check_loss():
            self.game_over = True
            self.reason = "Ball lost"
            return
        
        # Check win condition
        if self._check_win():
            self.winner = True
            self.reason = "All bricks destroyed!"
            return
    
    def get_pixels(self):
        """Return list of pixels to draw: [(x, y, r, g, b), ...]"""
        pixels = []
        
        # Draw paddle - cyan (dimmed)
        for dx in range(PADDLE_WIDTH):
            for dy in range(PADDLE_HEIGHT):
                x = int(self.paddle_x + dx)
                y = int(self.paddle_y + dy)
                if 0 <= x < self.width and 0 <= y < self.height:
                    pixels.append((x, y, 0, 127, 127))
        
        # Draw bricks - colored based on row (dimmed)
        colors = [
            (127, 0, 0),      # Red
            (127, 82, 0),     # Orange
            (127, 127, 0),    # Yellow
            (0, 127, 0),      # Green
            (0, 0, 127),      # Blue
        ]
        
        for brick in self.bricks:
            if not brick['alive']:
                continue
            
            row = (brick['y'] - BRICK_START_Y) // (BRICK_HEIGHT + 1)
            color = colors[row % len(colors)]

            for dx in range(brick['w']):
                for dy in range(BRICK_HEIGHT):
                    x = int(brick['x'] + dx)
                    y = int(brick['y'] + dy)
                    if 0 <= x < self.width and 0 <= y < self.height:
                        pixels.append((x, y, color[0], color[1], color[2]))
        
        # Draw ball - gray (dimmed white)
        ball_x = int(self.ball_x)
        ball_y = int(self.ball_y)
        if 0 <= ball_x < self.width and 0 <= ball_y < self.height:
            pixels.append((ball_x, ball_y, 255, 255, 255))
        
        return pixels


def RunBreakoutGame(disp):
    """Main game loop for Breakout game"""
    print("Running Breakout Game")
    print(f"Game duration: {GAME_TIME_SECONDS} seconds")
    print(f"Brick layout: {BRICK_COLS} columns x {BRICK_ROWS} rows, "
          f"brick_width={BRICK_WIDTH}, gap={BRICK_GAP}, "
          f"start_x={BRICK_START_X}, end_margin={BRICK_END_MARGIN}")

    start_time = time.time()
    game = BreakoutGame(disp.width, disp.height)

    # Surface the rightmost column's actual width so the user can tell
    # at a glance whether the layout is what they want. If the rightmost
    # column is much smaller than BRICK_WIDTH, they probably want to
    # reduce BRICK_GAP or BRICK_COLS.
    rightmost_w = game.bricks[-1]['w'] if game.bricks else 0
    print(f"Rightmost column width: {rightmost_w}px "
          f"(normal is {BRICK_WIDTH}px)")

    next_turn_time = time.time() + (FRAME_TIME_MS / 1000.0)
    
    while True:
        # Update game state
        game.update()
        
        # Clear and draw
        disp.clear()
        pixel_list = game.get_pixels()
        for x, y, r, g, b in pixel_list:
            disp.set_pixel(x, y, r, g, b)
        
        disp.show()
        
        # Frame timing
        current_time = time.time()
        sleep_time = next_turn_time - current_time
        if sleep_time > 0:
            time.sleep(sleep_time)
        next_turn_time = time.time() + (FRAME_TIME_MS / 1000.0)
        
        # Check end conditions
        if game.game_over:
            print(f"Game Over: {game.reason}")
            print(f"Final score: {game.score}")
            elapsed = time.time() - start_time
            print(f"Time: {elapsed:.1f}s")
            time.sleep(3.0)
            return
        
        if game.winner:
            print(f"You Won! {game.reason}")
            print(f"Final score: {game.score}")
            elapsed = time.time() - start_time
            print(f"Time: {elapsed:.1f}s")
            time.sleep(3.0)
            return
        
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed >= GAME_TIME_SECONDS:
            print(f"Time limit ({GAME_TIME_SECONDS}s) reached")
            print(f"Final score: {game.score}")
            remaining_bricks = sum(1 for brick in game.bricks if brick['alive'])
            print(f"Bricks remaining: {remaining_bricks}/{len(game.bricks)}")
            time.sleep(3.0)
            return
