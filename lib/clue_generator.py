import json
import re
from lib.llm_client import chat


def _parse_clues_from_response(response_text, words):
    """Parse JSON clues from LLM response text.

    Returns dict mapping uppercase word -> clue string.
    """
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if not json_match:
        print(f'[clue_generator] No JSON found in LLM response: {response_text[:200]}')
        return {}

    try:
        clues = json.loads(json_match.group())
    except json.JSONDecodeError:
        print(f'[clue_generator] JSON parse failed: {json_match.group()[:200]}')
        return {}

    # Build case-insensitive lookup
    clues_upper = {k.upper().strip(): v for k, v in clues.items() if isinstance(v, str)}

    result = {}
    for word in words:
        w = word.upper()
        clue = clues_upper.get(w)
        if clue:
            result[w] = clue

    return result


def _generate_clue_batch(words, system_prompt, user_message, api_key):
    """Send a batch of words to the LLM and parse the JSON response.

    Retries once for any missing words.
    Returns dict mapping uppercase word -> clue string.
    """
    response_text = chat(
        system=system_prompt,
        user_message=user_message,
        max_tokens=4000,
        api_key=api_key,
    )

    result = _parse_clues_from_response(response_text, words)

    # Retry once for any missing words
    missing = [w for w in words if w.upper() not in result]
    if missing and len(missing) < len(words):
        print(f'[clue_generator] Retrying {len(missing)} missing words: {missing}')
        retry_list = ', '.join(missing)
        retry_msg = user_message.rsplit('Answers', 1)[0] + f'Answers:\n{retry_list}\n\nReturn ONLY valid JSON mapping each answer (uppercase) to its clue:\n{{\n  "{missing[0]}": "Example clue here"\n}}'
        retry_text = chat(
            system=system_prompt,
            user_message=retry_msg,
            max_tokens=2000,
            api_key=api_key,
        )
        retry_clues = _parse_clues_from_response(retry_text, missing)
        result.update(retry_clues)

    still_missing = [w for w in words if w.upper() not in result]
    if still_missing:
        print(f'[clue_generator] Still missing after retry: {still_missing}')

    return result


def generate_clues(placed_words, summary, api_key=None):
    """Use an LLM to generate crossword-style clues for placed words.

    Themed words get article-context clues; fill words get generic crossword clues.
    If there are many words, they are batched into multiple LLM calls.

    Args:
        placed_words: list of PlacedWord objects (must have .word and .is_themed)
        summary: Article summary for context
        api_key: Optional Anthropic API key (uses Ollama if available)

    Returns:
        dict mapping uppercase word strings to clue strings
    """
    themed = [pw for pw in placed_words if getattr(pw, 'is_themed', True)]
    fill = [pw for pw in placed_words if not getattr(pw, 'is_themed', True)]

    result = {}

    # Generate clues for themed words (with article context)
    if themed:
        themed_words = [pw.word for pw in themed]
        # Batch themed words in groups of 15
        for i in range(0, len(themed_words), 15):
            batch = themed_words[i:i + 15]
            word_list_str = ', '.join(batch)
            example_word = batch[0]

            user_message = f"""I have a crossword puzzle themed around this topic:
"{summary}"

Write clues for these crossword answers. Use standard crossword conventions:
- Brief, typically 3-10 words per clue
- Use wordplay, definitions, or fill-in-the-blank where appropriate
- Reference the article's theme when it makes sense
- Vary difficulty levels (some easy, some tricky)
- Every clue must be solvable by a knowledgeable person
- Use standard crossword abbreviation hints (e.g., "Abbr." if the answer is an abbreviation)
- NEVER include the answer word itself in the clue. If you need to reference it, use a blank (___) instead

Answers to write clues for:
{word_list_str}

Return ONLY valid JSON mapping each answer (uppercase) to its clue:
{{
  "{example_word}": "Example clue here"
}}"""

            batch_clues = _generate_clue_batch(
                batch,
                'You are an expert crossword puzzle clue writer in the style of the New York Times crossword. Write concise, clever clues. Return only valid JSON.',
                user_message,
                api_key,
            )
            result.update(batch_clues)

    # Generate clues for fill words (with article theme for flavor)
    if fill:
        fill_words = [pw.word for pw in fill]
        for i in range(0, len(fill_words), 15):
            batch = fill_words[i:i + 15]
            word_list_str = ', '.join(batch)
            example_word = batch[0]

            user_message = f"""This crossword puzzle is themed around this topic:
"{summary}"

Write clues for these fill words. Use standard crossword conventions:
- Brief, typically 3-10 words per clue
- Use wordplay, definitions, or fill-in-the-blank where appropriate
- Where a word can plausibly connect to the article's theme, write a clue that ties into that theme (e.g., if the article is about space and the word is NET, clue it as "Safety device for astronaut training" rather than just "Fishing tool")
- Not every word needs a themed clue — if there's no natural connection, write a standard crossword clue instead
- Vary difficulty levels (some easy, some tricky)
- Every clue must be solvable by a knowledgeable person
- NEVER include the answer word itself in the clue. If you need to reference it, use a blank (___) instead

Answers:
{word_list_str}

Return ONLY valid JSON mapping each answer (uppercase) to its clue:
{{
  "{example_word}": "Example clue here"
}}"""

            batch_clues = _generate_clue_batch(
                batch,
                'You are an expert crossword puzzle clue writer in the style of the New York Times crossword. Write concise, clever clues. Return only valid JSON.',
                user_message,
                api_key,
            )
            result.update(batch_clues)

    # Fallback: retry missing words individually
    missing_words = [pw for pw in placed_words if pw.word.upper() not in result]
    if missing_words:
        print(f'[clue_generator] {len(missing_words)} words still missing clues, retrying individually')
        for pw in missing_words:
            w = pw.word.upper()
            try:
                fallback_text = chat(
                    system='You are a crossword clue writer. Return ONLY valid JSON.',
                    user_message=f'Write one crossword clue for the answer "{w}". NEVER include the answer word in the clue. Return JSON: {{"{w}": "your clue"}}',
                    max_tokens=200,
                    api_key=api_key,
                )
                fallback_clues = _parse_clues_from_response(fallback_text, [w])
                if w in fallback_clues:
                    result[w] = fallback_clues[w]
                    continue
            except Exception:
                pass
            # Last resort fallback
            result[w] = f'Crossword answer ({len(w)} letters)'

    return result
