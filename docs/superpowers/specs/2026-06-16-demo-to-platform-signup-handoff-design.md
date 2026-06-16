# Demo → Platform Signup Handoff — Design

**Date:** 2026-06-16
**Author:** andy@aiodin.com (with Claude)
**Status:** Draft for review

## Goal

Let anonymous users try the AI proposal **demo** (`ai_proposal_demo`), hit an
interaction limit, sign up at the main portal (`assist_link`), and find their
demo chat history waiting for them as a real project inside the proposal tool
(`ai_proposal_platform`).

The end-to-end claim machinery is **already built**. This work links the three
apps on the test servers and closes two small gaps surfaced by a recent schema
change.

## Test servers

| App | URL |
| --- | --- |
| `assist_link` (portal / OAuth IdP) | https://assist-link-dev.34-80-124-133.nip.io/ |
| `ai_proposal_platform` (real tool / OAuth client) | https://ai-dev.172.233.79.222.nip.io |
| `ai_proposal_demo` (demo) | https://demo-dev.172.233.79.222.nip.io/ |

## Roles of the three apps

- **`ai_proposal_demo`** (Nuxt 3 + FastAPI) — anonymous demo. Stores all
  interaction in a shared Supabase table `ai_proposal_platform.demo`, keyed by a
  `demo_session_id` cookie. On limit, redirects the user to the platform's
  redirect endpoint with `?ref=<session_id>`.
- **`ai_proposal_platform`** (Nuxt 3 + FastAPI) — the real tool. Acts as an
  **OAuth `authorization_code` client** against the portal. Owns the claim logic.
  Shares the same Supabase project as the demo.
- **`assist_link`** (Laravel 11 + Passport) — the portal. Acts as the **OAuth
  IdP** and signup provider. It does **not** need any claim/handoff logic — the
  `ref` never reaches it.

## Architecture / flow

```
Anonymous user
  │  prompts demo (writes ai_proposal_platform.demo row, keyed by demo_session_id)
  ▼
Demo limit reached
  │  modal CTA → GET https://ai-dev.../api/external-auth/redirect?ref=<session_id>
  ▼
ai_proposal_platform /api/external-auth/redirect
  │  stores ref in `pending_demo_claim` cookie (own domain)
  │  302 → https://assist-link-dev.../oauth/authorize?client_id=…&response_type=code&redirect_uri=<platform callback>&state=…
  ▼
assist_link /oauth/authorize
  │  user unauthenticated → /login → "register personal account" → /personal/register
  │  after signup, url.intended resumes /oauth/authorize → issues `code`
  ▼
ai_proposal_platform /api/external-auth/callback
  │  POST /oauth/token (authorization_code, client_secret_post) → access_token
  │  GET /api/user (Bearer) → { data: { id, email, subscription.plan.id, … } }
  │  resolve/create canonical Supabase user (provider='tgsa_oauth', provider_subject=data.id)
  │  claim_demo_session(ref, user_id): copy demo → new projects row
  ▼
Redirect → /projects/{id}   (demo chat now lives in the user's account)
```

Re-login later resolves the same canonical user (stable `provider_subject` =
assist_link `users.id`), so the claimed project persists across sessions.

## What already works (verified, no change needed)

- Demo writes `conversation_history`, `saved_plan`, `stored_answer` to the
  `demo` row and builds the CTA URL `{DEMO_REGISTER_REDIRECT_URL}?ref={session_id}`.
- Platform `/api/external-auth/redirect` + `/api/external-auth/callback`
  implement the full OAuth client, `pending_demo_claim` cookie, and
  `claim_demo_session()` (atomic SELECT … FOR UPDATE → INSERT projects → UPDATE
  demo status='claimed'; idempotent per user; cross-user safe).
- **OAuth field contract already matches.** Platform callback reads
  `data.sub || data.id`, `data.email`, role from `data.subscription.plan.id`.
  assist_link `/api/user` returns exactly `{ status, data: { id, name, email,
  subscription: { plan: { id } }, … } }`. **No adapter / field mapping needed.**
- assist_link `/oauth/authorize` redirects unauthenticated users to `/login`
  and resumes the intended authorize URL via `url.intended`.
- Platform forces the callback `redirect_uri` to HTTPS — correct behind the
  nip.io reverse proxies.
- Cross-domain cookies are **not** involved: the `ref` rides as a query param;
  the `pending_demo_claim` cookie lives only on the platform domain and is read
  back on the same-domain callback.

## Decisions

1. **Signup path:** demo users create a **personal account** (`/personal/register`),
   not the heavier enterprise `/register` (which requires company name + tax_id).
2. **OAuth client:** a **new dedicated** client UUID for `ai_proposal_platform`,
   added to assist_link's `skipsAuthorization` trusted list (no consent screen)
   and bound to an `engine_code` so engine-usage tracking attributes correctly.
   All demo users share this one client UUID — user identity is carried by the
   per-user login, not the client_id.
3. **Title source on claim:** prefer the explicit `demo.title`; fall back to
   `stored_answer['plan_name']`; final fallback `"從 Demo 匯入的計畫書"`.
4. **`section_versions`:** add the column to the shared `demo` table via
   migration, and copy it into `projects` on claim. This fixes the latent demo
   insert bug and gives claimed projects the creation-time version snapshot,
   matching the live system.

## Recent schema change (the two gaps)

The demo's latest commit (`2e3b651`, "matching live system schema") added two
columns the demo now writes to the shared `demo` table:

- **`title`** (TEXT, ≤255) — explicit, user-editable project title. Editable in
  the register modal and persisted via `PUT /demo` so it survives the handoff.
- **`section_versions`** (JSONB) — snapshot of section-schema versions at session
  creation, mirroring `projects.section_versions`. Captured via
  `_get_section_current_versions(grant_id, template_id)`.

The platform's `claim_demo_session()` (current `dev`, lines ~758–858) has **not**
caught up:

- It derives the title from `stored_answer['plan_name']` and **ignores
  `demo.title`** → the user's edited title is lost on claim.
- It does **not** read or copy `section_versions` → claimed projects land with
  `NULL` section_versions, breaking parity with natively-created projects (docx
  export / section-version resolution depend on it).

The demo commit shipped **no migration** for these columns — it assumes the live
shared schema already has them.

## Changes required

### 0. Shared `demo` table schema — VERIFIED 2026-06-16

Queried the shared Supabase project (`ai_proposal_platform` schema):

| Column | `demo` | `projects` |
| --- | --- | --- |
| `title` | present (27/27 rows set) | present |
| `section_versions` | **MISSING** | present |

- **`title`** works end-to-end; the title-precedence claim patch is valid.
- **`section_versions` is missing from `demo`.** The demo's new
  `ensure_demo_session` code writes `payload["section_versions"]` only when
  non-empty; it currently stays empty because `DEMO_GRANT_ID` is unset, so the
  insert succeeds. Once a grant is configured (the "multi-template demo prep"
  direction of the same commit), the insert against the nonexistent column will
  fail. **This is a latent bug independent of the handoff.**

**Decision (Decisions #4):** add `section_versions jsonb` to the shared `demo`
table via `ai_proposal_demo/database-migrations/002_demo_section_versions.sql`
(nullable, non-destructive). Run before relying on multi-template demo grants.
After this, the demo's `ensure_demo_session` write succeeds and the claim can
copy the column into `projects`.

### 1. `assist_link` (portal / IdP)

- Register a **new dedicated OAuth `authorization_code` client** (seeder
  migration or `php artisan passport:client`) with:
  - `redirect_uris` including `https://ai-dev.172.233.79.222.nip.io/api/external-auth/callback`
  - `grant_types`: `authorization_code`, `refresh_token`
  - an `engine_code` binding for the proposal tool
- Add the new client UUID to the `skipsAuthorization` trusted list
  (`app/Models/Passport/...` / `PassportClient.php`).
- Ensure new demo users can **register-and-resume**: `/login` surfaces a
  "register personal account" link, and `PersonalRegisteredUserController`
  honors `url.intended` / the same `resolvePostLoginRedirect` logic the login
  controller uses, so signup continues the `/oauth/authorize` flow.

### 2. `ai_proposal_platform` (real tool / OAuth client)

- `.env` (test):
  - `MOTHER_PLATFORM_BASE_URL=https://assist-link-dev.34-80-124-133.nip.io`
  - `EXTERNAL_OAUTH_CLIENT_ID` / `EXTERNAL_OAUTH_CLIENT_SECRET` = the new client
  - `EXTERNAL_OAUTH_PROVIDER=tgsa_oauth` (keep, so identities resolve consistently)
  - `EXTERNAL_OAUTH_FRONTEND_CALLBACK_URL` → the platform's own frontend callback
- **Code:** patch `claim_demo_session()` in
  `backend/app/services/supabase_service.py`:
  - add `title, section_versions` to the `SELECT … FROM ai_proposal_platform.demo`
  - title precedence: `demo.title` → `stored_answer['plan_name']` → default
  - add `section_versions` to the `INSERT INTO projects (...)` columns + values
    (JSON-encoded, like `saved_plan`)

### 3. `ai_proposal_demo` (demo)

- `.env` / frontend env (test):
  - `DEMO_REGISTER_REDIRECT_URL=https://ai-dev.172.233.79.222.nip.io/api/external-auth/redirect`
  - `NUXT_PUBLIC_PLATFORM_HOME_URL=https://ai-dev.172.233.79.222.nip.io/api/external-auth/redirect`

## Identity & data model

- Canonical user lives in Supabase (`ai_proposal_platform.users` +
  `user_identities`), federated by `(provider='tgsa_oauth',
  provider_subject=assist_link users.id)`.
- assist_link keeps its own users in MariaDB; it only authenticates. The link
  between the two is the OAuth subject (`data.id`).
- Personal vs enterprise account type does not affect identity resolution.

## Edge cases to verify in testing

- Consent screen is skipped (new client is on the trusted list).
- Brand-new user can register a personal account and resume the authorize flow.
- `provider_subject` is stable across logins → the claimed project reappears on
  re-login.
- HTTPS `redirect_uri` works behind the nip.io reverse proxy.
- Claim idempotency: a double callback for the same user returns the existing
  project; a different user claiming an already-claimed session fails silently.
- Edited title and `section_versions` both land on the claimed project.

## Out of scope

- Production (`portal.tgsaapp.com`) wiring — test servers only for now.
- Any claim/handoff logic in assist_link (not needed).
- Changes to the demo limit logic itself.

## Open risks

- Schema check is done (see step 0): `title` present everywhere; `demo` needs a
  `section_versions` migration (Decisions #4). The migration is a prerequisite
  for the claim's section_versions copy and for multi-template demo grants.
- assist_link's personal-signup resume may need a small controller change if it
  doesn't already honor `url.intended` — to be confirmed during implementation.
