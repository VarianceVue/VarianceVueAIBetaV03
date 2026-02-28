# AGENTS.md

## Cursor Cloud specific instructions

### Application overview

VueLogic (VarianceVueAI) is a Python/FastAPI web application for AI-driven project controls (scheduling, cost, risk, MEP/commissioning). The frontend is a React 19 SPA served from `schedule_agent_web/static/` — there is no separate frontend build step or npm project.

### Running the dev server

```
python3 -m uvicorn schedule_agent_web.main:app --reload --host 0.0.0.0 --port 8000
```

The app is then available at `http://localhost:8000`. Hot reload is enabled with `--reload`.

### Environment variables

Copy `.env.example` to `.env` at the repo root. At minimum, set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` for AI chat to work. Without a valid LLM key the app starts and the UI is fully functional, but chat responses will fail with "No response received from the server."

### Authentication & seeded data

On first startup the app auto-creates an SQLite database at `schedule_agent_web/file_store/users.db` and seeds it with:
- Client: `VARIANCEVUE`
- Project: `DEMO` (under VARIANCEVUE)
- User: `user1@variancevue.com` / `VivekVueTr14l` (role: user)
- Admin: `admin@variancevue.com` / `Admin@2026!` (role: admin)

New user registration only associates a client if the email domain is in `_DOMAIN_CLIENT_MAP` (currently only `variancevue.com`). Other domains register successfully but cannot create projects (no client association).

### Lint, tests, and build

This codebase currently has **no linter configuration**, **no automated test suite**, and **no build step**. The frontend is pre-built static HTML/JS loaded via CDN.

### Key gotchas

- Use `python3` not `python` (the VM may not have `python` symlinked).
- `uvicorn` installs to `~/.local/bin`; ensure `PATH` includes it or run via `python3 -m uvicorn`.
- The `.env` file at the repo root is loaded automatically by `python-dotenv` in `main.py`.
- SQLite database and file store are created under `schedule_agent_web/file_store/` — this directory is gitignored and ephemeral in cloud environments.
- Optional services (Qdrant, Upstash Redis, GraphRAG) degrade gracefully — the app falls back to local file store and keyword search.
- FastAPI auto-serves Swagger UI at `/docs` and ReDoc at `/redoc` (unauthenticated).
- The frontend is a single `index.html` (~4800 lines) with inline JS/CSS plus a minified React bundle in `static/assets/`. No npm or build tooling is needed.
- To test the full login-to-chat flow, use the seeded user `user1@variancevue.com` / `VivekVueTr14l` which has the `VARIANCEVUE` client and `DEMO` project pre-associated.
