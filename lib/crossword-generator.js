/**
 * Crossword grid generator.
 *
 * Faithful port of crossword_generator.py — same algorithm, data, and logic.
 */

import { WordList } from './word-list.js';

const GRID_SIZE = 15;
const MAX_BLACK_CELLS = Math.floor(GRID_SIZE * GRID_SIZE * 0.40); // 40% = 90

// ---------------------------------------------------------------------------
// Data classes (plain objects)
// ---------------------------------------------------------------------------

function makeCell(isBlack = false, letter = null, number = null) {
  return { isBlack, letter, number };
}

function makePlacedWord(word, row, col, direction, number = 0, isThemed = false) {
  return { word, row, col, direction, number, isThemed };
}

function makeSlot(row, col, direction, length, cells) {
  return { row, col, direction, length, cells };
}

function slotPattern(slot, grid) {
  return slot.cells.map(([r, c]) => grid[r][c].letter || '_').join('');
}

function slotIsFilled(slot, grid) {
  return slot.cells.every(([r, c]) => grid[r][c].letter !== null);
}

// ---------------------------------------------------------------------------
// Fisher-Yates shuffle (replaces Python random.shuffle)
// ---------------------------------------------------------------------------

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

// ---------------------------------------------------------------------------
// Black cell patterns defined as string grids (X=black, .=white)
// All have rotational symmetry and ~36-38 black cells
// ---------------------------------------------------------------------------

const PATTERN_STRINGS = [
  // Pattern A: "staircase" — 34 blacks, 70 words, max_run=12
  [
    '...##.....#....',
    '...#...........',
    '...#...........',
    '.......#...#...',
    '............###',
    '#........##....',
    '...#....##.....',
    '.....#...#.....',
    '.....##....#...',
    '....##........#',
    '###............',
    '...#...#.......',
    '...........#...',
    '...........#...',
    '....#.....##...',
  ],
  // Pattern B: "crossover" — 34 blacks, 74 words, max_run=15
  [
    '.......#...#...',
    '.......#...#...',
    '.......#.......',
    '...##..........',
    '...#....##.....',
    '.....##....#...',
    '##....#........',
    '....#.....#....',
    '........#....##',
    '...#....##.....',
    '.....##....#...',
    '..........##...',
    '.......#.......',
    '...#...#.......',
    '...#...#.......',
  ],
  // Pattern C: "diamond" — 35 blacks, 62 words, max_run=12
  [
    '.....##.......#',
    '......#.......#',
    '......#.......#',
    '............###',
    '...##.........#',
    '.....#...##....',
    '...........#...',
    '.......#.......',
    '...#...........',
    '....##...#.....',
    '#.........##...',
    '###............',
    '#.......#......',
    '#.......#......',
    '#.......##.....',
  ],
  // Pattern D: "dense staircase" — ~58 blacks, ~34 words
  [
    '##.....#..##...',
    '#......#.......',
    '......##.......',
    '...##....##....',
    '..#......#..##.',
    '.....##........',
    '##.......#.....',
    '...#.......#...',
    '.....#.......##',
    '........##.....',
    '.##..#......#..',
    '....##....##...',
    '.......##......',
    '.......#......#',
    '...##..#.....##',
  ],
  // Pattern E: "dense pinwheel" — ~60 blacks, ~32 words
  [
    '###....#.......',
    '#.....##.......',
    '......#...#....',
    '..##.....##....',
    '..#.......#..##',
    '........##.....',
    '#...#..........',
    '...#.......#...',
    '..........#...#',
    '.....##........',
    '##..#.......#..',
    '....##.....##..',
    '....#...#......',
    '.......##.....#',
    '.......#....###',
  ],
  // Pattern F: "dense blocks" — ~62 blacks, ~30 words
  [
    '##.....##..##..',
    '#......#.......',
    '......##.......',
    '...##....#.....',
    '..##......#..##',
    '.......##......',
    '##..#..........',
    '...#.......#...',
    '..........#..##',
    '......##.......',
    '##..#......##..',
    '.....#....##...',
    '.......##......',
    '.......#......#',
    '..##..##.....##',
  ],
];

// Preferred order: dense patterns first (D, E, F), then sparse (A, B, C)
const PATTERN_ORDER = [3, 4, 5, 0, 1, 2];

function parsePattern(patternRows) {
  const blackCells = new Set();
  for (let r = 0; r < patternRows.length; r++) {
    for (let c = 0; c < patternRows[r].length; c++) {
      if (patternRows[r][c] === 'X' || patternRows[r][c] === '#') {
        blackCells.add(`${r},${c}`);
      }
    }
  }
  return blackCells;
}

function validatePatternSymmetry(blackCells) {
  const result = new Set();
  for (const key of blackCells) {
    const [r, c] = key.split(',').map(Number);
    result.add(`${r},${c}`);
    result.add(`${14 - r},${14 - c}`);
  }
  return result;
}

const ALL_PATTERNS = PATTERN_STRINGS.map((ps) => {
  const cells = parsePattern(ps);
  return validatePatternSymmetry(cells);
});

// ---------------------------------------------------------------------------
// Grid helpers
// ---------------------------------------------------------------------------

function makeGrid() {
  return Array.from({ length: GRID_SIZE }, () =>
    Array.from({ length: GRID_SIZE }, () => makeCell())
  );
}

function getCell(grid, r, c) {
  if (r >= 0 && r < GRID_SIZE && c >= 0 && c < GRID_SIZE) {
    return grid[r][c];
  }
  return null;
}

function applyPattern(grid, blackCells) {
  for (const key of blackCells) {
    const [r, c] = key.split(',').map(Number);
    grid[r][c].isBlack = true;
  }
}

function fixLongSlots(grid, maxSlotLength = 8) {
  let changed = true;
  let iterations = 0;
  while (changed && iterations < 50) {
    changed = false;
    iterations++;

    // Horizontal runs
    let broke = false;
    for (let r = 0; r < GRID_SIZE && !broke; r++) {
      let c = 0;
      while (c < GRID_SIZE) {
        if (grid[r][c].isBlack) { c++; continue; }
        const start = c;
        while (c < GRID_SIZE && !grid[r][c].isBlack) c++;
        const runLen = c - start;
        if (runLen > maxSlotLength) {
          const mid = start + Math.floor(runLen / 2);
          grid[r][mid].isBlack = true;
          grid[14 - r][14 - mid].isBlack = true;
          changed = true;
          broke = true;
          break;
        }
      }
    }

    if (changed) continue;

    // Vertical runs
    for (let c = 0; c < GRID_SIZE && !broke; c++) {
      let r = 0;
      while (r < GRID_SIZE) {
        if (grid[r][c].isBlack) { r++; continue; }
        const start = r;
        while (r < GRID_SIZE && !grid[r][c].isBlack) r++;
        const runLen = r - start;
        if (runLen > maxSlotLength) {
          const mid = start + Math.floor(runLen / 2);
          grid[mid][c].isBlack = true;
          grid[14 - mid][14 - c].isBlack = true;
          changed = true;
          broke = true;
          break;
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Slot extraction
// ---------------------------------------------------------------------------

function extractSlots(grid) {
  const slots = [];

  // Horizontal (across)
  for (let r = 0; r < GRID_SIZE; r++) {
    let c = 0;
    while (c < GRID_SIZE) {
      if (grid[r][c].isBlack) { c++; continue; }
      const start = c;
      const cells = [];
      while (c < GRID_SIZE && !grid[r][c].isBlack) {
        cells.push([r, c]);
        c++;
      }
      if (cells.length >= 3) {
        slots.push(makeSlot(r, start, 'across', cells.length, cells));
      }
    }
  }

  // Vertical (down)
  for (let c = 0; c < GRID_SIZE; c++) {
    let r = 0;
    while (r < GRID_SIZE) {
      if (grid[r][c].isBlack) { r++; continue; }
      const start = r;
      const cells = [];
      while (r < GRID_SIZE && !grid[r][c].isBlack) {
        cells.push([r, c]);
        r++;
      }
      if (cells.length >= 3) {
        slots.push(makeSlot(start, c, 'down', cells.length, cells));
      }
    }
  }

  return slots;
}

// ---------------------------------------------------------------------------
// Themed word placement into slots
// ---------------------------------------------------------------------------

function placeThemedIntoSlots(grid, slots, keywords, wordList) {
  const placed = [];
  const usedSlotIndices = new Set();
  const usedWords = new Set();

  // Build cell -> slot index mapping
  const cellToSlots = new Map();
  for (let i = 0; i < slots.length; i++) {
    for (const [r, c] of slots[i].cells) {
      const key = `${r},${c}`;
      if (!cellToSlots.has(key)) cellToSlots.set(key, []);
      cellToSlots.get(key).push(i);
    }
  }

  function tryPlaceWord(word, threshold) {
    const candidates = [];
    for (let i = 0; i < slots.length; i++) {
      if (usedSlotIndices.has(i)) continue;
      const slot = slots[i];
      if (slot.length !== word.length) continue;

      const pattern = slotPattern(slot, grid);
      let compatible = true;
      let intersections = 0;
      for (let j = 0; j < word.length; j++) {
        if (pattern[j] !== '_' && pattern[j] !== word[j]) {
          compatible = false;
          break;
        }
        if (pattern[j] !== '_') intersections++;
      }
      if (!compatible) continue;

      const midR = slot.cells.reduce((s, [r]) => s + r, 0) / slot.cells.length;
      const midC = slot.cells.reduce((s, [, c]) => s + c, 0) / slot.cells.length;
      const centerDist = Math.abs(midR - 7) + Math.abs(midC - 7);
      const score = 100 - centerDist + intersections * 10;
      candidates.push([score, i]);
    }

    candidates.sort((a, b) => b[0] - a[0]); // best first

    for (const [, slotIdx] of candidates) {
      const slot = slots[slotIdx];

      // Tentatively place
      const oldLetters = [];
      for (let j = 0; j < word.length; j++) {
        const [r, c] = slot.cells[j];
        oldLetters.push(grid[r][c].letter);
        grid[r][c].letter = word[j];
      }

      // Check crossing slots
      let crossingOk = true;
      for (const [r, c] of slot.cells) {
        const key = `${r},${c}`;
        for (const crossIdx of (cellToSlots.get(key) || [])) {
          if (crossIdx === slotIdx || usedSlotIndices.has(crossIdx)) continue;
          const crossSlot = slots[crossIdx];
          const crossPattern = slotPattern(crossSlot, grid);
          if (!crossPattern.includes('_')) continue; // already filled
          const excludeSet = new Set([...usedWords, word]);
          const matches = wordList.matchPattern(crossPattern, excludeSet);
          if (matches.length < threshold) {
            crossingOk = false;
            break;
          }
        }
        if (!crossingOk) break;
      }

      if (crossingOk) {
        placed.push(makePlacedWord(word, slot.row, slot.col, slot.direction, 0, true));
        usedSlotIndices.add(slotIdx);
        usedWords.add(word);
        return true;
      } else {
        // Undo
        for (let j = 0; j < oldLetters.length; j++) {
          const [r, c] = slot.cells[j];
          grid[r][c].letter = oldLetters[j];
        }
      }
    }
    return false;
  }

  // Sort longest first with shuffle for variety
  const words = [...keywords].sort((a, b) => {
    if (b.length !== a.length) return b.length - a.length;
    return Math.random() - 0.5;
  });

  // Pass 1: strict threshold (need 3+ crossing candidates)
  const remaining = [];
  for (const word of words) {
    if (!tryPlaceWord(word, 3)) remaining.push(word);
  }

  // Pass 2: relaxed threshold (need 1+ crossing candidates)
  for (const word of remaining) {
    tryPlaceWord(word, 1);
  }

  return { placed, usedSlotIndices, usedWords };
}

// ---------------------------------------------------------------------------
// Backtracking fill
// ---------------------------------------------------------------------------

function getSlotCrossings(slots) {
  const cellToSlot = new Map();
  for (let i = 0; i < slots.length; i++) {
    for (let j = 0; j < slots[i].cells.length; j++) {
      const [r, c] = slots[i].cells[j];
      const key = `${r},${c}`;
      if (!cellToSlot.has(key)) cellToSlot.set(key, []);
      cellToSlot.get(key).push([i, j]);
    }
  }

  const crossings = {};
  for (let i = 0; i < slots.length; i++) crossings[i] = [];

  for (const entries of cellToSlot.values()) {
    if (entries.length === 2) {
      const [[i1, j1], [i2, j2]] = entries;
      crossings[i1].push([i2, j1, j2]);
      crossings[i2].push([i1, j2, j1]);
    }
  }

  return crossings;
}

function greedyFill(grid, slots, wordList, usedWords, maxWords = null) {
  const crossings = getSlotCrossings(slots);
  const unfilled = new Set();
  for (let i = 0; i < slots.length; i++) {
    if (!slotIsFilled(slots[i], grid)) unfilled.add(i);
  }
  const fillWords = [];
  const skipped = new Set();
  const maxPasses = 6;
  const deadline = Date.now() + 6000; // 6 seconds

  function scoreWord(word, slotIdx) {
    let crossScore = 0;
    for (const [crossIdx, posInThis, posInOther] of (crossings[slotIdx] || [])) {
      if (!unfilled.has(crossIdx) || crossIdx === slotIdx) continue;
      const crossSlot = slots[crossIdx];
      const crossPatternArr = slotPattern(crossSlot, grid).split('');
      crossPatternArr[posInOther] = word[posInThis];
      const hyp = crossPatternArr.join('');

      if (!hyp.includes('_')) {
        // Fully determined
        if (usedWords.has(hyp) || hyp === word) return [false, 0];
        if (wordList.matchPattern(hyp, new Set()).length === 0) return [false, 0];
        crossScore += 100;
      } else {
        const excludeSet = new Set([...usedWords, word]);
        const n = wordList.matchPattern(hyp, excludeSet).length;
        if (n === 0) return [false, 0];
        crossScore += Math.min(n, 200);
      }
    }
    return [true, crossScore];
  }

  function placeAndAccept(slotIdx, word) {
    const slot = slots[slotIdx];
    for (let j = 0; j < word.length; j++) {
      const [r, c] = slot.cells[j];
      grid[r][c].letter = word[j];
    }
    fillWords.push(makePlacedWord(word, slot.row, slot.col, slot.direction, 0, false));
    usedWords.add(word);
    unfilled.delete(slotIdx);

    // Accept auto-completed crossings
    for (const [crossIdx] of (crossings[slotIdx] || [])) {
      if (!unfilled.has(crossIdx)) continue;
      const cs = slots[crossIdx];
      if (slotIsFilled(cs, grid)) {
        const cw = slotPattern(cs, grid);
        if (!usedWords.has(cw) && wordList.matchPattern(cw, new Set()).length > 0) {
          fillWords.push(makePlacedWord(cw, cs.row, cs.col, cs.direction, 0, false));
          usedWords.add(cw);
          unfilled.delete(crossIdx);
        }
      }
    }
  }

  for (let passNum = 0; passNum < maxPasses; passNum++) {
    if (Date.now() > deadline) break;
    if (maxWords !== null && fillWords.length >= maxWords) break;

    let progress = true;
    while (progress) {
      if (Date.now() > deadline) break;
      if (maxWords !== null && fillWords.length >= maxWords) break;
      progress = false;

      // Find unfilled slots not skipped
      const candidates = [];
      for (const i of unfilled) {
        if (skipped.has(i)) continue;
        const pattern = slotPattern(slots[i], grid);
        const matches = wordList.matchPattern(pattern, usedWords);
        if (matches.length === 0) {
          skipped.add(i);
          continue;
        }
        candidates.push([matches.length, -slots[i].length, i, matches]);
      }

      if (candidates.length === 0) break;

      // Most constrained first
      candidates.sort((a, b) => a[0] - b[0] || a[1] - b[1]);

      for (const [, , tryIdx, tryCandidates] of candidates) {
        let candidateList = [...tryCandidates];
        if (candidateList.length > 60) {
          const top = candidateList.slice(0, 10);
          const rest = candidateList.slice(10);
          shuffle(rest);
          candidateList = [...top, ...rest.slice(0, 50)];
        }

        let bestWord = null;
        let bestScore = -9999;
        for (const word of candidateList.slice(0, 60)) {
          const [viable, score] = scoreWord(word, tryIdx);
          if (viable && score > bestScore) {
            bestScore = score;
            bestWord = word;
          }
        }

        if (bestWord === null) {
          skipped.add(tryIdx);
          continue;
        }

        placeAndAccept(tryIdx, bestWord);
        progress = true;
        break;
      }
    }

    if (passNum < maxPasses - 1) {
      skipped.clear();
    }
  }

  // Phase 2: force-fill short unfilled slots (length <= 7)
  let forceProgress = true;
  const forceDeadline = deadline + 2000;
  while (forceProgress && unfilled.size > 0) {
    if (maxWords !== null && fillWords.length >= maxWords) break;
    if (Date.now() > forceDeadline) break;
    forceProgress = false;

    const forceOrder = [];
    for (const idx of unfilled) {
      const s = slots[idx];
      if (s.length > 7) continue;
      const pattern = slotPattern(s, grid);
      const matches = wordList.matchPattern(pattern, usedWords);
      if (matches.length > 0) {
        forceOrder.push([matches.length, -s.length, idx, matches]);
      }
    }
    forceOrder.sort((a, b) => a[0] - b[0] || a[1] - b[1]);

    for (const [, , idx, matches] of forceOrder) {
      if (!unfilled.has(idx)) continue;
      let bestWord = null;
      let bestScore = -99999;
      for (const word of matches.slice(0, 40)) {
        const [viable, score] = scoreWord(word, idx);
        if (viable && score > bestScore) {
          bestScore = score;
          bestWord = word;
        }
      }
      if (bestWord === null) bestWord = matches[0];
      placeAndAccept(idx, bestWord);
      forceProgress = true;
      break;
    }
  }

  // Adopt valid incidental words from crossings
  for (let i = 0; i < slots.length; i++) {
    if (unfilled.has(i)) continue;
    const word = slotPattern(slots[i], grid);
    if (word.includes('_') || usedWords.has(word)) continue;
    if (wordList.matchPattern(word, new Set()).length > 0) {
      fillWords.push(makePlacedWord(word, slots[i].row, slots[i].col, slots[i].direction, 0, false));
      usedWords.add(word);
    }
  }

  return fillWords;
}

// ---------------------------------------------------------------------------
// Numbering
// ---------------------------------------------------------------------------

function numberCells(grid, placedWords) {
  const wordStarts = new Map();
  for (const pw of placedWords) {
    const key = `${pw.row},${pw.col}`;
    if (!wordStarts.has(key)) wordStarts.set(key, []);
    wordStarts.get(key).push(pw);
  }

  let number = 1;
  for (let r = 0; r < GRID_SIZE; r++) {
    for (let c = 0; c < GRID_SIZE; c++) {
      const cell = grid[r][c];
      if (cell.isBlack || cell.letter === null) continue;

      let startsAcross = false;
      let startsDown = false;

      const left = getCell(grid, r, c - 1);
      const right = getCell(grid, r, c + 1);
      if ((left === null || left.isBlack || left.letter === null) &&
          (right !== null && right.letter !== null && !right.isBlack)) {
        startsAcross = true;
      }

      const above = getCell(grid, r - 1, c);
      const below = getCell(grid, r + 1, c);
      if ((above === null || above.isBlack || above.letter === null) &&
          (below !== null && below.letter !== null && !below.isBlack)) {
        startsDown = true;
      }

      if (startsAcross || startsDown) {
        cell.number = number;
        const key = `${r},${c}`;
        if (wordStarts.has(key)) {
          for (const pw of wordStarts.get(key)) {
            pw.number = number;
          }
        }
        number++;
      }
    }
  }
}

function fixShortRuns(grid, placed) {
  const placedCells = new Set();
  for (const pw of placed) {
    if (pw.direction === 'across') {
      for (let j = 0; j < pw.word.length; j++) placedCells.add(`${pw.row},${pw.col + j}`);
    } else {
      for (let j = 0; j < pw.word.length; j++) placedCells.add(`${pw.row + j},${pw.col}`);
    }
  }

  let changed = true;
  while (changed) {
    changed = false;

    // Horizontal runs
    for (let r = 0; r < GRID_SIZE; r++) {
      let c = 0;
      while (c < GRID_SIZE) {
        if (grid[r][c].isBlack) { c++; continue; }
        const start = c;
        while (c < GRID_SIZE && !grid[r][c].isBlack) c++;
        const runLen = c - start;
        if (runLen >= 1 && runLen <= 2) {
          const runCells = [];
          for (let j = 0; j < runLen; j++) runCells.push(`${r},${start + j}`);
          if (!runCells.some((rc) => placedCells.has(rc))) {
            for (const rc of runCells) {
              const [rr, cc] = rc.split(',').map(Number);
              grid[rr][cc].isBlack = true;
              grid[rr][cc].letter = null;
            }
            changed = true;
          }
        }
      }
    }

    // Vertical runs
    for (let c = 0; c < GRID_SIZE; c++) {
      let r = 0;
      while (r < GRID_SIZE) {
        if (grid[r][c].isBlack) { r++; continue; }
        const start = r;
        while (r < GRID_SIZE && !grid[r][c].isBlack) r++;
        const runLen = r - start;
        if (runLen >= 1 && runLen <= 2) {
          const runCells = [];
          for (let j = 0; j < runLen; j++) runCells.push(`${start + j},${c}`);
          if (!runCells.some((rc) => placedCells.has(rc))) {
            for (const rc of runCells) {
              const [rr, cc] = rc.split(',').map(Number);
              grid[rr][cc].isBlack = true;
              grid[rr][cc].letter = null;
            }
            changed = true;
          }
        }
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Main entry point
// ---------------------------------------------------------------------------

function generateCrossword(keywords, maxRetries = 10) {
  const wordList = new WordList();

  let bestGrid = null;
  let bestPlaced = [];
  let bestScore = -Infinity;

  const maxKwLen = keywords.reduce((max, k) => Math.max(max, k.length), 8);

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const grid = makeGrid();

    // Step 1: Apply pattern
    const orderIdx = attempt % PATTERN_ORDER.length;
    const patternIdx = PATTERN_ORDER[orderIdx];
    applyPattern(grid, ALL_PATTERNS[patternIdx]);

    // Step 1b: Break up long slots
    let patternBlacks = 0;
    for (let r = 0; r < GRID_SIZE; r++) {
      for (let c = 0; c < GRID_SIZE; c++) {
        if (grid[r][c].isBlack) patternBlacks++;
      }
    }
    if (patternBlacks >= 50) {
      fixLongSlots(grid, Math.max(maxKwLen, 12));
    } else {
      fixLongSlots(grid, maxKwLen);
    }

    // Step 2: Extract slots
    const slots = extractSlots(grid);

    // Step 3: Place themed words
    const kwShuffled = [...keywords];
    if (attempt > 0) shuffle(kwShuffled);
    const { placed: themedPlaced, usedSlotIndices, usedWords } =
      placeThemedIntoSlots(grid, slots, kwShuffled, wordList);

    // Step 4: Adaptive fill cap
    const themedCount = themedPlaced.length;
    let emptyWhite = 0;
    let curBlacks = 0;
    for (let r = 0; r < GRID_SIZE; r++) {
      for (let c = 0; c < GRID_SIZE; c++) {
        if (grid[r][c].isBlack) curBlacks++;
        else if (grid[r][c].letter === null) emptyWhite++;
      }
    }
    const allowableNewBlacks = MAX_BLACK_CELLS - curBlacks;
    const minFillForBlacks = Math.max(0, Math.floor((emptyWhite - allowableNewBlacks) / 2.5));
    let maxFill = Math.max(minFillForBlacks, Math.floor(themedCount * 1.5));
    maxFill = Math.min(maxFill, Math.floor(themedCount * 2.5));

    const fillPlaced = greedyFill(grid, slots, wordList, usedWords, maxFill);
    const allPlaced = [...themedPlaced, ...fillPlaced];

    // Count unfilled and black
    let unfilled = 0;
    let blackCount = 0;
    for (let r = 0; r < GRID_SIZE; r++) {
      for (let c = 0; c < GRID_SIZE; c++) {
        if (grid[r][c].isBlack) blackCount++;
        else if (grid[r][c].letter === null) unfilled++;
      }
    }
    const projectedBlacks = blackCount + unfilled;

    // Score
    const totalWords = allPlaced.length;
    const themedRatio = themedCount / Math.max(totalWords, 1);

    let ratioBonus = 0;
    if (themedRatio >= 0.28 && themedRatio <= 0.45) ratioBonus = 200;
    else if (themedRatio > 0.45) ratioBonus = 100;

    const score =
      themedCount * 100 +
      ratioBonus +
      themedRatio * 200 +
      -unfilled * 10 +
      totalWords * 2 +
      -Math.max(0, projectedBlacks - MAX_BLACK_CELLS) * 80;

    if (score > bestScore) {
      bestScore = score;
      bestGrid = grid;
      bestPlaced = allPlaced;
    }

    if (themedRatio >= 0.28 && themedRatio <= 0.45 &&
        projectedBlacks <= MAX_BLACK_CELLS && unfilled <= 5) {
      break;
    }
  }

  if (bestGrid === null) bestGrid = makeGrid();

  const grid = bestGrid;
  const placed = bestPlaced;

  // Post-fill: mark remaining empty cells as black
  for (let r = 0; r < GRID_SIZE; r++) {
    for (let c = 0; c < GRID_SIZE; c++) {
      if (!grid[r][c].isBlack && grid[r][c].letter === null) {
        grid[r][c].isBlack = true;
      }
    }
  }

  // Fix short runs
  fixShortRuns(grid, placed);

  // Number cells
  numberCells(grid, placed);

  return [grid, placed];
}

// ---------------------------------------------------------------------------
// JSON export
// ---------------------------------------------------------------------------

function gridToJson(grid, placedWords, clues = null) {
  const gridData = [];
  for (let r = 0; r < GRID_SIZE; r++) {
    const rowData = [];
    for (let c = 0; c < GRID_SIZE; c++) {
      const cell = grid[r][c];
      const cellData = { black: cell.isBlack };
      if (!cell.isBlack) {
        cellData.letter = cell.letter || '';
        if (cell.number !== null) cellData.number = cell.number;
      }
      rowData.push(cellData);
    }
    gridData.push(rowData);
  }

  const acrossWords = [];
  const downWords = [];

  const sorted = [...placedWords].sort((a, b) => a.number - b.number);
  for (const pw of sorted) {
    const wordData = {
      number: pw.number,
      answer: pw.word,
      row: pw.row,
      col: pw.col,
      length: pw.word.length,
      isThemed: pw.isThemed,
    };
    if (clues && clues[pw.word]) {
      wordData.clue = clues[pw.word];
    } else {
      wordData.clue = `Clue for ${pw.word}`;
    }

    if (pw.direction === 'across') acrossWords.push(wordData);
    else downWords.push(wordData);
  }

  return {
    grid: gridData,
    words: { across: acrossWords, down: downWords },
    size: GRID_SIZE,
  };
}

export { generateCrossword, gridToJson };
