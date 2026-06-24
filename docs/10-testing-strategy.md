# 10 — Testing Strategy

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Test Philosophy](#test-philosophy)
2. [Test Types](#test-types)
3. [Backend Tests](#backend-tests)
4. [Frontend Tests](#frontend-tests)
5. [Test Coverage](#test-coverage)
6. [Running Tests](#running-tests)
7. [CI/CD Integration](#cicd-integration)
8. [Test Data](#test-data)

---

## Test Philosophy

The demo is a **public-facing, anonymous entry point** with hard usage limits. Testing prioritizes:

1. **Correctness of core flows** — session creation, chat, generation, migration
2. **Limit enforcement** — prompt caps, token throttling, generation limits
3. **Security** — session isolation, IP rate limiting, abuse prevention
4. **Migration integrity** — data preservation, idempotency, error handling

---

## Test Types

| Type | Scope | Tool | Priority |
|------|-------|------|----------|
| **Unit Tests** | Individual functions, utilities | pytest | High |
| **Integration Tests** | API endpoints, routers | pytest + TestClient | High |
| **End-to-End Tests** | Full user journey | Playwright (planned) | Medium |
| **Load Tests** | Concurrent session handling | k6 / Locust (planned) | Medium |
| **Security Tests** | Rate limiting, abuse | pytest + custom scripts | High |
| **Contract Tests** | API schema validation | schemathesis (planned) | Low |

---

## Backend Tests

### Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures (mock SupabaseService)
├── __init__.py
├── test_demo_session.py     # Demo session CRUD + cookie tests
├── test_demo_rate_limiter.py # Rate limiter logic tests
├── test_ip_extractor.py     # IP extraction utility tests
├── test_dead_routers.py     # Verify removed routers stay dead
└── README.md                # Test documentation
```

### 1. `test_demo_session.py`

**Scope:** Integration tests for the `/api/demo` router.

**Tested scenarios:**

| Test | Description | Method |
|------|-------------|--------|
| `test_first_get_mints_cookie` | First request creates session + sets cookie | `GET /api/demo` |
| `test_subsequent_get_reuses_cookie` | Second request returns same session | `GET /api/demo` |
| `test_garbage_cookie_replaced` | Invalid cookie triggers fresh mint | `GET /api/demo` |
| `test_put_round_trips_payload` | PUT updates and returns correct data | `PUT /api/demo` |
| `test_put_with_empty_body_noop` | Empty PUT returns current row | `PUT /api/demo` |
| `test_delete_clears_row` | DELETE removes row, next GET mints fresh | `DELETE /api/demo` |
| `test_rate_limit_returns_429` | Exceeded IP limit returns 429 | `GET /api/demo` |
| `test_rate_limit_skipped_when_cookie_present` | Existing cookie bypasses rate limit | `GET /api/demo` |
| `test_get_skips_claimed_row` | Claimed row triggers fresh mint | `GET /api/demo` |
| `test_cookie_max_age_matches_env` | Cookie max-age equals expiry config | `GET /api/demo` |
| `test_expired_session_rejected` | Expired row triggers fresh mint | `GET /api/demo` |
| `test_new_row_has_expires_at` | New session has future expiry | `GET /api/demo` |

**Mock Strategy:**
- `mock_supabase` — MagicMock with `get_db_session()` context manager
- `demo_store` — In-memory dict simulating `ai_proposal_platform.demo` rows
- `rate_limit_rows` — Mutable list controlling the rate limiter's return values

### 2. `test_demo_rate_limiter.py`

**Scope:** Unit tests for `app.utils.demo_rate_limiter.DemoRateLimiter`.

**Tested scenarios:**

| Test | Description |
|------|-------------|
| `test_allows_first_session` | Counts of 1 mean allowed |
| `test_allows_exactly_at_limit` | Equal-to limit is allowed |
| `test_rejects_when_hourly_exceeded` | Hourly +1 returns 429 with `retry_after` |
| `test_rejects_when_daily_exceeded` | Daily +1 returns 429 with `retry_after` |
| `test_hourly_takes_priority` | Both exceeded → hourly wins |
| `test_fail_open_on_db_error` | DB failure → allowed (fail-open) |

### 3. `test_ip_extractor.py`

**Scope:** Unit tests for `app.utils.ip_extractor.get_client_ip()`.

**Tested scenarios:**

| Test | Description |
|------|-------------|
| `test_x_forwarded_for` | Extracts first IP from comma-separated list |
| `test_x_real_ip` | Falls back to X-Real-IP |
| `test_request_client_host` | Falls back to request.client.host |
| `test_none_when_all_missing` | Returns None if no headers |

### 4. `test_dead_routers.py`

**Scope:** Verify that removed routers (auth, external_auth, datasets) do not exist.

| Test | Description |
|------|-------------|
| `test_auth_router_not_registered` | `GET /api/auth/me` → 404 |
| `test_external_auth_router_not_registered` | `GET /api/external-auth/redirect` → 404 |
| `test_datasets_router_not_registered` | `GET /api/datasets` → 404 |

---

## Frontend Tests

### Test Structure

```
frontend/tests/
└── components/
    └── DemoRegisterModal.spec.ts
```

### `DemoRegisterModal.spec.ts`

**Scope:** Component test for the registration modal.

**Tested scenarios:**

| Test | Description |
|------|-------------|
| `renders correctly when open` | Modal shows title, progress, register URL |
| `emits close event on dismiss` | Clicking X emits `close` |
| `emits update-title on input` | Typing in title field emits `update-title` |

### Planned Tests

| Test File | Description | Priority |
|-----------|-------------|----------|
| `DemoChatbox.spec.ts` | Chat message rendering, WebSocket mock, limit notices | High |
| `useDemoSession.spec.ts` | Memoization, retry behavior, SSR handling | High |
| `index.spec.ts` | Page-level integration: session bootstrap → catalog → WebSocket | Medium |
| `exportToWord.spec.ts` | Word export utility | Low |

---

## Test Coverage

### Current Coverage

| Module | Coverage | Notes |
|--------|----------|-------|
| `app.api.projects` | ✅ High | All CRUD endpoints tested |
| `app.api.dependencies` | ✅ High | Cookie mint, require, rate limit integration |
| `app.utils.demo_rate_limiter` | ✅ High | All branches covered |
| `app.utils.ip_extractor` | ✅ High | All fallback paths covered |
| `app.api.generate` | ⚠️ Partial | WebSocket chat tested manually; needs automated tests |
| `app.services.llm_service` | ❌ None | Requires LLM mocking |
| `app.services.supabase_service` | ⚠️ Partial | Mocked in tests; real integration not tested |
| `frontend components` | ⚠️ Partial | Only DemoRegisterModal tested |
| `frontend composables` | ❌ None | Needs Vitest setup |
| `E2E flow` | ❌ None | Needs Playwright |

### Target Coverage

| Module | Target | Timeline |
|--------|--------|----------|
| Backend routers | 90% | 2026-07 |
| Backend services | 70% | 2026-07 |
| Frontend components | 80% | 2026-08 |
| Frontend composables | 80% | 2026-08 |
| E2E critical path | 100% | 2026-08 |

---

## Running Tests

### Backend

```bash
cd backend

# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_demo_session.py

# Run specific test
pytest tests/test_demo_session.py::test_first_get_mints_cookie

# Run with verbose output
pytest -v

# Run async tests
pytest -v --asyncio-mode=auto
```

### Frontend

```bash
cd frontend

# Install test dependencies
npm install -D @vue/test-utils vitest @nuxt/test-utils

# Run tests
npx vitest

# Run with UI
npx vitest --ui

# Run specific test
npx vitest DemoRegisterModal
```

### E2E (Planned)

```bash
# Install Playwright
npm install -D @playwright/test
npx playwright install

# Run E2E tests
npx playwright test

# Run with UI
npx playwright test --ui
```

---

## CI/CD Integration

### GitHub Actions Test Job

```yaml
# Add to .github/workflows/deploy-dev.yml

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run backend tests
        run: |
          cd backend
          pytest -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm install

      - name: Run frontend tests
        run: |
          cd frontend
          npx vitest run
```

---

## Test Data

### Mock SupabaseService

Located in `backend/tests/conftest.py`:

```python
@pytest.fixture
def mock_supabase():
    """Returns a MagicMock SupabaseService with get_db_session() context manager."""
    ...

@pytest.fixture
def demo_store():
    """In-memory dict simulating ai_proposal_platform.demo rows."""
    ...

@pytest.fixture
def rate_limit_rows():
    """Mutable list controlling DemoRateLimiter return values."""
    ...

@pytest.fixture
def client(mock_supabase, demo_store, rate_limit_rows):
    """FastAPI TestClient with mocked dependencies."""
    ...
```

### Sample Test Data

```python
# Sample demo row
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "ip_address": "203.0.113.42",
    "grant_id": "sbir",
    "template_id": "sbir_p1",
    "interaction_count": 0,
    "has_generated_docx": False,
    "download_count": 0,
    "status": "active",
    "created_at": "2026-06-24T06:30:00+00:00",
    "expires_at": "2026-07-01T06:30:00+00:00",
}

# Sample rate limit rows
[("hour", 1), ("day", 1)]
```

---

## Known Test Gaps

| Gap | Risk | Plan |
|-----|------|------|
| WebSocket chat not auto-tested | High | Add WebSocket client test using `pytest-asyncio` |
| LLM service not tested | Medium | Mock `stream_external_api()` with fake chunks |
| Plan generation not tested | High | Test `generate_plan` with mocked template config |
| Plan revision not tested | Medium | Test `revise_plan_version` with mocked data |
| Frontend chat not tested | High | Add `DemoChatbox.vue` component tests |
| E2E migration not tested | High | Add Playwright test for full signup flow |
| Load testing not done | Medium | Run k6 against `/api/demo` and `/ws/chat_guidance` |

---

> Next: [`11-security-abuse-prevention.md`](11-security-abuse-prevention.md)

(End of file)
