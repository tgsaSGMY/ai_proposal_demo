# 04 — Database Schema

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24  
> **Schema:** `ai_proposal_platform` (shared with full platform)

---

## Table of Contents

1. [Core Tables](#core-tables)
2. [Demo Table](#demo-table)
3. [Demo IP Limits Table](#demo-ip-limits-table)
4. [JSONB Structures](#jsonb-structures)
5. [Indexes](#indexes)
6. [Migration Functions](#migration-functions)
7. [Field Mapping (Demo → Platform)](#field-mapping-demo--platform)

---

## Core Tables

The demo shares the `ai_proposal_platform` schema with the full platform. The demo **only writes** to `demo` and `demo_ip_limits`. It **reads** from `grants`, `plan_templates`, `sections`, `dynamic_sections`, `dynamic_fields`, `models`, `routing_rules`.

---

## Demo Table

**Table:** `ai_proposal_platform.demo`

This is the **single table** that stores all demo session state. One row = one anonymous visitor session.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `UUID` | No | `gen_random_uuid()` | Primary key |
| `session_id` | `TEXT` | No | — | Unique browser cookie UUID |
| `ip_address` | `INET` | Yes | `NULL` | Client IP for rate limiting |
| `grant_id` | `TEXT` | Yes | `NULL` | Grant identifier (e.g., `sbir`) |
| `template_id` | `TEXT` | Yes | `NULL` | Template identifier (e.g., `sbir_p1`) |
| `interaction_count` | `INT` | No | `0` | Number of user prompts sent |
| `total_tokens_used` | `INT` | No | `0` | Accumulated token usage (updated via `pending_usage_logs`) |
| `has_generated_docx` | `BOOLEAN` | No | `FALSE` | Whether the plan has been generated |
| `download_count` | `INT` | No | `0` | Number of Word downloads |
| `conversation_history` | `JSONB` | No | `'[]'` | Array of chat messages |
| `stored_answer` | `JSONB` | No | `'{}'` | User answers, metadata, and user input summary |
| `saved_plan` | `JSONB` | No | `'[]'` | Array of generated plan versions |
| `pending_execution_events` | `JSONB` | No | `'[]'` | Buffered execution events for migration |
| `pending_usage_logs` | `JSONB` | No | `'[]'` | Buffered usage logs for migration |
| `section_versions` | `JSONB` | Yes | `NULL` | Snapshot of section schema versions |
| `title` | `TEXT` | Yes | `NULL` | User-editable project title (≤255 chars) |
| `mode` | `TEXT` | Yes | `'interactive'` | Session mode |
| `status` | `TEXT` | No | `'active'` | `active` \| `claimed` \| `expired` |
| `created_at` | `TIMESTAMPTZ` | No | `NOW()` | Session creation time |
| `expires_at` | `TIMESTAMPTZ` | Yes | `NOW() + interval` | Session expiry time |
| `claimed_by` | `UUID` | Yes | `NULL` | FK to `users.id` — who claimed this session |
| `claimed_at` | `TIMESTAMPTZ` | Yes | `NULL` | When the session was claimed |
| `claimed_project_id` | `UUID` | Yes | `NULL` | FK to `projects.id` — the migrated project |

### Constraints

```sql
PRIMARY KEY (id)
UNIQUE (session_id)
CHECK (status IN ('active', 'claimed', 'expired'))
```

### Lifecycle States

```
┌─────────┐     created      ┌─────────┐
│  NEW    │ ───────────────> │ ACTIVE  │
│  (row   │                  │         │
│  minted)│                  │         │
└─────────┘                  └────┬────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              │ claimed            │ expired            │ deleted
              │                    │ (by cron)          │ (by admin)
              ▼                    ▼                    ▼
        ┌──────────┐        ┌──────────┐        ┌──────────┐
        │ CLAIMED  │        │ EXPIRED  │        │ DELETED  │
        │          │        │          │        │          │
        │ Data     │        │ Data     │        │ Row      │
        │ migrated │        │ retained │        │ gone     │
        │ to       │        │ for      │        │          │
        │ projects │        │ analytics│        │          │
        └──────────┘        └──────────┘        └──────────┘
```

---

## Demo IP Limits Table

**Table:** `ai_proposal_platform.demo_ip_limits`

Tracks per-IP session creation counts in hourly and daily windows.

### Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `ip_address` | `INET` | No | — | Client IP address |
| `window_start` | `TIMESTAMPTZ` | No | — | Window boundary (truncated to hour or day) |
| `window_type` | `TEXT` | No | — | `'hour'` or `'day'` |
| `session_count` | `INT` | No | `0` | Number of sessions created in this window |

### Constraints

```sql
PRIMARY KEY (ip_address, window_start, window_type)
```

### Upsert Logic

```sql
INSERT INTO ai_proposal_platform.demo_ip_limits
  (ip_address, window_start, window_type, session_count)
VALUES
  (:ip, date_trunc('hour', now()), 'hour', 1),
  (:ip, date_trunc('day',  now()), 'day',  1)
ON CONFLICT (ip_address, window_start, window_type)
  DO UPDATE SET session_count = demo_ip_limits.session_count + 1
RETURNING window_type, session_count;
```

This is an **atomic increment-first** design. Even a rejected request bumps the counter (removes check-then-increment race).

---

## JSONB Structures

### `conversation_history`

Array of message objects. Each message represents one turn in the chat.

```json
[
  {
    "id": "user-abc123de",
    "role": "user",
    "type": "text",
    "content": "Hi, I want to apply for SBIR Phase 1",
    "timestamp": "2026-06-24T06:30:00+00:00"
  },
  {
    "id": "assistant-efg456hi",
    "role": "assistant",
    "type": "text",
    "content": "您好！我是您的 SBIR Phase 1 計畫書智能助手...",
    "timestamp": "2026-06-24T06:30:05+00:00"
  }
]
```

**Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Unique message ID (prefix: `user-` or `assistant-` + UUID fragment) |
| `role` | `string` | `"user"` \| `"assistant"` \| `"system"` |
| `type` | `string` | `"text"` (only type used in demo) |
| `content` | `string` | Message text (may include hidden reply markers) |
| `timestamp` | `string` | ISO 8601 timestamp |

### `stored_answer`

Container for user answers, metadata, and input summary.

```json
{
  "chat_answers": {
    "company_overview::business_model": "B2B SaaS",
    "company_overview::company_name": "Acme Corp",
    "market_analysis::target_market": "Taiwanese SMBs in manufacturing",
    "market_analysis::market_size": "NTD 50 billion"
  },
  "chat_answers_meta": {
    "company_overview::business_model": {
      "updated_at": "2026-06-24T06:30:00+00:00"
    },
    "market_analysis::target_market": {
      "updated_at": "2026-06-24T06:35:00+00:00"
    }
  },
  "user_input": {
    "main_idea": "We build AI tools for grant proposals",
    "dynamic_fields": {
      "project_name": "GrantAI",
      "team_size": 5
    }
  }
}
```

**Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `chat_answers` | `object` | Map of field IDs to answer values |
| `chat_answers_meta` | `object` | Map of field IDs to metadata (updated_at timestamps) |
| `user_input` | `object` | User's free-form input summary |
| `user_input.main_idea` | `string` | Core project concept |
| `user_input.dynamic_fields` | `object` | Additional dynamic field answers |

**Field ID format:** `section_id::field_key` (e.g., `company_overview::business_model`)

### `saved_plan`

Array of plan version objects. Each version represents a complete plan assembled from selected candidates.

```json
[
  {
    "number": 1,
    "title": "Version 1",
    "timestamp": "2026-06-24T06:35:00+00:00",
    "data": {
      "company_overview": {
        "content": "{\"company_name\":\"Acme Corp\",\"business_model\":\"B2B SaaS\"}",
        "error": null
      },
      "market_analysis": {
        "content": "{\"target_market\":\"Taiwanese SMBs\",\"market_size\":\"50B\"}",
        "error": null
      }
    }
  }
]
```

**Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `number` | `integer` | Version sequence number |
| `title` | `string` | Version label (e.g., "Version 1") |
| `timestamp` | `string` | ISO 8601 creation time |
| `data` | `object` | Map of section IDs to content objects |
| `data[section_id].content` | `string` | Generated content (JSON string or plain text) |
| `data[section_id].error` | `string \| null` | Error message if generation failed |

### `pending_execution_events`

Array of execution events buffered for migration to `execution_logs`.

```json
[
  {
    "event_type": "stored_answer_updated",
    "section_id": null,
    "version_id": null,
    "payload": {
      "answers_count": 3,
      "field_changes": [
        {
          "field_id": "company_overview::business_model",
          "field_label": "Company Overview｜Business Model",
          "old_value": "",
          "new_value": "B2B SaaS",
          "change": "Company Overview｜Business Model：《》→《B2B SaaS》"
        }
      ],
      "changes_summary": "Company Overview｜Business Model：《》→《B2B SaaS》"
    },
    "logged_at": "2026-06-24T06:30:00+00:00"
  }
]
```

**Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `event_type` | `string` | Event type (e.g., `stored_answer_updated`) |
| `section_id` | `string \| null` | Affected section |
| `version_id` | `string \| null` | Affected version |
| `payload` | `object` | Event-specific data |
| `logged_at` | `string` | ISO 8601 timestamp |

### `pending_usage_logs`

Array of usage logs buffered for migration to `usage_logs`.

```json
[
  {
    "model_id": "gpt-5.1-chat-latest",
    "model_type": "external",
    "input_token": 1250,
    "output_token": 890,
    "image_token": 0,
    "cost": 0.001337,
    "action": "生成對話",
    "logged_at": "2026-06-24T06:30:00+00:00"
  }
]
```

**Schema:**

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | `string` | Model identifier |
| `model_type` | `string` | `"external"` \| `"internal"` |
| `input_token` | `integer` | Input token count |
| `output_token` | `integer` | Output token count |
| `image_token` | `integer` | Image token count |
| `cost` | `number` | Estimated cost in USD |
| `action` | `string` | Action description (e.g., "生成對話", "推薦計畫名稱") |
| `logged_at` | `string` | ISO 8601 timestamp |

### `section_versions`

Snapshot of section schema versions at session creation time.

```json
{
  "company_overview": 1,
  "market_analysis": 2,
  "financial_plan": 1,
  "team_introduction": 3
}
```

**Schema:** Map of section IDs to version numbers (integers). This is captured from `sections.current_version` and copied to `projects.section_versions` on migration.

---

## Indexes

```sql
-- demo table
CREATE INDEX idx_demo_session_id ON ai_proposal_platform.demo(session_id);
CREATE INDEX idx_demo_ip_created ON ai_proposal_platform.demo(ip_address, created_at);
CREATE INDEX idx_demo_expires ON ai_proposal_platform.demo(expires_at) WHERE status IN ('active', 'generated');
CREATE INDEX idx_demo_active ON ai_proposal_platform.demo(session_id) WHERE status = 'active';

-- demo_ip_limits table
-- Primary key is (ip_address, window_start, window_type) — covers all lookups
```

---

## Migration Functions

### `migrate_demo_to_project(p_demo_session_id TEXT, p_new_user_id UUID) → UUID`

**Location:** `database-migrations/003_demo_schema_update.sql`

**Purpose:** Atomically migrate a demo session to a full platform project.

**Requirements:**
- Demo row must have `status = 'active'`
- `expires_at` must be in the future

**Steps:**
1. Lock the demo row (`SELECT ... FOR UPDATE`)
2. Snapshot `section_versions` if missing (backward compat for old rows)
3. Insert new `projects` row with all demo data
4. Drain `pending_execution_events` → `execution_logs`
5. Drain `pending_usage_logs` → `usage_logs`
6. Mark demo row as `claimed`

**Returns:** New `project_id` (UUID)

**Throws:** `Demo session not found or not ready for migration`

---

## Field Mapping (Demo → Platform)

When `migrate_demo_to_project()` runs, it maps demo columns to `projects` columns:

| `demo` Column | `projects` Column | Notes |
|---------------|-------------------|-------|
| `grant_id` | `grant_id` | Direct copy |
| `template_id` | `template_id` | Direct copy |
| `saved_plan` | `saved_plan` | Direct copy |
| `stored_answer` | `stored_answer` | Direct copy |
| `conversation_history` | `conversation_history` | Direct copy |
| `title` (priority) | `title` | Primary source |
| `stored_answer->>'plan_name'` (fallback) | `title` | Used if `title` is NULL |
| `'從 Demo 匯入的計畫書'` (final fallback) | `title` | Used if both above are NULL |
| `section_versions` | `section_versions` | Direct copy |
| `mode` (default `'interactive'`) | `mode` | Direct copy |
| `claimed_by` | `user_id` | Set on new projects row |
| `created_at` | `created_at` | Direct copy |
| `NOW()` | `updated_at` | Set on creation |
| `FALSE` | `is_deleted` | Default |

---

> Next: [`05-api-endpoints.md`](05-api-endpoints.md)

(End of file)
