/**
 * API communication module for the crossword generator.
 */
const API = {
    /**
     * Generate a crossword puzzle from an article URL.
     * @param {string} url - The article URL
     * @returns {Promise<Object>} Puzzle data
     */
    async generatePuzzle(url) {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate puzzle');
        }

        return data;
    },
};
