# WebSocket Protocol Reference

> **Endpoint:** `wss://demo-aiproposal.tgsa.com.tw/ws/chat_guidance`  
> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24  
> **Authentication:** None — session is identified by the `demo_session_id` cookie sent during the HTTP handshake.

---

## Table of Contents

1. [Connection Establishment](#connection-establishment)
2. [Init Message](#init-message)
3. [Client → Server Messages](#client--server-messages)
4. [Server → Client Events](#server--client-events)
5. [Message Protocol](#message-protocol)
6. [Limit Enforcement](#limit-enforcement)
7. [Error Handling](#error-handling)
8. [Reconnection Strategy](#reconnection-strategy)
9. [State Machine](#state-machine)

---

## Connection Establishment

The WebSocket handshake is a standard HTTP upgrade. The client **must** include the `demo_session_id` cookie (obtained from a prior `GET /api/demo` call). The backend resolves the session from this cookie.

```
Client                                          Server
  │ ─── GET /api/demo ─────────────────────────> │
  │ <────────────────── Set-Cookie: demo_sid ─── │
  │                                              │
  │ ─── WebSocket handshake ───────────────────> │
  │     Cookie: demo_session_id=<uuid>           │
  │ <──────────────────── 101 Switching ─────── │
```

> **Important:** The query parameter `?session_id=xxx` is supported as a fallback for testing tools, but **production clients should rely on the cookie**.

---

## Init Message

Immediately after the WebSocket is accepted, the server waits for the client to send an **init message**. This is the first message from the client and establishes the conversation context.

### Client → Server: `init`

```json
{
  "project_title": "AI Proposal Automation",
  "project_summary": "We build AI tools for grant proposals.",
  "grant_name": "SBIR Phase 1",
  "all_questions": [
    {
      "id": "company_overview::business_model",
      "label": "Company Overview｜Business Model",
      "prompt": "Describe how your business operates and generates revenue"
    },
    {
      "id": "market_analysis::target_market",
      "label": "Market Analysis｜Target Market",
      "prompt": "Who are your target customers?"
    }
  ],
  "grant_id": "sbir",
  "template_id": "sbir_p1",
  "history": [
    { "role": "user", "content": "Hi, I want to apply for SBIR Phase 1" }
  ],
  "current_answers": {
    "company_overview::business_model": "B2B SaaS"
  },
  "current_answers_meta": {
    "company_overview::business_model": {
      "updated_at": "2026-06-24T06:30:00+00:00"
    }
  }
}
```

### Init Message Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_title` | `string` | No | User's project title |
| `project_summary` | `string` | No | User's project summary |
| `grant_name` | `string` | No | Display name of the grant |
| `all_questions` | `array` | Yes | Full list of questions (fields) for this template |
| `grant_id` | `string` | No | Grant identifier |
| `template_id` | `string` | No | Template identifier |
| `history` | `array` | No | Existing conversation history (loaded from DB or local state) |
| `current_answers` | `object` | No | Current field answers map |
| `current_answers_meta` | `object` | No | Metadata per answer (updated_at timestamps) |

---

## Client → Server Messages

After `init`, the client sends messages during the conversation. All messages are JSON.

### `user_message` — Send a chat message

```json
{
  "user_message": "Our target market is Taiwanese SMBs in the manufacturing sector.",
  "current_answers": {
    "market_analysis::target_market": "Taiwanese SMBs in manufacturing"
  },
  "current_answers_meta": {
    "market_analysis::target_market": {
      "updated_at": "2026-06-24T06:35:00+00:00"
    }
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_message` | `string` | Yes | The user's chat message |
| `current_answers` | `object` | No | Updated answers map (if user changed any fields via UI) |
| `current_answers_meta` | `object` | No | Updated metadata timestamps |

### `pause` — Cancel the current AI stream

```json
{
  "action": "pause"
}
```

The server will stop streaming the current response and send a `cancelled` event. The client can then restore the original user message to allow re-sending.

---

## Server → Client Events

All server messages are JSON objects with an `event` field.

### `ready` — Handshake complete

Sent after the `init` message is processed and the session is loaded.

```json
{
  "event": "ready",
  "message": "系统就绪",
  "interaction_count": 0,
  "interaction_limit": 20
}
```

| Field | Type | Description |
|-------|------|-------------|
| `event` | `string` | Always `"ready"` |
| `message` | `string` | Status message |
| `interaction_count` | `integer` | Current prompt count |
| `interaction_limit` | `integer` | Max prompts allowed |

---

### `chunk_start` — AI response begins

Sent before the first content chunk.

```json
{
  "event": "chunk_start"
}
```

---

### `chunk` — Streaming content

Sent repeatedly as the AI generates content. Each chunk is a text fragment.

```json
{
  "event": "chunk",
  "data": "好的，已記錄您的目標市場為台灣製造業中小企業。"
}
```

The client should concatenate all `data` values in order to reconstruct the full response.

---

### `done` — AI response complete

Sent after the last chunk.

```json
{
  "event": "done"
}
```

---

### `filled` — Hidden field answers extracted

When the AI response contains hidden reply fields (in the format `【回復結束】【隱藏回復欄位+答案】...【隱藏回復結束】`), the server parses them and sends this event so the frontend can update the answer form.

```json
{
  "event": "filled",
  "data": {
    "market_analysis::target_market": "Taiwanese SMBs in manufacturing",
    "company_overview::business_model": "B2B SaaS"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `data` | `object` | Map of field IDs to extracted answer values |

---

### `limit_reached` — Usage limit hit

Sent when the user hits either the prompt limit or the token limit. After this event, the server will **not** process new user messages. The frontend should display the registration CTA.

```json
{
  "event": "limit_reached",
  "reason": "prompts",
  "interaction_count": 20,
  "interaction_limit": 20,
  "token_usage": 45231,
  "token_limit": 100000,
  "register_url": "https://aiproposal.tgsa.com.tw/api/external-auth/redirect",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reason` | `string` | `"prompts"` or `"tokens"` |
| `interaction_count` | `integer` | Current prompt count |
| `interaction_limit` | `integer` | Max prompts |
| `token_usage` | `integer` | Accumulated token count |
| `token_limit` | `integer` | Max tokens |
| `register_url` | `string` | Registration redirect URL |
| `session_id` | `string` | Session ID for the `ref` parameter |

---

### `paused_ack` — Pause acknowledged

Sent in response to a client `pause` action.

```json
{
  "event": "paused_ack"
}
```

---

### `cancelled` — Stream cancelled by user

Sent when the AI stream was interrupted by a `pause` action.

```json
{
  "event": "cancelled",
  "restore_user_message": "Our target market is Taiwanese SMBs in the manufacturing sector.",
  "message": "stream_cancelled_by_user"
}
```

The client should restore the original `user_message` to the input field so the user can re-send or edit it.

---

### `error` — Server-side error

Sent when an unrecoverable error occurs.

```json
{
  "event": "error",
  "message": "missing demo_session_id cookie — open the demo page first to mint one"
}
```

Common error messages:

| Message | Cause |
|---------|-------|
| `missing demo_session_id cookie — open the demo page first to mint one` | Cookie not present during handshake |
| `supabase unavailable` | Database connection failure |
| `<exception string>` | LLM stream failure or unexpected error |

After an `error`, the server may close the WebSocket.

---

## Message Protocol

### Complete Conversation Flow

```
Client                                                          Server
  │ ─── WebSocket connect + Cookie ────────────────────────────> │
  │                                                              │
  │ ─── { init } ──────────────────────────────────────────────> │
  │ <────────────────── { ready } ───────────────────────────── │
  │                                                              │
  │ <────────────────── { chunk_start } ───────────────────────── │
  │ <────────────────── { chunk: "好的..." } ────────────────── │
  │ <────────────────── { chunk: "已記錄..." } ───────────────── │
  │ <────────────────── { done } ──────────────────────────────── │
  │ <────────────────── { filled: { ... } } ─────────────────── │
  │                                                              │
  │ ─── { user_message: "..." } ─────────────────────────────> │
  │ <────────────────── { chunk_start } ───────────────────────── │
  │ <────────────────── { chunk: "..." } ────────────────────── │
  │ <────────────────── { done } ──────────────────────────────── │
  │                                                              │
  │ ─── { action: "pause" } ───────────────────────────────────> │
  │ <────────────────── { paused_ack } ────────────────────────── │
  │ <────────────────── { cancelled } ───────────────────────── │
  │                                                              │
  │ ─── { user_message: "..." } ─────────────────────────────> │
  │ <────────────────── { limit_reached } ───────────────────── │
```

---

## Limit Enforcement

Limits are checked at two points:

### 1. Before processing a new user message

When a `user_message` arrives, the server checks:
- `interaction_count >= DEMO_INTERACTION_LIMIT` (default 20)
- `token_usage >= DEMO_MAX_TOKENS_PER_SESSION` (default 100,000)

If either is exceeded, the server sends `limit_reached` **instead of** calling the LLM.

### 2. After the AI response completes

After streaming finishes, the server:
1. Increments `interaction_count` via `increment_demo_interaction()`
2. Appends token usage to `pending_usage_logs`
3. Re-checks limits
4. If newly exceeded, sends a second `limit_reached` event

This ensures the user gets immediate feedback even if the limit was hit during the last successful turn.

### Token Counting

| Provider | Source | Notes |
|----------|--------|-------|
| OpenAI | `response.usage.total_tokens` | Exact |
| Google Gemini | `usageMetadata.totalTokenCount` | Exact |
| Ollama / Other | None | Not used in demo |

Token usage is buffered in `pending_usage_logs` (JSONB array) and drained to `usage_logs` on migration.

---

## Error Handling

### Connection Errors

| Scenario | Client Behavior | Server Behavior |
|----------|---------------|-----------------|
| Missing cookie | Show error, redirect to `/` | Send `error` + close WS |
| Invalid cookie | Show error, refresh page | Treat as missing, send `error` |
| Session expired | Show error, refresh page | Send `error` + close WS |
| Supabase down | Retry with backoff | Send `error` + close WS |
| LLM timeout | Show timeout notice | Send `error` + close WS |

### Reconnection

The client should implement **exponential backoff** reconnection:

```
Attempt 1: immediate
Attempt 2: 1 second
Attempt 3: 2 seconds
Attempt 4: 4 seconds
Attempt 5: 8 seconds
Max: 30 seconds
```

On reconnection:
1. Re-send `init` with the **latest** `history` and `current_answers`
2. The server will load the existing DB state and merge it with the init payload
3. If the last message was from the user (no assistant response), the opening message will be regenerated

---

## Reconnection Strategy

### Recommended Client Implementation

```typescript
// Pseudo-code
class DemoChatSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect() {
    this.ws = new WebSocket("wss://demo-aiproposal.tgsa.com.tw/ws/chat_guidance");
    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.sendInit();
    };
    this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
    this.ws.onclose = () => this.scheduleReconnect();
    this.ws.onerror = () => this.ws?.close();
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    const delay = Math.min(this.reconnectDelay * 2 ** this.reconnectAttempts, 30000);
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  private sendInit() {
    this.send({
      project_title: this.state.projectTitle,
      project_summary: this.state.projectSummary,
      grant_name: this.state.grantName,
      all_questions: this.state.questions,
      grant_id: this.state.grantId,
      template_id: this.state.templateId,
      history: this.state.messages,
      current_answers: this.state.answers,
      current_answers_meta: this.state.answersMeta,
    });
  }

  sendUserMessage(text: string) {
    this.send({
      user_message: text,
      current_answers: this.state.answers,
      current_answers_meta: this.state.answersMeta,
    });
  }

  pause() {
    this.send({ action: "pause" });
  }
}
```

---

## State Machine

```
┌─────────────┐     connect      ┌─────────────┐
│   CLOSED    │ ───────────────> │  CONNECTING │
└─────────────┘                  └─────────────┘
                                        │
                                   handshake
                                        │
                                        ▼
                                  ┌─────────────┐
                                  │  CONNECTED  │
                                  └─────────────┘
                                        │
                                   receive init
                                        │
                                        ▼
                                  ┌─────────────┐
                                  │    READY    │
                                  └─────────────┘
                                        │
                              ┌─────────┴─────────┐
                              │                     │
                              ▼                     ▼
                       ┌─────────────┐      ┌─────────────┐
                       │  STREAMING  │      │ LIMIT_REACHED│
                       │  (chunk*)   │      │             │
                       └─────────────┘      └─────────────┘
                              │                     │
                         done │              ┌─────┘
                              │              │ register CTA
                              ▼              ▼
                       ┌─────────────┐   ┌─────────────┐
                       │   ACTIVE    │   │   MIGRATED  │
                       │ (await msg) │   │  (closed)   │
                       └─────────────┘   └─────────────┘
```

---

> For REST API documentation, see [`05-api-endpoints.md`](05-api-endpoints.md).

(End of file)
