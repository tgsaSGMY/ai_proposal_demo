# 08 — Environment Variables

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Backend `.env`](#backend-env)
2. [Frontend `.env`](#frontend-env)
3. [Docker Compose `.env`](#docker-compose-env)
4. [Variable Reference](#variable-reference)
5. [Environment-Specific Configurations](#environment-specific-configurations)
6. [Security Best Practices](#security-best-practices)

---

## Backend `.env`

**File:** `backend/.env` (DO NOT commit — add to `.gitignore`)

```env
# ============================================
# SUPABASE / DATABASE
# ============================================
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
DATABASE_URL=postgresql://postgres:<password>@<host>:<port>/<database>?schema=ai_proposal_platform

# ============================================
# LLM PROVIDERS
# ============================================
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GEMINI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# DEMO CONFIGURATION
# ============================================
# Hard-coded grant/template IDs that the demo will load.
# When both are set (non-empty), the demo ALWAYS uses this exact pair
# and never falls back to the first item in the catalog.
DEMO_GRANT_ID=sbir
DEMO_TEMPLATE_ID=sbir_p1

# Hard cap on chat turns (user prompts) per session.
# DEMO_MAX_PROMPTS_PER_SESSION is the canonical name;
# DEMO_INTERACTION_LIMIT is kept as a legacy alias.
DEMO_MAX_PROMPTS_PER_SESSION=20
DEMO_INTERACTION_LIMIT=20

# Token cap per session (input + output tokens).
DEMO_MAX_TOKENS_PER_SESSION=100000

# Max .docx report generations per session.
DEMO_MAX_GENERATIONS_PER_SESSION=1

# Session expiry.
# DEMO_SESSION_EXPIRY_MINUTES takes priority (for dev testing).
# If not set, falls back to DEMO_SESSION_EXPIRY_DAYS (default 7 days).
DEMO_SESSION_EXPIRY_DAYS=7
DEMO_SESSION_EXPIRY_MINUTES=10080

# Per-IP cap on demo session creation (mint-time only).
DEMO_IP_HOURLY_LIMIT=3
DEMO_IP_DAILY_LIMIT=5

# Where the visitor is redirected when they hit the cap.
# Include ?ref=<session_id> server-side when emitting the redirect.
DEMO_REGISTER_REDIRECT_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect

# Full platform URL (used for CORS and signup redirects).
FULL_PLATFORM_URL=https://aiproposal.tgsa.com.tw

# Demo subdomain (used for CORS allowlist).
DEMO_FRONTEND_URL=https://demo-aiproposal.tgsa.com.tw

# ============================================
# APP SECURITY
# ============================================
APP_JWT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# EXTERNAL OAUTH (not used in demo, but kept for compatibility)
# ============================================
EXTERNAL_OAUTH_PROVIDER=tgsa_oauth
EXTERNAL_OAUTH_CLIENT_ID=
EXTERNAL_OAUTH_CLIENT_SECRET=
EXTERNAL_OAUTH_AUTHORIZE_URL=
EXTERNAL_OAUTH_TOKEN_URL=
EXTERNAL_OAUTH_USERINFO_URL=
EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL=http://localhost:3000/external-auth-callback

# ============================================
# EMBEDDING
# ============================================
EMBEDDING_MODEL_NAME=BAAI/bge-small-en
```

---

## Frontend `.env`

**File:** `frontend/.env` (DO NOT commit — add to `.gitignore`)

```env
# ============================================
# API BASE
# ============================================
NUXT_PUBLIC_API_BASE_URL=https://demo-aiproposal.tgsa.com.tw/api

# ============================================
# SUPABASE
# ============================================
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_ANON_KEY=<anon_key>

# ============================================
# PLATFORM URL
# ============================================
# Where to redirect for registration.
# Usually the full platform's OAuth redirect endpoint.
NUXT_PUBLIC_PLATFORM_HOME_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect

# ============================================
# DEMO CONFIGURATION
# ============================================
# Must match backend DEMO_GRANT_ID / DEMO_TEMPLATE_ID.
# When set, the frontend uses these exact values and never falls back.
NUXT_PUBLIC_DEMO_GRANT_ID=sbir
NUXT_PUBLIC_DEMO_TEMPLATE_ID=sbir_p1

# Session expiry in minutes (used for cookie max-age calculation).
NUXT_PUBLIC_DEMO_SESSION_EXPIRY_MINUTES=10080
```

---

## Docker Compose `.env`

**File:** `.env` (in project root, for Docker Compose)

```env
# ============================================
# DOCKER IMAGE TAGS
# ============================================
FRONTEND_IMAGE=tgsataiwan/ai-proposal-demo:frontend-dev
BACKEND_IMAGE=tgsataiwan/ai-proposal-demo:backend-dev

# ============================================
# NGINX
# ============================================
NGINX_PORT=80
NGINX_HTTPS_PORT=443

# ============================================
# BACKEND ENV (injected into container)
# ============================================
# All backend .env vars are passed through docker-compose.yml
# via the `env_file` or `environment` directive.
```

---

## Variable Reference

### Backend Variables

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `SUPABASE_URL` | ✅ | — | Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_SERVICE_KEY` | ✅ | — | Supabase service role key | `eyJ...` |
| `DATABASE_URL` | ✅ | — | Direct PostgreSQL connection | `postgresql://...` |
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key | `sk-...` |
| `GEMINI_API_KEY` | ⚠️ | — | Google Gemini API key | `...` |
| `DEMO_GRANT_ID` | ⚠️ | `""` | Hard-coded grant ID | `sbir` |
| `DEMO_TEMPLATE_ID` | ⚠️ | `""` | Hard-coded template ID | `sbir_p1` |
| `DEMO_MAX_PROMPTS_PER_SESSION` | ❌ | `20` | Max chat prompts | `20` |
| `DEMO_INTERACTION_LIMIT` | ❌ | `20` | Legacy alias for above | `20` |
| `DEMO_MAX_TOKENS_PER_SESSION` | ❌ | `100000` | Max tokens per session | `100000` |
| `DEMO_MAX_GENERATIONS_PER_SESSION` | ❌ | `1` | Max plan generations | `1` |
| `DEMO_SESSION_EXPIRY_DAYS` | ❌ | `7` | Session expiry in days | `7` |
| `DEMO_SESSION_EXPIRY_MINUTES` | ❌ | `10080` | Session expiry in minutes | `10080` |
| `DEMO_IP_HOURLY_LIMIT` | ❌ | `3` | Max sessions per IP per hour | `3` |
| `DEMO_IP_DAILY_LIMIT` | ❌ | `5` | Max sessions per IP per day | `5` |
| `DEMO_REGISTER_REDIRECT_URL` | ❌ | `https://aiproposal.tgsa.com.tw/api/external-auth/redirect` | Registration redirect URL | `https://...` |
| `FULL_PLATFORM_URL` | ❌ | `https://aiproposal.tgsa.com.tw` | Full platform URL | `https://...` |
| `DEMO_FRONTEND_URL` | ❌ | `https://demo-aiproposal.tgsa.com.tw` | Demo frontend URL | `https://...` |
| `APP_JWT_SECRET` | ⚠️ | — | JWT signing secret | `secret-...` |
| `EMBEDDING_MODEL_NAME` | ❌ | `BAAI/bge-small-en` | Embedding model | `BAAI/bge-small-en` |

### Frontend Variables

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `NUXT_PUBLIC_API_BASE_URL` | ✅ | — | Backend API base URL | `https://demo.../api` |
| `SUPABASE_URL` | ✅ | — | Supabase project URL | `https://abc123.supabase.co` |
| `SUPABASE_ANON_KEY` | ✅ | — | Supabase anon key | `eyJ...` |
| `NUXT_PUBLIC_PLATFORM_HOME_URL` | ✅ | — | Platform registration URL | `https://aiproposal...` |
| `NUXT_PUBLIC_DEMO_GRANT_ID` | ⚠️ | `""` | Demo grant ID | `sbir` |
| `NUXT_PUBLIC_DEMO_TEMPLATE_ID` | ⚠️ | `""` | Demo template ID | `sbir_p1` |
| `NUXT_PUBLIC_DEMO_SESSION_EXPIRY_MINUTES` | ❌ | `10080` | Cookie max-age in minutes | `10080` |

> **Note:** `NUXT_PUBLIC_` prefix means the variable is exposed to the browser. Never put secrets here.

---

## Environment-Specific Configurations

### Local Development

**Backend:**
```env
SUPABASE_URL=https://<dev-project>.supabase.co
DATABASE_URL=postgresql://...
DEMO_REGISTER_REDIRECT_URL=http://localhost:3000/api/external-auth/redirect
DEMO_FRONTEND_URL=http://localhost:3000
DEMO_SESSION_EXPIRY_MINUTES=60
```

**Frontend:**
```env
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NUXT_PUBLIC_PLATFORM_HOME_URL=http://localhost:3000/api/external-auth/redirect
```

### Dev VPS

**Backend:**
```env
DEMO_REGISTER_REDIRECT_URL=https://ai-dev.172.233.79.222.nip.io/api/external-auth/redirect
DEMO_FRONTEND_URL=https://demo-dev.172.233.79.222.nip.io
DEMO_SESSION_EXPIRY_DAYS=7
```

**Frontend:**
```env
NUXT_PUBLIC_API_BASE_URL=https://demo-dev.172.233.79.222.nip.io/api
NUXT_PUBLIC_PLATFORM_HOME_URL=https://ai-dev.172.233.79.222.nip.io/api/external-auth/redirect
```

### Production

**Backend:**
```env
DEMO_REGISTER_REDIRECT_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect
DEMO_FRONTEND_URL=https://demo-aiproposal.tgsa.com.tw
DEMO_SESSION_EXPIRY_DAYS=7
DEMO_IP_HOURLY_LIMIT=3
DEMO_IP_DAILY_LIMIT=5
```

**Frontend:**
```env
NUXT_PUBLIC_API_BASE_URL=https://demo-aiproposal.tgsa.com.tw/api
NUXT_PUBLIC_PLATFORM_HOME_URL=https://aiproposal.tgsa.com.tw/api/external-auth/redirect
```

---

## Security Best Practices

### 1. Never Commit `.env` Files

```gitignore
# .gitignore
backend/.env
frontend/.env
.env
```

### 2. Rotate Secrets Regularly

- `SUPABASE_SERVICE_KEY`: Rotate every 90 days
- `OPENAI_API_KEY`: Rotate every 90 days
- `GEMINI_API_KEY`: Rotate every 90 days
- `APP_JWT_SECRET`: Rotate every 180 days

### 3. Use Different Keys Per Environment

- Dev Supabase project ≠ Production Supabase project
- Dev API keys ≠ Production API keys

### 4. Restrict API Keys

- OpenAI: Use project-level keys with usage limits
- Gemini: Use API key restrictions (IP allowlist)
- Supabase: Use Row Level Security (RLS) on public tables

### 5. Cookie Security

- `HttpOnly`: Prevents JavaScript access to `demo_session_id`
- `SameSite=Lax`: Prevents CSRF in cross-site requests
- `Secure`: Only send over HTTPS (set to `True` in production)
- `Max-Age`: 30 days (configurable via `DEMO_SESSION_EXPIRY_MINUTES`)

### 6. Rate Limiting

- `DEMO_IP_HOURLY_LIMIT` and `DEMO_IP_DAILY_LIMIT` prevent session mint abuse
- Currently disabled in code but should be enabled in production

---

> Next: [`09-deployment-guide.md`](09-deployment-guide.md)

(End of file)
