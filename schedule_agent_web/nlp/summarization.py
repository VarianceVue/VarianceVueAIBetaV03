"""
Stage 3: Summarization — short abstractive summary via LLM.
"""
from __future__ import annotations

from schedule_agent_web.nlp.llm_utils import call_llm


def summarize_text(text: str, max_chars: int = 12000) -> str:
    """
    Produce a 2–4 sentence summary of the text. Uses LLM. Returns summary string or empty on failure.
    """
    if not (text or "").strip():
        return ""
    sample = (text or "")[:max_chars]
    system = (
        "You are a project controls analyst. Summarize the following document in 2 to 4 concise sentences. "
        "Focus on: scope, key dates, responsibilities, risks, or changes mentioned. Output only the summary, no preamble."
    )
    reply, err = call_llm(system, sample, max_tokens=512)
    if err:
        return ""
    return (reply or "").strip()
