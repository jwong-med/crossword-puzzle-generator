/**
 * Clue generator — uses LLM to generate crossword-style clues.
 *
 * Faithful port of clue_generator.py.
 */

import { chat } from './llm-client.js';

/**
 * Parse JSON clues from LLM response text.
 * @returns {Object<string, string>} mapping uppercase word -> clue string
 */
function _parseCluesFromResponse(responseText, words) {
  const jsonMatch = responseText.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    console.log(`[clue_generator] No JSON found in LLM response: ${responseText.slice(0, 200)}`);
    return {};
  }

  let clues;
  try {
    clues = JSON.parse(jsonMatch[0]);
  } catch {
    console.log(`[clue_generator] JSON parse failed: ${jsonMatch[0].slice(0, 200)}`);
    return {};
  }

  // Build case-insensitive lookup
  const cluesUpper = {};
  for (const [k, v] of Object.entries(clues)) {
    if (typeof v === 'string') {
      cluesUpper[k.toUpperCase().trim()] = v;
    }
  }

  const result = {};
  for (const word of words) {
    const w = word.toUpperCase();
    if (cluesUpper[w]) result[w] = cluesUpper[w];
  }
  return result;
}

/**
 * Send a batch of words to the LLM and parse the JSON response.
 * Retries once for any missing words.
 */
async function _generateClueBatch(words, systemPrompt, userMessage, apiKey) {
  const responseText = await chat({
    system: systemPrompt,
    userMessage,
    maxTokens: 4000,
    apiKey,
  });

  const result = _parseCluesFromResponse(responseText, words);

  // Retry once for any missing words
  const missing = words.filter((w) => !(w.toUpperCase() in result));
  if (missing.length > 0 && missing.length < words.length) {
    console.log(`[clue_generator] Retrying ${missing.length} missing words: ${missing}`);
    const retryList = missing.join(', ');
    const retryMsg =
      userMessage.split('Answers')[0] +
      `Answers:\n${retryList}\n\nReturn ONLY valid JSON mapping each answer (uppercase) to its clue:\n{\n  "${missing[0]}": "Example clue here"\n}`;

    const retryText = await chat({
      system: systemPrompt,
      userMessage: retryMsg,
      maxTokens: 2000,
      apiKey,
    });
    const retryClues = _parseCluesFromResponse(retryText, missing);
    Object.assign(result, retryClues);
  }

  const stillMissing = words.filter((w) => !(w.toUpperCase() in result));
  if (stillMissing.length > 0) {
    console.log(`[clue_generator] Still missing after retry: ${stillMissing}`);
  }

  return result;
}

/**
 * Use an LLM to generate crossword-style clues for placed words.
 *
 * Themed words get article-context clues; fill words get generic crossword clues.
 * If there are many words, they are batched into multiple LLM calls.
 *
 * @param {Array<{word: string, isThemed: boolean}>} placedWords
 * @param {string} summary - Article summary for context
 * @param {string|null} apiKey - Optional Anthropic API key
 * @returns {Promise<Object<string, string>>} mapping uppercase word -> clue
 */
async function generateClues(placedWords, summary, apiKey = null) {
  const themed = placedWords.filter((pw) => pw.isThemed !== false);
  const fill = placedWords.filter((pw) => pw.isThemed === false);

  const result = {};

  const systemPrompt =
    'You are an expert crossword puzzle clue writer in the style of the New York Times crossword. Write concise, clever clues. Return only valid JSON.';

  // Generate clues for themed words (with article context)
  if (themed.length > 0) {
    const themedWords = themed.map((pw) => pw.word);
    for (let i = 0; i < themedWords.length; i += 15) {
      const batch = themedWords.slice(i, i + 15);
      const wordListStr = batch.join(', ');
      const exampleWord = batch[0];

      const userMessage = `I have a crossword puzzle themed around this topic:
"${summary}"

Write clues for these crossword answers. Use standard crossword conventions:
- Brief, typically 3-10 words per clue
- Use wordplay, definitions, or fill-in-the-blank where appropriate
- Reference the article's theme when it makes sense
- Vary difficulty levels (some easy, some tricky)
- Every clue must be solvable by a knowledgeable person
- Use standard crossword abbreviation hints (e.g., "Abbr." if the answer is an abbreviation)
- NEVER include the answer word itself in the clue. If you need to reference it, use a blank (___) instead

Answers to write clues for:
${wordListStr}

Return ONLY valid JSON mapping each answer (uppercase) to its clue:
{
  "${exampleWord}": "Example clue here"
}`;

      const batchClues = await _generateClueBatch(batch, systemPrompt, userMessage, apiKey);
      Object.assign(result, batchClues);
    }
  }

  // Generate clues for fill words (with article theme for flavor)
  if (fill.length > 0) {
    const fillWords = fill.map((pw) => pw.word);
    for (let i = 0; i < fillWords.length; i += 15) {
      const batch = fillWords.slice(i, i + 15);
      const wordListStr = batch.join(', ');
      const exampleWord = batch[0];

      const userMessage = `This crossword puzzle is themed around this topic:
"${summary}"

Write clues for these fill words. Use standard crossword conventions:
- Brief, typically 3-10 words per clue
- Use wordplay, definitions, or fill-in-the-blank where appropriate
- Where a word can plausibly connect to the article's theme, write a clue that ties into that theme (e.g., if the article is about space and the word is NET, clue it as "Safety device for astronaut training" rather than just "Fishing tool")
- Not every word needs a themed clue — if there's no natural connection, write a standard crossword clue instead
- Vary difficulty levels (some easy, some tricky)
- Every clue must be solvable by a knowledgeable person
- NEVER include the answer word itself in the clue. If you need to reference it, use a blank (___) instead

Answers:
${wordListStr}

Return ONLY valid JSON mapping each answer (uppercase) to its clue:
{
  "${exampleWord}": "Example clue here"
}`;

      const batchClues = await _generateClueBatch(batch, systemPrompt, userMessage, apiKey);
      Object.assign(result, batchClues);
    }
  }

  // Fallback: retry missing words individually
  const missingWords = placedWords.filter((pw) => !(pw.word.toUpperCase() in result));
  if (missingWords.length > 0) {
    console.log(
      `[clue_generator] ${missingWords.length} words still missing clues, retrying individually`
    );
    for (const pw of missingWords) {
      const w = pw.word.toUpperCase();
      try {
        const fallbackText = await chat({
          system: 'You are a crossword clue writer. Return ONLY valid JSON.',
          userMessage: `Write one crossword clue for the answer "${w}". NEVER include the answer word in the clue. Return JSON: {"${w}": "your clue"}`,
          maxTokens: 200,
          apiKey,
        });
        const fallbackClues = _parseCluesFromResponse(fallbackText, [w]);
        if (w in fallbackClues) {
          result[w] = fallbackClues[w];
          continue;
        }
      } catch {
        // fall through to last resort
      }
      // Last resort fallback
      result[w] = `Crossword answer (${w.length} letters)`;
    }
  }

  return result;
}

export { generateClues };
