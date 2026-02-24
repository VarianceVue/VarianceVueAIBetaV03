# VueLogic persistence: conversation history, lessons learned, trust score

To persist conversation history, lessons learned, and trust score across redeploys, add **Upstash Redis** (used by Vercel for KV storage) and set the environment variables.

## 1. Create Upstash Redis

1. Go to **[console.upstash.com](https://console.upstash.com)** and sign in (or create an account).
2. Create a new **Redis** database (free tier is enough).
3. In the database dashboard, copy:
   - **UPSTASH_REDIS_REST_URL**
   - **UPSTASH_REDIS_REST_TOKEN**

## 2. Add env vars in Vercel

1. Vercel → your project → **Settings** → **Environment Variables**.
2. Add:
   - **Name:** `UPSTASH_REDIS_REST_URL`  
     **Value:** (paste the URL from Upstash)
   - **Name:** `UPSTASH_REDIS_REST_TOKEN`  
     **Value:** (paste the token from Upstash)
3. Enable **Production** (and **Preview** if you use preview deployments).
4. Save, then **redeploy** the project.

## 3. What gets stored

| Data | Key / API | Notes |
|------|-----------|--------|
| **Conversation history** | `vuelogic:conv:{session_id}` | Last 100 messages per session. Session ID is generated in the browser (localStorage). |
| **Lessons learned** | `vuelogic:lessons` | List of entries (event, what_happened, outcome, lesson, recommendation). VueLogic uses these in its system prompt when proposing options. |
| **Trust score** | `vuelogic:trust_score` | `approvals`, `total_proposals`, `historical_accuracy`. AI_Agency_Score is computed and shown; VueLogic uses it to decide Level 1 vs 2/3. |

## 4. APIs

- **GET /api/conversation?session_id=...** — Return stored messages for that session (used on page load to restore chat).
- **GET /api/lessons** — Return all lessons learned.
- **POST /api/lessons** — Add one lesson. Body: `{ "event": "", "what_happened": "", "outcome": "", "lesson": "", "recommendation": "" }`.
- **GET /api/trust_score** — Return `{ approvals, total_proposals, ai_agency_score }`.
- **POST /api/trust_score** — Record one proposal outcome. Body: `{ "approved": true }` or `{ "approved": false }`.

## 5. Without Redis

If the env vars are **not** set:

- Conversation is **not** persisted (refresh clears it; session still works in one tab).
- Lessons learned are **not** stored; VueLogic does not see any lessons.
- Trust score stays at 0; VueLogic always behaves in Advisory (Level 2/3) mode.

**GET /api/status** returns `"persistence_available": true` when Redis is configured.
