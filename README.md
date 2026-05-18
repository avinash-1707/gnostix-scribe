# Gnostix Scribe

An autonomous MDX content generation platform. Authenticated users submit a technical topic and a LangGraph agent produces a publication-ready `.mdx` tutorial — scraping GeeksForGeeks and TpointTech, supplementing with LLM knowledge, generating images, and emitting MDX that conforms to a strict component schema. Every node transition streams live to the dashboard over SSE.

## Stack

- **Client** — Next.js 15 (App Router) + TypeScript + Tailwind v4
- **Server** — FastAPI + Uvicorn (Python 3.12)
- **Agent** — LangGraph (10 nodes)
- **LLM** — Gemini 2.5 Pro/Flash via `langchain-google-genai`
- **Images** — Gemini 2.5 Flash Image (primary) + OpenAI `gpt-image-1` (fallback), hosted on Cloudinary
- **Scraping** — trafilatura
- **DB** — Neon Postgres + SQLAlchemy async + Alembic
- **Auth** — JWT (access + httpOnly refresh cookie), bcrypt password hashing

## Architecture

```
client/   Next.js — pages, SSE consumer, JWT auth
server/   FastAPI — REST + SSE, auth, generation orchestrator
  agent/  LangGraph pipeline (10 nodes, no FastAPI/DB coupling)
output/   Transient .mdx staging written by file_writer (gitignored)
```

Full spec lives in `context/` — read `project-overview.md` and `architecture.md` first.

## Pipeline

`topic_router → (gfg_scraper ∥ tpointtech_scraper ∥ llm_knowledge) → content_merger → content_analyser → image_generator → mdx_generator → mdx_validator → file_writer`

Merger has a conditional self-loop on coverage fail. Validator retries on schema fail.

## Prerequisites

- Python 3.12 + [`uv`](https://github.com/astral-sh/uv)
- Node.js 20+ and `pnpm`
- Neon Postgres database (or any Postgres reachable via `postgresql+asyncpg://`)
- API keys: Gemini (`GOOGLE_API_KEY`), OpenAI (`OPENAI_API_KEY`), Cloudinary (`CLOUDINARY_URL`)

## Setup

```bash
# 1. Clone + enter
git clone <repo-url> gnostix-scribe
cd gnostix-scribe

# 2. Install server + client deps (creates server/.venv via uv, runs pnpm install)
make install

# 3. Configure env
cp server/.env.example server/.env
# edit server/.env — fill DATABASE_URL, SECRET_KEY, GOOGLE_API_KEY,
# OPENAI_API_KEY, CLOUDINARY_URL, CLIENT_URL

# 4. Run migrations
make migrate
```

### Required env vars (`server/.env`)

| Var | Purpose |
|-----|---------|
| `DATABASE_URL` | Neon Postgres async URL (`postgresql+asyncpg://...?ssl=require`) |
| `SECRET_KEY` | 32-byte hex for JWT signing |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Default 30 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Default 7 |
| `GOOGLE_API_KEY` | Gemini LLM + image |
| `OPENAI_API_KEY` | Image fallback |
| `CLOUDINARY_URL` | `cloudinary://<key>:<secret>@<cloud_name>` |
| `CLIENT_URL` | CORS origin, e.g. `http://localhost:3000` |

## Run

```bash
make dev      # server (:8000) + client (:3000) together
make server   # FastAPI only
make client   # Next.js only
```

Open `http://localhost:3000` → register → submit a topic.

## Layout

```
gnostix-scribe/
├── client/              Next.js app
├── server/              FastAPI + LangGraph agent
│   ├── agent/nodes/     10 LangGraph nodes
│   ├── auth/            JWT + bcrypt
│   ├── generation/      SSE + orchestration
│   └── alembic/         DB migrations
├── scripts/run_agent.py CLI agent runner (no HTTP)
├── output/content/      Transient MDX staging
├── context/             Project spec + standards
└── Makefile
```

## Notes

- `output/` is gitignored and ephemeral — DB is the source of truth. `file_writer` writes locally; service deletes after DB commit succeeds.
- A user may have at most one active `/generate` SSE stream — second concurrent request returns HTTP 409.
- Client never stores access token in `localStorage` — in-memory only. Refresh token lives in an httpOnly cookie.
- Generated images upload to Cloudinary under `mdx-agent/<topic-slug>/<concept-slug>`; the `secure_url` is embedded directly in `<Figure src>`.
