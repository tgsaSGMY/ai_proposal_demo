# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

`ai_proposal_demo` is a **public, unauthenticated demo** of the AI Proposal Platform. A visitor lands on the URL, gets dropped straight into a guided-chat workspace against a preset Grant Template, and can interact for a capped number of turns before being prompted to register on the parent `ai_proposal_platform`. The parent platform reads the demo row by `demo_session_id` and migrates it into a real user account.

It was forked from `ai_proposal_platform` and then **gutted**: all authentication, OAuth, JWT issuance, role/quota/throttling logic, mother-platform engine-usage reporting, and the multi-project model were removed. The remaining surface is intentionally small.

- Inherited READMEs (`README.md`, `backend/README.md`, `frontend/README.md`) describe the parent platform's full feature set (14 routers, role-based access, OAuth flows, multi-project workspace). **These docs are stale for this repo.** Use this CLAUDE.md as the source of truth for what actually exists here.

## Commands

Backend (from `backend/`):
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
python -c "from app.main import app; print('OK', len(app.routes))"   # quick import sanity check
```

Frontend (from `frontend/`):
```bash
npm install
npm run dev        # localhost:3000
npm run build
```

Docker (from repo root):
```bash
docker compose up -d                                  # production
docker compose -f docker-compose.beta.yml up -d       # Dev VPS
```

No unit / integration tests configured. `stress-tests/` mentioned in inherited docs is gitignored.

## Database setup

Before the backend can serve real requests, apply **`demo_migration.sql`** at the repo root against the Supabase Postgres on the Dev VPS:

```bash
psql "$DATABASE_URL" -f demo_migration.sql
```

This creates `ai_proposal_platform.demo` — the single table that holds every visitor's session state. Schema:

| column                 | type        | notes                                                        |
|------------------------|-------------|--------------------------------------------------------------|
| `session_id`           | UUID PK     | mints `gen_random_uuid()`, matches the cookie value          |
| `created_at`           | TIMESTAMPTZ | auto                                                         |
| `updated_at`           | TIMESTAMPTZ | trigger keeps it fresh                                       |
| `expires_at`           | TIMESTAMPTZ | default `NOW() + 30 days` — daily pg_cron job deletes unclaimed rows past this |
| `grant_id`             | TEXT        | template the visitor is filling out                          |
| `template_id`          | TEXT        |                                                              |
| `title`                | TEXT        | default `'AI 計畫書草稿'` — hardcoded placeholder; visitor edits it on the parent platform after registering |
| `mode`                 | TEXT        | default `'interactive'` — demo only supports chat-guided mode |
| `conversation_history` | JSONB       | same shape as parent `projects.conversation_history`         |
| `stored_answer`        | JSONB       | same shape as parent `projects.stored_answer`                |
| `saved_plan`           | JSONB       |                                                              |
| `interaction_count`    | INTEGER     | enforces `DEMO_INTERACTION_LIMIT` (default 10)               |
| `pending_usage_logs`   | JSONB       | buffered token/cost records; parent drains into `usage_logs` on claim |
| `pending_execution_events` | JSONB   | buffered timeline events; parent drains into `execution_logs` on claim |
| `claimed_by`           | UUID FK     | nullable; parent platform sets this on register handoff      |
| `claimed_at`           | TIMESTAMPTZ |                                                              |

The catalog tables (`grants`, `plan_templates`, `sections`, `models`, `routing_rules`) are **shared with the parent platform** — the demo only reads from them.

## Architecture invariants

**No auth — cookie-scoped sessions.** Every HTTP request that touches visitor data uses `Depends(get_demo_session_id)` from `app/api/dependencies.py`. The dependency reads/mints a `demo_session_id` HttpOnly cookie (UUID, 30 days, SameSite=Lax). The cookie lifetime mirrors the row's `expires_at` default. WebSocket handshakes read the same cookie (with `?session_id=` as a fallback for testing).

**Three routers total** — registered in `app/main.py`:
- `app/api/projects.py` — `/api/demo` CRUD on the visitor's row
- `app/api/generate.py` — `/api/ws/chat_guidance` WebSocket only
- `app/api/config.py` — `/api/config`, `/api/datasets-lifecycle`, `/api/config/refresh`, `/api/plan_templates` (catalog reads, no scoping)

**SupabaseService surface in `app/services/supabase_service.py`:**
- `get_demo_session(session_id)`, `ensure_demo_session(session_id, grant_id, template_id)`, `update_demo_session(session_id, data)`, `increment_demo_interaction(session_id)` (raw SQL with RETURNING), `delete_demo_session(session_id)` — the demo's working set.
- Catalog readers (`get_all_grants_config`, `get_all_models`, `get_all_routing_rules`, `get_all_datasets`) still feed the startup cache in `app/core/lifecycle.py`.
- The file still contains user-scoped methods inherited from the parent (`get_projects_by_user`, `log_usage`, `check_project_slot_availability`, etc.). They are **dead code** — no router calls them. Their lazy `from app.config import …` imports of removed constants are safe because the imports only execute if the method is called.

**Hot-path caches** populated at startup in `lifecycle.py` (`app.state.all_grants_config`, `model_registry`, `routing_rules`, `all_datasets`). `/api/config/refresh` rebuilds them. There is no auth cache (`AUTH_CONTEXT_CACHE` was deleted).

**Demo-specific config** in `app/config.py`:
- `DEMO_INTERACTION_LIMIT` (env, default `10`) — once a session's `interaction_count` hits this, the WebSocket emits a `limit_reached` event with the parent platform's register URL.
- `DEMO_REGISTER_REDIRECT_URL` (env, default `https://portal.tgsaapp.com/register`).

The parent platform's `APP_JWT_*`, `EXTERNAL_OAUTH_*`, `MOTHER_PLATFORM_*`, `ENGINE_USAGE_*`, `QUOTA_*`, `SLOT_*`, `THROTTLING_*` constants are **all removed**. So is the `engine_usage_gate`/`engine_usage_reporter`/`mother_token_storage`/`provider_model_mapper` integration.

**CORS allowlist** in `backend/app/main.py:30` is hardcoded (not env). Currently `http://localhost:3000` + `https://demo-dev.172.233.79.222.nip.io`. Add new origins here, not in `.env`.

## Frontend conventions

The frontend was a Nuxt 3 app with full auth (Supabase + external OAuth) and a multi-project workspace. The demo rewrite:
- Deleted `pages/login.vue`, `pages/external-auth-callback.vue`, `pages/projects/[id].vue` (the old 4k-line workspace).
- `pages/index.vue` is now the **entire demo flow** — single Vue file, `layout: false`, `ssr: false`. On mount it fetches `/api/config` + `/api/demo` in parallel, auto-picks the first grant/template, derives `all_questions` from `section.json_schema.properties`, opens the chat WebSocket, streams responses, and shows the register-prompt modal when the server emits `limit_reached`.
- `middleware/auth.ts` and `middleware/redirectIfAuthenticated.ts` are **no-op passthroughs** (kept so any inherited `definePageMeta({ middleware: "auth" })` declarations keep resolving).
- `composables/useAppAuth.ts` is a **shim**: `authenticatedFetch` is plain `fetch(..., { credentials: "include" })`; `getAppSession` returns an always-authenticated demo session; `appLogout` calls `DELETE /api/demo` to wipe the row.
- `composables/useInternalCheck.ts` always returns `false`.
- `composables/useCurrentUser.ts` returns the visitor's `session_id` (from `GET /api/demo`) in place of a real user id.
- `utils/supabaseClient.ts` disables `autoRefreshToken`, `persistSession`, `detectSessionInUrl` — the SDK is now only for Realtime / catalog reads.

**Dead code left behind:** `components/chat/Chatbox.vue` (and its `helper/` subtree), `components/template-manager/*`, `layouts/default.vue`, several composables (`usePlanGenerator`, `useFileExtractor`, `useConfirm`, etc.) — all inherited from the parent platform, no longer imported by `pages/index.vue`. Safe to delete in a follow-up; left in place so this change set stays scoped.

## Deployment topology

- **`dev` branch** → `.github/workflows/deploy-dev.yml` builds `tgsa83609327/ai_proposal_demo:dev` (+ frontend), pushes to Docker Hub, SSHes into Dev VPS, runs `docker compose -f docker-compose.beta.yml pull && up -d` in `/opt/projects/ai-proposal-demo`.
- **`main`** has no auto-deploy.
- Dev VPS shares Supabase (`supabase_default` Docker network) and Nginx Proxy Manager (`npm-network`) with the parent platform — `docker-compose.beta.yml` deliberately has no `nginx-proxy` service.
- Public URL on Dev VPS: `https://demo-dev.172.233.79.222.nip.io`.

## When working in this repo

- The "single source of truth for current state" referenced in inherited docs (`STATUS.md`, stress-test reports, `database-backup-migrate-schema.md`) is **gitignored** — don't expect to find those files.
- DB schema is `ai_proposal_platform`. The demo lives in that schema alongside the parent's tables.
- Cleanup runs via **pg_cron** (`cron.schedule('demo_cleanup_expired', '15 3 * * *', ...)`) installed by `demo_migration.sql`. Daily at 03:15 UTC it deletes unclaimed rows past `expires_at` via the partial index `demo_expires_at_idx`. Claimed rows (with `claimed_by` set by the parent platform's register handoff) are preserved indefinitely as an audit trail — delete them manually when desired. If your Supabase project doesn't have `pg_cron`, the migration prints a fallback DELETE statement to run from any external scheduler.
- The "claim demo session" / migration endpoint lives on the **parent platform**, not here. This repo only produces demo rows; the parent reads them when a visitor registers.
- Asian-language docs at the root (`API文件.md`, `技術架構文.md`) describe the parent platform's architecture and are mostly stale for this fork.
