/**
 * Keyword extractor — uses LLM to pull crossword-ready words from articles.
 *
 * Faithful port of keyword_extractor.py.
 */

import { chat } from './llm-client.js';

/**
 * Use an LLM to extract crossword-ready keywords from article content.
 *
 * @param {string} mainText - The main article text
 * @param {string[]} linkedTexts - Texts from linked pages
 * @param {string} title - Article title
 * @param {string|null} apiKey - Optional Anthropic API key
 * @returns {Promise<{keywords: string[], summary: string}>}
 */
async function extractKeywords(mainText, linkedTexts, title, apiKey = null) {
  let linkedContext = '';
  for (let i = 0; i < Math.min(linkedTexts.length, 5); i++) {
    if (linkedTexts[i]) {
      linkedContext += `\n\n--- Related Page ${i + 1} ---\n${linkedTexts[i].slice(0, 1000)}`;
    }
  }

  const userMessage = `Here is an article titled "${title}":

${mainText.slice(0, 4000)}

${linkedContext ? `Additional context from related pages:${linkedContext}` : ''}

Extract 40-50 words that would work as crossword puzzle answers. Requirements:
- Each answer must be a single word (no spaces, no hyphens), 3-15 letters, only A-Z
- Include a mix of: key people (last names), places, technical terms, common related words
- Include some easier words (3-5 letters) and harder words (8+ letters)
- All words must relate to the article's themes or topics mentioned
- Include some general knowledge words related to the subject matter
- Avoid overly obscure words that most people wouldn't know

Return ONLY valid JSON with no other text:
{
  "keywords": ["WORD1", "WORD2", "WORD3"],
  "summary": "A 2-3 sentence summary of the article."
}`;

  const responseText = await chat({
    system:
      'You are an expert crossword puzzle constructor. Extract words from articles that make excellent crossword puzzle answers. Return only valid JSON.',
    userMessage,
    maxTokens: 2000,
    apiKey,
  });

  const jsonMatch = responseText.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    throw new Error('Claude did not return valid JSON');
  }

  const data = JSON.parse(jsonMatch[0]);

  const keywords = [];
  const seen = new Set();
  for (const word of data.keywords || []) {
    const cleaned = word.replace(/[^A-Za-z]/g, '').toUpperCase();
    if (cleaned.length >= 3 && cleaned.length <= 15 && !seen.has(cleaned)) {
      seen.add(cleaned);
      keywords.push(cleaned);
    }
  }

  return {
    keywords,
    summary: data.summary || '',
  };
}

/**
 * Use an LLM to suggest search queries for finding related information.
 *
 * @param {string} summary - Article summary text
 * @param {string|null} apiKey - Optional Anthropic API key
 * @returns {Promise<string[]>}
 */
async function searchRelatedTopics(summary, apiKey = null) {
  const responseText = await chat({
    system:
      'You suggest web search queries to find more information about a topic. Return only valid JSON.',
    userMessage: `Based on this article summary, suggest 3 search queries that would find additional related information useful for creating a crossword puzzle about this topic.

Summary: ${summary}

Return ONLY valid JSON:
{"queries": ["query 1", "query 2", "query 3"]}`,
    maxTokens: 500,
    apiKey,
  });

  const jsonMatch = responseText.match(/\{[\s\S]*\}/);
  if (jsonMatch) {
    const data = JSON.parse(jsonMatch[0]);
    return data.queries || [];
  }
  return [];
}

export { extractKeywords, searchRelatedTopics };
