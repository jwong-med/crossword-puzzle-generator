"""Unified LLM client that supports Anthropic API and local Ollama."""

import json
import requests


def chat(system, user_message, max_tokens=2000, api_key=None):
    """Send a chat request to either Ollama (local) or Anthropic API.

    Uses Ollama by default. Falls back to Anthropic only if api_key is provided
    and Ollama is not reachable.

    Args:
        system: System prompt string
        user_message: User message string
        max_tokens: Maximum tokens for response
        api_key: Optional Anthropic API key

    Returns:
        str: The model's response text
    """
    # Try Ollama first
    ollama_text = _try_ollama(system, user_message)
    if ollama_text is not None:
        return ollama_text

    # Fall back to Anthropic if we have a key
    if api_key and api_key != 'your-api-key-here':
        return _call_anthropic(system, user_message, max_tokens, api_key)

    raise RuntimeError(
        'No LLM available. Either start Ollama (ollama serve) or set ANTHROPIC_API_KEY in .env'
    )


def _try_ollama(system, user_message):
    """Try calling Ollama's local API. Returns response text or None if unavailable."""
    try:
        resp = requests.post(
            'http://localhost:11434/api/chat',
            json={
                'model': 'llama3.1:8b',
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user_message},
                ],
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'num_predict': 2000,
                },
            },
            timeout=120,
        )
        if resp.ok:
            data = resp.json()
            return data.get('message', {}).get('content', '')
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.Timeout:
        return None
    return None


def _call_anthropic(system, user_message, max_tokens, api_key):
    """Call Anthropic's Messages API directly via HTTP."""
    resp = requests.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': max_tokens,
            'system': system,
            'messages': [{'role': 'user', 'content': user_message}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data['content'][0]['text']
