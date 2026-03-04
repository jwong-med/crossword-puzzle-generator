/**
 * Static demo app controller (GitHub Pages version).
 * Loads the pre-built demo puzzle from demo_puzzle.json.
 */
(function () {
    // DOM references
    const inputSection = document.getElementById('input-section');
    const loadingSection = document.getElementById('loading-section');
    const errorSection = document.getElementById('error-section');
    const puzzleSection = document.getElementById('puzzle-section');
    const loadingText = document.getElementById('loading-text');
    const errorText = document.getElementById('error-text');
    const tryAgainBtn = document.getElementById('try-again-btn');
    const puzzleTitle = document.getElementById('puzzle-title');
    const puzzleSummary = document.getElementById('puzzle-summary');

    const btnCheck = document.getElementById('btn-check');
    const btnRevealWord = document.getElementById('btn-reveal-word');
    const btnRevealAll = document.getElementById('btn-reveal-all');
    const btnClear = document.getElementById('btn-clear');
    const puzzleToolbar = document.getElementById('puzzle-toolbar');

    const gridContainer = document.getElementById('crossword-grid');
    const acrossClues = document.getElementById('across-clues');
    const downClues = document.getElementById('down-clues');
    const activeClueBar = document.getElementById('active-clue-bar');

    const grid = new CrosswordGrid(gridContainer, acrossClues, downClues, activeClueBar);

    function showSection(section) {
        inputSection.style.display = 'none';
        loadingSection.style.display = 'none';
        errorSection.style.display = 'none';
        puzzleSection.style.display = 'none';
        section.style.display = '';
    }

    function showToolbarButtons(show) {
        puzzleToolbar.style.display = show ? '' : 'none';
    }

    function loadPuzzle(data) {
        showSection(puzzleSection);
        showToolbarButtons(true);
        puzzleTitle.textContent = data.title || 'Demo Crossword';
        if (data.summary) {
            puzzleSummary.textContent = data.summary;
            puzzleSummary.style.display = '';
        } else {
            puzzleSummary.style.display = 'none';
        }
        grid.init(data);
        gridContainer.focus();
    }

    // Demo button — fetch static JSON
    const demoBtn = document.getElementById('demo-btn');
    if (demoBtn) {
        demoBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            showSection(loadingSection);
            loadingText.textContent = 'Loading demo puzzle...';
            try {
                const resp = await fetch('./demo_puzzle.json');
                if (!resp.ok) throw new Error('Failed to load demo puzzle');
                const data = await resp.json();
                loadPuzzle(data);
            } catch (err) {
                errorText.textContent = 'Could not load demo puzzle.';
                showSection(errorSection);
            }
        });
    }

    tryAgainBtn.addEventListener('click', () => {
        showSection(inputSection);
        showToolbarButtons(false);
    });

    btnCheck.addEventListener('click', () => {
        const allCorrect = grid.checkPuzzle();
        if (allCorrect) {
            alert('Congratulations! All answers are correct!');
        }
    });

    btnRevealWord.addEventListener('click', () => {
        grid.revealCurrentWord();
    });

    btnRevealAll.addEventListener('click', () => {
        if (confirm('Are you sure you want to reveal all answers?')) {
            grid.revealAll();
        }
    });

    btnClear.addEventListener('click', () => {
        if (confirm('Clear all your entries?')) {
            grid.clearAll();
        }
    });

    showSection(inputSection);
    showToolbarButtons(false);
})();
