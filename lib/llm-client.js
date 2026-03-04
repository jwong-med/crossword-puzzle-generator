/**
 * Unified LLM client that supports Anthropic API and local Ollama.
 *
 * Faithful port of llm_client.py.
 */

import axios from 'axios';

/**
 * Send a chat request to either Ollama (local) or Anthropic API.
 *
 * Uses Ollama by default. Falls back to Anthropic only if apiKey is provided
 * and Ollama is not reachable.
 *
 * @param {object} opts
 * @param {string} opts.system - System prompt
 * @param {string} opts.userMessage - User message
 * @param {number} [opts.maxTokens=2000] - Max tokens for response
 * @param {string|null} [opts.apiKey=null] - Optional Anthropic API key
 * @returns {Promise<string>} The model's response text
 */
async function chat({ system, userMessage, maxTokens = 2000, apiKey = null }) {
  // Try Ollama first
  const ollamaText = await _tryOllama(system, userMessage);
  if (ollamaText !== null) return ollamaText;

  // Fall back to Anthropic if we have a key
  if (apiKey && apiKey !== 'your-api-key-here') {
    return _callAnthropic(system, userMessage, maxTokens, apiKey);
  }

  throw new Error(
    'No LLM available. Either start Ollama (ollama serve) or set ANTHROPIC_API_KEY in .env'
  );
}

async function _tryOllama(system, userMessage) {
  try {
    const resp = await axios.post(
      'http://localhost:11434/api/chat',
      {
        model: 'llama3.1:8b',
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: userMessage },
        ],
        stream: false,
        options: {
          temperature: 0.7,
          num_predict: 2000,
        },
      },
      { timeout: 120_000 }
    );
    if (resp.status === 200) {
      return resp.data?.message?.content ?? '';
    }
  } catch (err) {
    if (err.code === 'ECONNREFUSED' || err.code === 'ECONNRESET' || err.code === 'ENOTFOUND') {
      return null;
    }
    if (err.code === 'ECONNABORTED') {
      return null; // timeout
    }
    // For axios errors with no response (network errors), return null
    if (!err.response) return null;
  }
  return null;
}

async function _callAnthropic(system, userMessage, maxTokens, apiKey) {
  const resp = await axios.post(
    'https://api.anthropic.com/v1/messages',
    {
      model: 'claude-sonnet-4-20250514',
      max_tokens: maxTokens,
      system,
      messages: [{ role: 'user', content: userMessage }],
    },
    {
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      timeout: 60_000,
    }
  );
  return resp.data.content[0].text;
}

export { chat };
