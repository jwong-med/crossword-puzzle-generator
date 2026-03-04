/**
 * Article fetcher — scrapes web articles and linked pages.
 *
 * Faithful port of article_fetcher.py.
 * Uses axios + cheerio instead of requests + BeautifulSoup.
 */

import axios from 'axios';
import * as cheerio from 'cheerio';

const HEADERS = {
  'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  Accept:
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
  'Accept-Language': 'en-US,en;q=0.9',
  'Accept-Encoding': 'gzip, deflate, br',
  Connection: 'keep-alive',
  'Upgrade-Insecure-Requests': '1',
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'none',
  'Sec-Fetch-User': '?1',
  'Cache-Control': 'max-age=0',
};
const TIMEOUT = 15_000;
const MAX_LINKED_PAGES = 5;
const MAX_TEXT_LENGTH = 5000;
const MAX_LINKED_TEXT_LENGTH = 2000;

function _extractText($) {
  // Remove noise tags
  $('script, style, nav, footer, header, aside, noscript, iframe').remove();

  const content = $('article').length
    ? $('article')
    : $('main').length
      ? $('main')
      : $('body');

  if (!content.length) return '';

  const text = content.text();
  const lines = text
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);
  return lines.join('\n');
}

function _extractLinks($, baseUrl) {
  const content = $('article').length
    ? $('article')
    : $('main').length
      ? $('main')
      : $('body');

  if (!content.length) return [];

  const links = [];
  const seen = new Set();

  content.find('a[href]').each((_, el) => {
    if (links.length >= MAX_LINKED_PAGES) return false;

    const href = $(el).attr('href');
    let absolute;
    try {
      absolute = new URL(href, baseUrl).href;
    } catch {
      return; // skip invalid URLs
    }

    const parsed = new URL(absolute);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return;

    // Strip fragment
    if (absolute.includes('#')) absolute = absolute.split('#')[0];
    if (!absolute || absolute === baseUrl) return;
    if (seen.has(absolute)) return;

    seen.add(absolute);
    links.push(absolute);
  });

  return links;
}

function _isMedium(url) {
  try {
    const host = new URL(url).hostname.toLowerCase();
    return host.includes('medium.com');
  } catch {
    return false;
  }
}

function _toScribeUrl(url) {
  return url.replace('medium.com', 'scribe.rip');
}

async function _fetchWithSession(url) {
  const resp = await axios.get(url, {
    headers: HEADERS,
    timeout: TIMEOUT,
    maxRedirects: 5,
    responseType: 'text',
  });
  return resp.data;
}

/**
 * Fetch an article URL and extract its text content and links.
 *
 * @param {string} url
 * @returns {Promise<{title: string, main_text: string, links: string[]}>}
 */
async function fetchArticle(url) {
  let html;

  if (_isMedium(url)) {
    try {
      html = await _fetchWithSession(_toScribeUrl(url));
    } catch {
      html = await _fetchWithSession(url);
    }
  } else {
    html = await _fetchWithSession(url);
  }

  const $ = cheerio.load(html);

  const titleTag = $('title').first();
  const title = titleTag.length ? titleTag.text().trim() : 'Untitled';

  const mainText = _extractText($).slice(0, MAX_TEXT_LENGTH);
  const links = _extractLinks($, url);

  return { title, main_text: mainText, links };
}

async function _fetchSinglePage(url) {
  try {
    const html = await _fetchWithSession(url);
    const $ = cheerio.load(html);
    const text = _extractText($).slice(0, MAX_LINKED_TEXT_LENGTH);
    return { url, text };
  } catch {
    return { url, text: '' };
  }
}

/**
 * Fetch multiple linked pages concurrently.
 *
 * @param {string[]} links
 * @returns {Promise<{url: string, text: string}[]>}
 */
async function fetchLinkedPages(links) {
  const toFetch = links.slice(0, MAX_LINKED_PAGES);
  const results = await Promise.all(toFetch.map(_fetchSinglePage));
  return results.filter((r) => r.text);
}

export { fetchArticle, fetchLinkedPages };
