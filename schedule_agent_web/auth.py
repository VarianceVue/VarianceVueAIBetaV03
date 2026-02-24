"""
Authentication module for VueLogic.

Provides user registration, login, JWT token management, business email
validation, and multi-project support per client (company).

Data model:
  clients  — companies / organisations
  projects — each client can own multiple projects
  users    — belongs to one client; can access any project of that client
"""

import os
import re
import sqlite3
import hashlib
import secrets
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    import jwt  # PyJWT
except ImportError:
    jwt = None

try:
    import bcrypt
except ImportError:
    bcrypt = None


DB_DIR = Path(__file__).resolve().parent / "file_store"
DB_PATH = DB_DIR / "users.db"

JWT_SECRET = os.environ.get("VUELOGIC_JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

BLOCKED_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "yahoo.co.uk", "yahoo.co.in",
    "hotmail.com", "hotmail.co.uk", "outlook.com", "live.com",
    "msn.com", "aol.com", "icloud.com", "me.com", "mac.com",
    "mail.com", "protonmail.com", "proton.me", "zoho.com",
    "yandex.com", "yandex.ru", "gmx.com", "gmx.net",
    "inbox.com", "fastmail.com", "tutanota.com", "tuta.io",
    "mailinator.com", "guerrillamail.com", "tempmail.com",
    "rocketmail.com", "rediffmail.com",
}


# ── Database ────────────────────────────────────────────────────────────────

def _ensure_jwt_secret() -> str:
    global JWT_SECRET
    if JWT_SECRET:
        return JWT_SECRET
    secret_file = DB_DIR / ".jwt_secret"
    if secret_file.exists():
        JWT_SECRET = secret_file.read_text().strip()
    else:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        JWT_SECRET = secrets.token_hex(32)
        secret_file.write_text(JWT_SECRET)
    return JWT_SECRET


def _get_db() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys = ON")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            client_id   TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id  TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            client_id   TEXT NOT NULL REFERENCES clients(client_id),
            created_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name  TEXT    NOT NULL,
            last_name   TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            company     TEXT    NOT NULL,
            password    TEXT    NOT NULL,
            client_id   TEXT    DEFAULT NULL REFERENCES clients(client_id),
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Schema migration for older databases
    cols = {row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "client_id" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN client_id TEXT DEFAULT NULL REFERENCES clients(client_id)")
    if "role" not in cols:
        conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

    conn.commit()
    return conn


# ── Seed data ───────────────────────────────────────────────────────────────

_SEED_CLIENTS = [
    {"client_id": "VARIANCEVUE", "name": "VarianceVue"},
]

_SEED_PROJECTS = [
    {"project_id": "DEMO", "name": "Demo Project", "client_id": "VARIANCEVUE"},
]

_SEED_USERS = [
    {
        "email": "user1@variancevue.com",
        "client_id": "VARIANCEVUE",
        "first_name": "Trial",
        "last_name": "User",
        "company": "VarianceVue",
        "password": "VarianceVu3Tr14l",
        "role": "user",
    },
    {
        "email": "admin@variancevue.com",
        "client_id": "VARIANCEVUE",
        "first_name": "System",
        "last_name": "Admin",
        "company": "VarianceVue",
        "password": "Admin@2026!",
        "role": "admin",
    },
]


def _seed_db(conn: sqlite3.Connection) -> None:
    for c in _SEED_CLIENTS:
        if not conn.execute("SELECT 1 FROM clients WHERE client_id = ?", (c["client_id"],)).fetchone():
            conn.execute("INSERT INTO clients (client_id, name) VALUES (?, ?)", (c["client_id"], c["name"]))

    for p in _SEED_PROJECTS:
        if not conn.execute("SELECT 1 FROM projects WHERE project_id = ?", (p["project_id"],)).fetchone():
            conn.execute("INSERT INTO projects (project_id, name, client_id) VALUES (?, ?, ?)",
                         (p["project_id"], p["name"], p["client_id"]))

    for u in _SEED_USERS:
        if not conn.execute("SELECT 1 FROM users WHERE email = ?", (u["email"],)).fetchone():
            hashed = _hash_password(u["password"])
            conn.execute(
                "INSERT INTO users (first_name, last_name, email, company, password, client_id, role) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (u["first_name"], u["last_name"], u["email"], u["company"], hashed, u["client_id"], u.get("role", "user")),
            )
    conn.commit()


def ensure_seeded():
    db = _get_db()
    try:
        _seed_db(db)
    finally:
        db.close()


# ── Password helpers ────────────────────────────────────────────────────────

def _hash_password(plain: str) -> str:
    if bcrypt is not None:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 260_000)
    return f"pbkdf2:{salt}:{h.hex()}"


def _verify_password(plain: str, hashed: str) -> bool:
    if bcrypt is not None and hashed.startswith("$2"):
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    if hashed.startswith("pbkdf2:"):
        _, salt, digest = hashed.split(":", 2)
        h = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), 260_000)
        return secrets.compare_digest(h.hex(), digest)
    return False


# ── JWT helpers ─────────────────────────────────────────────────────────────

def _create_token(user_id: int, email: str, role: str = "user") -> str:
    secret = _ensure_jwt_secret()
    if jwt is None:
        payload = f"{user_id}:{email}:{role}:{int(time.time()) + JWT_EXPIRY_HOURS * 3600}"
        sig = hashlib.sha256((payload + secret).encode()).hexdigest()
        return f"{payload}:{sig}"
    exp = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS)
    return jwt.encode(
        {"sub": str(user_id), "email": email, "role": role, "exp": exp},
        secret,
        algorithm=JWT_ALGORITHM,
    )


def _decode_token(token: str) -> Optional[dict]:
    secret = _ensure_jwt_secret()
    if jwt is None:
        parts = token.rsplit(":", 1)
        if len(parts) != 2:
            return None
        payload, sig = parts
        expected = hashlib.sha256((payload + secret).encode()).hexdigest()
        if not secrets.compare_digest(sig, expected):
            return None
        segments = payload.split(":")
        if len(segments) == 4:
            uid_str, email, role, exp_str = segments
        else:
            uid_str, email, exp_str = segments[0], segments[1], segments[2]
            role = "user"
        if int(exp_str) < int(time.time()):
            return None
        return {"sub": int(uid_str), "email": email, "role": role}
    try:
        data = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        data["sub"] = int(data["sub"])
        if "role" not in data:
            data["role"] = "user"
        return data
    except Exception:
        return None


# ── Validation ──────────────────────────────────────────────────────────────

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_email(email: str) -> Optional[str]:
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return "Invalid email format."
    domain = email.split("@", 1)[1]
    if domain in BLOCKED_EMAIL_DOMAINS:
        return f"Personal email addresses (@{domain}) are not allowed. Please use your business email."
    return None


def validate_password(password: str) -> Optional[str]:
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return "Password must contain at least one digit."
    return None


# ── User dict helper ────────────────────────────────────────────────────────

def _user_dict(first_name, last_name, email, company, client_id, role="user") -> dict:
    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "company": company,
        "client_id": client_id,
        "role": role,
    }


# Maps email domains to client_ids (companies) for auto-assignment.
_DOMAIN_CLIENT_MAP: dict[str, str] = {
    "variancevue.com": "VARIANCEVUE",
}


def _resolve_client_id(conn: sqlite3.Connection, email: str) -> Optional[str]:
    domain = email.split("@", 1)[1].lower()
    cid = _DOMAIN_CLIENT_MAP.get(domain)
    if cid and conn.execute("SELECT 1 FROM clients WHERE client_id = ?", (cid,)).fetchone():
        return cid
    return None


# ── Registration & login ────────────────────────────────────────────────────

def register_user(first_name: str, last_name: str, email: str, company: str, password: str) -> dict:
    first_name = first_name.strip()
    last_name = last_name.strip()
    email = email.strip().lower()
    company = company.strip()

    if not first_name:
        return {"ok": False, "error": "First name is required."}
    if not last_name:
        return {"ok": False, "error": "Last name is required."}
    if not company:
        return {"ok": False, "error": "Company name is required."}

    email_err = validate_email(email)
    if email_err:
        return {"ok": False, "error": email_err}
    pwd_err = validate_password(password)
    if pwd_err:
        return {"ok": False, "error": pwd_err}

    hashed = _hash_password(password)
    db = _get_db()
    try:
        assigned_client = _resolve_client_id(db, email)
        db.execute(
            "INSERT INTO users (first_name, last_name, email, company, password, client_id) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name, last_name, email, company, hashed, assigned_client),
        )
        db.commit()
        row = db.execute("SELECT id, role FROM users WHERE email = ?", (email,)).fetchone()
        token = _create_token(row["id"], email, row["role"] or "user")
        return {"ok": True, "token": token, "user": _user_dict(first_name, last_name, email, company, assigned_client, row["role"] or "user")}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": "An account with this email already exists."}
    finally:
        db.close()


def login_user(email: str, password: str) -> dict:
    email = email.strip().lower()
    if not email or not password:
        return {"ok": False, "error": "Email and password are required."}

    db = _get_db()
    try:
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row is None or not _verify_password(password, row["password"]):
            return {"ok": False, "error": "Invalid email or password."}
        user_role = row["role"] if "role" in row.keys() else "user"
        token = _create_token(row["id"], email, user_role)
        return {
            "ok": True,
            "token": token,
            "user": _user_dict(row["first_name"], row["last_name"], row["email"], row["company"], row["client_id"], user_role),
        }
    finally:
        db.close()


def verify_token(token: str) -> Optional[dict]:
    payload = _decode_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    db = _get_db()
    try:
        row = db.execute("SELECT id, first_name, last_name, email, company, client_id, role FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        if "role" not in d or not d["role"]:
            d["role"] = "user"
        return d
    finally:
        db.close()


# ── Project queries ─────────────────────────────────────────────────────────

def get_projects_for_user(user_id: int) -> list[dict]:
    """Return all projects that belong to the user's client (company)."""
    db = _get_db()
    try:
        user = db.execute("SELECT client_id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or not user["client_id"]:
            return []
        rows = db.execute(
            "SELECT project_id, name FROM projects WHERE client_id = ? ORDER BY name",
            (user["client_id"],),
        ).fetchall()
        return [{"project_id": r["project_id"], "name": r["name"]} for r in rows]
    finally:
        db.close()


def get_projects_for_token(token: str) -> list[dict]:
    """Convenience: decode token then fetch projects."""
    payload = _decode_token(token)
    if not payload:
        return []
    uid = payload.get("sub")
    if uid is None:
        return []
    return get_projects_for_user(uid)


def create_project(project_id: str, name: str, client_id: Optional[str]) -> dict:
    """Create a new project under the given client. Returns {"ok": True, "project": {...}}."""
    project_id = project_id.strip().upper().replace(" ", "_")
    name = name.strip() or f"{project_id} Project"

    if not project_id:
        return {"ok": False, "error": "Project ID is required."}
    if len(project_id) < 2:
        return {"ok": False, "error": "Project ID must be at least 2 characters."}
    if not re.match(r"^[A-Z0-9_-]+$", project_id):
        return {"ok": False, "error": "Project ID may only contain letters, digits, hyphens, and underscores."}
    if not client_id:
        return {"ok": False, "error": "No company associated with your account."}

    db = _get_db()
    try:
        if db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,)).fetchone():
            return {"ok": False, "error": f"Project ID '{project_id}' already exists."}
        db.execute(
            "INSERT INTO projects (project_id, name, client_id) VALUES (?, ?, ?)",
            (project_id, name, client_id),
        )
        db.commit()
        return {"ok": True, "project": {"project_id": project_id, "name": name}}
    except sqlite3.IntegrityError:
        return {"ok": False, "error": f"Project ID '{project_id}' already exists."}
    finally:
        db.close()
