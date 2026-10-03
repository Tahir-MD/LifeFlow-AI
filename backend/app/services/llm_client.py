"""
Optional real-LLM upgrade path, using Groq.

Every AI feature in this project (report analyzer, chatbot) ships
with a rule-based engine (regex + keyword matching) in
`ai_analyzer_service.py` and `chatbot_service.py`, so the whole app
works out of the box with no API key, no cost, and no external calls.

If you want to upgrade the *free-text understanding* of those two
features to a real large language model, set the GROQ_API_KEY
environment variable (get one free at https://console.groq.com).
`call_llm_json` will then be used automatically -- nothing else in
the codebase needs to change. Without a key, this module quietly
does nothing and the rule-based engine is used, so leaving it unset
is completely safe. No extra package install is needed either way --
this talks to Groq's REST API directly over Python's standard
library, so there is nothing to add to requirements.txt.
"""
import json
import os
import urllib.request
import urllib.error
from typing import Optional

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"


def call_llm_json(system_prompt: str, user_message: str) -> Optional[dict]:
    """
    Sends one message to Groq and expects a JSON object back. Returns
    None (never raises) if no API key is configured or the call
    fails for any reason -- callers should always have a rule-based
    fallback ready.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    model = os.environ.get("GROQ_MODEL", GROQ_DEFAULT_MODEL)
    body = json.dumps({
        "model": model,
        "max_tokens": 500,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }).encode("utf-8")

    request = urllib.request.Request(
        GROQ_API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = payload["choices"][0]["message"]["content"]
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
        return None
