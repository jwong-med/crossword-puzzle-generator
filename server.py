import os
import sys
import json
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# Resolve the directory this script lives in so all paths are absolute.
# This avoids os.getcwd() calls that can fail in sandboxed environments.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from lib.article_fetcher import fetch_article, fetch_linked_pages
from lib.keyword_extractor import extract_keywords, search_related_topics
from lib.crossword_generator import generate_crossword, grid_to_json
from lib.clue_generator import generate_clues

load_dotenv(os.path.join(BASE_DIR, '.env'))

STATIC_DIR = os.path.join(BASE_DIR, 'static')
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')

app = Flask(
    __name__,
    static_folder=STATIC_DIR,
    instance_path=INSTANCE_DIR,
)

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')


@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, 'index.html')


@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_DIR, path)


@app.route('/api/test', methods=['POST'])
def test_puzzle():
    """Return a pre-built demo puzzle (no API key required)."""
    demo_path = os.path.join(STATIC_DIR, 'demo_puzzle.json')
    with open(demo_path) as f:
        return jsonify(json.load(f))


@app.route('/api/generate', methods=['POST'])
def generate():
    # Ollama runs locally without an API key; Anthropic needs one
    api_key = ANTHROPIC_API_KEY if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'your-api-key-here' else None

    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Please provide a URL in the request body.'}), 400

    url = data['url'].strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Step 1: Fetch the article
    try:
        article = fetch_article(url)
    except requests.exceptions.Timeout:
        return jsonify({'error': 'The article URL took too long to respond. Please try a different URL.'}), 400
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Could not fetch the article: {str(e)}'}), 400

    if len(article['main_text']) < 100:
        return jsonify({'error': 'Article content is too short. Please try a different URL with more text content.'}), 400

    # Step 2: Fetch linked pages
    try:
        linked_pages = fetch_linked_pages(article['links'])
        linked_texts = [p['text'] for p in linked_pages]
    except Exception:
        linked_texts = []

    # Step 3: Extract keywords using Claude
    try:
        extraction = extract_keywords(
            article['main_text'],
            linked_texts,
            article['title'],
            api_key,
        )
    except Exception as e:
        return jsonify({'error': f'Keyword extraction failed: {str(e)}'}), 500

    keywords = extraction['keywords']
    summary = extraction['summary']

    if len(keywords) < 5:
        return jsonify({'error': 'Could not extract enough keywords from the article. Please try a different URL.'}), 400

    # Step 4: Search for related topics and extract more keywords
    try:
        search_queries = search_related_topics(summary, api_key)
        # Perform web searches to augment keywords
        additional_texts = []
        for query in search_queries[:3]:
            try:
                search_url = f'https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}'
                resp = requests.get(search_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }, timeout=8)
                if resp.ok:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp.text, 'lxml')
                    snippets = [s.get_text(strip=True) for s in soup.select('.result__snippet')]
                    additional_texts.extend(snippets[:5])
            except Exception:
                continue

        # If we got search results, extract more keywords from them
        if additional_texts:
            combined_text = '\n'.join(additional_texts)[:3000]
            try:
                extra = extract_keywords(
                    combined_text,
                    [],
                    f'Related information about: {article["title"]}',
                    api_key,
                )
                # Merge keywords, avoiding duplicates
                existing = set(keywords)
                for kw in extra['keywords']:
                    if kw not in existing:
                        keywords.append(kw)
                        existing.add(kw)
            except Exception:
                pass
    except Exception:
        pass

    # Step 5: Generate crossword grid
    grid, placed_words = generate_crossword(keywords)

    if len(placed_words) < 5:
        return jsonify({'error': 'Could not generate a valid crossword with enough words. Please try a different article.'}), 400

    # Step 6: Generate clues
    try:
        clues = generate_clues(placed_words, summary, api_key)
    except Exception as e:
        # Fallback: use generic clues
        clues = {pw.word: f'Related to the article topic' for pw in placed_words}

    # Step 7: Build response
    puzzle_data = grid_to_json(grid, placed_words, clues)
    puzzle_data['summary'] = summary
    puzzle_data['title'] = article['title']
    puzzle_data['wordCount'] = len(placed_words)

    return jsonify(puzzle_data)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True,
        load_dotenv=False,
        use_reloader=False,
    )
