# Crossword Puzzle Generator

Generate themed crossword puzzles from any web article. Paste a URL, and the app extracts keywords, builds a 15x15 crossword grid, and generates clues — all tied to the article's theme.

![Crossword Puzzle Generator](https://img.shields.io/badge/python-3.9+-blue) ![Flask](https://img.shields.io/badge/flask-3.0-green)

## How It Works

1. **Fetch** — Scrapes the article and any linked pages for content
2. **Extract** — Uses an LLM to pull themed keywords from the text
3. **Research** — Searches for related topics to augment the word list
4. **Generate** — Places words on a 15x15 grid with rotational symmetry
5. **Clue** — Generates NYT-style crossword clues tied to the article's theme

## Quick Start

### Prerequisites

- Python 3.9+
- One of:
  - [Ollama](https://ollama.com) with `llama3.1:8b` (free, runs locally)
  - An [Anthropic API key](https://console.anthropic.com/) (uses Claude)

### Setup

```bash
# Clone the repo
git clone https://github.com/jwong-med/crossword-puzzle-generator.git
cd crossword-puzzle-generator

# Install dependencies
pip install -r requirements.txt

# Configure LLM (pick one)

# Option A: Ollama (recommended for local use)
ollama pull llama3.1:8b

# Option B: Anthropic API
cp .env.example .env
# Edit .env and add your API key
```

### Run

```bash
python server.py
```

Open [http://localhost:8080](http://localhost:8080) in your browser.

## Usage

1. Paste any article URL into the input field
2. Click **Generate Puzzle** and wait ~1-2 minutes
3. Solve the crossword — click cells or use arrow keys to navigate
4. Use **Check**, **Reveal Word**, or **Reveal All** to verify answers

A demo puzzle is available without any API key — click "try a demo puzzle" on the home page.

## Project Structure

```
.
├── server.py              # Flask app and API routes
├── lib/
│   ├── article_fetcher.py # Web scraping and content extraction
│   ├── keyword_extractor.py # LLM keyword extraction
│   ├── crossword_generator.py # Grid generation algorithm
│   ├── clue_generator.py  # LLM clue generation
│   ├── llm_client.py      # Ollama / Anthropic API client
│   └── word_list.py       # Crossword fill word database
├── static/
│   ├── index.html         # Single-page app
│   ├── css/style.css      # Styling
│   └── js/
│       ├── app.js         # UI orchestration
│       ├── grid.js        # Interactive grid and keyboard nav
│       └── api.js         # API client
├── requirements.txt
├── .env.example           # Environment config template
└── start.sh               # Convenience start script
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(none)* | Anthropic API key. If unset, Ollama is used. |
| `PORT` | `8080` | Server port |

## API

### `POST /api/generate`

Generate a crossword from an article URL.

**Request:**
```json
{ "url": "https://example.com/article" }
```

**Response:**
```json
{
  "grid": [[{"black": false, "letter": "A", "number": 1}, ...]],
  "words": {
    "across": [{"number": 1, "answer": "ANSWER", "clue": "...", "row": 0, "col": 0, "length": 6}],
    "down": [...]
  },
  "size": 15,
  "summary": "Article summary...",
  "title": "Article Title",
  "wordCount": 42
}
```

### `POST /api/test`

Returns a pre-built demo puzzle (no LLM required).

## License

MIT
