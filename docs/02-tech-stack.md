# 02 — Technology Stack

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Backend

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Runtime language |
| **FastAPI** | 0.100+ | Web framework (REST + WebSocket) |
| **Uvicorn** | 0.23+ | ASGI server |
| **Pydantic** | 2.x | Data validation & serialization |
| **SQLAlchemy** | 2.x | ORM for direct PostgreSQL access |
| **python-dotenv** | — | Environment variable loading |

### Database & Storage

| Technology | Purpose |
|------------|---------|
| **Supabase (PostgreSQL)** | Primary database — shared with full platform |
| **Supabase JS/REST SDK** | Admin operations via `supabase_service` |
| **SQLAlchemy (direct)** | Atomic transactions for rate limiting |

### AI / LLM

| Technology | Purpose |
|------------|---------|
| **OpenAI API** | GPT-5.1-chat-latest, GPT-4.1-mini, GPT-4o-mini |
| **Google Gemini API** | gemini-3-pro-preview, gemini-3-flash-preview |
| **Google Imagen API** | Available but not used in demo |
| **fastembed** | `BAAI/bge-small-en` — vector embeddings (few-shot retrieval) |
| **httpx** | Async HTTP client for LLM calls |

### Security

| Technology | Purpose |
|------------|---------|
| **PyJWT** | App token generation (not used in demo — no auth) |
| **UUID4** | Session ID generation |
| **python-multipart** | Form parsing (not actively used in demo) |

---

## Frontend

### Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Nuxt 3** | 3.x | Vue meta-framework (SSR + SPA) |
| **Vue 3** | 3.3+ | UI framework (Composition API) |
| **TypeScript** | 5.x | Type safety |
| **Vite** | 4.x | Build tool (via Nuxt) |

### Styling

| Technology | Purpose |
|------------|---------|
| **Tailwind CSS** | Utility-first CSS framework |
| **Nuxt Icon** | Icon system (local endpoint at `/_nuxt_icon`) |
| **nuxt-color-picker** | Color picker component (used in admin pages — not in demo) |

### Document Processing

| Technology | Purpose |
|------------|---------|
| **docx** | Word document generation (export) |
| **mammoth** | Word document parsing (import — not used in demo) |
| **pdfjs-dist** | PDF parsing (not used in demo) |

### State & Communication

| Technology | Purpose |
|------------|---------|
| **Native WebSocket** | Browser WebSocket API for chat |
| **fetch API** | HTTP requests (no Supabase client SDK in demo) |
| **localStorage** | Not used — session is cookie-based |

---

## Infrastructure

### Containerization

| Technology | Purpose |
|------------|---------|
| **Docker** | Container runtime |
| **Docker Compose** | Multi-container orchestration |
| **Docker Hub** | Image registry (`tgsataiwan/ai-proposal-demo`) |

### Reverse Proxy

| Technology | Purpose | Environment |
|------------|---------|-------------|
| **Nginx** | Reverse proxy, TLS termination, routing | Production |
| **Nginx Proxy Manager (NPM)** | GUI-based reverse proxy | Dev VPS |

### CI/CD

| Technology | Purpose |
|------------|---------|
| **GitHub Actions** | Build & deploy pipeline |
| **Docker Hub** | Image push |
| **SSH** | Deploy to VPS |

### Hosting

| Environment | Specs | Domain |
|-------------|-------|--------|
| **Dev VPS** | 1 vCPU / 2GB RAM + 4GB swap | `demo-dev.172.233.79.222.nip.io` |
| **Production** | TBD (separate infrastructure) | `demo-aiproposal.tgsa.com.tw` |

---

## External Services

| Service | Purpose | Auth |
|---------|---------|------|
| **Supabase** | PostgreSQL database + Storage | Service Key + Anon Key |
| **OpenAI** | LLM text generation | API Key |
| **Google AI (Gemini)** | LLM text generation | API Key |
| **assist_link (OAuth IdP)** | User registration & login | OAuth 2.0 (handled by full platform) |

---

## Dependencies

### Backend (requirements.txt)

```text
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0
sqlalchemy>=2.0.0
python-dotenv>=1.0.0
httpx>=0.24.0
supabase>=1.0.0
fastembed>=0.1.0
PyJWT>=2.8.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### Frontend (package.json)

```text
nuxt: ^3.8.0
vue: ^3.3.0
typescript: ^5.2.0
tailwindcss: ^3.3.0
@nuxtjs/tailwindcss: ^6.8.0
@nuxt/icon: ^1.0.0
nuxt-color-picker: ^2.0.0
docx: ^8.2.0
mammoth: ^1.6.0
pdfjs-dist: ^4.0.0
```

---

## Architecture Decision Records

### ADR-001: Hard Fork vs. Shared Codebase

**Decision:** Hard fork the full platform codebase.

**Rationale:**
- The demo has fundamentally different auth model (anonymous vs. authenticated)
- Removing auth from existing code is riskier than building a clean fork
- The demo's scope is narrow (single grant, no admin) — a fork allows aggressive simplification
- Deployment separation (different subdomain, different Docker Compose) makes a fork natural

**Trade-off:** Code duplication for auth/session logic. Changes to LLM service or Supabase layer need to be manually synced.

### ADR-002: Cookie-Based Sessions vs. Header Tokens

**Decision:** Use `demo_session_id` HttpOnly cookie instead of `x-demo-session-id` header.

**Rationale:**
- Cookies are automatically sent by the browser for all requests (HTTP + WebSocket)
- No frontend code needed to attach headers
- No risk of frontend losing the session ID (e.g., localStorage cleared)
- Same security properties as header (opaque UUID, 30-day expiry)

**Trade-off:** Slightly harder to test with tools like curl (need `-b` flag). WebSocket fallback uses `?session_id=` query param for testing.

### ADR-003: Shared Database vs. Separate Database

**Decision:** Share the same Supabase PostgreSQL instance with the full platform.

**Rationale:**
- Seamless migration — data is already in the same database
- No ETL pipeline needed for session transfer
- Schema changes are visible to both apps immediately
- Reduces infrastructure cost

**Trade-off:** Demo bugs could affect the full platform (mitigated by writing only to `demo` table). Schema changes must be backward-compatible.

### ADR-004: Reuse Existing Routers vs. New Demo Router

**Decision:** Adapt existing `generate.py` and `projects.py` routers instead of creating a new `/api/demo/*` router.

**Rationale:**
- The full platform's `generate_plan` and `chat_guidance` have complex logic that would be expensive to duplicate
- Changing the scoping key from `user_id` to `session_id` is a minimal change
- The `projects.py` router already maps to the `demo` table (it was adapted from the full platform's `projects` router)

**Trade-off:** The API surface is larger than a pure demo router (e.g., `/api/template-manager/*` is still present). Some endpoints are not used by the frontend.

---

> Next: [`03-architecture.md`](03-architecture.md)

(End of file)
