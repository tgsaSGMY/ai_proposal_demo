# API Endpoints Reference

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24  
> **Base URL:** `https://demo-aiproposal.tgsa.com.tw/api`  
> **Authentication:** None — all requests are anonymous. Session scope is provided by the `demo_session_id` cookie (HttpOnly, SameSite=Lax, 30-day max-age).

---

## Table of Contents

1. [Demo Session](#demo-session)
2. [Plan Generation](#plan-generation)
3. [Config](#config)
4. [Error Handling](#error-handling)
5. [Common Headers](#common-headers)

---

## Demo Session

### `GET /api/demo`

**Bootstrap the visitor's demo session.**

- On the **first request**, mints a new `demo_session_id` cookie and creates a row in `ai_proposal_platform.demo`.
- On **subsequent requests**, reuses the existing cookie if the row is still `active` and not expired.
- If the row was claimed, expired, or never existed, a **fresh session** is minted (and the cookie is rotated).

> **Rate limiting:** On the **mint branch only** (when a new session is created), a per-IP check is performed against `demo_ip_limits`. Reuse of an existing cookie **never** triggers rate limiting.

#### Request

```http
GET /api/demo
Cookie: demo_session_id=<existing_uuid_or_absent>
```

#### Response — `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "ip_address": "203.0.113.42",
  "grant_id": "sbir",
  "template_id": "sbir_p1",
  "interaction_count": 0,
  "total_tokens_used": 0,
  "has_generated_docx": false,
  "download_count": 0,
  "conversation_history": [],
  "stored_answer": {},
  "saved_plan": [],
  "pending_execution_events": [],
  "pending_usage_logs": [],
  "section_versions": null,
  "title": null,
  "mode": "interactive",
  "status": "active",
  "created_at": "2026-06-24T06:30:00+00:00",
  "expires_at": "2026-07-01T06:30:00+00:00",
  "claimed_by": null,
  "claimed_at": null,
  "claimed_project_id": null
}
```

**Response Headers:**

```http
Set-Cookie: demo_session_id=550e8400-e29b-41d4-a716-446655440000; Max-Age=2592000; HttpOnly; Path=/; SameSite=Lax
```

#### Response — `429 Too Many Requests` (mint branch only)

```json
{
  "detail": {
    "code": "DEMO_HOURLY_LIMIT_EXCEEDED",
    "retry_after": 1800
  }
}
```

**Response Headers:**

```http
Retry-After: 1800
```

| Error Code | Condition | `retry_after` |
|------------|-----------|---------------|
| `DEMO_HOURLY_LIMIT_EXCEEDED` | IP created ≥ 3 sessions this hour | Seconds until next hour boundary |
| `DEMO_DAILY_LIMIT_EXCEEDED` | IP created ≥ 5 sessions today | Seconds until next day boundary |

---

### `PUT /api/demo`

**Update the demo session payload.**

Only fields provided in the request body are updated. Other fields are left untouched.

#### Request

```http
PUT /api/demo
Content-Type: application/json
Cookie: demo_session_id=<uuid>

{
  "grant_id": "sbir",
  "template_id": "sbir_p1",
  "saved_plan": [
    {
      "number": 1,
      "title": "Version 1",
      "timestamp": "2026-06-24T06:35:00+00:00",
      "data": { "company_overview": { "content": "..." } }
    }
  ],
  "stored_answer": {
    "chat_answers": { "company_overview::business_model": "B2B SaaS" },
    "chat_answers_meta": { "company_overview::business_model": { "updated_at": "2026-06-24T06:35:00+00:00" } }
  },
  "conversation_history": [
    { "id": "user-abc123", "role": "user", "type": "text", "content": "Hi", "timestamp": "2026-06-24T06:30:00+00:00" }
  ],
  "has_generated_docx": true,
  "download_count": 1,
  "title": "My SBIR Project"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `grant_id` | `string` | No | Grant identifier (e.g. `sbir`) |
| `template_id` | `string` | No | Template identifier (e.g. `sbir_p1`) |
| `saved_plan` | `array` | No | Array of plan version objects |
| `stored_answer` | `object` | No | `{ chat_answers, chat_answers_meta, user_input }` |
| `conversation_history` | `array` | No | Array of message objects |
| `has_generated_docx` | `boolean` | No | Whether the plan has been generated |
| `download_count` | `integer` | No | Number of downloads (0 or 1) |
| `title` | `string` | No | User-editable project title |

#### Response — `200 OK`

Returns the **updated** row (same schema as `GET /api/demo`).

#### Response — `400 Bad Request`

```json
{
  "detail": "missing demo_session_id cookie — load the demo page (GET /demo) first"
}
```

---

### `DELETE /api/demo`

**Reset the demo session.**

Wipes the `demo` row. The cookie is **not** cleared from the browser, but the next `GET /api/demo` will see a stale/invalid cookie and mint a fresh session.

#### Request

```http
DELETE /api/demo
Cookie: demo_session_id=<uuid>
```

#### Response — `200 OK`

```json
{
  "status": "reset",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### `GET /api/demo/status`

**Return the current demo session status and configured template.**

The frontend uses this to:
1. Determine the exact `grant_id` / `template_id` to load from the catalog
2. Check if any limits have been reached
3. Get the registration redirect URL

> **Note:** If `DEMO_GRANT_ID` and `DEMO_TEMPLATE_ID` are configured in the backend `.env`, the session row is **patched** to match them automatically. This ensures old sessions always use the current demo template.

#### Request

```http
GET /api/demo/status
Cookie: demo_session_id=<uuid>
```

#### Response — `200 OK`

```json
{
  "grant_id": "sbir",
  "template_id": "sbir_p1",
  "interaction_limit": 20,
  "interaction_count": 5,
  "limit_reached": false,
  "chat_limit_reached": false,
  "generation_limit_reached": false,
  "download_limit_reached": false,
  "all_limits_reached": false,
  "has_generated_docx": false,
  "download_count": 0,
  "register_url": "https://aiproposal.tgsa.com.tw/api/external-auth/redirect",
  "expires_at": "2026-07-01T06:30:00+00:00",
  "section_versions": null
}
```

#### Response Schema

| Field | Type | Description |
|-------|------|-------------|
| `grant_id` | `string \| null` | Configured grant ID from `.env` |
| `template_id` | `string \| null` | Configured template ID from `.env` |
| `interaction_limit` | `integer` | Max prompts per session (default 20) |
| `interaction_count` | `integer` | Current prompt count |
| `limit_reached` | `boolean` | `true` if `interaction_count >= interaction_limit` |
| `chat_limit_reached` | `boolean` | Same as `limit_reached` |
| `generation_limit_reached` | `boolean` | `true` if `has_generated_docx` is `true` |
| `download_limit_reached` | `boolean` | `true` if `download_count >= 1` |
| `all_limits_reached` | `boolean` | `true` if chat + generation + download all reached |
| `has_generated_docx` | `boolean` | Whether plan has been generated |
| `download_count` | `integer` | Download count |
| `register_url` | `string` | Full platform registration redirect URL |
| `expires_at` | `string \| null` | ISO 8601 session expiry timestamp |
| `section_versions` | `object \| null` | Section version snapshot |

#### Response — `401 Unauthorized`

```json
{
  "detail": "Demo session expired or not found"
}
```

Occurs when the session row has been deleted, claimed, or expired.

---

### `GET /api/demo/dynamic-fields`

**Return dynamic question fields for a grant/template.**

If the template has dynamic sections configured in the `_builder` admin panel, this returns the exact question list. Otherwise, the frontend falls back to parsing the static `sections.json_schema`.

#### Request

```http
GET /api/demo/dynamic-fields?grant_id=sbir&template_id=sbir_p1
Cookie: demo_session_id=<uuid>
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `grant_id` | `string` | Yes | Grant identifier |
| `template_id` | `string` | Yes | Template identifier |

#### Response — `200 OK`

```json
{
  "grant_id": "sbir",
  "template_id": "sbir_p1",
  "sections": [
    {
      "section_key": "company_overview",
      "title": "Company Overview",
      "fields": [
        {
          "field_key": "business_model",
          "title": "Business Model",
          "description": "Describe how your business operates and generates revenue",
          "type": "text"
        }
      ]
    }
  ],
  "count": 1
}
```

---

### `POST /api/demo/download`

**Increment the session's download count.**

Atomically bumps `download_count`. Returns `429` if the session has already reached the per-session download limit (hard-coded to 1).

#### Request

```http
POST /api/demo/download
Cookie: demo_session_id=<uuid>
```

#### Response — `200 OK`

```json
{
  "download_count": 1
}
```

#### Response — `429 Too Many Requests`

```json
{
  "detail": "下載次數已達上限，免費註冊即可繼續使用。"
}
```

---

## Plan Generation

### `POST /api/generate_plan`

**Generate a full proposal plan with multiple candidates per section.**

Each section receives `num_candidates` parallel generations. The backend filters sections based on the visitor's actually-answered fields (keys matching `section_id::field_key` pattern). If no answers exist, all sections are generated.

> **Demo limit check:** If `has_generated_docx` is already `true`, returns `429` immediately.

#### Request

```http
POST /api/generate_plan
Content-Type: application/json
Cookie: demo_session_id=<uuid>

{
  "grant": "sbir",
  "template": "sbir_p1",
  "user_input": "We are a B2B SaaS company providing AI-driven proposal automation for SMBs in Taiwan.",
  "num_candidates": 2,
  "is_external": false,
  "selected_model": "gpt-5.1-chat-latest"
}
```

#### Request Schema

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `grant` | `string` | Yes | — | Grant identifier |
| `template` | `string` | Yes | — | Template identifier |
| `user_input` | `string` | Yes | `""` | User's project summary / main idea |
| `num_candidates` | `integer` | No | `1` | Number of candidates per section |
| `is_external` | `boolean` | No | `false` | Use external model flag |
| `selected_model` | `string` | No | Auto | Model ID. If omitted, auto-selects first non-Gemini external model |

#### Response — `200 OK`

```json
{
  "company_overview": [
    {
      "section_id": "company_overview",
      "content": "{\"company_name\":\"...\", \"business_model\":\"...\"}",
      "error": null,
      "raw_json_content": "{...}",
      "candidate_number": 1
    },
    {
      "section_id": "company_overview",
      "content": "{\"company_name\":\"...\", \"business_model\":\"...\"}",
      "error": null,
      "raw_json_content": "{...}",
      "candidate_number": 2
    }
  ],
  "market_analysis": [
    { ... }
  ]
}
```

**Response schema:** `Record<string, Array<Candidate>>`

Where each candidate object contains:

| Field | Type | Description |
|-------|------|-------------|
| `section_id` | `string` | Section identifier |
| `content` | `string` | Generated content (JSON string or plain text) |
| `error` | `string \| null` | Error message if generation failed |
| `raw_json_content` | `string \| null` | Raw JSON response from LLM |
| `candidate_number` | `integer` | Candidate index |

#### Response — `429 Too Many Requests`

```json
{
  "detail": "報告生成次數已達上限，免費註冊即可繼續使用。"
}
```

#### Response — `400 Bad Request`

```json
{
  "detail": "Template sbir_p1 not found in Grant sbir."
}
```

#### Response — `500 Internal Server Error`

```json
{
  "detail": "No sections found in the selected template."
}
```

---

### `POST /api/revise_plan_version`

**Revise an existing plan version with new candidates.**

Takes the currently selected version (`current_version`), builds a revision prompt incorporating the latest answers and user input, and generates new candidates per section.

> **Demo limit check:** Same as `generate_plan` — returns `429` if `has_generated_docx` is `true`.

#### Request

```http
POST /api/revise_plan_version
Content-Type: application/json
Cookie: demo_session_id=<uuid>

{
  "grant": "sbir",
  "template": "sbir_p1",
  "current_version": {
    "company_overview": { "content": "{...}" },
    "market_analysis": { "content": "{...}" }
  },
  "stored_answer": {
    "chat_answers": { "company_overview::business_model": "B2B SaaS" }
  },
  "project_title": "AI Proposal Automation",
  "project_summary": "We build AI tools for grant proposals.",
  "num_candidates": 2,
  "is_external": false,
  "selected_model": "gpt-5.1-chat-latest"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `grant` | `string` | Yes | Grant identifier |
| `template` | `string` | Yes | Template identifier |
| `current_version` | `object` | Yes | Existing version map: `{ section_id: { content: ... } }` |
| `stored_answer` | `object` | No | Latest answers and metadata |
| `project_title` | `string` | No | Project title |
| `project_summary` | `string` | No | Project summary |
| `num_candidates` | `integer` | No | Number of candidates per section |
| `is_external` | `boolean` | No | External model flag |
| `selected_model` | `string` | No | Model ID (auto-selected if omitted) |

#### Response — `200 OK`

Same schema as `POST /api/generate_plan`.

#### Response — `400 Bad Request`

```json
{
  "detail": "current_version is required for revision."
}
```

---

### `POST /api/recommend_project_names`

**Recommend up to 5 project names based on filled answers.**

Tries multiple candidate models in priority order (cheaper/faster first). Falls back to any available external model if rate-limited.

#### Request

```http
POST /api/recommend_project_names
Content-Type: application/json
Cookie: demo_session_id=<uuid>

{
  "current_answers": {
    "company_overview::business_model": "B2B SaaS",
    "market_analysis::target_market": "Taiwanese SMBs"
  },
  "project_title": "AI Proposal Tool",
  "grant_name": "SBIR Phase 1",
  "template_name": "SBIR Phase 1",
  "grant_id": "sbir",
  "template_id": "sbir_p1"
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current_answers` | `object` | No | Map of field IDs to answer values |
| `project_title` | `string` | No | Current project title |
| `grant_name` | `string` | No | Grant name |
| `template_name` | `string` | No | Template name |
| `grant_id` | `string` | No | Grant identifier |
| `template_id` | `string` | No | Template identifier |

#### Response — `200 OK`

```json
{
  "names": [
    "Smart Proposal AI: Automated Grant Writing for SMBs",
    "GrantEngine Taiwan: AI-Powered Funding Assistance",
    "ProposalPilot: Intelligent Document Generation",
    "FundFlow AI: Streamlined Grant Application Platform",
    "WriteWin: Next-Generation Proposal Automation"
  ]
}
```

#### Response — `502 Bad Gateway`

```json
{
  "detail": "Recommendation service error"
}
```

---

## Config

### `GET /api/config`

**Read the grants / templates / sections catalog.**

Returns the full configuration tree loaded from Supabase at startup. The frontend uses this to render the template selector and load section schemas.

#### Request

```http
GET /api/config
```

#### Response — `200 OK`

```json
[
  {
    "id": "sbir",
    "name": "SBIR Phase 1",
    "templates": [
      {
        "id": "sbir_p1",
        "name": "SBIR Phase 1 Standard",
        "sections": [
          {
            "id": "company_overview",
            "name": "Company Overview",
            "json_schema": { "properties": { ... } },
            "prompt": "..."
          }
        ]
      }
    ]
  }
]
```

---

### `POST /api/config/refresh`

**Manually refresh the configuration cache.**

Forces the backend to reload `all_grants_config` and `model_registry` from Supabase. Useful after updating templates in the admin panel.

#### Request

```http
POST /api/config/refresh
```

#### Response — `200 OK`

```json
{
  "status": "refreshed",
  "grants_count": 1,
  "models_count": 5
}
```

---

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Typical Cause |
|--------|---------|---------------|
| `200` | Success | Request completed normally |
| `400` | Bad Request | Missing required field, invalid cookie, malformed JSON |
| `401` | Unauthorized | Session expired, claimed, or missing cookie |
| `429` | Too Many Requests | Rate limit reached, generation limit reached, download limit reached |
| `500` | Internal Server Error | Database failure, LLM service error, unexpected exception |
| `502` | Bad Gateway | LLM provider error (rate limit, timeout) |

### Rate Limit Responses

All `429` responses from demo endpoints include a human-readable message in Chinese for the frontend to display:

```json
{
  "detail": "報告生成次數已達上限，免費註冊即可繼續使用。"
}
```

The `Retry-After` header is present only for IP-based session mint limits:

```http
Retry-After: 1800
```

---

## Common Headers

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Cookie: demo_session_id=<uuid>` | Yes for all except `GET /api/config` | Session identifier (HttpOnly cookie) |
| `Content-Type: application/json` | Yes for POST/PUT | Request body format |

### Response Headers

| Header | Present When | Description |
|--------|--------------|-------------|
| `Set-Cookie: demo_session_id=...` | `GET /api/demo` mint branch | New session cookie |
| `Retry-After: <seconds>` | `429` on mint | Seconds until rate limit window resets |

---

> For WebSocket protocol documentation, see [`06-websocket-protocol.md`](06-websocket-protocol.md).

(End of file)
