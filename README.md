# FlowMind AI

[![CI](https://github.com/Nikhil-creat/flowmind-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Nikhil-creat/flowmind-ai/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/backend-Python%20%2F%20FastAPI-3776AB)
![Next.js](https://img.shields.io/badge/frontend-Next.js%20%2F%20TypeScript-000000)

**AI-powered workflow automation and document intelligence platform.**

FlowMind AI combines two of the highest-demand skill areas in software right now —
applied AI / RAG systems, and no-code workflow automation — into a single
full-stack product. Upload documents and ask grounded questions about them,
then wire the same data into visual automations that run on a schedule, on
a webhook, or on demand.

## Why this project

Built as a portfolio / major project to demonstrate:
- **Full-stack engineering** — Next.js 14 (TypeScript, App Router) + FastAPI (Python)
- **Applied AI** — retrieval-augmented generation (RAG) with Chroma + sentence-transformer
  embeddings + Claude for grounded answers
- **Automation engineering** — a real DAG-based workflow engine (trigger → action nodes),
  cron scheduling via APScheduler, and inbound webhooks
- **Production practices** — JWT auth, Dockerized services, environment-based config,
  a documented REST API (OpenAPI/Swagger at `/docs`)

## Features

- **Document intelligence** — upload PDFs, text files, **or images**; automatic background
  chunking + embedding (images are described via vision AI), natural-language Q&A with
  cited sources, live word-by-word streaming answers over WebSocket, and **voice input**
  (browser speech-to-text, no extra setup)
- **Multi-provider AI** — Claude is the primary reasoning model; Gemini is an automatic
  fallback if Claude errors out or isn't configured, so AI features stay up during a
  single-vendor outage
- **Multi-step AI agent** — a bounded ReAct-style workflow node that iteratively searches
  your documents, reasons about what it still needs, and produces a final answer — with
  every reasoning step logged for inspection
- **Visual workflow builder** — drag-and-drop canvas (React Flow) with trigger nodes
  (manual / schedule / webhook) and action nodes: document search, AI summarize, AI agent,
  send email, **Slack message, WhatsApp message, Google Sheets append**, HTTP request, condition
- **Automation engine** — topologically executes each workflow's node graph, resolves
  `{{node_id.field}}` template variables between steps, and logs every run
- **Scheduling & webhooks** — cron-based recurring workflows and a public webhook
  endpoint so external tools (forms, CRMs, cron services) can trigger a workflow
- **Teams & roles** — every account gets a personal workspace; invite teammates as
  owner/admin/member, and documents + workflows are shared within the workspace
- **Billing** — optional Stripe Checkout to upgrade a workspace to "pro" (fully functional
  once `STRIPE_SECRET_KEY` is set; shows a clear "not configured" message otherwise)
- **Analytics dashboard** — documents indexed, workflow run history, success/failure
  rates, 7-day activity chart, and a live system-status panel
- **Auth** — email/password signup and login with JWT bearer tokens, plus one-tap
  **Google Sign-In**
- **Reliability & performance** — Redis-backed response caching and rate limiting
  (falls back to safe in-memory behavior if Redis isn't configured), background
  document processing so uploads return instantly, retry-with-backoff around every
  AI call, structured logging with request correlation IDs, and Prometheus metrics
  at `/metrics`

## Tech stack

| Layer          | Choice                                                             |
|----------------|---------------------------------------------------------------------|
| Frontend       | Next.js 14, TypeScript, Tailwind CSS, React Flow, Recharts           |
| Backend        | Python, FastAPI, SQLAlchemy, Pydantic                                |
| AI / RAG       | Anthropic Claude + Google Gemini (auto-fallback, incl. vision), ChromaDB, sentence-transformers |
| Automation     | Custom DAG workflow engine + multi-step agent node, APScheduler (cron), webhooks, WebSocket streaming |
| Integrations   | Slack (webhooks), WhatsApp (Twilio), Google Sheets (service account) |
| Auth & teams   | JWT (python-jose) + bcrypt, Google Sign-In, workspaces with owner/admin/member roles |
| Billing        | Stripe Checkout (optional, direct REST integration)                  |
| Reliability    | Redis (cache + rate limiting, optional), tenacity retries, loguru, Prometheus |
| Database       | SQLite (dev) / PostgreSQL (production-ready via `DATABASE_URL`)      |
| Deployment     | Docker + Docker Compose (backend, frontend, Redis)                    |

Python + TypeScript were chosen deliberately: Python is the default for AI/ML
tooling (embeddings, LLM SDKs, data processing), while TypeScript gives the
frontend type safety and is the standard for modern React/Next.js apps —
together they cover the two most in-demand language ecosystems in current
job postings for full-stack and AI roles.

## Architecture

```
┌────────────────┐        REST/JSON        ┌──────────────────────┐
│   Next.js UI    │  ───────────────────▶  │      FastAPI          │
│  (dashboard,     │  ◀───────────────────  │  ┌────────────────┐  │
│   doc chat,      │                        │  │ Auth (JWT)      │  │
│   flow builder)  │                        │  ├────────────────┤  │
└────────────────┘                        │  │ RAG engine      │──┼──▶ ChromaDB
                                            │  │ (Claude)        │  │
                                            │  ├────────────────┤  │
        webhook ─────────────────────────▶ │  │ Workflow engine │  │
                                            │  ├────────────────┤  │
        cron ───────────────────────────▶  │  │ Scheduler       │  │
                                            │  └────────────────┘  │
                                            │        SQLAlchemy      │
                                            │           │             │
                                            └───────────┼─────────────┘
                                                         ▼
                                                 SQLite / PostgreSQL
```

## How AI, RAG, and Automation connect

These aren't three separate features bolted together - they share the same
pipeline. The **workflow engine** treats a document search or an AI call as
just another node, so any automation can pull retrieved context (RAG) into
a prompt (AI) and act on the result (automation) in one run:

```
trigger.schedule  →  action.document_search  →  action.ai_summarize  →  action.send_email
   (automation)            (RAG retrieval)          (AI generation)        (automation)
```

The same `ai_provider.generate()` call and the same `rag.search()` function
power both the interactive document-chat UI *and* the `action.ai_summarize`
/ `action.document_search` workflow nodes - one engine, two surfaces. Open
**Workflows → "Try RAG + AI + Automation template"** in the app to create
this exact pipeline pre-wired and run it immediately.

## Getting started

### Option A — Docker (recommended)

```bash
git clone https://github.com/Nikhil-creat/flowmind-ai.git
cd flowmind-ai
cp backend/.env.example backend/.env   # add your ANTHROPIC_API_KEY (optional but recommended)
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend docs (Swagger): http://localhost:8000/docs

### Option B — Run locally

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

The app works end-to-end without any API keys: without `ANTHROPIC_API_KEY` or
`GOOGLE_API_KEY` the document chat falls back to an extractive answer, and
without SMTP credentials the `send_email` workflow action logs instead of
sending. Redis and Google Sign-In are optional in the same way.

### Getting Google API keys (optional but recommended)

**Gemini (AI fallback)** — free tier available:
1. Go to https://aistudio.google.com/app/apikey
2. Create an API key and put it in `backend/.env` as `GOOGLE_API_KEY`

**Google Sign-In (OAuth login)**:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create an **OAuth client ID** → Application type: *Web application*
3. Add `http://localhost:3000` under Authorized JavaScript origins
4. Copy the Client ID into `backend/.env` as `GOOGLE_CLIENT_ID` **and** into
   `frontend/.env.local` as `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (same value, both places)

## Setting up the optional integrations

Every one of these is optional — the app runs and every feature still works
(by logging instead of sending) without them.

| Integration | What it needs | Where to get it |
|---|---|---|
| Slack messages | `SLACK_DEFAULT_WEBHOOK_URL` (or set per-node) | Slack → Apps → Incoming Webhooks |
| WhatsApp messages | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM` | twilio.com/console → WhatsApp sandbox |
| Google Sheets | `GOOGLE_SERVICE_ACCOUNT_JSON` (path to a service account key file, shared with edit access on the target sheet) | console.cloud.google.com → IAM → Service Accounts |
| Stripe billing | `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID_PRO` | dashboard.stripe.com → Developers → API keys |

## Reliability & observability

- `GET /health` — basic liveness check
- `GET /health/detailed` — status of the database, cache, scheduler, and each AI provider
- `GET /metrics` — Prometheus-format request counts and latency histograms
- Every response carries an `X-Request-ID` header, and logs are tagged with the same ID
- Chat and workflow-run endpoints are rate-limited (`RATE_LIMIT_CHAT`, `RATE_LIMIT_WORKFLOW_RUN`
  in `.env`) to protect against abuse and runaway automation loops

## Project structure

```
flowmind-ai/
├── backend/
│   ├── app/
│   │   ├── core/          # config, database, security, auth deps
│   │   ├── models/        # SQLAlchemy models + Pydantic schemas
│   │   ├── routers/       # auth, documents, workflows, webhooks, analytics
│   │   ├── services/      # rag.py, workflow_engine.py, scheduler.py, mailer.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── dashboard/      # overview, documents, workflows (+ builder)
│   │   ├── login/ signup/
│   │   └── page.tsx        # landing page
│   ├── components/
│   └── lib/api.ts
└── docker-compose.yml
```

## Testing

```bash
cd backend
pip install -r requirements.txt
pytest -q
```

Tests cover auth (signup/login/duplicate handling), workspace creation +
invites + role permissions, the workflow engine (templating, topological
ordering, condition logic), workflow CRUD + manual run + webhook triggering,
and the health/metrics endpoints. They run against an isolated in-memory
SQLite database and don't touch your dev data. The same suite runs
automatically on every push via GitHub Actions (see the CI badge above).

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for step-by-step instructions to put
this live on Vercel (frontend) + Render (backend, Postgres, Redis) for free.

## Roadmap ideas

- Multi-step AI agent nodes (tool-use, not just single prompts)
- Team workspaces with shared documents and workflows
- More trigger types (email-in, RSS, database change)
- Usage-based billing tier

## Author

**Nikhil Chary Sriramoju**
BTech CSE (Final Year)

- GitHub: [Nikhil-creat](https://github.com/Nikhil-creat)
- LinkedIn: [nikhil-chary-sriramoju](https://in.linkedin.com/in/nikhil-chary-sriramoju-95041b38a)
- Email: sriramojunikhil66@gmail.com
- Mobile: +91 63005 56302
- Instagram: [@nikhil__sriramoju](https://www.instagram.com/nikhil__sriramoju)
- Facebook: [Profile](https://www.facebook.com/profile.php?id=100079201124141)

## License

MIT — see [LICENSE](./LICENSE).
