import random
import time

# =========================================================================
# USER-ADJUSTABLE PARAMETERS
# =========================================================================
FRAME_TIME_MS = 100  # Time between frames (in milliseconds)
RUNTIME_SECONDS = 60  # How long the game runs (in seconds)
# =========================================================================

def generate_maze(width, height):
    """
    Generate a random solvable maze using recursive backtracking.

    Args:
        width: Width of the maze (in pixels)
        height: Height of the maze (in pixels)

    Returns:
        A 2D list representing the maze (True = wall, False = path).
    """
    maze = [[True for _ in range(width)] for _ in range(height)]

    def carve_passages(x, y):
        directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and maze[ny][nx]:
                maze[ny][nx] = False
                maze[y + dy // 2][x + dx // 2] = False
                carve_passages(nx, ny)

    # Start carving from the top-left corner
    maze[1][1] = False
    carve_passages(1, 1)

    return maze

def RunMazeGame(disp):
    """
    Main game loop for the Maze game with 2-pixel wide walls and paths.
    Player attempts to traverse the maze, making random choices at intersections.
    Never backtracks - won't go the way it came.
    Moves one step at a time for smooth animation.
    Tracks visited paths to avoid redundant exploration (memory/mapping behavior).
    """
    print("Running Maze Game")

    # Generate a smaller maze with odd dimensions (31x31) that will be scaled up 2x
    maze_size = 31
    maze = generate_maze(maze_size, maze_size)
    
    # Define start and goal positions (in maze coordinates)
    start_x, start_y = 1, 1
    goal_x, goal_y = maze_size - 2, maze_size - 2
    
    # Player starts at the start position
    player_x, player_y = start_x, start_y
    player_dir_x, player_dir_y = 1, 0  # Initial direction (moving right)
    reached_goal = False
    
    # Track visited paths: set of (from_x, from_y, to_x, to_y) tuples
    visited_paths = set()

    start_time = time.time()
    display_maze_time = 3.0  # Show maze for 3 seconds before starting movement
    last_move_time = start_time
    move_interval = 0.1  # Move every 0.1 seconds (one step)
    
    def get_valid_moves(x, y):
        """Get all valid moves from position (x, y) - paths that are not walls"""
        valid = []
        for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            new_x, new_y = x + dx, y + dy
            if 0 <= new_x < maze_size and 0 <= new_y < maze_size:
                if not maze[new_y][new_x]:  # 0 = path, 1 = wall
                    valid.append((dx, dy))
        return valid
    
    def get_unvisited_moves(x, y, exclude_dir_x=None, exclude_dir_y=None):
        """Get moves that haven't been visited yet"""
        valid_moves = get_valid_moves(x, y)
        unvisited = []
        
        for dx, dy in valid_moves:
            # Skip the direction we came from
            if exclude_dir_x is not None and dx == -exclude_dir_x and dy == -exclude_dir_y:
                continue
            
            new_x, new_y = x + dx, y + dy
            # Check if this path has been visited
            if (x, y, new_x, new_y) not in visited_paths:
                unvisited.append((dx, dy))
        
        return unvisited
    
    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        
        # Clear the display
        disp.clear()

        # Draw the maze scaled 2x (each maze cell becomes a 2x2 pixel block)
        # Center with 1 pixel offset on all sides
        for y in range(maze_size):
            for x in range(maze_size):
                if maze[y][x]:
                    # Draw 2x2 block for wall (offset by 1 to center)
                    disp.set_pixel(x * 2 + 1, y * 2 + 1, 139, 69, 19)        # Brown for walls
                    disp.set_pixel(x * 2 + 2, y * 2 + 1, 139, 69, 19)
                    disp.set_pixel(x * 2 + 1, y * 2 + 2, 139, 69, 19)
                    disp.set_pixel(x * 2 + 2, y * 2 + 2, 139, 69, 19)

        # Draw the goal as a 2x2 red square (always visible)
        for dx in range(2):
            for dy in range(2):
                disp.set_pixel(goal_x * 2 + dx + 1, goal_y * 2 + dy + 1, 255, 0, 0)

        # Draw the player as a 2x2 green square
        for dx in range(2):
            for dy in range(2):
                disp.set_pixel(player_x * 2 + dx + 1, player_y * 2 + dy + 1, 0, 255, 0)

        # Show the display
        disp.show()

        # After initial display time, start moving the player one step at a time
        if elapsed > display_maze_time and (current_time - last_move_time) >= move_interval:
            # Try to move in current direction
            next_x = player_x + player_dir_x
            next_y = player_y + player_dir_y
            
            # Check if next position is valid (in bounds and not a wall)
            can_move_forward = (0 <= next_x < maze_size and 0 <= next_y < maze_size 
                               and not maze[next_y][next_x])
            
            if can_move_forward:
                # Mark this path as visited
                visited_paths.add((player_x, player_y, next_x, next_y))
                
                # Move forward
                player_x, player_y = next_x, next_y
                
                # Check if reached goal
                if player_x == goal_x and player_y == goal_y:
                    reached_goal = True
                    print(f"Goal reached in {elapsed:.1f} seconds!")
                    time.sleep(3.0)
                    return
                
                # Check if we're at an intersection (2+ unvisited moves excluding where we came from)
                unvisited_moves = get_unvisited_moves(player_x, player_y, player_dir_x, player_dir_y)
                
                if len(unvisited_moves) >= 2:
                    # At an intersection with unvisited choices - randomly pick a new direction
                    player_dir_x, player_dir_y = random.choice(unvisited_moves)
                elif len(unvisited_moves) == 1:
                    # Only one unvisited path - take it
                    player_dir_x, player_dir_y = unvisited_moves[0]
            else:
                # Can't move forward - we're at a dead end or wall
                # Find unvisited directions (excluding where we came from)
                unvisited_moves = get_unvisited_moves(player_x, player_y, player_dir_x, player_dir_y)
                
                if unvisited_moves:
                    # Pick a new unvisited direction and move immediately
                    player_dir_x, player_dir_y = random.choice(unvisited_moves)
                    next_x = player_x + player_dir_x
                    next_y = player_y + player_dir_y
                    
                    # Move in the new direction
                    if 0 <= next_x < maze_size and 0 <= next_y < maze_size and not maze[next_y][next_x]:
                        visited_paths.add((player_x, player_y, next_x, next_y))
                        player_x, player_y = next_x, next_y
                        
                        # Check if reached goal
                        if player_x == goal_x and player_y == goal_y:
                            reached_goal = True
                            print(f"Goal reached in {elapsed:.1f} seconds!")
                            time.sleep(3.0)
                            return
                else:
                    # All paths visited - find any valid move that isn't where we came from
                    valid_moves = get_valid_moves(player_x, player_y)
                    available_moves = [m for m in valid_moves 
                                     if not (m[0] == -player_dir_x and m[1] == -player_dir_y)]
                    
                    if available_moves:
                        player_dir_x, player_dir_y = random.choice(available_moves)
                        next_x = player_x + player_dir_x
                        next_y = player_y + player_dir_y
                        
                        if 0 <= next_x < maze_size and 0 <= next_y < maze_size and not maze[next_y][next_x]:
                            visited_paths.add((player_x, player_y, next_x, next_y))
                            player_x, player_y = next_x, next_y
                            
                            if player_x == goal_x and player_y == goal_y:
                                reached_goal = True
                                print(f"Goal reached in {elapsed:.1f} seconds!")
                                time.sleep(3.0)
                                return
                    elif valid_moves:
                        # Only option is to turn around
                        player_dir_x, player_dir_y = random.choice(valid_moves)
                        next_x = player_x + player_dir_x
                        next_y = player_y + player_dir_y
                        
                        if 0 <= next_x < maze_size and 0 <= next_y < maze_size and not maze[next_y][next_x]:
                            visited_paths.add((player_x, player_y, next_x, next_y))
                            player_x, player_y = next_x, next_y
                            
                            if player_x == goal_x and player_y == goal_y:
                                reached_goal = True
                                print(f"Goal reached in {elapsed:.1f} seconds!")
                                time.sleep(3.0)
                                return
            
            last_move_time = current_time
        
        # Check if runtime limit exceeded
        if elapsed >= RUNTIME_SECONDS:
            if reached_goal:
                print(f"Goal reached in {elapsed:.1f} seconds!")
            else:
                print(f"Maze game runtime limit ({RUNTIME_SECONDS}s) reached - goal not found")
            time.sleep(3.0)
            return

        # Frame timing
        time.sleep(FRAME_TIME_MS / 1000.0)
    
    while True:
        current_time = time.time()
        elapsed = current_time - start_time
        
        # Clear the display
        disp.clear()

        # Draw the maze scaled 2x (each maze cell becomes a 2x2 pixel block)
        # Center with 1 pixel offset on all sides
        for y in range(maze_size):
            for x in range(maze_size):
                if maze[y][x]:
                    # Draw 2x2 block for wall (offset by 1 to center)
                    disp.set_pixel(x * 2 + 1, y * 2 + 1, 139, 69, 19)        # Brown for walls
                    disp.set_pixel(x * 2 + 2, y * 2 + 1, 139, 69, 19)
                    disp.set_pixel(x * 2 + 1, y * 2 + 2, 139, 69, 19)
                    disp.set_pixel(x * 2 + 2, y * 2 + 2, 139, 69, 19)

        # Draw the goal as a 2x2 red square (always visible)
        for dx in range(2):
            for dy in range(2):
                disp.set_pixel(goal_x * 2 + dx + 1, goal_y * 2 + dy + 1, 255, 0, 0)

        # Draw the player as a 2x2 green square
        for dx in range(2):
            for dy in range(2):
                disp.set_pixel(player_x * 2 + dx + 1, player_y * 2 + dy + 1, 0, 255, 0)

        # Show the display
        disp.show()

        # After initial display time, start moving the player one step at a time
        if elapsed > display_maze_time and (current_time - last_move_time) >= move_interval:
            # Try to move in current direction
            next_x = player_x + player_dir_x
            next_y = player_y + player_dir_y
            
            # Check if next position is valid (in bounds and not a wall)
            can_move_forward = (0 <= next_x < maze_size and 0 <= next_y < maze_size 
                               and not maze[next_y][next_x])
            
            if can_move_forward:
                # Move forward
                player_x, player_y = next_x, next_y
                
                # Check if reached goal
                if player_x == goal_x and player_y == goal_y:
                    reached_goal = True
                    print(f"Goal reached in {elapsed:.1f} seconds!")
                    time.sleep(3.0)
                    return
                
                # Check if we're at an intersection (2+ valid moves excluding where we came from)
                valid_moves = get_valid_moves(player_x, player_y)
                # Filter out the direction we came from
                available_moves = [m for m in valid_moves 
                                 if not (m[0] == -player_dir_x and m[1] == -player_dir_y)]
                
                if len(available_moves) >= 2:
                    # At an intersection with choices - randomly pick a new direction
                    player_dir_x, player_dir_y = random.choice(available_moves)
            else:
                # Can't move forward - we're at a dead end or wall
                # Find available directions (excluding where we came from)
                valid_moves = get_valid_moves(player_x, player_y)
                available_moves = [m for m in valid_moves 
                                 if not (m[0] == -player_dir_x and m[1] == -player_dir_y)]
                
                if available_moves:
                    # Pick a new direction and move immediately
                    player_dir_x, player_dir_y = random.choice(available_moves)
                    next_x = player_x + player_dir_x
                    next_y = player_y + player_dir_y
                    
                    # Move in the new direction
                    if 0 <= next_x < maze_size and 0 <= next_y < maze_size and not maze[next_y][next_x]:
                        player_x, player_y = next_x, next_y
                        
                        # Check if reached goal
                        if player_x == goal_x and player_y == goal_y:
                            reached_goal = True
                            print(f"Goal reached in {elapsed:.1f} seconds!")
                            time.sleep(3.0)
                            return
                elif valid_moves:
                    # Only option is to turn around
                    player_dir_x, player_dir_y = random.choice(valid_moves)
                    next_x = player_x + player_dir_x
                    next_y = player_y + player_dir_y
                    
                    # Move in the new direction
                    if 0 <= next_x < maze_size and 0 <= next_y < maze_size and not maze[next_y][next_x]:
                        player_x, player_y = next_x, next_y
                        
                        # Check if reached goal
                        if player_x == goal_x and player_y == goal_y:
                            reached_goal = True
                            print(f"Goal reached in {elapsed:.1f} seconds!")
                            time.sleep(3.0)
                            return
            
            last_move_time = current_time
        
        # Check if runtime limit exceeded
        if elapsed >= RUNTIME_SECONDS:
            if reached_goal:
                print(f"Goal reached in {elapsed:.1f} seconds!")
            else:
                print(f"Maze game runtime limit ({RUNTIME_SECONDS}s) reached - goal not found")
            time.sleep(3.0)
            return

        # Frame timing
        time.sleep(FRAME_TIME_MS / 1000.0)