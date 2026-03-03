import random
import time
from dataclasses import dataclass, field

from lib.word_list import WordList

GRID_SIZE = 15
MAX_BLACK_CELLS = int(GRID_SIZE * GRID_SIZE * 0.40)  # 40% of grid = 90


@dataclass
class Cell:
    is_black: bool = False
    letter: str = None
    number: int = None


@dataclass
class PlacedWord:
    word: str
    row: int
    col: int
    direction: str  # 'across' or 'down'
    number: int = 0
    is_themed: bool = False


@dataclass
class Slot:
    row: int
    col: int
    direction: str
    length: int
    cells: list = field(default_factory=list)  # list of (r, c)

    def pattern(self, grid):
        """Get current pattern from grid: letters or _ for empty."""
        return ''.join(grid[r][c].letter if grid[r][c].letter else '_' for r, c in self.cells)

    def is_filled(self, grid):
        return all(grid[r][c].letter is not None for r, c in self.cells)


# ---------------------------------------------------------------------------
# Black cell patterns defined as string grids (X=black, .=white)
# All have rotational symmetry and ~36-38 black cells
# ---------------------------------------------------------------------------

_PATTERN_STRINGS = [
    # Pattern A: "staircase" — 34 blacks, 70 words, max_run=12
    [
        "...##.....#....",
        "...#...........",
        "...#...........",
        ".......#...#...",
        "............###",
        "#........##....",
        "...#....##.....",
        ".....#...#.....",
        ".....##....#...",
        "....##........#",
        "###............",
        "...#...#.......",
        "...........#...",
        "...........#...",
        "....#.....##...",
    ],
    # Pattern B: "crossover" — 34 blacks, 74 words, max_run=15
    [
        ".......#...#...",
        ".......#...#...",
        ".......#.......",
        "...##..........",
        "...#....##.....",
        ".....##....#...",
        "##....#........",
        "....#.....#....",
        "........#....##",
        "...#....##.....",
        ".....##....#...",
        "..........##...",
        ".......#.......",
        "...#...#.......",
        "...#...#.......",
    ],
    # Pattern C: "diamond" — 35 blacks, 62 words, max_run=12
    [
        ".....##.......#",
        "......#.......#",
        "......#.......#",
        "............###",
        "...##.........#",
        ".....#...##....",
        "...........#...",
        ".......#.......",
        "...#...........",
        "....##...#.....",
        "#.........##...",
        "###............",
        "#.......#......",
        "#.......#......",
        "#.......##.....",
    ],
    # Pattern D: "dense staircase" — ~58 blacks, ~34 words
    [
        "##.....#..##...",
        "#......#.......",
        "......##.......",
        "...##....##....",
        "..#......#..##.",
        ".....##........",
        "##.......#.....",
        "...#.......#...",
        ".....#.......##",
        "........##.....",
        ".##..#......#..",
        "....##....##...",
        ".......##......",
        ".......#......#",
        "...##..#.....##",
    ],
    # Pattern E: "dense pinwheel" — ~60 blacks, ~32 words
    [
        "###....#.......",
        "#.....##.......",
        "......#...#....",
        "..##.....##....",
        "..#.......#..##",
        "........##.....",
        "#...#..........",
        "...#.......#...",
        "..........#...#",
        ".....##........",
        "##..#.......#..",
        "....##.....##..",
        "....#...#......",
        ".......##.....#",
        ".......#....###",
    ],
    # Pattern F: "dense blocks" — ~62 blacks, ~30 words
    [
        "##.....##..##..",
        "#......#.......",
        "......##.......",
        "...##....#.....",
        "..##......#..##",
        ".......##......",
        "##..#..........",
        "...#.......#...",
        "..........#..##",
        "......##.......",
        "##..#......##..",
        ".....#....##...",
        ".......##......",
        ".......#......#",
        "..##..##.....##",
    ],
]

# Preferred order: dense patterns first (D, E, F) for better themed ratio,
# then sparse patterns (A, B, C) as fallback.
_PATTERN_ORDER = [3, 4, 5, 0, 1, 2]


def _parse_pattern(pattern_rows):
    """Parse a string-based pattern into a set of (row, col) black cell positions."""
    black_cells = set()
    for r, row in enumerate(pattern_rows):
        for c, ch in enumerate(row):
            if ch in ('X', '#'):
                black_cells.add((r, c))
    return black_cells


def _validate_pattern_symmetry(black_cells):
    """Check rotational symmetry and return the symmetric version."""
    result = set()
    for r, c in black_cells:
        result.add((r, c))
        result.add((14 - r, 14 - c))
    return result


_ALL_PATTERNS = []
for ps in _PATTERN_STRINGS:
    cells = _parse_pattern(ps)
    cells = _validate_pattern_symmetry(cells)
    _ALL_PATTERNS.append(cells)


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------

def _make_grid():
    return [[Cell() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]


def _get_cell(grid, r, c):
    if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
        return grid[r][c]
    return None


def _apply_pattern(grid, black_cells):
    """Apply a black cell pattern to the grid."""
    for r, c in black_cells:
        grid[r][c].is_black = True


def _fix_long_slots(grid, max_slot_length=8):
    """Break up any slot longer than max_slot_length by adding symmetric black cells.

    Iteratively finds the longest run in any direction and splits it at
    the midpoint, preserving rotational symmetry.  Stops when all runs
    are within bounds.
    """
    changed = True
    iterations = 0
    while changed and iterations < 50:
        changed = False
        iterations += 1

        # --- horizontal runs ---
        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                if grid[r][c].is_black:
                    c += 1
                    continue
                start = c
                while c < GRID_SIZE and not grid[r][c].is_black:
                    c += 1
                run_len = c - start
                if run_len > max_slot_length:
                    mid = start + run_len // 2
                    grid[r][mid].is_black = True
                    grid[14 - r][14 - mid].is_black = True
                    changed = True
                    break
            if changed:
                break

        if changed:
            continue

        # --- vertical runs ---
        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                if grid[r][c].is_black:
                    r += 1
                    continue
                start = r
                while r < GRID_SIZE and not grid[r][c].is_black:
                    r += 1
                run_len = r - start
                if run_len > max_slot_length:
                    mid = start + run_len // 2
                    grid[mid][c].is_black = True
                    grid[14 - mid][14 - c].is_black = True
                    changed = True
                    break
            if changed:
                break


# ---------------------------------------------------------------------------
# Slot extraction
# ---------------------------------------------------------------------------

def _extract_slots(grid):
    """Find all horizontal and vertical slots (runs of non-black cells >= 3)."""
    slots = []

    # Horizontal (across)
    for r in range(GRID_SIZE):
        c = 0
        while c < GRID_SIZE:
            if grid[r][c].is_black:
                c += 1
                continue
            start = c
            cells = []
            while c < GRID_SIZE and not grid[r][c].is_black:
                cells.append((r, c))
                c += 1
            if len(cells) >= 3:
                slots.append(Slot(r, start, 'across', len(cells), cells))

    # Vertical (down)
    for c in range(GRID_SIZE):
        r = 0
        while r < GRID_SIZE:
            if grid[r][c].is_black:
                r += 1
                continue
            start = r
            cells = []
            while r < GRID_SIZE and not grid[r][c].is_black:
                cells.append((r, c))
                r += 1
            if len(cells) >= 3:
                slots.append(Slot(start, c, 'down', len(cells), cells))

    return slots


# ---------------------------------------------------------------------------
# Themed word placement into slots
# ---------------------------------------------------------------------------

def _place_themed_into_slots(grid, slots, keywords, word_list):
    """Place themed keywords into existing slots.

    Strategy: for each keyword (longest first), find the best matching slot
    and verify that crossing slots remain fillable. If placing a themed word
    makes any crossing slot unfillable, skip it.

    Uses aggressive placement (threshold=1) to maximize themed word count.
    Does two passes: first strict (threshold=3), then relaxed (threshold=1)
    for remaining unplaced keywords.

    Returns list of PlacedWord for placed themed words, and the set of slot indices used.
    """
    placed = []
    used_slot_indices = set()
    used_words = set()

    # Build cell -> slot index mapping for cross-checking
    cell_to_slots = {}
    for i, slot in enumerate(slots):
        for r, c in slot.cells:
            cell_to_slots.setdefault((r, c), []).append(i)

    def _try_place_word(word, threshold):
        """Try to place a single keyword. Returns True if placed."""
        # Collect all compatible slots with scores
        candidates = []
        for i, slot in enumerate(slots):
            if i in used_slot_indices:
                continue
            if slot.length != len(word):
                continue

            pattern = slot.pattern(grid)
            compatible = True
            intersections = 0
            for j, (ch, pat_ch) in enumerate(zip(word, pattern)):
                if pat_ch != '_' and pat_ch != ch:
                    compatible = False
                    break
                if pat_ch != '_':
                    intersections += 1

            if not compatible:
                continue

            mid_r = sum(r for r, c in slot.cells) / len(slot.cells)
            mid_c = sum(c for r, c in slot.cells) / len(slot.cells)
            center_dist = abs(mid_r - 7) + abs(mid_c - 7)
            score = 100 - center_dist + intersections * 10
            candidates.append((score, i))

        # Try candidates in score order (best first)
        candidates.sort(reverse=True)
        for score, slot_idx in candidates:
            slot = slots[slot_idx]

            # Tentatively place the word
            old_letters = []
            for j, ch in enumerate(word):
                r, c = slot.cells[j]
                old_letters.append(grid[r][c].letter)
                grid[r][c].letter = ch

            # Check all crossing slots still have fill candidates
            crossing_ok = True
            for r, c in slot.cells:
                for cross_idx in cell_to_slots.get((r, c), []):
                    if cross_idx == slot_idx or cross_idx in used_slot_indices:
                        continue
                    cross_slot = slots[cross_idx]
                    cross_pattern = cross_slot.pattern(grid)
                    if '_' not in cross_pattern:
                        continue  # Already filled
                    matches = word_list.match_pattern(cross_pattern, exclude=used_words | {word})
                    if len(matches) < threshold:
                        crossing_ok = False
                        break
                if not crossing_ok:
                    break

            if crossing_ok:
                placed.append(PlacedWord(word, slot.row, slot.col, slot.direction, is_themed=True))
                used_slot_indices.add(slot_idx)
                used_words.add(word)
                return True
            else:
                # Undo placement
                for j, old_letter in enumerate(old_letters):
                    r, c = slot.cells[j]
                    grid[r][c].letter = old_letter

        return False

    # Sort keywords longest first (with shuffle for variety)
    words = sorted(keywords, key=lambda w: (-len(w), random.random()))

    # Pass 1: strict threshold (need 3+ crossing candidates)
    remaining = []
    for word in words:
        if not _try_place_word(word, threshold=3):
            remaining.append(word)

    # Pass 2: relaxed threshold (need 1+ crossing candidates) for remaining
    still_remaining = []
    for word in remaining:
        if not _try_place_word(word, threshold=1):
            still_remaining.append(word)

    return placed, used_slot_indices, used_words


# ---------------------------------------------------------------------------
# Backtracking fill
# ---------------------------------------------------------------------------

def _get_slot_crossings(slots):
    """Precompute which slots cross each other.

    Returns dict: slot_index -> list of (other_slot_index, pos_in_this, pos_in_other)
    """
    # Build cell -> (slot_index, position) map
    cell_to_slot = {}
    for i, slot in enumerate(slots):
        for j, (r, c) in enumerate(slot.cells):
            cell_to_slot.setdefault((r, c), []).append((i, j))

    crossings = {i: [] for i in range(len(slots))}
    for (r, c), entries in cell_to_slot.items():
        if len(entries) == 2:
            (i1, j1), (i2, j2) = entries
            crossings[i1].append((i2, j1, j2))
            crossings[i2].append((i1, j2, j1))

    return crossings


def _greedy_fill(grid, slots, word_list, used_words, max_words=None):
    """Fill unfilled slots greedily with crossing validation.

    Strategy:
    - Most-constrained-first: fill the slot with fewest candidates first
    - Hard-reject if ANY crossing drops to 0 candidates
    - Validate auto-completed crossings before accepting
    - Multiple passes with skipped-slot reset
    - Time-limited to avoid infinite loops

    Args:
        max_words: if set, stop filling after placing this many fill words
                   (used to cap fill words for themed word ratio targets)
    """
    crossings = _get_slot_crossings(slots)
    unfilled = set(i for i, s in enumerate(slots) if not s.is_filled(grid))
    fill_words = []
    skipped = set()
    max_passes = 6
    deadline = time.time() + 6.0

    def _score_word(word, slot_idx):
        """Score a candidate. Returns (viable, score).

        Hard-rejects if any crossing drops to 0 candidates or if a
        fully-determined crossing is not a valid word.
        """
        cross_score = 0
        for cross_idx, pos_in_this, pos_in_other in crossings.get(slot_idx, []):
            if cross_idx not in unfilled or cross_idx == slot_idx:
                continue
            cross_slot = slots[cross_idx]
            cross_pattern = list(cross_slot.pattern(grid))
            cross_pattern[pos_in_other] = word[pos_in_this]
            hyp = ''.join(cross_pattern)

            if '_' not in hyp:
                # Fully determined — must be valid and unused
                if hyp in used_words or hyp == word:
                    return False, 0
                if not word_list.match_pattern(hyp, exclude=set()):
                    return False, 0
                cross_score += 100
            else:
                n = len(word_list.match_pattern(hyp, exclude=used_words | {word}))
                if n == 0:
                    return False, 0
                cross_score += min(n, 200)
        return True, cross_score

    def _place_and_accept(slot_idx, word):
        """Place a word and accept any valid auto-completed crossings."""
        slot = slots[slot_idx]
        for j, ch in enumerate(word):
            r, c = slot.cells[j]
            grid[r][c].letter = ch
        fill_words.append(PlacedWord(
            word, slot.row, slot.col, slot.direction, is_themed=False))
        used_words.add(word)
        unfilled.discard(slot_idx)

        for cross_idx, _, _ in crossings.get(slot_idx, []):
            if cross_idx not in unfilled:
                continue
            cs = slots[cross_idx]
            if cs.is_filled(grid):
                cw = cs.pattern(grid)
                if cw not in used_words and word_list.match_pattern(cw, exclude=set()):
                    fill_words.append(PlacedWord(
                        cw, cs.row, cs.col, cs.direction, is_themed=False))
                    used_words.add(cw)
                    unfilled.discard(cross_idx)

    for pass_num in range(max_passes):
        if time.time() > deadline:
            break
        if max_words is not None and len(fill_words) >= max_words:
            break

        progress = True
        while progress and (unfilled - skipped):
            if time.time() > deadline:
                break
            if max_words is not None and len(fill_words) >= max_words:
                break
            progress = False

            slot_options = []
            for i in sorted(unfilled - skipped):
                pattern = slots[i].pattern(grid)
                matches = word_list.match_pattern(pattern, exclude=used_words)
                if not matches:
                    skipped.add(i)
                    continue
                slot_options.append((len(matches), -slots[i].length, i, matches))

            if not slot_options:
                break

            slot_options.sort()  # most constrained first

            for _, _, try_idx, try_candidates in slot_options:
                candidates = list(try_candidates)
                if len(candidates) > 60:
                    top = candidates[:10]
                    rest = candidates[10:]
                    random.shuffle(rest)
                    candidates = top + rest[:50]

                best_word = None
                best_score = -9999
                for word in candidates[:60]:
                    viable, score = _score_word(word, try_idx)
                    if viable and score > best_score:
                        best_score = score
                        best_word = word

                if best_word is None:
                    skipped.add(try_idx)
                    continue

                _place_and_accept(try_idx, best_word)
                progress = True
                break

        if pass_num < max_passes - 1:
            skipped.clear()

    # Phase 2: force-fill short unfilled slots (length <= 7).
    # Short slots have many candidates and are less likely to create
    # impossible crossing patterns.
    # Skip phase 2 if we've already hit the fill word cap.
    force_progress = True
    force_deadline = deadline + 2.0
    while force_progress and unfilled:
        if max_words is not None and len(fill_words) >= max_words:
            break
        if time.time() > force_deadline:
            break
        force_progress = False
        force_order = []
        for idx in sorted(unfilled):
            s = slots[idx]
            if s.length > 7:
                continue
            pattern = s.pattern(grid)
            matches = word_list.match_pattern(pattern, exclude=used_words)
            if matches:
                force_order.append((len(matches), -s.length, idx, matches))
        force_order.sort()

        for _, _, idx, matches in force_order:
            if idx not in unfilled:
                continue
            # Try strict first, then any
            best_word = None
            best_score = -99999
            for word in matches[:40]:
                viable, score = _score_word(word, idx)
                if viable and score > best_score:
                    best_score = score
                    best_word = word
            if best_word is None:
                best_word = matches[0]
            _place_and_accept(idx, best_word)
            force_progress = True
            break

    # Adopt valid incidental words from crossings
    for i, s in enumerate(slots):
        if i in unfilled:
            continue
        word = s.pattern(grid)
        if '_' in word or word in used_words:
            continue
        if word_list.match_pattern(word, exclude=set()):
            fill_words.append(PlacedWord(
                word, s.row, s.col, s.direction, is_themed=False))
            used_words.add(word)

    return fill_words


# ---------------------------------------------------------------------------
# Numbering
# ---------------------------------------------------------------------------

def _number_cells(grid, placed_words):
    """Assign clue numbers to cells that start words."""
    word_starts = {}
    for pw in placed_words:
        key = (pw.row, pw.col)
        word_starts.setdefault(key, []).append(pw)

    number = 1
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cell = grid[r][c]
            if cell.is_black or cell.letter is None:
                continue

            starts_across = False
            starts_down = False

            left = _get_cell(grid, r, c - 1)
            right = _get_cell(grid, r, c + 1)
            if (left is None or left.is_black or left.letter is None) and \
               (right is not None and right.letter is not None and not right.is_black):
                starts_across = True

            above = _get_cell(grid, r - 1, c)
            below = _get_cell(grid, r + 1, c)
            if (above is None or above.is_black or above.letter is None) and \
               (below is not None and below.letter is not None and not below.is_black):
                starts_down = True

            if starts_across or starts_down:
                cell.number = number
                if (r, c) in word_starts:
                    for pw in word_starts[(r, c)]:
                        pw.number = number
                number += 1


def _fix_short_runs(grid, placed):
    """Convert runs of 1-2 white cells to black to eliminate unclued fragments.

    After fill + marking empty cells black, the grid may have isolated clusters
    of 1-2 letter cells that don't belong to any clued word.  These are cosmetic
    defects.  This function makes them black and removes any placed words that
    now have cells overwritten.

    Only removes cells that are NOT part of any placed word.
    """
    placed_cells = set()
    for pw in placed:
        if pw.direction == 'across':
            for j in range(len(pw.word)):
                placed_cells.add((pw.row, pw.col + j))
        else:
            for j in range(len(pw.word)):
                placed_cells.add((pw.row + j, pw.col))

    changed = True
    while changed:
        changed = False
        # Horizontal runs
        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                if grid[r][c].is_black:
                    c += 1
                    continue
                start = c
                while c < GRID_SIZE and not grid[r][c].is_black:
                    c += 1
                run_len = c - start
                if 1 <= run_len <= 2:
                    # Check if any cell in this run is part of a placed word
                    run_cells = [(r, start + j) for j in range(run_len)]
                    if not any(rc in placed_cells for rc in run_cells):
                        for rc in run_cells:
                            grid[rc[0]][rc[1]].is_black = True
                            grid[rc[0]][rc[1]].letter = None
                        changed = True

        # Vertical runs
        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                if grid[r][c].is_black:
                    r += 1
                    continue
                start = r
                while r < GRID_SIZE and not grid[r][c].is_black:
                    r += 1
                run_len = r - start
                if 1 <= run_len <= 2:
                    run_cells = [(start + j, c) for j in range(run_len)]
                    if not any(rc in placed_cells for rc in run_cells):
                        for rc in run_cells:
                            grid[rc[0]][rc[1]].is_black = True
                            grid[rc[0]][rc[1]].letter = None
                        changed = True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_crossword(keywords, max_retries=10):
    """Generate a 15x15 crossword puzzle from a list of keywords.

    Pipeline:
      1. Apply black cell pattern (rotationally symmetric)
         — tries dense patterns first (~55-65 blacks, ~30-35 slots) for
           higher themed ratio, then sparser patterns as fallback
      2. Break up long slots to create varied lengths matching keywords
      3. Extract slots from the pattern
      4. Place themed keywords into matching slots (aggressive: 2-pass placement)
      5. Fill ALL remaining slots (no cap) — dense patterns naturally yield
         30-40% themed ratio because they have fewer total slots
      6. Number cells

    Tries multiple patterns and random orderings, keeping the best result.
    Scoring targets 30-40% themed ratio with <40% black cells.

    Args:
        keywords: list of uppercase keyword strings
        max_retries: number of attempts with different patterns/orderings

    Returns:
        tuple of (grid, placed_words) where placed_words includes themed + fill
    """
    word_list = WordList()

    best_grid = None
    best_placed = []
    best_score = -float('inf')

    # Determine the longest keyword length so we can break slots appropriately
    max_kw_len = max((len(k) for k in keywords), default=8)

    for attempt in range(max_retries):
        grid = _make_grid()

        # Step 1: Apply pattern — try dense patterns first for better ratio
        order_idx = attempt % len(_PATTERN_ORDER)
        pattern_idx = _PATTERN_ORDER[order_idx]
        _apply_pattern(grid, _ALL_PATTERNS[pattern_idx])

        # Step 1b: Break up long slots to create varied slot lengths.
        # Dense patterns (≥50 blacks) already have shorter runs — use a higher
        # threshold to avoid over-fragmenting and creating too many slots.
        pattern_blacks = sum(
            1 for r in range(GRID_SIZE) for c in range(GRID_SIZE)
            if grid[r][c].is_black
        )
        if pattern_blacks >= 50:
            _fix_long_slots(grid, max_slot_length=max(max_kw_len, 12))
        else:
            _fix_long_slots(grid, max_slot_length=max_kw_len)

        # Step 2: Extract slots
        slots = _extract_slots(grid)

        # Step 3: Place themed words into slots (shuffle for variety)
        kw_shuffled = list(keywords)
        if attempt > 0:
            random.shuffle(kw_shuffled)
        themed_placed, used_slot_indices, used_words = _place_themed_into_slots(grid, slots, kw_shuffled, word_list)

        # Step 4: Adaptive fill cap — balance themed ratio vs black cells.
        # Fill enough to keep blacks under MAX_BLACK_CELLS, but cap for ratio.
        themed_count = len(themed_placed)
        empty_white = sum(
            1 for r in range(GRID_SIZE) for c in range(GRID_SIZE)
            if not grid[r][c].is_black and grid[r][c].letter is None
        )
        cur_blacks = sum(
            1 for r in range(GRID_SIZE) for c in range(GRID_SIZE)
            if grid[r][c].is_black
        )
        # Empirical: each fill word eliminates ~2.5 potential black cells
        allowable_new_blacks = MAX_BLACK_CELLS - cur_blacks
        min_fill_for_blacks = max(0, int((empty_white - allowable_new_blacks) / 2.5))
        # Floor: at least enough fill to control blacks. Ceiling: themed * 2.5 for ratio.
        max_fill = max(min_fill_for_blacks, int(themed_count * 1.5))
        max_fill = min(max_fill, int(themed_count * 2.5))

        fill_placed = _greedy_fill(grid, slots, word_list, used_words, max_words=max_fill)

        all_placed = themed_placed + fill_placed

        # Count unfilled white cells
        unfilled = sum(
            1 for r in range(GRID_SIZE) for c in range(GRID_SIZE)
            if not grid[r][c].is_black and grid[r][c].letter is None
        )

        black_count = sum(
            1 for r in range(GRID_SIZE) for c in range(GRID_SIZE)
            if grid[r][c].is_black
        )
        # After post-fill, unfilled white cells become black
        projected_blacks = black_count + unfilled

        # Score: balance themed count, ratio, and black cell limit
        total_words = len(all_placed)
        themed_ratio = themed_count / max(total_words, 1)

        # Bonus for ratio in sweet spot (30-40%)
        ratio_bonus = 0
        if 0.28 <= themed_ratio <= 0.45:
            ratio_bonus = 200  # in target range
        elif themed_ratio > 0.45:
            ratio_bonus = 100  # above target, still good

        score = (
            themed_count * 100          # Important: number of themed words
            + ratio_bonus               # Bonus for 30-40% ratio
            + themed_ratio * 200        # Themed ratio bonus
            - unfilled * 10             # Penalise unfilled cells
            + total_words * 2           # Small bonus for more total words
            - max(0, projected_blacks - MAX_BLACK_CELLS) * 80  # Heavy penalty for >40% blacks
        )

        if score > best_score:
            best_score = score
            best_grid = grid
            best_placed = all_placed

        if 0.28 <= themed_ratio <= 0.45 and projected_blacks <= MAX_BLACK_CELLS and unfilled <= 5:
            break

    if best_grid is None:
        best_grid = _make_grid()

    grid = best_grid
    placed = best_placed

    # Post-fill: mark remaining empty cells as black
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if not grid[r][c].is_black and grid[r][c].letter is None:
                grid[r][c].is_black = True

    # Fix short runs: any run of 1-2 white cells becomes all black.
    # This eliminates unclued single/double letter fragments.
    _fix_short_runs(grid, placed)

    _number_cells(grid, placed)

    return grid, placed


def grid_to_json(grid, placed_words, clues=None):
    """Convert grid and placed words to JSON-serializable format."""
    grid_data = []
    for r in range(GRID_SIZE):
        row_data = []
        for c in range(GRID_SIZE):
            cell = grid[r][c]
            cell_data = {'black': cell.is_black}
            if not cell.is_black:
                cell_data['letter'] = cell.letter or ''
                if cell.number is not None:
                    cell_data['number'] = cell.number
            row_data.append(cell_data)
        grid_data.append(row_data)

    across_words = []
    down_words = []

    for pw in sorted(placed_words, key=lambda pw: pw.number):
        word_data = {
            'number': pw.number,
            'answer': pw.word,
            'row': pw.row,
            'col': pw.col,
            'length': len(pw.word),
            'isThemed': pw.is_themed,
        }
        if clues and pw.word in clues:
            word_data['clue'] = clues[pw.word]
        else:
            word_data['clue'] = f'Clue for {pw.word}'

        if pw.direction == 'across':
            across_words.append(word_data)
        else:
            down_words.append(word_data)

    return {
        'grid': grid_data,
        'words': {
            'across': across_words,
            'down': down_words,
        },
        'size': GRID_SIZE,
    }
