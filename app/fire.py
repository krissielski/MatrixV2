import random
import time

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
RUNTIME_SECONDS = 300   # How long the fire runs (in seconds)
COOLING        = 80     # How fast fire cools per row (range 20–80; higher = shorter flames)
WIND           = 0      # Horizontal drift: negative = left, positive = right, 0 = none
FRAME_DELAY    = 0.03   # Seconds between frames (~33 fps)
# ============================================================================


# ---------------------------------------------------------------------------
# Color palette: black (0) → red → orange → yellow → white (255)
# 256 entries, pre-built once at module load so get_pixels() stays fast.
# ---------------------------------------------------------------------------
def _build_palette():
    palette = []
    for i in range(256):
        if i < 64:
            # Black → deep red
            t = i / 63.0
            palette.append((int(180 * t), 0, 0))
        elif i < 128:
            # Deep red → bright red
            t = (i - 64) / 63.0
            palette.append((int(180 + 75 * t), 0, 0))
        elif i < 192:
            # Bright red → orange → yellow
            t = (i - 128) / 63.0
            palette.append((255, int(255 * t), 0))
        else:
            # Yellow → white
            t = (i - 192) / 63.0
            palette.append((255, 255, int(255 * t)))
    return palette


_PALETTE = _build_palette()


class Fire:
    """Classic upward-propagating cellular fire simulation.

    The heat grid stores values 0–255 per cell (0 = cold / black,
    255 = hottest / white).  Each frame:
      1. The bottom two rows are re-seeded with near-maximum heat.
      2. Every other row is computed by averaging three neighbours
         from the row below, subtracting a small random cooling
         amount, and optionally drifting one pixel in the wind
         direction.  This makes heat rise and dissipate naturally.
      3. Cell values are mapped through a pre-built 256-entry
         hot-colour palette before being sent to the display.
    """

    def __init__(self, width=64, height=64):
        self.width  = width
        self.height = height
        # heat[y][x], y=0 is top, y=height-1 is bottom
        self.heat = [[0] * width for _ in range(height)]

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------
    def update(self):
        """Advance the fire simulation by one step."""
        w = self.width
        h = self.height

        # ---- Step 1: seed the base of the fire ----
        # Bottom row: full intensity with mild flicker
        for x in range(w):
            self.heat[h - 1][x] = random.randint(220, 255)

        # Second-to-bottom row: slightly lower, random gaps for texture
        for x in range(w):
            self.heat[h - 2][x] = random.randint(180, 245) if random.random() < 0.85 else random.randint(80, 160)

        # ---- Step 2: propagate heat upward (y decreasing) ----
        # We iterate top-to-bottom in array order (y=0 … h-3) so that
        # each row is computed from the original values of the row below,
        # not values already updated this frame.  We build a new grid
        # row-by-row to respect that requirement.
        new_heat = [row[:] for row in self.heat]

        for y in range(h - 2):          # rows 0 … h-3  (leave bottom two untouched)
            for x in range(w):
                # Average three neighbours from the row below
                left  = self.heat[y + 1][(x - 1) % w]
                mid   = self.heat[y + 1][x]
                right = self.heat[y + 1][(x + 1) % w]
                avg   = (left + mid + mid + right) >> 2   # weight centre pixel ×2

                # Random cooling proportional to COOLING constant
                decay = random.randint(0, max(1, COOLING >> 3))

                val = max(0, avg - decay)

                # Apply wind drift: store the result one pixel left/right
                dest_x = (x + WIND) % w
                new_heat[y][dest_x] = val

        self.heat = new_heat

    # ------------------------------------------------------------------
    # Pixel output
    # ------------------------------------------------------------------
    def get_pixels(self):
        """Return list of (x, y, r, g, b) tuples for every non-black cell."""
        pixels = []
        for y in range(self.height):
            row = self.heat[y]
            for x in range(self.width):
                v = row[x]
                if v > 0:
                    r, g, b = _PALETTE[v]
                    pixels.append((x, y, r >> 1, g >> 1, b >> 1))
        return pixels


# ---------------------------------------------------------------------------
# Game loop
# ---------------------------------------------------------------------------
def RunFire(disp):
    """Run the fire simulation on *disp* until RUNTIME_SECONDS elapses."""

    print("Running Fire")

    start_time = time.time()
    fire = Fire(disp.width, disp.height)

    while True:
        fire.update()

        pixel_list = fire.get_pixels()

        disp.clear()

        for x, y, r, g, b in pixel_list:
            disp.set_pixel(x, y, r, g, b)

        disp.show()
        time.sleep(FRAME_DELAY)

        elapsed = time.time() - start_time
        if elapsed >= RUNTIME_SECONDS:
            print(f"Fire runtime limit ({RUNTIME_SECONDS} seconds) reached")
            return
