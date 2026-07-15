import random
import time

# ============================================================================
# USER-ADJUSTABLE PARAMETERS
# ============================================================================
# Layout
NUM_BARS = 60            # Total number of vertical bars
UNIQUE_SIZES = 30        # How many distinct bar lengths exist (bars per size = NUM_BARS // UNIQUE_SIZES)
MIN_LENGTH = 4           # Shortest bar height in pixels
# Tallest bar height. With range(MIN_LENGTH, MAX_LENGTH+1) producing UNIQUE_SIZES
# values, MAX_LENGTH must equal MIN_LENGTH + UNIQUE_SIZES - 1 (not +UNIQUE_SIZES).
MAX_LENGTH = MIN_LENGTH + UNIQUE_SIZES - 1
BORDER_X = 2             # Horizontal border on each side (so bars sit at x=BORDER_X..width-BORDER_X-1)
BOTTOM_OFFSET = 10       # Vertical offset (in pixels) that lifts the bars up from the bottom.
                          # 0 = bars sit on the bottom row. ~21 = bars lifted ~1/3 of the way up
                          # on a 64-tall matrix. The constraint is:
                          # BOTTOM_OFFSET + MAX_LENGTH <= height.

# Visual
COLOR_BY_LENGTH = True   # True: color is a function of bar length (rainbow). False: random per-bar color
SATURATION = 255         # HSV saturation 0-255
VALUE = 127              # HSV value/brightness 0-255 (127 ~= 50% to keep the matrix from being blinding)

# Animation
SETTLE_DELAY_SECONDS = 3   # Pause after creating the initial set, before the sort begins
STEP_DELAY_MS = 30         # Delay between bubble-sort compare/swap steps (milliseconds)
FINAL_HOLD_SECONDS = 5     # Pause after the sort completes, showing the final sorted state
FRAME_TIME_MS = 50         # Frame delay in milliseconds (used for the initial display loop)

# Algorithm
RANDOMIZE_START = True     # If True, the starting bar order is shuffled. If False, bars are in
                            # ascending height order (useful for debugging).
# ============================================================================


# ----------------------------------------------------------------------------
# Algorithm rotation
# ----------------------------------------------------------------------------
# Each call to RunSort() picks the next algorithm from this list and advances
# the index. The list is in-memory (resets on script restart) — the user chose
# in-memory persistence over a JSON file. Add more algorithms here as they're
# implemented on SortVisualizer.
_ALGORITHMS = ['selection', 'insertion', 'merge', 'bubble', 'quick']
_algorithm_index = 0  # module-level: persists across RunSort() calls in the same process


def _next_algorithm():
    """Return the next algorithm name and advance the rotation pointer."""
    global _algorithm_index
    name = _ALGORITHMS[_algorithm_index % len(_ALGORITHMS)]
    _algorithm_index += 1
    return name


# Methods on SortVisualizer that sort in place and return (comparisons, swaps).
# Keep this in sync with the names in _ALGORITHMS.
_SORT_METHODS = {
    'selection': 'selection_sort',
    'insertion': 'insertion_sort',
    'merge':     'merge_sort',
    'bubble':    'bubble_sort',
    'quick':     'quick_sort',
}


class SortVisualizer:
    """
    Visualizes a list of vertical bars and (eventually) sorts them.

    State held:
        self.items   : list of (length, (r,g,b)) pairs, indexed left-to-right.
                       Bundling length and color together means a swap always
                       moves the bar *and* its color in one step.
        self.bars    : view over self.items, just the lengths.
        self.colors  : view over self.items, just the colors.

    The class is renderer-agnostic; it only computes layout and colors.
    Sorting algorithms mutate self.items in place; rendering reads it back.
    """

    def __init__(self, width=64, height=64):
        self.width = width
        self.height = height

        # Sanity-check the layout against the actual matrix size.
        if NUM_BARS % UNIQUE_SIZES != 0:
            raise ValueError(
                f"NUM_BARS ({NUM_BARS}) must be evenly divisible by "
                f"UNIQUE_SIZES ({UNIQUE_SIZES}) so each size appears the same "
                f"number of times."
            )
        if MAX_LENGTH + BOTTOM_OFFSET > self.height:
            raise ValueError(
                f"Tallest bar (MAX_LENGTH={MAX_LENGTH}) + BOTTOM_OFFSET="
                f"{BOTTOM_OFFSET} exceeds matrix height {self.height}."
            )
        if BORDER_X * 2 + NUM_BARS > self.width:
            raise ValueError(
                f"BORDER_X*2 + NUM_BARS = {BORDER_X * 2 + NUM_BARS} exceeds "
                f"matrix width {self.width}."
            )

        self.bars_per_size = NUM_BARS // UNIQUE_SIZES  # 2 with current defaults
        self.items = self._build_initial_items(ordered=not RANDOMIZE_START)
        # Set of bar indices to draw in white (highlighted "current" bars).
        # Algorithms mutate this set to mark the bars they're currently
        # working on. The set is rendered as a highlight in get_pixels() —
        # any bar whose column index is in the set is drawn in white
        # instead of its normal color. The bar's own color in self.items
        # is never modified, so removing an index from the set instantly
        # restores the bar's normal color.
        #
        # Algorithms that use this MUST clear the set before returning
        # (or on exception). Use try/finally to be safe.
        self.highlighted_indices = set()

    # Convenient read-only views so callers (and get_pixels) don't have to unpack.
    @property
    def bars(self):
        return [length for length, _ in self.items]

    @property
    def colors(self):
        return [color for _, color in self.items]

    # ---------------------------------------------------------------------
    # State construction
    # ---------------------------------------------------------------------
    def _build_initial_items(self, ordered=True):
        """
        Build the starting (length, color) list.

        If ordered=True, the lengths go MIN_LENGTH..MAX_LENGTH in order with
        self.bars_per_size copies each, and the colors line up with length
        (so the result is the smooth left-to-right rainbow staircase).

        If ordered=False, the items are returned in random order — the
        starting state for a sorting run.
        """
        # Build the multiset of sizes: [4,4, 5,5, 6,6, ..., MAX,MAX]
        sizes = []
        for length in range(MIN_LENGTH, MAX_LENGTH + 1):
            sizes.extend([length] * self.bars_per_size)
        assert len(sizes) == NUM_BARS

        colors = self._assign_colors(sizes)
        items = list(zip(sizes, colors))

        if not ordered:
            random.shuffle(items)

        return items

    def shuffle(self):
        """Re-randomize the current order in place."""
        random.shuffle(self.items)

    def is_sorted(self):
        """True if bars are in non-decreasing order left-to-right."""
        return all(self.bars[i] <= self.bars[i + 1] for i in range(len(self.bars) - 1))

    def _add_highlight(self, index):
        """Add a bar index to the highlight set. No-op if already present."""
        self.highlighted_indices.add(index)

    def _clear_highlights(self):
        """Remove all highlights. Called by algorithms on entry and exit."""
        self.highlighted_indices.clear()

    def selection_sort(self, disp):
        """
        In-place selection sort with a moving "current minimum" highlight.

        Algorithm:
          - The sorted region grows on the right (i.e., positions [0..i-1]
            are sorted after the i-th outer iteration).
          - For each i from 0 to n-2, scan [i..n-1] for the minimum, then
            swap that minimum into position i.

        Pacing: redraw whenever the running minimum changes (so the white
        highlight visibly sweeps leftward across the unsorted region) and
        again after the final swap into position i. Comparisons that
        don't change the running minimum don't pause — otherwise the
        screen would freeze on long stretches of "this is still the min".

        Highlight: the current minimum bar is drawn in white.

        Returns (comparisons, swaps). Always clears self.highlighted_indices
        before returning so subsequent algorithms aren't affected.
        """
        n = len(self.items)
        comparisons = 0
        swaps = 0

        try:
            for i in range(n - 1):
                # Start the scan assuming position i is the minimum, and
                # light it up so the viewer can track the highlight.
                self._clear_highlights()
                self._add_highlight(i)
                self._redraw(disp)
                time.sleep(STEP_DELAY_MS / 1000.0)

                min_idx = i
                for j in range(i + 1, n):
                    comparisons += 1
                    if self.bars[j] < self.bars[min_idx]:
                        # New minimum found — move the highlight from the
                        # old min to the new one.
                        self._clear_highlights()
                        min_idx = j
                        self._add_highlight(min_idx)
                        self._redraw(disp)
                        time.sleep(STEP_DELAY_MS / 1000.0)

                # Place the found minimum at position i. If min_idx == i
                # this is a no-op (the bar was already in place), but
                # always count a comparison and skip the swap to keep
                # the stats honest.
                if min_idx != i:
                    self.items[i], self.items[min_idx] = self.items[min_idx], self.items[i]
                    swaps += 1

                # Clear the highlight before the next outer iteration.
                self._clear_highlights()
                self._redraw(disp)
        finally:
            # Defensive: even if the sort raises, don't leave a stale
            # highlight on for the next algorithm.
            self._clear_highlights()

        return comparisons, swaps

    def merge_sort(self, disp):
        """
        Bottom-up iterative merge sort.

        Algorithm:
          - Start with runs of length 1 (every bar is its own "sorted run").
          - Each pass merges adjacent runs of length `width` into runs of
            length 2*width. Double `width` and repeat until it covers the
            whole array.

        Highlight: the next write position `k` is drawn in white. As the
        merged run fills in, the highlight marches rightward from `start`
        to `end`, then jumps back to the start of the next run to merge.

        Pacing: redraw after every element placed during a merge (so viewers
        watch the merged run "fill in" from left to right). Comparisons are
        counted but don't pause on their own.

        Returns (comparisons, writes) — merge sort doesn't swap, it writes.
        """
        n = len(self.items)
        if n <= 1:
            return 0, 0

        comparisons = 0
        writes = 0
        width = 1

        try:
            while width < n:
                for start in range(0, n, 2 * width):
                    mid = min(start + width, n)
                    end = min(start + 2 * width, n)

                    # Nothing to merge if the right half is empty.
                    if mid >= end:
                        continue

                    # Slice out the two runs. We copy because we'll be writing
                    # back into self.items[start:end] in place.
                    left = self.items[start:mid]
                    right = self.items[mid:end]

                    i, j, k = 0, 0, start
                    # Mark the next write position so the viewer can see
                    # the merge "fill in" left to right.
                    self._clear_highlights()
                    self._add_highlight(k)
                    self._redraw(disp)
                    time.sleep(STEP_DELAY_MS / 1000.0)

                    while i < len(left) and j < len(right):
                        comparisons += 1
                        if left[i][0] <= right[j][0]:
                            self.items[k] = left[i]
                            i += 1
                        else:
                            self.items[k] = right[j]
                            j += 1
                        k += 1
                        writes += 1
                        # Advance the highlight to the new write position.
                        self._clear_highlights()
                        self._add_highlight(k)
                        self._redraw(disp)
                        time.sleep(STEP_DELAY_MS / 1000.0)

                    # One side is exhausted. Drain the rest. We can bulk-assign
                    # here since the values are already in their final relative
                    # order, but for visual continuity we still redraw once at
                    # the end of the merge.
                    if i < len(left):
                        self.items[k:end] = left[i:]
                        writes += end - k
                    elif j < len(right):
                        self.items[k:end] = right[j:]
                        writes += end - k
                    self._clear_highlights()
                    self._redraw(disp)

                width *= 2
        finally:
            self._clear_highlights()

        return comparisons, writes

    def insertion_sort(self, disp):
        """
        In-place insertion sort.

        Algorithm:
          - Maintain a growing sorted region on the left (initially just
            self.items[0], a run of length 1).
          - For each i from 1 to n-1, take self.items[i] and shift it
            leftward through the sorted region until it lands in its
            correct position.

        Highlight: the bar currently being inserted (column j) is drawn in
        white. The highlight tracks the bar as it drifts leftward through
        the sorted region, then clears when the bar finds its slot.

        Pacing: redraw after every swap (one shift left = one swap). This
        makes the visual signature unmistakable — you can watch a single
        bar "drift" leftward across the sorted region as the algorithm
        finds its place.

        Returns (comparisons, swaps).
        """
        n = len(self.items)
        comparisons = 0
        swaps = 0

        try:
            for i in range(1, n):
                # Mark the bar we're about to insert. It might not move
                # at all if it's already in place — in that case the
                # single inner-iter compare will tell us and we'll clear
                # the highlight.
                j = i
                self._clear_highlights()
                self._add_highlight(j)
                self._redraw(disp)
                time.sleep(STEP_DELAY_MS / 1000.0)

                # Shift self.items[j] left through the sorted region
                # [0..j-1] until it's >= its left neighbor (or j == 0).
                while j > 0:
                    comparisons += 1
                    if self.bars[j - 1] > self.bars[j]:
                        # Swap items as a single unit so color moves with the bar.
                        self.items[j - 1], self.items[j] = self.items[j], self.items[j - 1]
                        swaps += 1
                        j -= 1
                        # Clear-then-add (not just add) so the highlight
                        # follows only the *currently moving* bar. Without
                        # the clear, every previous j would stay in the
                        # set, and the highlight would trail behind like
                        # a comet — confusing, since the user expects
                        # "this one bar" to be marked.
                        self._clear_highlights()
                        self._add_highlight(j)
                        self._redraw(disp)
                        time.sleep(STEP_DELAY_MS / 1000.0)
                    else:
                        # Found the right place; sorted region is still sorted.
                        break

                # The bar found its place (or was already there). Clear
                # the highlight before the next outer iteration.
                self._clear_highlights()
                self._redraw(disp)
        finally:
            self._clear_highlights()

        return comparisons, swaps

    def bubble_sort(self, disp):
        """
        In-place bubble sort. After each swap the matrix is redrawn and
        STEP_DELAY_MS is slept so the animation is watchable on the LED panel.

        Highlight: only the two bars being swapped are drawn in white,
        and only at the moment of the swap. No-swap comparisons don't
        highlight anything, so the viewer sees a clean "two bars flash
        white, then they swap, then static" rhythm rather than a
        continuously moving pair (which can read as "one bar moves and
        the other just sits there").

        Returns (comparisons, swaps) once sorted.
        """
        n = len(self.items)
        comparisons = 0
        swaps = 0

        try:
            # Standard bubble sort with an early-exit when a full pass makes
            # no swaps (the list is already sorted at that point).
            #
            # Highlight: only the *two bars involved in a swap* are marked
            # white, and only on the iteration where the swap happens. On
            # no-swap iterations, nothing is highlighted and the matrix
            # isn't redrawn — this keeps the highlight meaningful ("a swap
            # is happening right here") and saves CPU on the bulk of the
            # comparisons, which don't move anything visually.
            for i in range(n - 1):
                made_swap = False
                for j in range(n - 1 - i):
                    comparisons += 1
                    if self.bars[j] > self.bars[j + 1]:
                        # Swap items as a single unit so color moves with the bar.
                        self.items[j], self.items[j + 1] = self.items[j + 1], self.items[j]
                        swaps += 1
                        made_swap = True
                        # Mark the pair briefly, redraw, then sleep so
                        # the viewer sees "two white bars, then they swap."
                        self._clear_highlights()
                        self._add_highlight(j)
                        self._add_highlight(j + 1)
                        self._redraw(disp)
                        time.sleep(STEP_DELAY_MS / 1000.0)
                    # No-swap path: no highlight, no redraw. The matrix
                    # keeps showing whatever it last showed (which is
                    # either the initial state or the previous swap's
                    # post-swap state). Static during long no-swap
                    # stretches is the right behavior — there's nothing
                    # to show.
                if not made_swap:
                    break
        finally:
            self._clear_highlights()

        return comparisons, swaps

    def quick_sort(self, disp):
        """
        In-place quicksort using Lomuto partitioning with an explicit stack
        (avoids Python's recursion-depth concerns and keeps the call sequence
        easy to instrument).

        Highlight: two bars are drawn in white during each partition —
        the pivot (a fixed bar throughout the partition) and the current
        compare position j (sweeps left to right). When a swap happens,
        both highlights are kept up to date; in particular, if the swap
        moves the pivot itself, the pivot highlight follows it to its
        new column.

        Pacing: we only redraw/sleep on a *swap* (the moment something visibly
        moves). Comparisons are counted but don't pause — otherwise quicksort
        would crawl through thousands of no-op comparisons on a 60-element
        array and the matrix would look frozen.

        Returns (comparisons, swaps).
        """
        n = len(self.items)
        if n <= 1:
            return 0, 0

        comparisons = 0
        swaps = 0
        # Stack holds (lo, hi) inclusive ranges still to be partitioned.
        # Start with the whole array. We shrink ranges as we place pivots.
        stack = [(0, n - 1)]

        try:
            while stack:
                lo, hi = stack.pop()
                if lo >= hi:
                    continue

                # Use the last element as the pivot. Median-of-three would be
                # nicer on adversarial input, but for shuffled starting data
                # this is fine and keeps the code simple.
                pivot_index = hi

                # Light up the pivot at the start of the partition. The
                # compare-position highlight (j) gets set inside the loop.
                self._clear_highlights()
                self._add_highlight(pivot_index)
                self._redraw(disp)
                time.sleep(STEP_DELAY_MS / 1000.0)

                # Lomuto partition: walk i from lo..hi-1, growing the "less
                # than pivot" region. When we're done, swap the pivot into
                # its final place right after that region.
                i = lo
                for j in range(lo, hi):
                    comparisons += 1
                    # Mark the pivot + current compare position. The
                    # pivot is in the set; add/remove j as the loop runs.
                    self._clear_highlights()
                    self._add_highlight(pivot_index)
                    self._add_highlight(j)
                    if self.bars[j] < self.bars[pivot_index]:
                        if i != j:
                            # Swap items as a single unit so color moves with the bar.
                            self.items[i], self.items[j] = self.items[j], self.items[i]
                            swaps += 1
                            # pivot_index may have shifted if i == pivot_index
                            if pivot_index == i:
                                pivot_index = j
                            # Redraw with the updated highlight set
                            # (pivot may have moved, j has moved).
                            self._clear_highlights()
                            self._add_highlight(pivot_index)
                            self._add_highlight(j)
                            self._redraw(disp)
                            time.sleep(STEP_DELAY_MS / 1000.0)
                        i += 1

                # Place the pivot just after the "less than" region.
                if i != pivot_index:
                    self.items[i], self.items[pivot_index] = self.items[pivot_index], self.items[i]
                    swaps += 1
                    pivot_index = i  # pivot is now at its final column
                    self._clear_highlights()
                    self._add_highlight(pivot_index)
                    self._redraw(disp)
                    time.sleep(STEP_DELAY_MS / 1000.0)

                # Push the two sub-ranges. The smaller side first limits
                # worst-case stack depth to O(log n) on average.
                left_size = i - 1 - lo
                right_size = hi - (i + 1)
                if left_size < right_size:
                    stack.append((lo, i - 1))
                    stack.append((i + 1, hi))
                else:
                    stack.append((i + 1, hi))
                    stack.append((lo, i - 1))
        finally:
            self._clear_highlights()

        return comparisons, swaps

    def _redraw(self, disp):
        """Clear the matrix and re-render the current state."""
        disp.clear()
        for x, y, r, g, b in self.get_pixels():
            disp.set_pixel(x, y, r, g, b)
        disp.show()

    def _assign_colors(self, sizes):
        """
        Return a list of (r,g,b) colors, one per bar.
        If COLOR_BY_LENGTH is True, color is a function of the bar's length
        (rainbow by size). Otherwise, each bar gets an independent random hue.
        """
        colors = []
        if COLOR_BY_LENGTH:
            # Map length -> hue. Shortest bars are red, longest are violet.
            # range(UNIQUE_SIZES) produces UNIQUE_SIZES distinct hues, so
            # bars of the same length always share a color (good for reading).
            for length in sizes:
                # size_index: 0 for the shortest, UNIQUE_SIZES-1 for the tallest
                size_index = length - MIN_LENGTH
                # Distribute hues across the full 0..359 range
                hue = int((size_index * 359) / max(1, UNIQUE_SIZES - 1))
                colors.append(self._hsv_to_rgb(hue, SATURATION, VALUE))
        else:
            for _ in sizes:
                hue = random.randint(0, 359)
                colors.append(self._hsv_to_rgb(hue, SATURATION, VALUE))
        return colors

    @staticmethod
    def _hsv_to_rgb(h, s, v):
        """Convert HSV to RGB. h: 0-359, s/v: 0-255."""
        h = h % 360
        s = s / 255.0
        v = v / 255.0

        c = v * s
        x = c * (1 - abs((h / 60.0) % 2 - 1))
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

    # ---------------------------------------------------------------------
    # Rendering
    # ---------------------------------------------------------------------
    def get_pixels(self):
        """
        Return a list of (x, y, r, g, b) tuples for the current bar state.

        Bars are vertical, 1px wide, drawn from the bottom up. Any bar
        whose column index is in self.highlighted_indices is drawn in
        white so it stands out against the rainbow — used by every sort
        to mark the bar(s) currently being worked on.
        """
        pixels = []
        for col, (length, color) in enumerate(self.items):
            x = BORDER_X + col
            # Apply the highlight by recoloring the bar to white. The bar's
            # own color in self.items stays untouched, so the highlight is
            # purely a rendering effect and is automatically restored when
            # the index is removed from self.highlighted_indices.
            if col in self.highlighted_indices:
                r, g, b = 255, 255, 255
            else:
                r, g, b = color
            # The base of the bar sits at y = (height - 1) - BOTTOM_OFFSET,
            # so the bar grows upward from there for `length` pixels.
            # Setting BOTTOM_OFFSET > 0 lifts the whole chart up off the bottom.
            for i in range(length):
                y = (self.height - 1 - BOTTOM_OFFSET) - i
                if 0 <= y < self.height:
                    pixels.append((x, y, r, g, b))
        return pixels


def RunSort(disp):
    """
    Entry point called by main.py.

    Each invocation rotates to the next algorithm in _ALGORITHMS, so the
    same call from main.py produces a different sort each time (within one
    process lifetime).

    1. Build the (randomized) bar layout.
    2. Hold it on screen for SETTLE_DELAY_SECONDS so the initial chaos is readable.
    3. Animate the selected sort, redrawing between meaningful steps.
    4. Hold the final sorted state for FINAL_HOLD_SECONDS.
    """
    algo_name = _next_algorithm()
    if algo_name not in _SORT_METHODS:
        print(f"  WARNING: unknown algorithm '{algo_name}', falling back to bubble")
        algo_name = 'bubble'
    sort_method = getattr(SortVisualizer, _SORT_METHODS[algo_name])

    print(f"Running Sort Visualizer ({algo_name} sort)")
    print(f"  {NUM_BARS} bars, {UNIQUE_SIZES} sizes, "
          f"lengths {MIN_LENGTH}..{MAX_LENGTH}, "
          f"randomize_start={RANDOMIZE_START}")

    viz = SortVisualizer(disp.width, disp.height)

    # 1) Settle: show the initial (randomized) state.
    _hold(disp, viz, SETTLE_DELAY_SECONDS, "initial")

    # 2) Run the selected sort. The method redraws after each meaningful
    #    step, so all we need to do is drive it and report what happened.
    #    The return shape is (comparisons, moves) where 'moves' is swaps
    #    for in-place sorts and writes for merge sort.
    print("  sorting...")
    comparisons, moves = sort_method(viz, disp)
    print(f"  done: {comparisons} comparisons, {moves} moves")

    if not viz.is_sorted():
        # Shouldn't happen, but worth flagging.
        print(f"  WARNING: {algo_name} exited but bars are not sorted!")

    # 3) Hold the final sorted state.
    _hold(disp, viz, FINAL_HOLD_SECONDS, "sorted")


def _hold(disp, viz, seconds, label):
    """Show the current viz state on the matrix for `seconds` seconds."""
    end_time = time.time() + seconds
    while time.time() < end_time:
        viz._redraw(disp)  # reuse the same redraw helper the sort uses
        time.sleep(FRAME_TIME_MS / 1000.0)
    print(f"  ({label} state shown for {seconds}s)")
