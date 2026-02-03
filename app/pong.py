import random
import time
import math

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
BALL_SPEED = 1.5          # Initial ball speed (pixels per frame). Increase for faster gameplay
MAX_BALL_SPEED = 4.0      # Maximum ball speed (speeds up after paddle hits)
PADDLE_HEIGHT = 10        # Height of each paddle in pixels
PADDLE_WIDTH = 2          # Width of each paddle
PADDLE_SPEED = 1.5        # Paddle movement speed (pixels per frame)
GAME_TIME_SECONDS = 120   # How long the game runs (in seconds)
FRAME_TIME_MS = 50        # Time between frames (in milliseconds)
WINNING_SCORE = 10        # First to N points wins (set to 0 to ignore score wins)
BALL_SIZE = 2             # Ball size in pixels (1 = single pixel)
AI_REACTION_TIME = 0.5    # AI reaction delay (seconds) before adjusting paddle
# ============================================================================

class PongGame:
    def __init__(self, width=64, height=64):
        self.width = width
        self.height = height
        
        # Paddle positions (x, y) - y is the top of the paddle
        self.left_paddle_y = (height - PADDLE_HEIGHT) // 2
        self.right_paddle_y = (height - PADDLE_HEIGHT) // 2
        
        # Paddle x positions (static)
        self.left_paddle_x = 2
        self.right_paddle_x = width - PADDLE_WIDTH - 2
        
        # Ball state: position (float) and velocity
        self.ball_x = width / 2.0
        self.ball_y = height / 2.0
        self.ball_vx = random.choice([-BALL_SPEED, BALL_SPEED])
        self.ball_vy = (random.random() - 0.5) * BALL_SPEED
        
        # Score
        self.left_score = 0
        self.right_score = 0
        
        # Game state
        self.game_over = False
        self.winner = None  # "left", "right", or None
        self.reason = ""
        
        # AI state - stable targets to prevent jiggling
        self.left_target_y = self.left_paddle_y
        self.right_target_y = self.right_paddle_y
        self.last_target_update_time = time.time()
    
    def _clamp(self, value, min_val, max_val):
        """Clamp value to range"""
        return max(min_val, min(max_val, value))
    
    def _predict_ball_at_paddle(self, is_left):
        """
        Predict where the ball will be when it reaches the paddle's x position.
        Returns the predicted y coordinate, or None if ball is moving away.
        """
        paddle_x = self.left_paddle_x if is_left else self.right_paddle_x
        
        # Check if ball is moving toward this paddle
        if is_left and self.ball_vx >= 0:
            return None  # Ball moving right, away from left paddle
        if not is_left and self.ball_vx <= 0:
            return None  # Ball moving left, away from right paddle
        
        # Calculate frames until ball reaches paddle
        dx = abs(paddle_x - self.ball_x)
        frames_to_paddle = dx / abs(self.ball_vx) if self.ball_vx != 0 else 0
        
        # Predict ball y position at that time
        predicted_y = self.ball_y + self.ball_vy * frames_to_paddle
        
        # Handle wall bounces (simple bouncing logic)
        while predicted_y < 0 or predicted_y >= self.height:
            if predicted_y < 0:
                predicted_y = -predicted_y
            elif predicted_y >= self.height:
                predicted_y = 2 * self.height - predicted_y
        
        return predicted_y
    
    def _move_paddle(self, is_left):
        """Move paddle toward predicted ball position (only if ball approaching)"""
        # Get predicted ball position when it reaches this paddle
        predicted_y = self._predict_ball_at_paddle(is_left)
        
        # Only move if ball is approaching this paddle
        if predicted_y is None:
            return
        
        # Update target position occasionally (0.1s) to prevent jiggling
        current_time = time.time()
        if current_time - self.last_target_update_time > 0.1:
            self.last_target_update_time = current_time
            
            # Aim for top-third of paddle for a looser target area
            # This gives the paddle a bigger hit zone (upper 1/3 of paddle)
            target_offset = PADDLE_HEIGHT * 0.33  # Aim for top 1/3
            new_target = predicted_y - target_offset
            new_target = self._clamp(new_target, 0, self.height - PADDLE_HEIGHT)
            
            if is_left:
                self.left_target_y = new_target
            else:
                self.right_target_y = new_target
        
        # Move toward the stable target
        if is_left:
            current_y = self.left_paddle_y
            target_y = self.left_target_y
        else:
            current_y = self.right_paddle_y
            target_y = self.right_target_y
        
        # Move smoothly toward target
        if current_y < target_y:
            new_y = current_y + PADDLE_SPEED
            new_y = min(new_y, target_y)
        elif current_y > target_y:
            new_y = current_y - PADDLE_SPEED
            new_y = max(new_y, target_y)
        else:
            new_y = current_y
        
        # Clamp to bounds
        new_y = self._clamp(new_y, 0, self.height - PADDLE_HEIGHT)
        
        if is_left:
            self.left_paddle_y = new_y
        else:
            self.right_paddle_y = new_y
    
    def _check_paddle_collision(self):
        """Check if ball collides with paddles, accounting for ball trajectory"""
        ball_x = self.ball_x
        ball_y = self.ball_y
        prev_ball_x = ball_x - self.ball_vx
        
        # Left paddle collision - check if ball crossed into paddle area
        if self.ball_vx < 0:  # Ball moving left
            paddle_right = self.left_paddle_x + PADDLE_WIDTH
            # Check if ball crossed from right of paddle to left of it
            if prev_ball_x >= paddle_right and ball_x <= paddle_right:
                # Check if ball is within paddle height
                if self.left_paddle_y <= ball_y < self.left_paddle_y + PADDLE_HEIGHT:
                    # Reflect ball
                    self.ball_vx = abs(self.ball_vx)
                    
                    # Add spin based on where ball hit paddle
                    hit_pos = (ball_y - self.left_paddle_y) / PADDLE_HEIGHT
                    hit_pos = self._clamp(hit_pos, 0, 1)
                    
                    # Ball hits top of paddle = upward angle, bottom = downward
                    angle_factor = (hit_pos - 0.5) * 1.5
                    self.ball_vy = self.ball_vy * 0.9 + angle_factor * BALL_SPEED
                    
                    # Speed up ball (up to max)
                    speed = math.sqrt(self.ball_vx ** 2 + self.ball_vy ** 2)
                    if speed < MAX_BALL_SPEED:
                        scale = (speed + 0.5) / speed
                        self.ball_vx *= scale
                        self.ball_vy *= scale
                    
                    # Push ball away from paddle
                    self.ball_x = paddle_right + 0.5
        
        # Right paddle collision - check if ball crossed into paddle area
        if self.ball_vx > 0:  # Ball moving right
            paddle_left = self.right_paddle_x
            # Check if ball crossed from left of paddle to right of it
            if prev_ball_x < paddle_left and ball_x >= paddle_left:
                # Check if ball is within paddle height
                if self.right_paddle_y <= ball_y < self.right_paddle_y + PADDLE_HEIGHT:
                    # Reflect ball
                    self.ball_vx = -abs(self.ball_vx)
                    
                    # Add spin based on where ball hit paddle
                    hit_pos = (ball_y - self.right_paddle_y) / PADDLE_HEIGHT
                    hit_pos = self._clamp(hit_pos, 0, 1)
                    
                    angle_factor = (hit_pos - 0.5) * 1.5
                    self.ball_vy = self.ball_vy * 0.9 + angle_factor * BALL_SPEED
                    
                    # Speed up ball
                    speed = math.sqrt(self.ball_vx ** 2 + self.ball_vy ** 2)
                    if speed < MAX_BALL_SPEED:
                        scale = (speed + 0.5) / speed
                        self.ball_vx *= scale
                        self.ball_vy *= scale
                    
                    # Push ball away from paddle
                    self.ball_x = paddle_left - 0.5
    
    def _check_wall_collision(self):
        """Check if ball collides with top/bottom walls"""
        if self.ball_y < 0:
            self.ball_y = -self.ball_y
            self.ball_vy = abs(self.ball_vy)
        elif self.ball_y >= self.height:
            self.ball_y = 2 * self.height - self.ball_y
            self.ball_vy = -abs(self.ball_vy)
    
    def _check_scoring(self):
        """Check if ball went out of bounds (scoring)"""
        if self.ball_x < 0:
            # Right player scores
            self.right_score += 1
            self._reset_ball()
            return True
        elif self.ball_x >= self.width:
            # Left player scores
            self.left_score += 1
            self._reset_ball()
            return True
        return False
    
    def _reset_ball(self):
        """Reset ball to center with random direction"""
        self.ball_x = self.width / 2.0
        self.ball_y = self.height / 2.0
        
        # Random direction
        angle = random.uniform(-math.pi / 4, math.pi / 4)
        if random.random() < 0.5:
            angle += math.pi
        
        self.ball_vx = BALL_SPEED * math.cos(angle)
        self.ball_vy = BALL_SPEED * math.sin(angle)
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        # Move paddles (only the one the ball is approaching)
        self._move_paddle(is_left=True)
        self._move_paddle(is_left=False)
        
        # Update ball position
        self.ball_x += self.ball_vx
        self.ball_y += self.ball_vy
        
        # Check collisions
        self._check_wall_collision()
        self._check_paddle_collision()
        self._check_scoring()
        
        # Check win conditions
        if WINNING_SCORE > 0:
            if self.left_score >= WINNING_SCORE:
                self.game_over = True
                self.winner = "left"
                self.reason = f"Left wins {self.left_score}-{self.right_score}"
            elif self.right_score >= WINNING_SCORE:
                self.game_over = True
                self.winner = "right"
                self.reason = f"Right wins {self.right_score}-{self.left_score}"
    
    def get_pixels(self):
        """Return list of pixels to draw: [(x, y, r, g, b), ...]"""
        pixels = []
        
        # Draw left paddle - cyan (dimmed)
        for dx in range(PADDLE_WIDTH):
            for dy in range(PADDLE_HEIGHT):
                x = int(self.left_paddle_x + dx)
                y = int(self.left_paddle_y + dy)
                if 0 <= x < self.width and 0 <= y < self.height:
                    pixels.append((x, y, 0, 127, 127))
        
        # Draw right paddle - magenta (dimmed)
        for dx in range(PADDLE_WIDTH):
            for dy in range(PADDLE_HEIGHT):
                x = int(self.right_paddle_x + dx)
                y = int(self.right_paddle_y + dy)
                if 0 <= x < self.width and 0 <= y < self.height:
                    pixels.append((x, y, 127, 0, 127))
        
        # Draw ball - gray (dimmed white)
        ball_x = int(self.ball_x)
        ball_y = int(self.ball_y)
        if 0 <= ball_x < self.width and 0 <= ball_y < self.height:
            pixels.append((ball_x, ball_y, 255, 255, 255))
        
        # Draw center line (dashed) - dark gray
        for y in range(0, self.height, 2):
            mid_x = self.width // 2
            pixels.append((mid_x, y, 50, 50, 50))
        
        return pixels


def RunPongGame(disp):
    """Main game loop for Pong game"""
    print("Running Pong Game")
    
    start_time = time.time()
    game = PongGame(disp.width, disp.height)
    
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
            elapsed = time.time() - start_time
            print(f"Time: {elapsed:.1f}s")
            time.sleep(3.0)
            return
        
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed >= GAME_TIME_SECONDS:
            print(f"Time limit ({GAME_TIME_SECONDS}s) reached")
            print(f"Final score: Left {game.left_score} - Right {game.right_score}")
            time.sleep(3.0)
            return
