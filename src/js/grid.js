/**
 * Crossword grid rendering and interaction module.
 */
export class CrosswordGrid {
    constructor(containerEl, cluesContainerAcross, cluesContainerDown, activeClueBar) {
        this.container = containerEl;
        this.cluesAcross = cluesContainerAcross;
        this.cluesDown = cluesContainerDown;
        this.activeClueBar = activeClueBar;

        this.gridData = null;
        this.words = null;
        this.size = 15;

        // User state
        this.userLetters = [];
        this.selectedRow = -1;
        this.selectedCol = -1;
        this.currentDirection = 'across';
        this.revealedCells = new Set();

        // DOM references
        this.cells = [];

        this._onCellClick = this._onCellClick.bind(this);
        this._onKeyDown = this._onKeyDown.bind(this);
    }

    /**
     * Initialize the grid with puzzle data from the API.
     */
    init(puzzleData) {
        this.gridData = puzzleData.grid;
        this.words = puzzleData.words;
        this.size = puzzleData.size || 15;

        // Initialize user letters
        this.userLetters = Array.from({ length: this.size }, () =>
            Array.from({ length: this.size }, () => '')
        );

        this.selectedRow = -1;
        this.selectedCol = -1;
        this.currentDirection = 'across';
        this.revealedCells = new Set();

        this._buildGrid();
        this._buildClues();
        this._attachEvents();

        // Select the first across word's starting cell
        if (this.words.across.length > 0) {
            const first = this.words.across[0];
            this.selectedRow = first.row;
            this.selectedCol = first.col;
            this.currentDirection = 'across';
            this._updateDisplay();
        }
    }

    // ===== Build DOM =====

    _buildGrid() {
        this.container.innerHTML = '';
        this.container.style.gridTemplateColumns = `repeat(${this.size}, 36px)`;
        this.container.style.gridTemplateRows = `repeat(${this.size}, 36px)`;
        this.cells = [];

        for (let r = 0; r < this.size; r++) {
            const row = [];
            for (let c = 0; c < this.size; c++) {
                const cellData = this.gridData[r][c];
                const div = document.createElement('div');
                div.className = 'cell' + (cellData.black ? ' black' : '');
                div.dataset.row = r;
                div.dataset.col = c;

                if (!cellData.black) {
                    if (cellData.number) {
                        const numSpan = document.createElement('span');
                        numSpan.className = 'cell-number';
                        numSpan.textContent = cellData.number;
                        div.appendChild(numSpan);
                    }
                    const letterSpan = document.createElement('span');
                    letterSpan.className = 'cell-letter';
                    letterSpan.textContent = '';
                    div.appendChild(letterSpan);
                }

                this.container.appendChild(div);
                row.push(div);
            }
            this.cells.push(row);
        }
    }

    _buildClues() {
        this.cluesAcross.innerHTML = '';
        this.cluesDown.innerHTML = '';

        for (const word of this.words.across) {
            this.cluesAcross.appendChild(this._createClueItem(word, 'across'));
        }
        for (const word of this.words.down) {
            this.cluesDown.appendChild(this._createClueItem(word, 'down'));
        }
    }

    _createClueItem(word, direction) {
        const li = document.createElement('li');
        li.className = 'clue-item';
        li.dataset.number = word.number;
        li.dataset.direction = direction;

        const numSpan = document.createElement('span');
        numSpan.className = 'clue-number';
        numSpan.textContent = word.number;

        const textSpan = document.createElement('span');
        textSpan.className = 'clue-text';
        textSpan.textContent = word.clue;

        li.appendChild(numSpan);
        li.appendChild(textSpan);

        li.addEventListener('click', () => {
            this.selectedRow = word.row;
            this.selectedCol = word.col;
            this.currentDirection = direction;
            this._updateDisplay();
            this.container.focus();
        });

        return li;
    }

    // ===== Events =====

    _attachEvents() {
        this.container.addEventListener('click', this._onCellClick);
        this.container.addEventListener('keydown', this._onKeyDown);
    }

    _onCellClick(e) {
        const cell = e.target.closest('.cell');
        if (!cell || cell.classList.contains('black')) return;

        const r = parseInt(cell.dataset.row);
        const c = parseInt(cell.dataset.col);

        if (r === this.selectedRow && c === this.selectedCol) {
            // Toggle direction
            this.currentDirection = this.currentDirection === 'across' ? 'down' : 'across';
        } else {
            this.selectedRow = r;
            this.selectedCol = c;
        }

        this._updateDisplay();
        this.container.focus();
    }

    _onKeyDown(e) {
        if (this.selectedRow < 0) return;

        const key = e.key;

        if (key >= 'a' && key <= 'z' || key >= 'A' && key <= 'Z') {
            e.preventDefault();
            this._enterLetter(key.toUpperCase());
        } else if (key === 'Backspace') {
            e.preventDefault();
            this._deleteLetter();
        } else if (key === 'Delete') {
            e.preventDefault();
            this.userLetters[this.selectedRow][this.selectedCol] = '';
            this._updateDisplay();
        } else if (key === 'ArrowRight') {
            e.preventDefault();
            this._moveSelection(0, 1);
        } else if (key === 'ArrowLeft') {
            e.preventDefault();
            this._moveSelection(0, -1);
        } else if (key === 'ArrowDown') {
            e.preventDefault();
            this._moveSelection(1, 0);
        } else if (key === 'ArrowUp') {
            e.preventDefault();
            this._moveSelection(-1, 0);
        } else if (key === 'Tab') {
            e.preventDefault();
            this._moveToNextWord(e.shiftKey);
        } else if (key === ' ') {
            e.preventDefault();
            this.currentDirection = this.currentDirection === 'across' ? 'down' : 'across';
            this._updateDisplay();
        }
    }

    // ===== Input =====

    _enterLetter(letter) {
        this.userLetters[this.selectedRow][this.selectedCol] = letter;
        this._advanceCursor();
        this._updateDisplay();
    }

    _deleteLetter() {
        if (this.userLetters[this.selectedRow][this.selectedCol]) {
            this.userLetters[this.selectedRow][this.selectedCol] = '';
            this._updateDisplay();
        } else {
            this._retreatCursor();
            this.userLetters[this.selectedRow][this.selectedCol] = '';
            this._updateDisplay();
        }
    }

    _advanceCursor() {
        const dr = this.currentDirection === 'down' ? 1 : 0;
        const dc = this.currentDirection === 'across' ? 1 : 0;
        let nr = this.selectedRow + dr;
        let nc = this.selectedCol + dc;

        if (this._isValidWhiteCell(nr, nc)) {
            this.selectedRow = nr;
            this.selectedCol = nc;
        }
    }

    _retreatCursor() {
        const dr = this.currentDirection === 'down' ? -1 : 0;
        const dc = this.currentDirection === 'across' ? -1 : 0;
        let nr = this.selectedRow + dr;
        let nc = this.selectedCol + dc;

        if (this._isValidWhiteCell(nr, nc)) {
            this.selectedRow = nr;
            this.selectedCol = nc;
        }
    }

    _moveSelection(dr, dc) {
        let nr = this.selectedRow + dr;
        let nc = this.selectedCol + dc;

        // Skip black cells
        while (nr >= 0 && nr < this.size && nc >= 0 && nc < this.size) {
            if (this._isValidWhiteCell(nr, nc)) {
                this.selectedRow = nr;
                this.selectedCol = nc;

                // Update direction based on movement
                if (dr !== 0) this.currentDirection = 'down';
                if (dc !== 0) this.currentDirection = 'across';

                this._updateDisplay();
                return;
            }
            nr += dr;
            nc += dc;
        }
    }

    _moveToNextWord(reverse) {
        const allWords = [
            ...this.words.across.map(w => ({ ...w, direction: 'across' })),
            ...this.words.down.map(w => ({ ...w, direction: 'down' })),
        ].sort((a, b) => a.number - b.number);

        const currentWord = this._getCurrentWord();
        let currentIdx = -1;
        if (currentWord) {
            currentIdx = allWords.findIndex(
                w => w.number === currentWord.number && w.direction === currentWord.direction
            );
        }

        let nextIdx;
        if (reverse) {
            nextIdx = currentIdx <= 0 ? allWords.length - 1 : currentIdx - 1;
        } else {
            nextIdx = currentIdx >= allWords.length - 1 ? 0 : currentIdx + 1;
        }

        const next = allWords[nextIdx];
        this.selectedRow = next.row;
        this.selectedCol = next.col;
        this.currentDirection = next.direction;
        this._updateDisplay();
    }

    // ===== Display Update =====

    _updateDisplay() {
        const highlightedCells = this._getHighlightedCells();

        for (let r = 0; r < this.size; r++) {
            for (let c = 0; c < this.size; c++) {
                const div = this.cells[r][c];
                const cellData = this.gridData[r][c];

                if (cellData.black) continue;

                // Update letter display
                const letterSpan = div.querySelector('.cell-letter');
                if (letterSpan) {
                    letterSpan.textContent = this.userLetters[r][c] || '';
                }

                // Update highlight classes
                div.classList.remove('selected', 'highlighted');

                if (r === this.selectedRow && c === this.selectedCol) {
                    div.classList.add('selected');
                }
                if (highlightedCells.has(`${r},${c}`)) {
                    div.classList.add('highlighted');
                }
            }
        }

        this._updateActiveClue();
        this._updateClueHighlights();
    }

    _getHighlightedCells() {
        const cells = new Set();
        const word = this._getCurrentWord();
        if (!word) return cells;

        const dr = word.direction === 'down' ? 1 : 0;
        const dc = word.direction === 'across' ? 1 : 0;

        for (let i = 0; i < word.length; i++) {
            cells.add(`${word.row + dr * i},${word.col + dc * i}`);
        }

        return cells;
    }

    _getCurrentWord() {
        if (this.selectedRow < 0) return null;

        const wordList = this.currentDirection === 'across' ? this.words.across : this.words.down;
        const dr = this.currentDirection === 'down' ? 1 : 0;
        const dc = this.currentDirection === 'across' ? 1 : 0;

        for (const word of wordList) {
            for (let i = 0; i < word.length; i++) {
                const wr = word.row + dr * i;
                const wc = word.col + dc * i;
                if (wr === this.selectedRow && wc === this.selectedCol) {
                    return { ...word, direction: this.currentDirection };
                }
            }
        }

        // If not found in current direction, try the other
        const otherDir = this.currentDirection === 'across' ? 'down' : 'across';
        const otherList = otherDir === 'across' ? this.words.across : this.words.down;
        const dr2 = otherDir === 'down' ? 1 : 0;
        const dc2 = otherDir === 'across' ? 1 : 0;

        for (const word of otherList) {
            for (let i = 0; i < word.length; i++) {
                const wr = word.row + dr2 * i;
                const wc = word.col + dc2 * i;
                if (wr === this.selectedRow && wc === this.selectedCol) {
                    return { ...word, direction: otherDir };
                }
            }
        }

        return null;
    }

    _updateActiveClue() {
        const bar = this.activeClueBar;
        const numEl = document.getElementById('active-clue-number');
        const textEl = document.getElementById('active-clue-text');

        const word = this._getCurrentWord();
        if (word) {
            const dirLabel = word.direction === 'across' ? 'A' : 'D';
            numEl.textContent = `${word.number}${dirLabel}`;
            textEl.textContent = word.clue;
        } else {
            numEl.textContent = '';
            textEl.textContent = 'Click a cell to begin';
        }
    }

    _updateClueHighlights() {
        // Remove all active highlights
        document.querySelectorAll('.clue-item.active').forEach(el => {
            el.classList.remove('active');
        });

        const word = this._getCurrentWord();
        if (!word) return;

        const selector = `.clue-item[data-number="${word.number}"][data-direction="${word.direction}"]`;
        const clueEl = document.querySelector(selector);
        if (clueEl) {
            clueEl.classList.add('active');
            // Scroll within the clues container only, without moving the page
            const container = clueEl.closest('.clues-container');
            if (container) {
                const elTop = clueEl.offsetTop - container.offsetTop;
                const elBottom = elTop + clueEl.offsetHeight;
                const viewTop = container.scrollTop;
                const viewBottom = viewTop + container.clientHeight;
                if (elTop < viewTop) {
                    container.scrollTop = elTop;
                } else if (elBottom > viewBottom) {
                    container.scrollTop = elBottom - container.clientHeight;
                }
            }
        }
    }

    // ===== Helpers =====

    _isValidWhiteCell(r, c) {
        return r >= 0 && r < this.size && c >= 0 && c < this.size &&
               !this.gridData[r][c].black;
    }

    // ===== Public Methods =====

    /**
     * Check all entered letters against the correct answers.
     */
    checkPuzzle() {
        let allCorrect = true;

        for (let r = 0; r < this.size; r++) {
            for (let c = 0; c < this.size; c++) {
                const cellData = this.gridData[r][c];
                const div = this.cells[r][c];
                if (cellData.black) continue;

                div.classList.remove('correct', 'incorrect');
                const userLetter = this.userLetters[r][c];

                if (userLetter) {
                    if (userLetter === cellData.letter) {
                        div.classList.add('correct');
                    } else {
                        div.classList.add('incorrect');
                        allCorrect = false;
                    }
                } else if (cellData.letter) {
                    allCorrect = false;
                }
            }
        }

        return allCorrect;
    }

    /**
     * Reveal the current word's letters.
     */
    revealCurrentWord() {
        const word = this._getCurrentWord();
        if (!word) return;

        const dr = word.direction === 'down' ? 1 : 0;
        const dc = word.direction === 'across' ? 1 : 0;

        for (let i = 0; i < word.length; i++) {
            const r = word.row + dr * i;
            const c = word.col + dc * i;
            const cellData = this.gridData[r][c];
            this.userLetters[r][c] = cellData.letter;
            this.revealedCells.add(`${r},${c}`);
            this.cells[r][c].classList.add('revealed');
            this.cells[r][c].classList.remove('incorrect');
        }

        this._updateDisplay();
    }

    /**
     * Reveal all answers.
     */
    revealAll() {
        for (let r = 0; r < this.size; r++) {
            for (let c = 0; c < this.size; c++) {
                const cellData = this.gridData[r][c];
                if (!cellData.black && cellData.letter) {
                    this.userLetters[r][c] = cellData.letter;
                    this.revealedCells.add(`${r},${c}`);
                    this.cells[r][c].classList.add('revealed');
                    this.cells[r][c].classList.remove('incorrect', 'correct');
                }
            }
        }
        this._updateDisplay();
    }

    /**
     * Clear all user-entered letters.
     */
    clearAll() {
        for (let r = 0; r < this.size; r++) {
            for (let c = 0; c < this.size; c++) {
                this.userLetters[r][c] = '';
                this.cells[r][c].classList.remove('correct', 'incorrect', 'revealed');
            }
        }
        this.revealedCells.clear();
        this._updateDisplay();
    }
}
