"""
Claude with vision — describe site images for project progress understanding.
Requires ANTHROPIC_API_KEY. Uses Claude's image content block (base64).
"""
from __future__ import annotations

import base64
import os
from pathlib import Path


def _get_anthropic_key() -> str:
    raw = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY_FILE")
    if raw and Path(raw).is_file():
        return Path(raw).read_text().strip()
    return raw or ""


def describe_image(
    image_bytes: bytes,
    media_type: str = "image/jpeg",
    prompt: str = "Describe what you see in this image. If it looks like a construction or project site, summarize the visible progress, work in place, and any notable conditions (e.g. scaffolding, concrete, MEP, safety). Be concise.",
    max_tokens: int = 1024,
) -> tuple[str, str | None]:
    """
    Send image to Claude with vision; return (description_text, error).
    image_bytes: raw image bytes (JPEG, PNG, GIF, WebP).
    media_type: "image/jpeg", "image/png", "image/gif", "image/webp".
    """
    key = _get_anthropic_key()
    if not key or len(key) < 10:
        return ("", "ANTHROPIC_API_KEY not set. Get a key at console.anthropic.com.")
    try:
        from anthropic import Anthropic
    except ImportError:
        return ("", "anthropic package not installed. pip install anthropic.")

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")
    # Claude message content: image block + text block
    content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": b64},
        },
        {"type": "text", "text": prompt},
    ]
    model = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
    try:
        client = Anthropic(api_key=key)
        resp = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        text = (resp.content[0].text if resp.content else "").strip()
        return (text, None)
    except Exception as e:
        return ("", str(e))
