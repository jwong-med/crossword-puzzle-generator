/**
 * Express server for the Crossword Puzzle Generator.
 *
 * Faithful port of server.py (Flask → Express).
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { readFileSync } from 'fs';
import express from 'express';
import axios from 'axios';
import * as cheerio from 'cheerio';
import 'dotenv/config';

import { fetchArticle, fetchLinkedPages } from './lib/article-fetcher.js';
import { extractKeywords, searchRelatedTopics } from './lib/keyword-extractor.js';
import { generateCrossword, gridToJson } from './lib/crossword-generator.js';
import { generateClues } from './lib/clue-generator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const STATIC_DIR = join(__dirname, 'dist');
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY || null;

const app = express();
app.use(express.json());

// Serve index.html at root
app.get('/', (_req, res) => {
  res.sendFile(join(STATIC_DIR, 'index.html'));
});

// Serve static assets
app.use(express.static(STATIC_DIR));

// Demo puzzle endpoint (no API key required)
app.post('/api/test', (_req, res) => {
  try {
    const demoPath = join(__dirname, 'data', 'demo_puzzle.json');
    const data = JSON.parse(readFileSync(demoPath, 'utf-8'));
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: `Failed to load demo puzzle: ${err.message}` });
  }
});

// Full generation pipeline
app.post('/api/generate', async (req, res) => {
  const apiKey =
    ANTHROPIC_API_KEY && ANTHROPIC_API_KEY !== 'your-api-key-here'
      ? ANTHROPIC_API_KEY
      : null;

  const data = req.body;
  if (!data || !data.url) {
    return res.status(400).json({ error: 'Please provide a URL in the request body.' });
  }

  let url = data.url.trim();
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = 'https://' + url;
  }

  // Step 1: Fetch the article
  let article;
  try {
    article = await fetchArticle(url);
  } catch (err) {
    if (err.code === 'ECONNABORTED') {
      return res
        .status(400)
        .json({ error: 'The article URL took too long to respond. Please try a different URL.' });
    }
    return res.status(400).json({ error: `Could not fetch the article: ${err.message}` });
  }

  if (article.main_text.length < 100) {
    return res.status(400).json({
      error: 'Article content is too short. Please try a different URL with more text content.',
    });
  }

  // Step 2: Fetch linked pages
  let linkedTexts = [];
  try {
    const linkedPages = await fetchLinkedPages(article.links);
    linkedTexts = linkedPages.map((p) => p.text);
  } catch {
    linkedTexts = [];
  }

  // Step 3: Extract keywords using LLM
  let extraction;
  try {
    extraction = await extractKeywords(article.main_text, linkedTexts, article.title, apiKey);
  } catch (err) {
    return res.status(500).json({ error: `Keyword extraction failed: ${err.message}` });
  }

  let keywords = extraction.keywords;
  const summary = extraction.summary;

  if (keywords.length < 5) {
    return res.status(400).json({
      error: 'Could not extract enough keywords from the article. Please try a different URL.',
    });
  }

  // Step 4: Search for related topics and extract more keywords
  try {
    const searchQueries = await searchRelatedTopics(summary, apiKey);
    const additionalTexts = [];

    for (const query of searchQueries.slice(0, 3)) {
      try {
        const searchUrl = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
        const resp = await axios.get(searchUrl, {
          headers: {
            'User-Agent':
              'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
          },
          timeout: 8000,
        });
        if (resp.status === 200) {
          const $ = cheerio.load(resp.data);
          const snippets = [];
          $('.result__snippet').each((_, el) => {
            snippets.push($(el).text().trim());
          });
          additionalTexts.push(...snippets.slice(0, 5));
        }
      } catch {
        continue;
      }
    }

    // If we got search results, extract more keywords
    if (additionalTexts.length > 0) {
      const combinedText = additionalTexts.join('\n').slice(0, 3000);
      try {
        const extra = await extractKeywords(
          combinedText,
          [],
          `Related information about: ${article.title}`,
          apiKey
        );
        const existing = new Set(keywords);
        for (const kw of extra.keywords) {
          if (!existing.has(kw)) {
            keywords.push(kw);
            existing.add(kw);
          }
        }
      } catch {
        // ignore
      }
    }
  } catch {
    // ignore
  }

  // Step 5: Generate crossword grid
  const [grid, placedWords] = generateCrossword(keywords);

  if (placedWords.length < 5) {
    return res.status(400).json({
      error:
        'Could not generate a valid crossword with enough words. Please try a different article.',
    });
  }

  // Step 6: Generate clues
  let clues;
  try {
    clues = await generateClues(placedWords, summary, apiKey);
  } catch {
    // Fallback: use generic clues
    clues = {};
    for (const pw of placedWords) {
      clues[pw.word] = 'Related to the article topic';
    }
  }

  // Step 7: Build response
  const puzzleData = gridToJson(grid, placedWords, clues);
  puzzleData.summary = summary;
  puzzleData.title = article.title;
  puzzleData.wordCount = placedWords.length;

  res.json(puzzleData);
});

const port = parseInt(process.env.PORT || '8080', 10);
app.listen(port, '0.0.0.0', () => {
  console.log(`Crossword server running on http://localhost:${port}`);
});
