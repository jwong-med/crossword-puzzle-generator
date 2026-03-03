import json
import re
from lib.llm_client import chat


def extract_keywords(main_text, linked_texts, title, api_key=None):
    """Use an LLM to extract crossword-ready keywords from article content.

    Args:
        main_text: The main article text
        linked_texts: List of text strings from linked pages
        title: Article title
        api_key: Optional Anthropic API key (uses Ollama if available)

    Returns:
        dict with keys: keywords (list of uppercase strings), summary (str)
    """

    linked_context = ''
    for i, text in enumerate(linked_texts[:5]):
        if text:
            linked_context += f"\n\n--- Related Page {i+1} ---\n{text[:1000]}"

    user_message = f"""Here is an article titled "{title}":

{main_text[:4000]}

{f"Additional context from related pages:{linked_context}" if linked_context else ""}

Extract 40-50 words that would work as crossword puzzle answers. Requirements:
- Each answer must be a single word (no spaces, no hyphens), 3-15 letters, only A-Z
- Include a mix of: key people (last names), places, technical terms, common related words
- Include some easier words (3-5 letters) and harder words (8+ letters)
- All words must relate to the article's themes or topics mentioned
- Include some general knowledge words related to the subject matter
- Avoid overly obscure words that most people wouldn't know

Return ONLY valid JSON with no other text:
{{
  "keywords": ["WORD1", "WORD2", "WORD3"],
  "summary": "A 2-3 sentence summary of the article."
}}"""

    response_text = chat(
        system='You are an expert crossword puzzle constructor. Extract words from articles that make excellent crossword puzzle answers. Return only valid JSON.',
        user_message=user_message,
        max_tokens=2000,
        api_key=api_key,
    )

    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        raise ValueError('Claude did not return valid JSON')

    data = json.loads(json_match.group())

    keywords = []
    seen = set()
    for word in data.get('keywords', []):
        cleaned = re.sub(r'[^A-Za-z]', '', word).upper()
        if 3 <= len(cleaned) <= 15 and cleaned not in seen:
            seen.add(cleaned)
            keywords.append(cleaned)

    return {
        'keywords': keywords,
        'summary': data.get('summary', ''),
    }


def search_related_topics(summary, api_key=None):
    """Use an LLM to suggest search queries for finding related information.

    Args:
        summary: Article summary text
        api_key: Optional Anthropic API key (uses Ollama if available)

    Returns:
        list of search query strings
    """
    response_text = chat(
        system='You suggest web search queries to find more information about a topic. Return only valid JSON.',
        user_message=f"""Based on this article summary, suggest 3 search queries that would find additional related information useful for creating a crossword puzzle about this topic.

Summary: {summary}

Return ONLY valid JSON:
{{"queries": ["query 1", "query 2", "query 3"]}}""",
        max_tokens=500,
        api_key=api_key,
    )
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        data = json.loads(json_match.group())
        return data.get('queries', [])
    return []
