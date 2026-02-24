"""
Stage 1 metadata extraction: from filename, size, date; optional rules for document_type / project_code.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def extract_metadata(
    filename: str,
    size_bytes: int,
    format_type: str,
    source: str = "upload",
    raw_text_preview: str = "",
) -> dict[str, Any]:
    """
    Build metadata dict: document_type, author, project_code, date, version, source, filename, size, format.
    Uses filename/size/format; optional simple rules from filename (e.g. PRJ-123_Scope_v2.pdf → project_code, version).
    """
    meta: dict[str, Any] = {
        "source": source,
        "filename": filename or "unknown",
        "size_bytes": size_bytes,
        "format": format_type,
        "ingested_at": datetime.utcnow().isoformat() + "Z",
    }
    # Optional: parse filename for project code / version (e.g. PRJ-001_Scope_v1.2.pdf, 12345-SOW.docx)
    name = (filename or "").strip()
    if name:
        # Project code: common patterns like PRJ-xxx, 12345-, SOW-, etc.
        project_match = re.search(r"([A-Z]{2,5}[-_]?\d{3,}|^\d{5,})", name, re.IGNORECASE)
        if project_match:
            meta["project_code"] = project_match.group(1).replace("_", "-")
        # Version: v1, v1.2, rev2, etc.
        version_match = re.search(r"[_\s](v\d+(?:\.\d+)?|rev\s*\d+)", name, re.IGNORECASE)
        if version_match:
            meta["version"] = version_match.group(1).strip()
        # Document type from extension or keywords
        lower = name.lower()
        if "scope" in lower or "sow" in lower:
            meta["document_type"] = "scope"
        elif "schedule" in lower or "xer" in lower or "p6" in lower:
            meta["document_type"] = "schedule"
        elif "rfi" in lower or "submittal" in lower:
            meta["document_type"] = "rfi_submittal"
        elif "risk" in lower:
            meta["document_type"] = "risk"
        else:
            meta["document_type"] = "site_photo" if format_type == "image" else format_type
    if not meta.get("project_code"):
        meta["project_code"] = None
    if not meta.get("version"):
        meta["version"] = None
    if not meta.get("author"):
        meta["author"] = None
    return meta
