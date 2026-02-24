# Schedule Agent Web

Browser-accessible **VueLogic** (scheduling agent): chat in plain language for CPM, WBS, DCMA 14-Point, re-sequencing, and what-if scenarios. The backend uses the scheduling-agent skill as the LLM system prompt.

## Quick start (local)

1. **From the repo root** (the folder that contains both `.cursor` and `schedule_agent_web`):

   ```bash
   cd schedule_agent_web
   pip install -r requirements.txt
   ```

2. **Set your OpenAI API key**

   - Copy `.env.example` to `.env` and set `OPENAI_API_KEY=sk-...`
   - Or: `set OPENAI_API_KEY=sk-...` (Windows) / `export OPENAI_API_KEY=sk-...` (Mac/Linux)

3. **Run the server**

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Open in a browser**

   - http://localhost:8000

You’ll see the chat UI; the backend loads the skill from `../.cursor/skills/scheduling-agent/SKILL.md` automatically.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for chat. |
| `OPENAI_CHAT_MODEL` | No | Model name (default: `gpt-4o-mini`). |
| `SCHEDULE_AGENT_SKILL_PATH` | No | Override path to `SKILL.md` (e.g. in Docker). |

## Deploying so it’s accessible via a web browser

Run the app on a server (cloud or on-prem) and open its URL in a browser.

### Vercel (recommended)

From the **repo root** (the folder that contains `schedule_agent_web`, `.cursor`, and `app.py`):

1. Push the repo to GitHub/GitLab/Bitbucket.
2. At [vercel.com/new](https://vercel.com/new), import the repo (leave Root Directory as repo root).
3. In the project **Settings → Environment Variables**, add `OPENAI_API_KEY` = `sk-...`.
4. Deploy. The chat UI is at `https://your-project.vercel.app`.

See **`.cursor/VERCEL_DEPLOY.md`** for step-by-step and troubleshooting.

### Option A: Docker

Example Dockerfile (run from **repo root** so `.cursor` is available):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY schedule_agent_web/requirements.txt ./schedule_agent_web/
RUN pip install --no-cache-dir -r schedule_agent_web/requirements.txt
COPY .cursor /app/.cursor
COPY schedule_agent_web /app/schedule_agent_web
WORKDIR /app/schedule_agent_web
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run (from repo root):

```bash
docker build -t schedule-agent-web .
docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... schedule-agent-web
```

Then open http://localhost:8000 (or your server’s hostname).

### Option B: Cloud / PaaS

- **Azure App Service**: Create a web app (Python 3.11), set `OPENAI_API_KEY` in Application settings, deploy this folder (or the whole repo) and set start command to `uvicorn main:app --host 0.0.0.0 --port 8000` (or the port your platform uses).
- **Railway / Render / Fly.io**: Connect the repo, set root or subfolder to `schedule_agent_web`, add `OPENAI_API_KEY`, and use start command `uvicorn main:app --host 0.0.0.0 --port 8000`. Ensure the deployed context includes the `.cursor/skills/scheduling-agent/SKILL.md` path (e.g. deploy from repo root and set working dir to `schedule_agent_web`, or set `SCHEDULE_AGENT_SKILL_PATH` to a path that includes the skill file).
- **AWS**: Use Elastic Beanstalk (Python) or Lambda + API Gateway with a small adapter; store the key in Secrets Manager or env.

### Option C: On-prem

- Run on a Windows or Linux server with Python 3.10+, e.g. `uvicorn main:app --host 0.0.0.0 --port 8000`, behind IIS or nginx if you want HTTPS and a stable hostname. Users open `http://your-server:8000` (or the URL you expose).

## API

- **GET /** — Serves the chat UI (index.html).
- **GET /health** — Returns `{"status":"ok","agent":"schedule-agent"}`.
- **POST /api/chat** — Body: `{"message": "user text", "history": [{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}`. Returns `{"reply": "assistant text", "error": null}` (or `error` set on failure).

## Security note

This app does not include authentication. For production, add auth (e.g. API key, OAuth, or VPN) and use HTTPS so the browser connection and `OPENAI_API_KEY` handling are secure.
