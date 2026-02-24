"""
Persistence for VueLogic: conversation history, lessons learned, trust score.
Uses Upstash Redis (Vercel KV). If UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN
are not set, all functions no-op or return empty/defaults.
"""
import os
import json
from datetime import datetime

_redis = None

def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    if not url or not token:
        return None
    try:
        from upstash_redis import Redis
        _redis = Redis(url=url, token=token)
        return _redis
    except Exception:
        return None


# --- Conversation (persisted so agent can learn from all chat) ---
CONV_KEY_PREFIX = "vuelogic:conv:"
CONV_MAX_LEN = 100


def _conv_local_path(session_id: str) -> str:
    """Path to conversation.json for this session (used when Redis unavailable)."""
    base = os.path.dirname(os.path.abspath(__file__))
    store = os.path.join(base, "file_store")
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (session_id or "default"))
    return os.path.join(store, safe, "conversation.json")


def _conv_local_get(session_id: str) -> list:
    if not session_id:
        return []
    try:
        path = _conv_local_path(session_id)
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _conv_local_append(session_id: str, role: str, content: str) -> None:
    if not session_id:
        return
    try:
        path = _conv_local_path(session_id)
        conv = _conv_local_get(session_id)
        conv.append({"role": role, "content": content or "", "created_at": datetime.utcnow().isoformat()})
        conv = conv[-CONV_MAX_LEN:]
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(conv, f, ensure_ascii=False, indent=0)
    except Exception:
        pass


def _conv_local_save(session_id: str, full_history: list) -> None:
    if not session_id:
        return
    try:
        path = _conv_local_path(session_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(full_history[-CONV_MAX_LEN:], f, ensure_ascii=False, indent=0)
    except Exception:
        pass


def get_conversation(session_id: str) -> list:
    """Return list of {role, content} for this session. Persisted in Redis or local file store."""
    r = _get_redis()
    if r and session_id:
        try:
            raw = r.get(CONV_KEY_PREFIX + session_id)
            if raw:
                return json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            pass
    return _conv_local_get(session_id)


def append_to_conversation(session_id: str, role: str, content: str) -> None:
    """Append one message; keep last CONV_MAX_LEN messages. Persisted in Redis or local file store."""
    if not session_id:
        return
    r = _get_redis()
    if r:
        try:
            conv = get_conversation(session_id)
            conv.append({"role": role, "content": content or "", "created_at": datetime.utcnow().isoformat()})
            conv = conv[-CONV_MAX_LEN:]
            r.set(CONV_KEY_PREFIX + session_id, json.dumps(conv))
            return
        except Exception:
            pass
    _conv_local_append(session_id, role, content)


def save_conversation(session_id: str, full_history: list) -> None:
    """Replace stored conversation with this list. Persisted in Redis or local file store."""
    if not session_id:
        return
    r = _get_redis()
    if r:
        try:
            r.set(CONV_KEY_PREFIX + session_id, json.dumps(full_history[-CONV_MAX_LEN:]))
            return
        except Exception:
            pass
    _conv_local_save(session_id, full_history)


# --- Lessons learned ---
LESSONS_KEY = "vuelogic:lessons"

def get_lessons() -> list:
    """Return list of lesson dicts (date, event, what_happened, outcome, lesson, recommendation)."""
    r = _get_redis()
    if not r:
        return []
    try:
        raw = r.get(LESSONS_KEY)
        if not raw:
            return []
        return json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return []


def append_lesson(entry: dict) -> None:
    """Append one lesson. entry should have event, what_happened, outcome, lesson, recommendation."""
    r = _get_redis()
    if not r:
        return
    try:
        lessons = get_lessons()
        entry = dict(entry)
        entry.setdefault("date", datetime.utcnow().strftime("%Y-%m-%d"))
        lessons.append(entry)
        r.set(LESSONS_KEY, json.dumps(lessons))
    except Exception:
        pass


# --- Trust score ---
TRUST_KEY = "vuelogic:trust_score"

def get_trust_score() -> dict:
    """Return { approvals, total_proposals, historical_accuracy, ai_agency_score }."""
    r = _get_redis()
    default = {"approvals": 0, "total_proposals": 0, "historical_accuracy": 1.0, "ai_agency_score": 0.0}
    if not r:
        return default
    try:
        raw = r.get(TRUST_KEY)
        if not raw:
            return default
        data = json.loads(raw) if isinstance(raw, str) else raw
        approvals = int(data.get("approvals", 0))
        total = int(data.get("total_proposals", 0))
        ha = float(data.get("historical_accuracy", 1.0))
        score = (approvals / total * ha) if total else 0.0
        data["ai_agency_score"] = round(score, 2)
        return data
    except Exception:
        return default


def record_proposal(approved: bool) -> None:
    """Record one proposal outcome: total_proposals += 1, approvals += 1 if approved."""
    r = _get_redis()
    if not r:
        return
    try:
        data = get_trust_score()
        data["total_proposals"] = data.get("total_proposals", 0) + 1
        if approved:
            data["approvals"] = data.get("approvals", 0) + 1
        r.set(TRUST_KEY, json.dumps(data))
    except Exception:
        pass


def is_persistence_available() -> bool:
    return _get_redis() is not None


# --- Conversation Digest (PCM review & vectorization governance) ---

def _digest_dir(session_id: str) -> str:
    base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "file_store", _safe_session(session_id), "digests")
    os.makedirs(d, exist_ok=True)
    return d


def _digest_path(session_id: str) -> str:
    return os.path.join(_digest_dir(session_id), "pending.json")


def _approved_path(session_id: str) -> str:
    return os.path.join(_digest_dir(session_id), "approved.json")


def _discarded_path(session_id: str) -> str:
    return os.path.join(_digest_dir(session_id), "discarded.json")


def _load_json(path: str) -> list:
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_json(path: str, data: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_pending_digest(session_id: str) -> list:
    """Return pending digest items awaiting PCM review.
    Each item: {id, timestamp, topic, summary, messages: [{role,content}], priority, status}
    """
    return _load_json(_digest_path(session_id))


def save_pending_digest(session_id: str, items: list) -> None:
    """Replace pending digest with new items."""
    _save_json(_digest_path(session_id), items)


def append_pending_digest(session_id: str, item: dict) -> None:
    """Add one item to the pending digest."""
    items = get_pending_digest(session_id)
    items.append(item)
    save_pending_digest(session_id, items)


def approve_digest_items(session_id: str, item_ids: list[str]) -> list[dict]:
    """Move items from pending or discarded to approved. Returns the approved items."""
    ids = set(item_ids)
    pending = get_pending_digest(session_id)
    discarded_log = _load_json(_discarded_path(session_id))
    approved_log = _load_json(_approved_path(session_id))

    to_approve = [i for i in pending if i.get("id") in ids]
    remaining_pending = [i for i in pending if i.get("id") not in ids]

    from_discarded = [i for i in discarded_log if i.get("id") in ids]
    remaining_discarded = [i for i in discarded_log if i.get("id") not in ids]

    to_approve.extend(from_discarded)

    for item in to_approve:
        item["status"] = "approved"
        item["approved_at"] = datetime.utcnow().isoformat()
        item.pop("discarded_at", None)
        approved_log.append(item)

    save_pending_digest(session_id, remaining_pending)
    _save_json(_discarded_path(session_id), remaining_discarded)
    _save_json(_approved_path(session_id), approved_log)
    return to_approve


def discard_digest_items(session_id: str, item_ids: list[str]) -> int:
    """Move items from pending or approved to discarded log (30-day retention). Returns count discarded."""
    ids = set(item_ids)
    pending = get_pending_digest(session_id)
    approved_log = _load_json(_approved_path(session_id))
    discarded_log = _load_json(_discarded_path(session_id))

    to_discard = [i for i in pending if i.get("id") in ids]
    remaining_pending = [i for i in pending if i.get("id") not in ids]

    from_approved = [i for i in approved_log if i.get("id") in ids]
    remaining_approved = [i for i in approved_log if i.get("id") not in ids]

    to_discard.extend(from_approved)

    for item in to_discard:
        item["status"] = "discarded"
        item["discarded_at"] = datetime.utcnow().isoformat()
        item.pop("approved_at", None)
        discarded_log.append(item)

    save_pending_digest(session_id, remaining_pending)
    _save_json(_approved_path(session_id), remaining_approved)
    _save_json(_discarded_path(session_id), discarded_log)
    return len(to_discard)


def get_discarded_log(session_id: str) -> list:
    """Return discarded digest items (within 30-day retention)."""
    purge_expired_discards(session_id)
    return _load_json(_discarded_path(session_id))


def get_approved_log(session_id: str) -> list:
    """Return all approved (vectorized) digest items."""
    return _load_json(_approved_path(session_id))


def purge_expired_discards(session_id: str) -> int:
    """Remove discarded items older than 30 days. Returns count purged."""
    items = _load_json(_discarded_path(session_id))
    if not items:
        return 0
    from datetime import timedelta
    cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
    kept = [i for i in items if (i.get("discarded_at") or "") >= cutoff]
    purged = len(items) - len(kept)
    if purged > 0:
        _save_json(_discarded_path(session_id), kept)
    return purged


# --- Files (project documents) ---
FILES_KEY_PREFIX = "vuelogic:files:"
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB per file (no practical limit for uploads)

# Local file fallback when Redis is not configured (e.g. run_desktop.bat without Upstash)
def _file_store_dir():
    """Directory for local file store (used when Redis unavailable)."""
    base = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(base, "file_store")
    try:
        os.makedirs(out, exist_ok=True)
    except Exception:
        pass
    return out


def _safe_session(session_id: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in (session_id or "default"))


def _safe_filename(filename: str) -> str:
    name = (filename or "file").replace("\\", "_").replace("/", "_").replace("..", "_").strip()
    return name if name else "file"


def _get_files_meta_path(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "meta.json")


def _get_file_content_path(session_id: str, filename: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "contents", _safe_filename(filename))


def _files_local_get(session_id: str) -> list:
    if not session_id:
        return []
    try:
        path = _get_files_meta_path(session_id)
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _files_local_save(session_id: str, filename: str, content: str) -> dict | None:
    if not session_id or content is None:
        return None
    try:
        content_str = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
        content_bytes = content_str.encode("utf-8")
        if len(content_bytes) > MAX_FILE_SIZE:
            return None
        root = os.path.join(_file_store_dir(), _safe_session(session_id))
        contents_dir = os.path.join(root, "contents")
        os.makedirs(contents_dir, exist_ok=True)
        meta_path = os.path.join(root, "meta.json")
        files = _files_local_get(session_id)
        existing = [f for f in files if f.get("filename") == filename]
        old_meta = existing[0] if existing else {}
        files = [f for f in files if f.get("filename") != filename]
        file_info = {
            "filename": filename,
            "size": len(content_bytes),
            "uploaded_at": datetime.utcnow().isoformat(),
            "category": old_meta.get("category", ""),
            "vectorized": old_meta.get("vectorized", False),
        }
        files.append(file_info)
        content_path = _get_file_content_path(session_id, filename)
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(content_str)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(files, f, indent=0)
        return file_info
    except Exception:
        return None


def _files_local_get_content(session_id: str, filename: str) -> str | None:
    if not session_id:
        return None
    try:
        path = _get_file_content_path(session_id, filename)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _files_local_delete(session_id: str, filename: str) -> bool:
    if not session_id:
        return False
    try:
        files = _files_local_get(session_id)
        files = [f for f in files if f.get("filename") != filename]
        meta_path = _get_files_meta_path(session_id)
        content_path = _get_file_content_path(session_id, filename)
        if os.path.isfile(content_path):
            os.remove(content_path)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(files, f, indent=0)
        return True
    except Exception:
        return False


def update_file_meta(session_id: str, filename: str, **kwargs) -> bool:
    """Update metadata fields (category, vectorized, etc.) for a stored file."""
    if not session_id or not filename:
        return False
    files = _files_local_get(session_id)
    found = False
    for f in files:
        if f.get("filename") == filename:
            for k, v in kwargs.items():
                f[k] = v
            found = True
            break
    if not found:
        return False
    try:
        meta_path = _get_files_meta_path(session_id)
        with open(meta_path, "w", encoding="utf-8") as f_out:
            json.dump(files, f_out, indent=0)
        return True
    except Exception:
        return False


def get_files(session_id: str) -> list:
    """Return list of {filename, size, uploaded_at, category, vectorized} for this session."""
    r = _get_redis()
    if r:
        try:
            raw = r.get(FILES_KEY_PREFIX + session_id)
            if not raw:
                return []
            return json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return []
    return _files_local_get(session_id)


def save_file(session_id: str, filename: str, content: str) -> dict | None:
    """Save file content. Returns {filename, size, uploaded_at} or None if too large. Uses Redis or local file store."""
    if not session_id or content is None:
        return None
    content_str = content if isinstance(content, str) else None
    if content_str is None:
        try:
            content_str = content.decode("utf-8", errors="replace")
        except Exception:
            return None
    r = _get_redis()
    if r:
        try:
            content_bytes = content_str.encode("utf-8")
            if len(content_bytes) > MAX_FILE_SIZE:
                return None
            files = get_files(session_id)
            file_info = {"filename": filename, "size": len(content_bytes), "uploaded_at": datetime.utcnow().isoformat()}
            files = [f for f in files if f.get("filename") != filename]
            files.append(file_info)
            r.set(FILES_KEY_PREFIX + session_id, json.dumps(files))
            r.set(FILES_KEY_PREFIX + session_id + ":content:" + filename, content_str)
            return file_info
        except Exception:
            return None
    return _files_local_save(session_id, filename, content_str)


def get_file_content(session_id: str, filename: str) -> str | None:
    """Return file content as string, or None if not found."""
    r = _get_redis()
    if r:
        try:
            raw = r.get(FILES_KEY_PREFIX + session_id + ":content:" + filename)
            return raw if isinstance(raw, str) else None
        except Exception:
            return None
    return _files_local_get_content(session_id, filename)


def delete_file(session_id: str, filename: str) -> bool:
    """Delete file and its entry. Returns True if deleted."""
    r = _get_redis()
    if r:
        try:
            files = get_files(session_id)
            files = [f for f in files if f.get("filename") != filename]
            r.set(FILES_KEY_PREFIX + session_id, json.dumps(files))
            r.delete(FILES_KEY_PREFIX + session_id + ":content:" + filename)
            return True
        except Exception:
            return False
    return _files_local_delete(session_id, filename)


# --- Extracted schedule (activities, WBS) per session ---
SCHEDULE_KEY_PREFIX = "vuelogic:schedule:"


def save_schedule(session_id: str, data: dict) -> bool:
    """Save extracted schedule { activities, wbs?, projectName? } for this session. Works with Redis or local file store."""
    if not session_id:
        return False
    try:
        payload = json.dumps(data)
    except Exception:
        return False
    r = _get_redis()
    if r:
        try:
            r.set(SCHEDULE_KEY_PREFIX + session_id, payload)
            return True
        except Exception:
            return False
    # Local file store
    try:
        root = os.path.join(_file_store_dir(), _safe_session(session_id))
        os.makedirs(root, exist_ok=True)
        path = os.path.join(root, "schedule.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(payload)
        return True
    except Exception:
        return False


def get_schedule(session_id: str) -> dict | None:
    """Return saved schedule { activities, wbs?, projectName? } or None."""
    if not session_id:
        return None
    r = _get_redis()
    if r:
        try:
            raw = r.get(SCHEDULE_KEY_PREFIX + session_id)
            if not raw:
                return None
            return json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return None
    try:
        root = os.path.join(_file_store_dir(), _safe_session(session_id))
        path = os.path.join(root, "schedule.json")
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


# --- Generated documents (schedule basis, etc.) from chat — persistent for download ---
DOCS_KEY_PREFIX = "vuelogic:docs:"
DOCS_LIST_KEY_SUFFIX = ":list"


def _docs_local_dir(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "generated_docs")


def _docs_local_meta_path(session_id: str) -> str:
    return os.path.join(_docs_local_dir(session_id), "meta.json")


def _docs_local_content_path(session_id: str, doc_id: str) -> str:
    return os.path.join(_docs_local_dir(session_id), f"{_safe_filename(doc_id)}.md")


def _generate_doc_id() -> str:
    import time
    return f"doc-{int(time.time() * 1000)}-{os.urandom(4).hex()}"


def save_generated_document(session_id: str, title: str, content: str) -> dict | None:
    """Save a generated document (e.g. schedule basis from chat). Returns { id, title, created_at } or None."""
    if not session_id or not title:
        return None
    doc_id = _generate_doc_id()
    created_at = datetime.utcnow().isoformat()
    entry = {"id": doc_id, "title": title[:200], "created_at": created_at}
    r = _get_redis()
    if r:
        try:
            key_list = DOCS_KEY_PREFIX + session_id + DOCS_LIST_KEY_SUFFIX
            key_content = DOCS_KEY_PREFIX + session_id + ":" + doc_id
            raw = r.get(key_list)
            docs = json.loads(raw) if raw else []
            docs.append(entry)
            r.set(key_list, json.dumps(docs))
            r.set(key_content, content or "")
            return entry
        except Exception:
            return None
    try:
        root = _docs_local_dir(session_id)
        os.makedirs(root, exist_ok=True)
        meta_path = _docs_local_meta_path(session_id)
        docs = []
        if os.path.isfile(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                docs = json.load(f)
        docs.append(entry)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(docs, f, ensure_ascii=False, indent=0)
        with open(_docs_local_content_path(session_id, doc_id), "w", encoding="utf-8") as f:
            f.write(content or "")
        return entry
    except Exception:
        return None


def get_generated_documents(session_id: str) -> list:
    """Return list of { id, title, created_at } for this session."""
    if not session_id:
        return []
    r = _get_redis()
    if r:
        try:
            raw = r.get(DOCS_KEY_PREFIX + session_id + DOCS_LIST_KEY_SUFFIX)
            if not raw:
                return []
            return json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return []
    try:
        path = _docs_local_meta_path(session_id)
        if not os.path.isfile(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_generated_document_content(session_id: str, doc_id: str) -> str | None:
    """Return document content or None."""
    if not session_id or not doc_id:
        return None
    r = _get_redis()
    if r:
        try:
            raw = r.get(DOCS_KEY_PREFIX + session_id + ":" + doc_id)
            return raw if isinstance(raw, str) else None
        except Exception:
            return None
    try:
        path = _docs_local_content_path(session_id, doc_id)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


# ── Philosophy settings persistence ─────────────────────────────────────────
PHILOSOPHY_DEFAULTS = {
    "governance": {
        "missingLogicTolerance": 5,
        "highFloatDays": 44,
        "highDurationDays": 20,
        "negativeLagTolerance": 0,
        "hardConstraintTolerance": 5,
        "complianceStandard": "dcma",
        "narrativeTone": "Executive",
        "rules": {
            "leadRestriction": True,
            "sfBan": True,
            "hardConstraintAudit": True,
            "calendarCheck": False,
            "fsPreferred": False,
        },
    },
    "basis": {
        "deliveryMethod": "Design-Build",
        "ntpDate": "",
        "completionDate": "",
        "wbsDriver": "area",
        "wbsLevels": 4,
        "wbsRationale": "",
        "workWeek": "5-day",
        "hoursPerDay": 8,
        "shiftsPerDay": 1,
        "weatherNotes": "",
        "milestones": [],
        "logicRationale": {"fsPref": "", "zeroLead": "", "floatThreshold": ""},
        "costLoadingLevel": "work-package",
        "costLoadingNotes": "",
    },
    "playbook": {
        "reviewStandard": "approve-noted",
        "maxDefectsBeforeReject": 20,
        "missingScopeThreshold": 10,
        "checklist": {
            "scopeCompleteness": True,
            "logicIntegrity": True,
            "floatReasonableness": True,
            "costLoading": True,
            "calendarAssignments": True,
            "milestoneAlignment": False,
            "ownerActivityModeling": False,
            "durationReasonableness": False,
        },
        "ownerActivities": [
            {"name": "Permit Approvals", "duration": 30, "required": True},
            {"name": "Design Reviews", "duration": 14, "required": True},
            {"name": "Inspections (Progressive)", "duration": 5, "required": True},
            {"name": "Third-Party Coordination", "duration": 21, "required": False},
            {"name": "Utility Coordination", "duration": 45, "required": True},
        ],
    },
}


def _philosophy_path(session_id: str) -> str:
    return os.path.join(_file_store_dir(), _safe_session(session_id), "philosophy.json")


def get_philosophy(session_id: str) -> dict:
    """Load philosophy settings for a project, returning defaults for any missing keys."""
    import copy
    defaults = copy.deepcopy(PHILOSOPHY_DEFAULTS)
    if not session_id:
        return defaults
    path = _philosophy_path(session_id)
    if not os.path.isfile(path):
        return defaults
    try:
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for section in defaults:
            if section in saved:
                if isinstance(defaults[section], dict):
                    defaults[section].update(saved[section])
                else:
                    defaults[section] = saved[section]
        return defaults
    except Exception:
        return defaults


def save_philosophy(session_id: str, data: dict) -> bool:
    """Save philosophy settings for a project."""
    if not session_id:
        return False
    path = _philosophy_path(session_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False
