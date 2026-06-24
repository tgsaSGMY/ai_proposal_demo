# AI Proposal Demo — English Overview

> **Free Demo Version:** Allows anonymous visitors to experience AI-powered SBIR Phase 1 proposal generation without login, then seamlessly migrate their session to the full platform upon signup.

---

## Project Overview

This repository is a **hard-forked, stripped-down version** of the full AI Proposal Platform (補助引擎). Unlike the full platform which supports multiple grants, templates, admin management, and authenticated flows, **this demo** focuses on a single purpose:

> **Let any visitor experience AI-powered SBIR Phase 1 proposal generation for free, with hard limits, then seamlessly transfer their session to the full platform upon signup.**

### User Journey

```
Anonymous Visitor
    ↓
Lands on demo-aiproposal.tgsa.com.tw (no login required)
    ↓
Instantly enters AI Chat workspace (SBIR Phase 1 only)
    ↓
Chat with AI (max 20 prompts per session — configurable via .env)
    ↓
Generate .docx report (max 1 per session)
    ↓
See preview + upsell modal
    ↓
Click "Sign Up FREE" → redirected to full platform
    ↓
Session data migrated → continues on aiproposal.tgsa.com.tw
```

### Hard Limits

| Limit | Value | Enforcement |
|-------|-------|-------------|
| Chat prompts per session | **20** (configurable) | Backend counter `demo.interaction_count` |
| .docx report generations | **1** | Backend flag `demo.has_generated_docx` |
| Tokens per session | **100,000** | Backend accumulator via `pending_usage_logs` |
| Demo sessions per IP / hour | **3** | `demo_ip_limits` table (enforcement currently disabled) |
| Demo sessions per IP / day | **5** | `demo_ip_limits` table (enforcement currently disabled) |
| Session data retention | **7 days** (configurable) | `demo.expires_at` + daily cleanup |

---

## Core Features

### AI Guided Chat

- Real-time WebSocket streaming AI conversation
- Automatic parsing of hidden reply field format to extract answers
- Tracks unanswered fields and intelligently prompts the next question
- Multi-candidate version generation (choose best per section)
- Plan revision (revise) based on existing versions

### Report Generation

- Full SBIR Phase 1 plan generation based on answered fields
- Parallel multi-candidate generation per section
- Filter sections by actually-answered fields (fallback to all if none)
- Project name recommendation based on filled answers

### Session Migration

- When limits are reached, a "Sign Up FREE" CTA appears
- Redirects to full platform OAuth with `?ref=<session_id>`
- On successful signup, session data (chat history, answers, generated plan, execution logs, usage logs) is atomically migrated to a new `projects` row

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Nuxt 3 (Vue 3 + TypeScript) + Tailwind CSS |
| Backend | FastAPI + Uvicorn |
| Database | Supabase PostgreSQL (shared with full platform) |
| AI Models | OpenAI GPT-5/4.1, Google Gemini |
| Deployment | Docker Compose + Nginx |
| CI/CD | GitHub Actions |

---

## Project Structure

```text
.
├── backend/                   # Backend service
│   ├── app/
│   │   ├── api/               # API routers (3 routers)
│   │   │   ├── generate.py    # Generation, WebSocket chat, name recommendation
│   │   │   ├── projects.py    # Demo session CRUD, status, dynamic fields
│   │   │   ├── config.py      # Grant/template catalog
│   │   │   └── dependencies.py # DI: cookie session, rate limiter
│   │   ├── core/              # Startup lifecycle
│   │   ├── services/          # LLM / Supabase services
│   │   ├── utils/             # IP extractor, rate limiter
│   │   ├── config.py          # Environment variables
│   │   ├── main.py            # FastAPI entrypoint
│   │   └── models.py          # Pydantic models
│   ├── tests/                 # Tests (session, rate limiter, IP extractor)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
├── frontend/                  # Frontend service
│   ├── components/
│   │   └── chat/
│   │       ├── DemoChatbox.vue       # Demo chat workspace
│   │       └── helper/
│   │           └── DemoRegisterModal.vue  # Registration prompt modal
│   ├── composables/
│   │   ├── useDemoSession.ts  # Memoized session bootstrap
│   │   ├── useAppAuth.ts      # Auth helpers (no Bearer token)
│   │   └── usePlanGenerator.ts # Plan generation flow
│   ├── pages/
│   │   └── index.vue          # Root = demo workspace (no landing page)
│   ├── middleware/
│   │   └── auth.ts            # Auth middleware (allows root path)
│   ├── utils/                 # exportToWord, Supabase client
│   ├── nuxt.config.ts
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── nginx/                     # Reverse proxy
├── database-migrations/       # SQL migrations
├── docs/                      # Documentation
│   ├── README.md              # Doc navigation
│   ├── 05-api-endpoints.md    # REST API reference
│   └── 06-websocket-protocol.md # WebSocket protocol
├── docs-private/              # Internal specs
│   └── specs/
│       └── 2026-06-16-demo-to-platform-signup-handoff-design.md
├── docker-compose.yml         # Production
├── docker-compose.beta.yml    # Dev VPS
├── STATUS.md                  # Development status (latest)
├── dev-vps.md                 # Dev VPS deployment guide
└── README.md                  # This file (Chinese version)
```

---

## Quick Start

### Prerequisites

- Docker + Docker Compose v2
- Local dev: Python 3.10+, Node.js 20+
- Supabase project + Service Key
- OpenAI / Gemini API Key

### Option 1: Docker Compose (Recommended)

```bash
docker compose up -d
docker compose ps
docker compose logs -f --tail=200 fastapi-backend nuxt-frontend nginx-proxy
```

### Option 2: Local Separate Start

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

### Backend `.env`

```env
# Supabase
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service_key>
DATABASE_URL=postgresql://...

# LLM
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Demo Configuration
DEMO_GRANT_ID=sbir
DEMO_TEMPLATE_ID=sbir_p1
DEMO_MAX_PROMPTS_PER_SESSION=20
DEMO_MAX_TOKENS_PER_SESSION=100000
DEMO_MAX_GENERATIONS_PER_SESSION=1
DEMO_SESSION_EXPIRY_DAYS=7
DEMO_SESSION_EXPIRY_MINUTES=10080
DEMO_IP_HOURLY_LIMIT=3
DEMO_IP_DAILY_LIMIT=5
DEMO_REGISTER_REDIRECT_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect
FULL_PLATFORM_URL=https://aiproposal.tgsa.com.tw
DEMO_FRONTEND_URL=https://demo-aiproposal.tgsa.com.tw
```

### Frontend `.env`

```env
NUXT_PUBLIC_API_BASE_URL=https://demo-aiproposal.tgsa.com.tw/api
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon_key>

NUXT_PUBLIC_PLATFORM_HOME_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect
NUXT_PUBLIC_DEMO_GRANT_ID=sbir
NUXT_PUBLIC_DEMO_TEMPLATE_ID=sbir_p1
NUXT_PUBLIC_DEMO_SESSION_EXPIRY_MINUTES=10080
```

---

## API Endpoints (Summary)

### Demo Session

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/demo` | GET | Create/get session (mints cookie) |
| `/api/demo` | PUT | Update session data |
| `/api/demo` | DELETE | Reset session |
| `/api/demo/status` | GET | Session status & limits |
| `/api/demo/dynamic-fields` | GET | Dynamic field questions |
| `/api/demo/download` | POST | Increment download count |

### Generation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generate_plan` | POST | Generate full plan |
| `/api/revise_plan_version` | POST | Revise existing version |
| `/api/recommend_project_names` | POST | Recommend project names |
| `/ws/chat_guidance` | WS | AI guided chat |

### Config

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/config` | GET | Read catalog |
| `/api/config/refresh` | POST | Refresh cache |

---

## Key Workflows

### 1. Demo Startup Flow

1. Visitor enters `/` (no login required)
2. Frontend calls `GET /api/demo` → backend mints `demo_session_id` cookie + creates `demo` row
3. Frontend calls `GET /api/config` → loads grants/templates catalog
4. Frontend selects SBIR Phase 1 based on `DEMO_GRANT_ID` + `DEMO_TEMPLATE_ID`
5. WebSocket connects to `/ws/chat_guidance` → AI starts guided filling

### 2. AI Chat Flow

1. Visitor sends message → WebSocket transmits
2. Backend parses hidden reply fields, updates `stored_answer.chat_answers`
3. Backend checks `interaction_count` and token accumulation
4. If under limit → AI replies and asks next question
5. If limit reached → sends `limit_reached` event, frontend shows registration CTA
6. Auto-saves `conversation_history` and `stored_answer` to `demo` row after each turn

### 3. Plan Generation Flow

1. Visitor clicks "輸出完整推演"
2. Frontend calls `POST /api/generate_plan` (with `grant_id` + `template_id` + user summary)
3. Backend filters sections by answered fields (or all if none)
4. Parallel generation of `num_candidates` candidates per section
5. Frontend shows `PlanCandidateSelector` → visitor picks best version per section
6. After selection, calls `PUT /api/demo` to save `saved_plan` + `has_generated_docx = true`
7. Visitor can download Word file (via `utils/exportToWord.ts`)

### 4. Demo → Platform Migration Flow

1. Visitor clicks "免費註冊" after hitting limits
2. Frontend redirects: `https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<session_id>`
3. Full platform stores `ref` in `pending_demo_claim` cookie
4. Redirects to OAuth IdP (assist_link) for registration/login
5. After callback, platform calls `claim_demo_session(ref, user_id)`
6. SQL function `migrate_demo_to_project()` atomically copies data:
   - `demo` → `projects` (with `title`, `section_versions`, `saved_plan`, `stored_answer`, `conversation_history`)
   - `pending_execution_events` → `execution_logs`
   - `pending_usage_logs` → `usage_logs`
7. Marks `demo` row as `claimed`
8. Redirects to `/projects/<new_id>`

---

## Documentation

- [`docs/05-api-endpoints.md`](docs/05-api-endpoints.md) — Detailed REST API reference
- [`docs/06-websocket-protocol.md`](docs/06-websocket-protocol.md) — WebSocket message protocol
- [`STATUS.md`](STATUS.md) — Development status & architecture
- [`docs-private/specs/2026-06-16-demo-to-platform-signup-handoff-design.md`](docs-private/specs/2026-06-16-demo-to-platform-signup-handoff-design.md) — Signup handoff design

---

## License

Internal use only.

## Version

### v1.0.0-demo (2026-06-24)

- **Anonymous AI workspace:** No login required to interact with SBIR Phase 1 AI assistant
- **WebSocket real-time chat:** Streaming AI responses with automatic hidden field parsing
- **Plan generation:** Multi-candidate parallel generation with answer-based filtering
- **Plan revision:** Full version revision with candidate regeneration
- **Session management:** Cookie-based session CRUD with `GET/PUT/DELETE /api/demo`
- **Rate limiting infrastructure:** IP hour/day counters (enforcement ready, disabled)
- **Migration function:** Complete `migrate_demo_to_project()` with execution_logs + usage_logs drainage
- **Schema migrations:** 3 migration files for claim columns, download count, section_versions
- **Tests:** Backend test suite for demo session and rate limiter

> For the latest progress, see [`STATUS.md`](STATUS.md).

(End of file)
