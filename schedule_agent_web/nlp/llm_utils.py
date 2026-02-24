"""
Shared LLM caller for NLP pipeline (Claude/OpenAI). Uses same env as main app.
"""
from __future__ import annotations

import os
from pathlib import Path


def _get_openai_key() -> str:
    raw = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_FILE")
    if raw and Path(raw).is_file():
        return Path(raw).read_text().strip()
    return raw or ""


def _get_anthropic_key() -> str:
    raw = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY_FILE")
    if raw and Path(raw).is_file():
        return Path(raw).read_text().strip()
    return raw or ""


def call_llm(system: str, user_message: str, max_tokens: int = 2048) -> tuple[str, str | None]:
    """
    Call Claude (preferred if key set) or OpenAI. Returns (reply_text, error).
    """
    messages = [{"role": "user", "content": user_message}]
    # Prefer Claude
    key = _get_anthropic_key()
    if key and len(key) > 10:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=key)
            model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            text = (resp.content[0].text if resp.content else "").strip()
            return (text, None)
        except Exception as e:
            return ("", str(e))
    # OpenAI
    key = _get_openai_key()
    if not key or len(key) < 10:
        return ("", "No API key. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        model = os.environ.get("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "system", "content": system}] + messages,
            temperature=0.3,
        )
        reply = (resp.choices[0].message.content or "").strip()
        return (reply, None)
    except Exception as e:
        return ("", str(e))
