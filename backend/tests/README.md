# Backend test suite

Phase 10 of `next-implementation.md`, scoped to what's actually built on this
branch. Run from `backend/`:

```powershell
pip install -r requirements-dev.txt
pytest
```

## Coverage

| Area | File | What it covers |
|------|------|----------------|
| IP extraction | `test_ip_extractor.py` | `X-Forwarded-For` precedence, `X-Real-IP` fallback, no-source case |
| IP rate limiter | `test_demo_rate_limiter.py` | Hourly/daily caps, hourly-wins precedence, fail-open on DB error |
| Demo session router | `test_demo_session.py` | Cookie mint + reuse, garbage-cookie remint, PUT/DELETE round trip, 429 path, cookie-set short-circuits rate limit |
| Dead-router guard | `test_dead_routers.py` | Removed `auth/datasets/generate/projects` endpoints must stay 404; CORS preflight from unknown origin must not echo |

## Out of scope (intentionally)

The plan listed tests for code that isn't built on this branch — skipped to
avoid testing non-existent code paths:

- `test_demo_chat.py` — no prompt limit endpoint and no server-side token
  cap enforcement; the `pending_usage_logs` JSONB column exists but no drain.
- `test_demo_finalize.py` — `/api/demo/finalize` route does not exist.
- `test_demo_migrate.py` — `/api/demo/migrate` and the SQL claim function
  live on the parent platform branch.
- `test_demo_session.py::expiry` — `expires_at` is enforced by the
  `demo_cleanup_expired` cron job, not by any API path.

## How the test client works

`conftest.py` overrides `get_supabase_service` / `get_llm_service` with a
`MagicMock` so tests never touch real Supabase. `TestClient(app)` is used
*without* the context-manager form — Starlette only fires `on_event("startup")`
inside `with TestClient(app) as c:`, so this skips the real
`startup_event_handler` (which would hit Supabase + download `fastembed`).
