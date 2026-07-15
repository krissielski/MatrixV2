"""
Fish tank: fish, bubbles, seaweed, and a sandy bottom against a black
"water" background.

Design notes:
- Water is intentionally NOT drawn. The matrix's off-state (black) IS the
  water, so every lit pixel is a fish, bubble, or piece of scenery.
- Fish are tiny (3x2 or 4x2 sprites) because the matrix is 64x64. Even at
  1-pixel resolution the directional sprite + horizontal motion reads as
  "fish." Each fish is one of two designs (small / long) and faces either
  left or right. They also swim vertically, not just horizontally.
- Bubbles are single pixels spawned one at a time at the bottom of the
  screen, rising with slight horizontal sway. When they reach the top
  they pop (no respawn).
- Seaweed is short pixel columns rooted in the sand that gently sway. It
  gives the tank a "floor" and makes the upward bubble motion more readable.
- Sand is the bottom 2-4 rows, with a per-column height that gives the
  sea floor some contour. Seaweed grows out of the sand; fish swim above
  the sand; bubbles rise from the sand.
"""

import random
import time

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
# Animation
RUNTIME_SECONDS = 90       # How long the tank runs before returning to main.py
FRAME_TIME_MS = 110         # Time between frames (milliseconds). ~12 fps.

# Population
NUM_FISH = 7               # Number of fish in the tank
NUM_SEAWEED = 10           # Number of seaweed stalks rooted in the sand

# Fish motion (both 1 pixel per frame at default — at 64x64 there's no
# room for faster motion without losing readability)
FISH_HORIZ_SPEED = 1       # Horizontal pixels per frame (always +-1 at this scale)
FISH_VERT_SPEED = 1        # Vertical pixels per frame
FISH_FLIP_CHANCE = 0.05    # Per-frame probability a fish flips horizontal direction
FISH_VERT_FLIP_CHANCE = 0.05  # Per-frame probability a fish flips vertical direction

# Bubble spawning
BUBBLE_SPAWN_CHANCE = 0.22 # Per-frame probability of spawning a new bubble.
                            # At 0.22 we get roughly one bubble every 4-5 frames,
                            # which produces a steady-state population of ~14 bubbles
                            # (a bubble takes ~64 frames to rise from bottom to top).
BUBBLE_RISE_SPEED = 1      # Vertical pixels per frame a bubble rises
BUBBLE_SWAY_CHANCE = 0.4   # Per-frame probability a bubble sways left or right

# Seaweed
SEAWEED_MIN_HEIGHT = 4     # Minimum seaweed height in pixels
SEAWEED_MAX_HEIGHT = 8     # Maximum seaweed height in pixels
SEAWEED_SWAY_CHANCE = 0.3  # Per-frame probability a stalk sways
SEAWEED_COLOR = (0, 127, 0)  # Dim green

# Sand
SAND_MIN_ROWS = 2          # Minimum sand depth (rows) in any column
SAND_MAX_ROWS = 4          # Maximum sand depth -- gives the sea floor some contour
SAND_COLOR = (160, 130, 70)  # Warm sandy tan, dimmer than the fish
# ============================================================================


# ----------------------------------------------------------------------------
# Fish sprite definitions
# ----------------------------------------------------------------------------
# Each sprite is a list of (dx, dy) offsets from the fish's anchor point
# (the leftmost pixel of the sprite's bounding box).
#
# Two designs, two facings:
#   small_r / small_l : 3 wide, 2 tall. Compact body with a tail pixel.
#   long_r  / long_l  : 4 wide, 2 tall. Slimmer body, longer tail.
#
# Right-facing:  .##.    Left-facing:  .##.
#               ##..                  ..##
#
# Long right:  .###.    Long left:   .###.
#              ##..                 ..##
#
# In the offsets below, (0,0) is the top-left of the bounding box.

SMALL_FISH_R = [(1, 0), (2, 0),
                (0, 1), (1, 1)]

SMALL_FISH_L = [(1, 0), (2, 0),
                (1, 1), (2, 1)]

LONG_FISH_R = [(1, 0), (2, 0), (3, 0),
               (0, 1), (1, 1)]

LONG_FISH_L = [(1, 0), (2, 0), (3, 0),
               (1, 1), (2, 1)]

_SPRITES = {
    'small_r': (SMALL_FISH_R, 3, 2),  # (pixel offsets, width, height)
    'small_l': (SMALL_FISH_L, 3, 2),
    'long_r':  (LONG_FISH_R,  4, 2),
    'long_l':  (LONG_FISH_L,  4, 2),
}


# ----------------------------------------------------------------------------
# Entity classes
# ----------------------------------------------------------------------------
class Fish:
    """A single fish: position, velocity, sprite, and color.

    Fish swim both horizontally and vertically at 1 pixel per frame each
    direction, so the school has organic 2D motion. They bounce off the
    screen edges (and the sand surface below) and randomly flip direction
    with FISH_FLIP_CHANCE and FISH_VERT_FLIP_CHANCE for added life.
    """

    def __init__(self, width, height, sand_profile):
        # Pick a sprite design (small or long) and initial facing.
        size = random.choice(['small', 'long'])
        facing = random.choice(['r', 'l'])
        self.sprite_key = f'{size}_{facing}'
        _, self.sprite_w, self.sprite_h = _SPRITES[self.sprite_key]

        # The fish's y range is bounded above by the top of the screen
        # (with a small margin) and below by the highest sand point
        # (so the fish never swim through the sand).
        sand_top = height - max(sand_profile)
        margin_top = 4
        y_min = margin_top
        y_max = sand_top - self.sprite_h
        if y_max < y_min:
            y_max = y_min  # degenerate case: tank too small
        self.y = random.randint(y_min, y_max)

        # Horizontal velocity (positive = moving right).
        self.vx = FISH_HORIZ_SPEED if facing == 'r' else -FISH_HORIZ_SPEED
        # Vertical velocity -- random up or down at start.
        self.vy = FISH_VERT_SPEED if random.random() < 0.5 else -FISH_VERT_SPEED
        # x is the leftmost column of the sprite's bounding box.
        self.x = random.randint(0, max(0, width - self.sprite_w))

        # Color: warm fish colors. Slightly dimmed so it doesn't blind.
        palette = [
            (255, 127, 0),   # orange
            (255, 200, 0),   # gold
            (200, 127, 255), # purple
            (255, 127, 127), # salmon
            (127, 200, 255), # cyan-blue
            (255, 255, 127), # pale yellow
        ]
        self.color = random.choice(palette)

    def update(self, width, height, sand_profile):
        # Random chance to flip horizontal direction.
        if random.random() < FISH_FLIP_CHANCE:
            self.vx = -self.vx
            self.sprite_key = self._flipped_sprite_key()
            _, self.sprite_w, self.sprite_h = _SPRITES[self.sprite_key]

        # Random chance to flip vertical direction.
        if random.random() < FISH_VERT_FLIP_CHANCE:
            self.vy = -self.vy

        self.x += self.vx
        self.y += self.vy

        # Bounce off the side walls. When we bounce, flip the sprite so
        # the fish faces the new direction of travel.
        if self.x <= 0:
            self.x = 0
            self.vx = abs(self.vx)
            self.sprite_key = self._flipped_sprite_key()
            _, self.sprite_w, self.sprite_h = _SPRITES[self.sprite_key]
        elif self.x + self.sprite_w > width:
            self.x = width - self.sprite_w
            self.vx = -abs(self.vx)
            self.sprite_key = self._flipped_sprite_key()
            _, self.sprite_w, self.sprite_h = _SPRITES[self.sprite_key]

        # Bounce off the top edge and the sand surface below.
        # The fish's bottom (y + sprite_h) must stay above the sand at
        # the column the fish is over, with a 1-pixel gap so it never
        # appears to swim through the sand.
        margin_top = 4
        if self.y < margin_top:
            self.y = margin_top
            self.vy = abs(self.vy)
        else:
            # The sand surface varies by column. Use the *highest* sand
            # under the fish (i.e., the shallowest water) so the fish
            # never goes through any sand.
            x_start = max(0, self.x)
            x_end = min(width, self.x + self.sprite_w)
            if x_end > x_start:
                highest_sand_top = height - min(sand_profile[x_start:x_end])
                fish_bottom = self.y + self.sprite_h
                if fish_bottom > highest_sand_top - 1:
                    self.y = highest_sand_top - 1 - self.sprite_h
                    if self.y < margin_top:
                        self.y = margin_top
                    self.vy = -abs(self.vy)  # always bounce up

    def _flipped_sprite_key(self):
        """Return the sprite key with the facing direction swapped."""
        size, facing = self.sprite_key.split('_')
        new_facing = 'l' if facing == 'r' else 'r'
        return f'{size}_{new_facing}'

    def get_pixels(self):
        """Return the list of (x, y, r, g, b) for this fish's sprite."""
        offsets, _, _ = _SPRITES[self.sprite_key]
        r, g, b = self.color
        return [(self.x + dx, self.y + dy, r, g, b) for dx, dy in offsets]


class Bubble:
    """A single bubble: a pixel that rises with slight horizontal sway.

    Bubbles do NOT respawn when they reach the top -- they pop. The
    FishTank spawns new bubbles one at a time at the bottom of the screen
    with BUBBLE_SPAWN_CHANCE per frame.
    """

    def __init__(self, x, y):
        # Spawn position is set explicitly by the FishTank so bubbles
        # start at the bottom of the screen.
        self.x = x
        self.y = y

    def update(self, width, height):
        # Rise.
        self.y -= BUBBLE_RISE_SPEED
        # Occasional horizontal sway.
        if random.random() < BUBBLE_SWAY_CHANCE:
            self.x += random.choice([-1, 0, 0, 1])  # bias toward "no sway"
        # Clamp x to the screen.
        if self.x < 0:
            self.x = 0
        elif self.x >= width:
            self.x = width - 1

    def is_popped(self):
        """True when the bubble has risen above the top of the screen."""
        return self.y < 0

    def get_pixels(self):
        # Pale blue-white, like an air bubble in water.
        return [(self.x, self.y, 200, 220, 255)]


class Seaweed:
    """A single seaweed stalk: a vertical column of pixels rooted in the
    sand at the bottom of the screen, with a swaying tip.

    The base of the stalk sits at y = (height - sand_height_at[x]) -- on
    top of the sand at the stalk's column -- and the stalk grows upward
    from there. The top pixel sways by +-1.
    """

    def __init__(self, x, height, sand_profile):
        # Stalks are positioned at columns chosen by FishTank (which
        # distributes them with minimum separation).
        self.x = x
        self.height = random.randint(SEAWEED_MIN_HEIGHT, SEAWEED_MAX_HEIGHT)
        # Sway: a per-stalk x-offset of -1, 0, or +1, which we randomly
        # change over time to make the tip wiggle.
        self.sway = 0
        # Cache the screen height and the sand profile.
        self._screen_height = height
        self._sand_profile = sand_profile

    def update(self, width, height):
        if random.random() < SEAWEED_SWAY_CHANCE:
            # Choose a new sway, but don't let it jump too far in one step
            # (limit to +-1 change per sway event for smooth motion).
            self.sway += random.choice([-1, 0, 1])
            self.sway = max(-1, min(1, self.sway))
        # Clamp the swayed x to the screen.
        if self.x + self.sway < 0 or self.x + self.sway >= width:
            self.sway = 0

    def get_pixels(self):
        """Return pixels for this stalk. The base is anchored on top of the
        sand, the tip sways."""
        r, g, b = SEAWEED_COLOR
        pixels = []
        # The base of the stalk sits one row above the sand at this column.
        sand_here = self._sand_profile[self.x] if 0 <= self.x < len(self._sand_profile) else 0
        base_y = self._screen_height - sand_here - 1
        for i in range(self.height):
            if i == self.height - 1:
                # Tip pixel: swayed
                px = self.x + self.sway
            else:
                # Body pixels: anchored
                px = self.x
            y = base_y - i
            if 0 <= y < self._screen_height and 0 <= px < len(self._sand_profile):
                pixels.append((px, y, r, g, b))
        return pixels


# ----------------------------------------------------------------------------
# Tank
# ----------------------------------------------------------------------------
class Sand:
    """The sea floor: a per-column row count, SAND_MIN_ROWS..SAND_MAX_ROWS deep.

    The fish swim above the sand; bubbles rise from the sand; seaweed
    grows out of it. The height varies by column to give the floor some
    contour, like a real sea floor.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Per-column depth, randomized.
        self.profile = [random.randint(SAND_MIN_ROWS, SAND_MAX_ROWS)
                        for _ in range(width)]

    def get_pixels(self):
        """Return sand pixels, drawn from the bottom up to the configured
        depth in each column."""
        r, g, b = SAND_COLOR
        pixels = []
        for x, depth in enumerate(self.profile):
            for i in range(depth):
                y = self.height - 1 - i
                pixels.append((x, y, r, g, b))
        return pixels


class FishTank:
    """Owns the sand, fish, bubbles, and seaweed. Renderer-agnostic.

    Sand is generated first (it determines the contour of the sea floor),
    then seaweed is positioned on top of it, then fish swim in the water
    above the sand, and bubbles percolate upward.
    """

    def __init__(self, width=64, height=64):
        self.width = width
        self.height = height

        # Build the sand first -- the seaweed and fish need to know the
        # sand profile to position themselves correctly.
        self.sand = Sand(width, height)

        # Distribute seaweed stalks across the screen with minimum separation.
        seaweed_xs = self._distribute_columns(NUM_SEAWEED, min_sep=3)
        self.seaweed = [Seaweed(x, height, self.sand.profile)
                        for x in seaweed_xs]

        # Fish know the sand profile so they can stay above it.
        self.fish = [Fish(width, height, self.sand.profile)
                     for _ in range(NUM_FISH)]

        # Bubbles are spawned one at a time (no pre-spawned population).
        self.bubbles = []

    def _distribute_columns(self, n, min_sep, max_tries=200):
        """Pick n columns for seaweed, ensuring each is at least min_sep
        columns away from every other. Returns a sorted list of x positions."""
        chosen = []
        tries = 0
        while len(chosen) < n and tries < max_tries:
            tries += 1
            x = random.randint(0, self.width - 1)
            if all(abs(x - c) >= min_sep for c in chosen):
                chosen.append(x)
        # If we couldn't find n well-separated positions, fill the rest
        # with random columns (overlap is OK at that point).
        while len(chosen) < n:
            chosen.append(random.randint(0, self.width - 1))
        chosen.sort()
        return chosen

    def update(self):
        # Fish move (using the sand profile to keep them above the floor).
        for f in self.fish:
            f.update(self.width, self.height, self.sand.profile)

        # Spawn new bubbles with BUBBLE_SPAWN_CHANCE per frame.
        if random.random() < BUBBLE_SPAWN_CHANCE:
            x = random.randint(0, self.width - 1)
            y = self.height - 1  # bottom row
            self.bubbles.append(Bubble(x, y))

        # Move existing bubbles, then remove any that have popped at the top.
        for b in self.bubbles:
            b.update(self.width, self.height)
        self.bubbles = [b for b in self.bubbles if not b.is_popped()]

        # Seaweed sways.
        for s in self.seaweed:
            s.update(self.width, self.height)

    def get_pixels(self):
        """Return the list of (x, y, r, g, b) tuples for everything in the tank.

        Note: the water itself is NOT drawn -- the matrix's off-state is the
        water. Only sand, seaweed, fish, and bubbles produce pixels.

        Layering (back to front): sand -> seaweed -> fish -> bubbles.
        """
        pixels = []
        pixels.extend(self.sand.get_pixels())
        for s in self.seaweed:
            pixels.extend(s.get_pixels())
        for f in self.fish:
            pixels.extend(f.get_pixels())
        for b in self.bubbles:
            pixels.extend(b.get_pixels())
        return pixels


# ----------------------------------------------------------------------------
# Entry point called by main.py
# ----------------------------------------------------------------------------
def RunFishTank(disp):
    """Run the fish tank for RUNTIME_SECONDS, then return."""
    print("Running Fish Tank")
    print(f"  {NUM_FISH} fish, {NUM_SEAWEED} seaweed stalks, "
          f"spawn_chance={BUBBLE_SPAWN_CHANCE}")
    print(f"  runtime: {RUNTIME_SECONDS}s, frame: {FRAME_TIME_MS}ms")

    tank = FishTank(disp.width, disp.height)
    start_time = time.time()
    next_frame_time = start_time

    while True:
        # Update simulation.
        tank.update()

        # Render.
        disp.clear()
        for x, y, r, g, b in tank.get_pixels():
            disp.set_pixel(x, y, r, g, b)
        disp.show()

        # Frame timing.
        next_frame_time += FRAME_TIME_MS / 1000.0
        sleep_time = next_frame_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)
        else:
            # If we fell behind, reset the schedule so we don't accumulate
            # delay over a long session.
            next_frame_time = time.time()

        # Check runtime limit.
        if time.time() - start_time >= RUNTIME_SECONDS:
            print(f"  Fish tank runtime ({RUNTIME_SECONDS}s) reached")
            return
