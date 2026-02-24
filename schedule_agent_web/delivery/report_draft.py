"""
Stage 5: Report drafting — LLM + template + RAG + structured NLP outputs.
"""
from __future__ import annotations

from typing import Any

from schedule_agent_web.nlp.llm_utils import call_llm


def build_report_context(
    session_id: str,
    max_rag_chars: int = 4000,
    max_summaries: int = 10,
    max_signals: int = 20,
) -> str:
    """Gather RAG-relevant text, NLP summaries, and signals for report context."""
    parts = []
    try:
        from schedule_agent_web.intelligence import list_signals
        from schedule_agent_web.nlp import list_nlp_documents, get_nlp_document
        signals = list_signals(session_id)[-max_signals:]
        if signals:
            parts.append("## Recent signals (risk/change/dispute)\n")
            for s in signals:
                parts.append(f"- [{s.get('signal_type', '')}] {s.get('text_snippet', '')[:200]}\n")
        nlp_list = list_nlp_documents(session_id)
        for item in nlp_list[:max_summaries]:
            doc_id = item.get("doc_id")
            if not doc_id:
                continue
            doc = get_nlp_document(session_id, doc_id)
            if doc and doc.summary:
                parts.append(f"\n## Doc {doc_id}\nSummary: {doc.summary[:500]}\n")
    except Exception:
        pass
    return "\n".join(parts) if parts else "No signals or NLP summaries available for this session."


def draft_report(
    session_id: str,
    title: str,
    template_hint: str = "",
    rag_query: str = "project scope, schedule, risks, changes",
    max_tokens: int = 2048,
) -> tuple[str, str | None]:
    """
    Generate a report draft using LLM with context from signals + NLP summaries.
    Optionally pass template_hint (e.g. "weekly status", "risk summary"). 
    Returns (draft_text, error).
    """
    context = build_report_context(session_id)
    system = (
        "You are a project controls analyst. Generate a concise report based on the following context. "
        "Use clear sections and bullet points. Do not invent data not present in the context. "
    )
    if template_hint:
        system += f"Report style: {template_hint}. "
    user = f"Report title: {title}\n\nContext:\n{context}\n\nProduce the report draft."
    return call_llm(system, user, max_tokens=max_tokens)
