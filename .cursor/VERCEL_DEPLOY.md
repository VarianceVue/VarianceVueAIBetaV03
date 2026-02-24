# Deploy Schedule Agent to Vercel

Deploy the **Schedule Agent (VueLogic)** so it’s accessible in a browser on Vercel.

## Prerequisites

- Vercel account ([vercel.com](https://vercel.com))
- **One** of:
  - **Claude (Anthropic) API key** — [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) — recommended if OpenAI billing is an issue
  - **OpenAI API key** — [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## Deploy steps

### 1. Push the repo to Git (if not already)

Vercel deploys from Git (GitHub, GitLab, or Bitbucket). Commit and push this project so Vercel can connect to it.

### 2. Import the project in Vercel

1. Go to [vercel.com/new](https://vercel.com/new).
2. **Import** your repository (the one that contains `app.py`, `schedule_agent_web/`, `.cursor/`, `public/`, `vercel.json`, `requirements.txt`).
3. Leave **Root Directory** as the repo root (don’t set it to `schedule_agent_web`).
4. **Framework Preset**: Vercel should auto-detect (Python/FastAPI). If it picks something else, you can set it to **Other** or leave as detected.
5. Do **not** override Build Command or Output Directory unless you have a reason.

### 3. Set environment variables

In the Vercel project: **Settings → Environment Variables**, add **one** of these:

**Option A — Claude (recommended if OpenAI quota/billing is an issue):**

| Name                | Value           | Environments   |
|---------------------|-----------------|----------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...`    | Production, Preview |

Get a key at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys). Optionally set `ANTHROPIC_MODEL` (default: `claude-3-5-sonnet-latest`).

**Option B — OpenAI:**

| Name              | Value        | Environments   |
|-------------------|-------------|-----------------|
| `OPENAI_API_KEY`  | `sk-...`    | Production, Preview |

Optionally: `OPENAI_CHAT_MODEL` — e.g. `gpt-4o` (default is `gpt-4o-mini`).

If **both** are set, the app uses **Claude**.

Then **Save**.

### 4. Deploy

- If you just imported: click **Deploy**.
- For later updates: push to your connected branch; Vercel will redeploy automatically.

### 5. Open the app

When the deployment finishes, open the **Visit** URL (e.g. `https://your-project.vercel.app`). You should see the Schedule Agent chat UI. The page is served from `public/index.html`; the chat calls `/api/chat`, which runs the FastAPI app and the scheduling skill.

## What gets deployed

| Item | Role |
|------|------|
| **app.py** (root) | Vercel FastAPI entrypoint; imports `schedule_agent_web.main.app`. |
| **schedule_agent_web/main.py** | Defines `/api/chat` and `/health`, loads `.cursor/skills/scheduling-agent/SKILL.md`. |
| **public/index.html** | Chat UI; served at `/` by Vercel CDN. |
| **.cursor/skills/scheduling-agent/SKILL.md** | Shipped with the app; used as the LLM system prompt. |
| **requirements.txt** (root) | Python dependencies for the serverless function. |

## Local test before deploy

```bash
# From repo root
pip install -r requirements.txt
set OPENAI_API_KEY=sk-your-key
vercel dev
```

Then open the URL shown (e.g. http://localhost:3000). Requires [Vercel CLI](https://vercel.com/docs/cli) (`npm i -g vercel`).

## Troubleshooting

- **“OPENAI_API_KEY not set”**  
  Add `OPENAI_API_KEY` in Vercel → Project → Settings → Environment Variables, then redeploy.

- **“Skill file not found”**  
  Deploy must be from the **repo root** so that `.cursor/skills/scheduling-agent/SKILL.md` is in the bundle. Don’t set Root Directory to a subfolder.

- **Build fails**  
  Ensure `requirements.txt` is at the repo root and that `app.py` exists at the root and contains `from schedule_agent_web.main import app`.

- **Python version**  
  To pin Python (e.g. 3.12), add a `.python-version` file with `3.12` in the repo root, or set it in Project Settings on Vercel.
