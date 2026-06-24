# 15 - Demo to Platform Handoff

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24  
> **Design Doc:** `docs-private/specs/2026-06-16-demo-to-platform-signup-handoff-design.md`

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [API Contracts](#api-contracts)
5. [Database Schema](#database-schema)
6. [Field Mapping](#field-mapping)
7. [Error Handling](#error-handling)
8. [Security Considerations](#security-considerations)
9. [Testing Checklist](#testing-checklist)

---

## Overview

The demo-to-platform handoff is the **critical conversion mechanism**. When a demo visitor hits a usage limit (20 prompts, 100K tokens, 1 generation, 1 download), they are prompted to sign up for the full platform. Upon successful signup, all their demo session data is **atomically migrated** to a new project in their account.

**Key principles:**
- **Zero data loss** - All chat history, answers, generated plans, and execution logs are preserved
- **Seamless UX** - User clicks one button, completes OAuth, and lands on their new project
- **Idempotent** - Same user claiming same session twice returns the same project
- **Cross-user safe** - One user cannot claim another user's session

---

## Architecture

### Three-App System

- **ai_proposal_demo** (Demo): Anonymous chat, cookie session, upsell CTA
- **ai_proposal_platform** (Full Platform): OAuth client, claim_demo_session(), project CRUD
- **assist_link** (OAuth IdP): User registry, authentication, subscription

### Shared Database

Both demo and platform read/write to the same Supabase project:
- **Demo writes:** `demo` table, `demo_ip_limits` table
- **Platform writes:** `users`, `projects`, `execution_logs`, `usage_logs`
- **Migration writes:** Platform calls `migrate_demo_to_project()` which writes to platform tables and updates the demo row

---

## Data Flow

### Step 1: Upsell CTA

**Trigger:** User hits any limit (prompts, tokens, generation, download).

**Frontend behavior:**
```typescript
const registerUrl = `${config.public.platformHomeUrl}?ref=${sessionId}`;
window.open(registerUrl, '_blank');
```

**URL:**
```
https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<session_id>
```

### Step 2: Store Ref

**Platform endpoint:** `GET /api/external-auth/redirect`

**Backend behavior:**
- Validate `ref` is UUID
- Set `pending_demo_claim` cookie (15 min expiry)
- Redirect to OAuth IdP

### Step 3: OAuth Flow

**Standard OAuth 2.0 authorization code flow:**
1. Platform redirects to `assist_link` OAuth authorize endpoint
2. User registers or logs in
3. `assist_link` redirects back to platform callback with `?code=...`

### Step 4: Callback & Claim

**Platform endpoint:** `GET /api/external-auth/callback`

**Backend behavior:**
- Read `pending_demo_claim` cookie
- Exchange code for token
- Get user info
- Create or resolve Supabase user
- Call `claim_demo_session(ref, user_id)`
- Redirect to `/projects/<id>` or `/projects`

### Step 5: SQL Migration

**Function:** `ai_proposal_platform.migrate_demo_to_project(session_id TEXT, user_id UUID) -> UUID`

**Atomic steps:**
1. Lock the demo row (SELECT ... FOR UPDATE)
2. Snapshot `section_versions` if missing
3. Create new `projects` row with all demo data
4. Drain `pending_execution_events` -> `execution_logs`
5. Drain `pending_usage_logs` -> `usage_logs`
6. Mark demo row as `claimed`
7. Return new `project_id`

---

## API Contracts

### Demo -> Platform

**Request:**
```
GET https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<session_id>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ref` | `UUID` | Yes | Demo session ID |

**Response:**
- `302` -> Redirect to OAuth IdP
- `Set-Cookie: pending_demo_claim=<ref>; Max-Age=900; HttpOnly; SameSite=Lax`

### Platform -> OAuth IdP

**Request:**
```
GET https://portal.tgsaapp.com/oauth/authorize?client_id=<id>&redirect_uri=<callback>&response_type=code&state=<state>
```

### OAuth IdP -> Platform

**Request:**
```
GET https://aiproposal.tgsa.com.tw/api/external-auth/callback?code=<code>&state=<state>
```

**Response:**
- `302` -> Redirect to `/projects/<id>` (if claim succeeded)
- `302` -> Redirect to `/projects` (if claim failed or no ref)

---

## Database Schema

### Demo Table (Pre-Claim)

```
demo row (status = 'active')
- session_id: UUID
- conversation_history: JSONB array
- stored_answer: {chat_answers, chat_answers_meta, user_input}
- saved_plan: [{version 1}]
- pending_execution_events: [{event_type, payload, logged_at}]
- pending_usage_logs: [{model_id, cost, action, logged_at}]
- section_versions: {section_id: version_number}
- title: "My Project"
- mode: "interactive"
- status: "active"
- claimed_by: NULL
- claimed_at: NULL
- claimed_project_id: NULL
```

### After Claim

```
demo row (status = 'claimed')
- status: "claimed"
- claimed_by: user UUID
- claimed_at: timestamp
- claimed_project_id: project UUID

projects row (newly created)
- id: project UUID
- user_id: user UUID
- title: "My Project"
- description: "Imported from demo"
- grant_id: "sbir"
- template_id: "sbir_p1"
- saved_plan: [{version 1}]
- stored_answer: {chat_answers: {...}}
- conversation_history: [...]
- section_versions: {...}
- mode: "interactive"
- created_at: original demo timestamp
- updated_at: now
- is_deleted: FALSE

execution_logs (new rows)
- project_id: project UUID
- user_id: user UUID
- event_type: "stored_answer_updated"
- payload: {...}
- created_at: original event timestamp

usage_logs (new rows)
- user_id: user UUID
- model_id: "gpt-5.1-chat-latest"
- input_token: 1250
- output_token: 890
- cost: 0.001337
- action: "generate_chat"
- project_id: project UUID
```

---

## Field Mapping

| Demo Column | Projects Column | Transformation | Notes |
|-------------|-----------------|----------------|-------|
| `grant_id` | `grant_id` | Direct copy | - |
| `template_id` | `template_id` | Direct copy | - |
| `saved_plan` | `saved_plan` | Direct copy | JSONB -> JSONB |
| `stored_answer` | `stored_answer` | Direct copy | JSONB -> JSONB |
| `conversation_history` | `conversation_history` | Direct copy | JSONB -> JSONB |
| `title` | `title` | Direct copy | Priority 1 |
| `stored_answer->>'plan_name'` | `title` | Fallback | Priority 2 |
| `'Imported from demo'` | `title` | Default | Priority 3 |
| `section_versions` | `section_versions` | Direct copy | Snapshot of versions |
| `mode` | `mode` | Direct copy | Default: 'interactive' |
| `claimed_by` | `user_id` | Set on new row | - |
| `created_at` | `created_at` | Direct copy | - |
| `NOW()` | `updated_at` | Set to now | - |
| `FALSE` | `is_deleted` | Default | - |
| `pending_execution_events` | `execution_logs` | Drain array | One row per event |
| `pending_usage_logs` | `usage_logs` | Drain array | One row per log |

---

## Error Handling

### Error Cases

| Error | Cause | User Experience | Backend Action |
|-------|-------|-----------------|----------------|
| `not_found` | Session ID does not exist or expired | User lands on default page | Log warning, no error shown |
| `already_claimed` | Another user claimed this session | User lands on default page | Log warning, no error shown |
| `invalid_ref` | `ref` is not a valid UUID | User lands on default page | Log warning, no error shown |
| `db_error` | Database connection failed | User lands on default page | Log error, retry or fail silently |
| `oauth_error` | OAuth provider error | User sees OAuth error | Log error, redirect to login |

### Idempotency

**Same user, same session:**
- First claim: Creates project, returns project_id
- Second claim: Returns **same** project_id (idempotent)

**Different user, same session:**
- First claim: Success
- Second claim: Returns `already_claimed` error silently

**Implementation:**
```sql
-- The FOR UPDATE lock ensures only one claim succeeds
-- The claimed_by column prevents double-claim
-- The status='claimed' prevents re-claim
```

---

## Security Considerations

### 1. Ref Validation

- `ref` must be a valid UUID format
- Invalid refs are rejected before cookie is set

### 2. Cookie Security

- `pending_demo_claim` cookie:
  - `HttpOnly`: Prevents XSS theft
  - `SameSite=Lax`: Prevents CSRF
  - `Max-Age=900`: 15-minute expiry
  - `Secure`: HTTPS only in production

### 3. Cross-Domain Safety

- `pending_demo_claim` cookie is **domain-scoped** to the platform
- Demo cannot read or forge this cookie
- Cookie is only read on the platform callback

### 4. Atomicity

- `SELECT ... FOR UPDATE` locks the demo row
- `INSERT` and `UPDATE` happen in the same transaction
- No partial migration possible

### 5. Data Privacy

- Demo data is **anonymous** (no PII)
- Migration only copies user-provided project data
- No sensitive data (passwords, API keys) is migrated

---

## Testing Checklist

### End-to-End Test Flow

```
1. Open demo in browser
   - Verify: Page loads, session created, cookie set

2. Chat with AI (fill some fields)
   - Verify: Messages appear, fields populated

3. Hit prompt limit (or click generate)
   - Verify: Limit notice appears, register CTA shown

4. Click "Sign Up"
   - Verify: Redirected to platform /api/external-auth/redirect?ref=<id>

5. Complete OAuth signup
   - Verify: Redirected to platform /api/external-auth/callback
   - Verify: pending_demo_claim cookie is set

6. Land on platform
   - Verify: Redirected to /projects/<new_id>
   - Verify: Project title matches demo title
   - Verify: Chat history present
   - Verify: Answers present
   - Verify: Generated plan present

7. Check demo row
   - Verify: status = 'claimed'
   - Verify: claimed_by = user UUID
   - Verify: claimed_project_id = project UUID

8. Re-login
   - Verify: Same project appears (idempotent)
```

### Edge Cases

| Case | Expected Result |
|------|-----------------|
| Expired session | Fresh mint, no migration attempt |
| Already claimed | Silent failure, default redirect |
| Invalid ref | Silent failure, default redirect |
| No chat data | Empty project created |
| No plan generated | Empty project created |
| Same user re-claims | Returns same project_id |

### Database Verification Queries

```sql
-- Check migration success
SELECT 
  d.session_id,
  d.status,
  d.claimed_by,
  d.claimed_at,
  d.claimed_project_id,
  p.title,
  p.created_at as project_created_at
FROM ai_proposal_platform.demo d
LEFT JOIN ai_proposal_platform.projects p ON d.claimed_project_id = p.id
WHERE d.status = 'claimed'
ORDER BY d.claimed_at DESC
LIMIT 10;

-- Check data completeness
SELECT 
  p.id,
  p.title,
  jsonb_array_length(p.conversation_history) as messages,
  jsonb_object_keys(p.stored_answer->'chat_answers') as answers,
  jsonb_array_length(p.saved_plan) as versions
FROM ai_proposal_platform.projects p
WHERE p.created_at > NOW() - INTERVAL '24 hours';

-- Check execution logs
SELECT 
  project_id,
  COUNT(*) as event_count,
  MIN(created_at) as first_event,
  MAX(created_at) as last_event
FROM ai_proposal_platform.execution_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY project_id;

-- Check usage logs
SELECT 
  project_id,
  SUM(cost) as total_cost,
  SUM(input_token + output_token) as total_tokens
FROM ai_proposal_platform.usage_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY project_id;
```

---

> End of Documentation

(End of file)
