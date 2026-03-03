/**
 * Main application controller.
 */
(function () {
    // DOM references
    const inputSection = document.getElementById('input-section');
    const loadingSection = document.getElementById('loading-section');
    const errorSection = document.getElementById('error-section');
    const puzzleSection = document.getElementById('puzzle-section');
    const urlForm = document.getElementById('url-form');
    const urlInput = document.getElementById('url-input');
    const generateBtn = document.getElementById('generate-btn');
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

    // Grid instance (exposed globally for testing)
    const grid = new CrosswordGrid(gridContainer, acrossClues, downClues, activeClueBar);
    window._crosswordGrid = grid;

    // State management
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

    // Loading text animation
    const loadingStages = [
        'Fetching article...',
        'Reading linked pages...',
        'Searching for related information...',
        'Extracting keywords with AI...',
        'Building crossword grid...',
        'Generating clues...',
        'Almost done...',
    ];

    let loadingInterval = null;

    function startLoadingAnimation() {
        let stage = 0;
        loadingText.textContent = loadingStages[0];
        loadingInterval = setInterval(() => {
            stage++;
            if (stage < loadingStages.length) {
                loadingText.textContent = loadingStages[stage];
            }
        }, 4000);
    }

    function stopLoadingAnimation() {
        if (loadingInterval) {
            clearInterval(loadingInterval);
            loadingInterval = null;
        }
    }

    // Generate puzzle
    async function generatePuzzle(url) {
        showSection(loadingSection);
        showToolbarButtons(false);
        startLoadingAnimation();

        try {
            const data = await API.generatePuzzle(url);

            stopLoadingAnimation();
            showSection(puzzleSection);
            showToolbarButtons(true);

            // Set title and summary
            puzzleTitle.textContent = data.title || 'Crossword Puzzle';
            if (data.summary) {
                puzzleSummary.textContent = data.summary;
                puzzleSummary.style.display = '';
            } else {
                puzzleSummary.style.display = 'none';
            }

            // Initialize the grid
            grid.init(data);

            // Focus the grid for keyboard input
            gridContainer.focus();

        } catch (err) {
            stopLoadingAnimation();
            errorText.textContent = err.message || 'Something went wrong. Please try again.';
            showSection(errorSection);
        }
    }

    // Event listeners
    urlForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (url) {
            generatePuzzle(url);
        }
    });

    tryAgainBtn.addEventListener('click', () => {
        showSection(inputSection);
        showToolbarButtons(false);
    });

    // Demo button
    const demoBtn = document.getElementById('demo-btn');
    if (demoBtn) {
        demoBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            showSection(loadingSection);
            loadingText.textContent = 'Building demo puzzle...';
            try {
                const resp = await fetch('/api/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: '{}',
                });
                const data = await resp.json();
                showSection(puzzleSection);
                showToolbarButtons(true);
                puzzleTitle.textContent = data.title || 'Demo Crossword';
                if (data.summary) {
                    puzzleSummary.textContent = data.summary;
                    puzzleSummary.style.display = '';
                }
                grid.init(data);
                gridContainer.focus();
            } catch (err) {
                errorText.textContent = 'Could not load demo puzzle.';
                showSection(errorSection);
            }
        });
    }

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

    // Allow loading puzzle data directly (for testing)
    window._loadPuzzle = function(data) {
        showSection(puzzleSection);
        showToolbarButtons(true);
        puzzleTitle.textContent = data.title || 'Crossword Puzzle';
        if (data.summary) {
            puzzleSummary.textContent = data.summary;
            puzzleSummary.style.display = '';
        } else {
            puzzleSummary.style.display = 'none';
        }
        grid.init(data);
        gridContainer.focus();
    };

    // Start with input section visible
    showSection(inputSection);
    showToolbarButtons(false);
})();
