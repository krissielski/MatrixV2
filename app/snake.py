import random
import time
from collections import deque
import sys
import heapq

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
START_LENGTH = 20         # Initial snake length
NUM_FRUITS = 50           # How many fruits to eat before winning
DELAY_MS = 50             # Frame/move delay in milliseconds
MAX_GAME_TIME = 300       # Maximum game time in seconds
OBSTACLE_COVERAGE = 5     # Percentage of field to cover with obstacles (0-50)
# ============================================================================

class SnakeGame:
    def __init__(self, width=64, height=64, start_length=START_LENGTH, 
                 num_fruits=NUM_FRUITS, obstacle_coverage=OBSTACLE_COVERAGE):
        self.width = width
        self.height = height
        self.start_length = start_length
        self.num_fruits = num_fruits
        self.obstacle_coverage = max(0, min(50, obstacle_coverage))  # Clamp 0-50%
        
        # Generate obstacles
        self.obstacles = self._generate_obstacles()
        
        # Initialize snake centered, moving right
        center_x = width // 2
        center_y = height // 2
        self.snake = deque()
        for i in range(start_length):
            self.snake.append((center_x - i, center_y))
        
        self.direction = (1, 0)  # Moving right
        self.fruit_pos = None
        self.fruits_eaten = 0
        self.game_over = False
        self.win = False
        self.reason = ""
        
        # Spawn initial fruit
        self._spawn_fruit()
    
    def _spawn_fruit(self):
        """Spawn fruit at random empty location"""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) not in self.snake and (x, y) not in self.obstacles:
                self.fruit_pos = (x, y)
                return
    
    def _generate_obstacles(self):
        """Generate random 5x5 square obstacles until coverage% is reached"""
        obstacles = set()
        target_cells = int((self.width * self.height * self.obstacle_coverage) / 100)
        
        size = 5
        
        # Keep placing random squares until we reach target coverage
        # (overlaps are allowed and don't count as wasted attempts)
        while len(obstacles) < target_cells:
            x = random.randint(0, self.width - size)
            y = random.randint(0, self.height - size)
            
            # Add square to obstacles (overlaps are fine)
            for dx in range(size):
                for dy in range(size):
                    obstacles.add((x + dx, y + dy))
        
        return obstacles
    
    def _is_valid_position(self, pos):
        """Check if position is within bounds and not a wall or obstacle"""
        x, y = pos
        return (0 <= x < self.width and 0 <= y < self.height and 
                pos not in self.obstacles)
    
    def _get_neighbors(self, pos):
        """Get valid neighboring positions"""
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_pos = (x + dx, y + dy)
            if self._is_valid_position(new_pos):
                neighbors.append(new_pos)
        return neighbors
    
    def _astar_path_to_target(self, start, target, avoid_positions):
        """
        A* pathfinding with proper open set management.
        Returns list of positions forming path, or empty list if no path exists.
        
        Args:
            start: Starting position (x, y)
            target: Target position (x, y)
            avoid_positions: Set of positions to avoid (walls, body, etc.)
        """
        if start == target:
            return [start]
        
        def heuristic(pos):
            """Weighted Manhattan distance heuristic for faster suboptimal pathfinding.
            Weight > 1 makes A* greedier, finding paths faster at cost of optimality.
            This prevents pathfinding stalls on long snakes."""
            manhattan = abs(pos[0] - target[0]) + abs(pos[1] - target[1])
            return manhattan * 1.5  # 1.5x weight = 50% greedier, much faster convergence
        
        # Allow searching the full board. On a 64x64 board with 5% obstacles,
        # optimal paths often exceed 128 steps. Using board area is more realistic.
        max_nodes_explored = 4000
        
        # Use parent pointers instead of storing full paths (major optimization)
        parent = {start: None}
        g_score = {start: 0}
        
        # Priority queue: (f_score, counter, position)
        # Track which positions are in the open set to avoid duplicate processing
        counter = 0
        open_set = [(heuristic(start), counter, start)]
        open_set_positions = {start}
        closed_set = set()
        
        while open_set and len(closed_set) < max_nodes_explored:
            _, _, current = heapq.heappop(open_set)
            
            # Skip if already processed
            if current in closed_set:
                continue
            
            open_set_positions.discard(current)
            
            if current == target:
                # Reconstruct path from parent pointers
                path = []
                node = target
                while node is not None:
                    path.append(node)
                    node = parent[node]
                return path[::-1]
            
            closed_set.add(current)
            current_g = g_score[current]
            
            for neighbor in self._get_neighbors(current):
                if neighbor in closed_set or neighbor in avoid_positions:
                    continue
                
                tentative_g = current_g + 1
                
                # Only process if this is a new node or better path
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    parent[neighbor] = current
                    counter += 1
                    f_score = tentative_g + heuristic(neighbor)
                    # Add to open set (old duplicates will be skipped when popped)
                    heapq.heappush(open_set, (f_score, counter, neighbor))
                    open_set_positions.add(neighbor)
        
        return []  # No path found
    
    def _is_safe_move(self, next_head_pos):
        """
        Check if moving to next_head_pos is safe:
        1. Not colliding with wall
        2. Not colliding with own body (excluding tail, which will move)
        
        Returns True if the move is safe, False otherwise.
        """
        if not self._is_valid_position(next_head_pos):
            return False
        
        # Check collision with body (excluding tail since it will move)
        snake_body = set(self.snake)
        snake_body.discard(self.snake[-1])  # Exclude tail
        
        if next_head_pos in snake_body:
            return False
        
        return True
    
    def _can_reach_tail_after_move(self, new_head_pos, will_eat_fruit=False):
        """
        Verify that snake won't trap itself after this move by checking if there's
        a path from new head to tail after accounting for the move.
        
        Args:
            new_head_pos: The position the head will move to
            will_eat_fruit: Whether this move eats the fruit (snake grows)
        
        Returns True if there's a safe path from new_head to tail after the move
        """
        tail = self.snake[-1]
        
        if will_eat_fruit:
            # If eating fruit, snake grows - new_head_pos becomes part of body.
            # Obstacles are: entire current body except the tail (which will become new_head)
            # but we need to avoid the current body minus tail, plus the new head will be there
            obstacles_for_search = set(self.snake)
            obstacles_for_search.discard(tail)
            # Remove new_head_pos if it's in obstacles (shouldn't be, but be safe)
            obstacles_for_search.discard(new_head_pos)
        else:
            # If not eating, tail will pop after this move.
            # State after move: head is at new_head_pos, body is snake[:-1], tail is gone.
            # So obstacles should be: current body minus tail, PLUS new_head_pos (which becomes the new body)
            # But we're searching FROM new_head_pos, so exclude it from obstacles.
            snake_list = list(self.snake)
            obstacles_for_search = set(snake_list[:-1])
            # new_head_pos will become body, but exclude it since it's our search start
        
        # Can we reach the tail position from new_head_pos?
        path = self._astar_path_to_target(new_head_pos, tail, obstacles_for_search)
        return len(path) >= 1
    
    def _find_best_move(self):
        """
        Compute the best next move using intelligent A* pathfinding.
        
        Strategy:
        1. Try to find safe path to fruit (avoid entire body including tail)
        2. If fruit unreachable, relax constraints and make any safe move to wait
        3. If fruit reachable, find safest move toward tail as fallback
        4. If all else fails, find move that maximizes distance to obstacles
        
        Returns next position to move to, or None if no safe move exists.
        """
        head = self.snake[0]
        tail = self.snake[-1]
        snake_list = list(self.snake)
        snake_body_obstacles = set(snake_list[:-1])
        
        # Strategy 1: Try to reach fruit
        # Exclude the tail from obstacles since it will pop as snake moves (creating a tunnel).
        # Include rest of body to avoid paths that would loop back through the snake.
        fruit_reachable = False
        if self.fruit_pos:
            fruit_obstacles = set(self.snake)
            fruit_obstacles.discard(self.snake[-1])  # Exclude tail - it will move away
            path_to_fruit = self._astar_path_to_target(head, self.fruit_pos, fruit_obstacles)
            
            if path_to_fruit and len(path_to_fruit) >= 2:
                next_pos = path_to_fruit[1]
                # Trust the A* path - it found a route considering the snake body.
                # No need for expensive trap-checking; the path itself is valid.
                return next_pos
        
        # Strategy 2: If fruit is unreachable/blocked, just make a safe move to wait
        # Don't require trap checking - we're just waiting for the fruit to become accessible
        if not fruit_reachable:
            # Find any valid neighbor move without strict trap requirements
            for neighbor in self._get_neighbors(head):
                if neighbor in snake_body_obstacles or not self._is_valid_position(neighbor):
                    continue
                # This move is safe (doesn't collide), good enough when waiting for fruit
                return neighbor
        
        # Strategy 3: Move toward tail as fallback (only if fruit WAS reachable)
        # Exclude tail from obstacles since it will move away
        path_to_tail = self._astar_path_to_target(head, tail, snake_body_obstacles)
        
        if path_to_tail and len(path_to_tail) >= 2:
            next_pos = path_to_tail[1]
            
            # Verify this move is safe and won't trap us
            if self._is_valid_position(next_pos) and next_pos not in snake_body_obstacles:
                if self._can_reach_tail_after_move(next_pos, will_eat_fruit=False):
                    return next_pos
        
        # Strategy 4: Choose safest available move that won't immediately trap us
        best_move = None
        best_distance = -1
        
        for neighbor in self._get_neighbors(head):
            if neighbor in snake_body_obstacles or not self._is_valid_position(neighbor):
                continue
            
            # Verify we won't trap ourselves with this move
            if not self._can_reach_tail_after_move(neighbor, will_eat_fruit=False):
                continue
            
            # Calculate minimum distance to any obstacle
            min_distance = float('inf')
            
            # Distance to walls
            x, y = neighbor
            wall_distance = min(x, y, self.width - 1 - x, self.height - 1 - y)
            min_distance = min(min_distance, wall_distance)
            
            # Distance to body
            for body_part in snake_body_obstacles:
                bx, by = body_part
                dist = abs(x - bx) + abs(y - by)  # Manhattan distance
                min_distance = min(min_distance, dist)
            
            if min_distance > best_distance:
                best_distance = min_distance
                best_move = neighbor
        
        return best_move
    
    def update(self):
        """Update snake position, handle fruit eating, check game over"""
        if self.game_over or self.win:
            return
        
        # Compute next move
        next_pos = self._find_best_move()
        
        if next_pos is None:
            # No safe move available
            self.game_over = True
            self.reason = "Trapped - no safe moves"
            return
        
        head_x, head_y = self.snake[0]
        next_x, next_y = next_pos
        
        # Check wall collision
        if not self._is_valid_position(next_pos):
            self.game_over = True
            self.reason = "Hit wall"
            return
        
        # Check self collision (body excluding tail)
        snake_body = set(self.snake)
        snake_body.discard(self.snake[-1])
        if next_pos in snake_body:
            self.game_over = True
            self.reason = "Hit self"
            return
        
        # Move snake
        self.snake.appendleft(next_pos)
        
        # Check if fruit eaten
        if next_pos == self.fruit_pos:
            self.fruits_eaten += 1
            if self.fruits_eaten >= self.num_fruits:
                self.win = True
                return
            self._spawn_fruit()
            # Grow by 10 pixels
            for _ in range(9):  # Already added 1 above, so add 9 more
                if self.snake:
                    self.snake.append(self.snake[-1])
        else:
            # Remove tail if no fruit eaten
            self.snake.pop()
    
    def get_pixels(self):
        """Return list of pixels to draw: [(x, y, r, g, b), ...]"""
        pixels = []
        
        # Draw obstacles - light blue
        for x, y in self.obstacles:
            pixels.append((x, y, 25, 50, 64))
        
        # Draw snake body
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                # Head - bright green
                pixels.append((x, y, 0, 255, 0))
            else:
                # Body - darker green
                pixels.append((x, y, 0, 150, 0))
        
        # Draw fruit - red
        if self.fruit_pos:
            fx, fy = self.fruit_pos
            pixels.append((fx, fy, 255, 0, 0))
        
        return pixels


def RunSnakeGame(disp):
    """Main game loop for snake game"""
    print("Running Snake Game")
        
    start_time = time.time()
    game = SnakeGame(disp.width, disp.height, START_LENGTH, NUM_FRUITS, OBSTACLE_COVERAGE)
    
    next_turn_time = time.time() + (DELAY_MS / 1000.0)
    
    while True:
        # Update game state
        game.update()
        
        # Clear and draw
        disp.clear()
        pixel_list = game.get_pixels()
        for x, y, r, g, b in pixel_list:
            disp.set_pixel(x, y, r, g, b)
        
        disp.show()
        
        # Calculate remaining time to reach next turn time
        current_time = time.time()
        sleep_time = next_turn_time - current_time
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        # Set next turn time
        next_turn_time = time.time() + (DELAY_MS / 1000.0)
        
        # Check end conditions
        if game.game_over:
            print(f"Game Over: {game.reason}")
            print(f"Fruits eaten: {game.fruits_eaten}/{game.num_fruits}")
            elapsed = time.time() - start_time
            print(f"Time: {elapsed:.1f}s")
            time.sleep(3.0)
            return
        
        if game.win:
            print(f"You Won! Ate {game.fruits_eaten} fruits!")
            elapsed = time.time() - start_time
            print(f"Time: {elapsed:.1f}s")
            time.sleep(3.0)
            return
        
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed >= MAX_GAME_TIME:
            print(f"Time limit ({MAX_GAME_TIME}s) reached")
            print(f"Fruits eaten: {game.fruits_eaten}/{game.num_fruits}")
            time.sleep(3.0)
            return
