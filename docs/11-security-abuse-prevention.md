# 11 — Security & Abuse Prevention

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Threat Model](#threat-model)
2. [Session Security](#session-security)
3. [Rate Limiting](#rate-limiting)
4. [IP Extraction](#ip-extraction)
5. [Data Isolation](#data-isolation)
6. [CORS Policy](#cors-policy)
7. [LLM Abuse Prevention](#llm-abuse-prevention)
8. [Known Limitations](#known-limitations)
9. [Future Hardening](#future-hardening)

---

## Threat Model

### Assets

| Asset | Value | Risk |
|-------|-------|------|
| API keys (OpenAI, Gemini) | $$ | Cost abuse |
| Supabase database | $$$ | Data pollution, unauthorized access |
| Demo sessions | $ | Session hijacking, data theft |
| Full platform projects | $$$ | Unauthorized migration |

### Threat Actors

| Actor | Motivation | Capability |
|-------|------------|------------|
| **Casual abuser** | Free LLM usage | Low — basic scripting |
| **Bot operator** | Sell free LLM access | Medium — automated tools, proxy rotation |
| **Competitor** | Disrupt service, steal data | High — sophisticated attacks |
| **Curious user** | Test limits | Low — manual interaction |

### Attack Scenarios

| Scenario | Likelihood | Impact | Mitigation |
|----------|------------|--------|------------|
| Bot creates unlimited sessions | Medium | High | IP rate limiting (ready, not active) |
| Bot sends unlimited prompts | Medium | High | Session prompt limit + token cap |
| Session cookie stolen | Low | Medium | HttpOnly, SameSite, short expiry |
| API keys leaked | Low | Critical | .env only, rotate regularly |
| Prompt injection | Medium | Medium | Input validation (partial) |
| DDoS on WebSocket | Medium | Medium | Nginx rate limiting, connection limits |
| Data migration abuse | Low | High | Atomic claim, idempotent, cross-user safe |

---

## Session Security

### Cookie Properties

The `demo_session_id` cookie is set with these flags:

```python
response.set_cookie(
    key="demo_session_id",
    value=new_id,
    max_age=DEMO_SESSION_EXPIRY_MINUTES * 60,
    httponly=True,      # JavaScript cannot read
    samesite="lax",     # CSRF protection
    secure=False,       # Set to True in production (HTTPS only)
    path="/",
)
```

| Flag | Value | Security Benefit |
|------|-------|------------------|
| `HttpOnly` | ✅ | Prevents XSS from stealing session ID |
| `SameSite=Lax` | ✅ | Prevents CSRF in cross-origin POSTs |
| `Secure` | ⚠️ (False in dev) | Should be `True` in production |
| `Max-Age` | 30 days | Limits window for session replay |
| `Path=/` | ✅ | Cookie sent to all endpoints |

### Session Lifecycle

```
┌─────────┐     ┌─────────────┐     ┌─────────┐
│  MINT   │────>│   ACTIVE    │────>│ EXPIRED │
│ (new)   │     │ (usable)    │     │ (dead)  │
└─────────┘     └─────────────┘     └─────────┘
                      │
                      │ claimed
                      ▼
                ┌─────────────┐
                │   CLAIMED   │
                │ (migrated)  │
                └─────────────┘
```

**Rules:**
- A claimed session **cannot** be reused (status changes to `claimed`)
- An expired session **cannot** be extended (new session is minted)
- A session ID is **never** reused (always UUIDv4)

### Session Hijacking Mitigation

| Risk | Mitigation |
|------|------------|
| Cookie theft via XSS | HttpOnly flag prevents JS access |
| Cookie theft via network | Secure flag (HTTPS) + TLS |
| Cookie replay | Short expiry (7 days) + status check |
| Session fixation | New UUID on every mint |
| Brute-force session ID | 128-bit UUID — computationally infeasible |

---

## Rate Limiting

### Architecture

```
Visitor makes request
    │
    ▼
┌─────────────────────────────────────┐
│  Nginx (optional layer)             │
│  limit_req zone=api:10m rate=10r/s  │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  FastAPI                            │
│  get_demo_session_id()              │
│  ├──> Check cookie                  │
│  ├──> If valid: return (no limit) │
│  └──> If missing: check IP limit    │
│       ├──> Atomic upsert            │
│       ├──> Compare to limits        │
│       └──> Return 429 or mint       │
└─────────────────────────────────────┘
```

### IP Rate Limiter

**File:** `backend/app/utils/demo_rate_limiter.py`

**Design:** Increment-first atomic upsert

```sql
INSERT INTO demo_ip_limits (ip_address, window_start, window_type, session_count)
VALUES (:ip, date_trunc('hour', now()), 'hour', 1),
       (:ip, date_trunc('day',  now()), 'day',  1)
ON CONFLICT (ip_address, window_start, window_type)
  DO UPDATE SET session_count = demo_ip_limits.session_count + 1
RETURNING window_type, session_count;
```

**Why increment-first?**
- Removes the check-then-increment race condition
- Treats abuse attempts as hits (correctly)
- Simpler code, no transaction needed

**Current Status:**
- ✅ Table exists (`demo_ip_limits`)
- ✅ Upsert logic implemented
- ✅ Unit tests written (`test_demo_rate_limiter.py`)
- ⚠️ **Enforcement is commented out** (lines 72–86 in `demo_rate_limiter.py`)

### Limits

| Limit | Value | Status |
|-------|-------|--------|
| 3 sessions / IP / hour | `DEMO_IP_HOURLY_LIMIT=3` | Ready, not active |
| 5 sessions / IP / day | `DEMO_IP_DAILY_LIMIT=5` | Ready, not active |
| 20 prompts / session | `DEMO_INTERACTION_LIMIT=20` | ✅ Active |
| 100K tokens / session | `DEMO_MAX_TOKENS_PER_SESSION=100000` | ✅ Active |
| 1 generation / session | `DEMO_MAX_GENERATIONS_PER_SESSION=1` | ✅ Active |
| 1 download / session | Hard-coded in code | ✅ Active |

### Enabling IP Rate Limiting

To activate the IP rate limiter, uncomment lines 72–86 in `backend/app/utils/demo_rate_limiter.py`:

```python
if counts.get("hour", 0) > DEMO_IP_HOURLY_LIMIT:
    next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    return RateLimitResult(
        allowed=False,
        reason="DEMO_HOURLY_LIMIT_EXCEEDED",
        retry_after=max(1, int((next_hour - now).total_seconds())),
    )

if counts.get("day", 0) > DEMO_IP_DAILY_LIMIT:
    next_day = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return RateLimitResult(
        allowed=False,
        reason="DEMO_DAILY_LIMIT_EXCEEDED",
        retry_after=max(1, int((next_day - now).total_seconds())),
    )
```

---

## IP Extraction

**File:** `backend/app/utils/ip_extractor.py`

**Priority:**
1. `X-Forwarded-For` (leftmost IP)
2. `X-Real-IP`
3. `request.client.host`

**Trust Model:**
- The demo runs behind Nginx Proxy Manager on the Dev VPS
- Nginx sets `X-Forwarded-For` and `X-Real-IP`
- We trust the leftmost forwarded IP
- **Caveat:** A determined attacker could spoof `X-Forwarded-For` if they bypass Nginx

**Mitigation:**
- This is acceptable for **casual abuse friction**, not a security boundary
- For production, consider a more robust proxy configuration

---

## Data Isolation

### Demo → Platform Isolation

| Data | Demo Table | Platform Table | Risk |
|------|------------|----------------|------|
| Session state | `demo` | — | Low — no PII |
| Chat history | `demo.conversation_history` | `projects.conversation_history` | Low — user-provided |
| Answers | `demo.stored_answer` | `projects.stored_answer` | Low — user-provided |
| Generated plan | `demo.saved_plan` | `projects.saved_plan` | Low — AI-generated |
| Usage logs | `demo.pending_usage_logs` | `usage_logs` | Low — internal metrics |
| Execution events | `demo.pending_execution_events` | `execution_logs` | Low — internal metrics |

### Write Protection

The demo **only writes** to:
- `ai_proposal_platform.demo`
- `ai_proposal_platform.demo_ip_limits`

It **never writes** to:
- `projects` (only the migration function does, atomically)
- `users` (only the full platform does)
- `execution_logs` (only the migration function does)
- `usage_logs` (only the migration function does)

---

## CORS Policy

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://demo-dev.172.233.79.222.nip.io",
        "https://demo-aiproposal.tgsa.com.tw",
        "https://aiproposal.tgsa.com.tw",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

| Setting | Value | Risk |
|---------|-------|------|
| `allow_credentials=True` | ✅ | Required for cookie transmission |
| `allow_origins` | Whitelist | Prevents unauthorized domains |
| `allow_methods=["*"]` | ⚠️ | Acceptable for demo, but should restrict in production |
| `allow_headers=["*"]` | ⚠️ | Acceptable for demo, but should restrict in production |

**Production recommendation:**
```python
allow_origins=["https://demo-aiproposal.tgsa.com.tw"]
allow_methods=["GET", "POST", "PUT", "DELETE"]
allow_headers=["Content-Type", "Authorization", "X-Requested-With"]
```

---

## LLM Abuse Prevention

### Prompt Limits

| Limit | Value | Enforcement Point |
|-------|-------|-------------------|
| 20 prompts | Per session | WebSocket `interaction_count` check |
| 100K tokens | Per session | `pending_usage_logs` accumulation |
| 1 generation | Per session | `has_generated_docx` flag |

### Cost Per Session

| Model | Input | Output | Max Cost |
|-------|-------|--------|----------|
| GPT-4.1-mini | $0.40/1M | $1.60/1M | ~$0.20 |
| GPT-5.1-chat-latest | $1.25/1M | $10.00/1M | ~$1.00 |
| Gemini 3 Flash | $0.075/1M | $0.30/1M | ~$0.03 |

**Average demo session cost:** $0.10–$0.50

**Worst case (100K tokens, GPT-5.1):** ~$1.00

### Bot Mitigation

| Layer | Effectiveness | Status |
|-------|---------------|--------|
| IP rate limiting | Medium | Ready, not active |
| Session prompt limit | High | ✅ Active |
| Token cap | High | ✅ Active |
| Generation limit | High | ✅ Active |
| CAPTCHA | High | ❌ Not implemented |
| Behavior analysis | Medium | ❌ Not implemented |

---

## Known Limitations

### 1. Incognito Mode Bypass

**Problem:** Incognito windows start with a fresh cookie jar, so each visit mints a new session.

**Impact:** A user could theoretically create unlimited sessions by opening new incognito windows.

**Mitigation:** IP rate limiting (when enabled) catches this at the network level.

**Residual risk:** Users behind corporate NAT or VPN share IPs, so legitimate users could be blocked.

### 2. IP Spoofing

**Problem:** `X-Forwarded-For` can be spoofed if the request bypasses Nginx.

**Impact:** An attacker could appear to come from a different IP.

**Mitigation:** Nginx should strip existing `X-Forwarded-For` headers and set its own. Verify Nginx config:

```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

### 3. Cookie Replay

**Problem:** A stolen cookie could be reused until expiry.

**Impact:** Session hijacking.

**Mitigation:**
- HttpOnly prevents XSS theft
- Short expiry (7 days) limits window
- No sensitive data in session (only proposal draft)

### 4. No CAPTCHA

**Problem:** Bots can easily automate the chat flow.

**Impact:** API cost abuse.

**Mitigation:**
- Rate limiting (ready)
- Token caps (active)
- Future: CAPTCHA on registration, not on demo entry

### 5. No Input Sanitization

**Problem:** User input is passed directly to the LLM.

**Impact:** Prompt injection could manipulate the LLM.

**Mitigation:**
- The LLM is scoped to a specific system prompt
- No sensitive data in the demo context
- Full platform has more robust input handling

---

## Future Hardening

### Phase 1: Enable Rate Limiting (Immediate)

- Uncomment IP rate limit enforcement
- Monitor false-positive rate
- Adjust limits based on traffic

### Phase 2: CAPTCHA (Short-term)

- Add reCAPTCHA v3 or hCaptcha on the registration CTA
- Add optional CAPTCHA on session creation if abuse detected

### Phase 3: Behavior Analysis (Medium-term)

- Track time-to-first-message, typing speed, message patterns
- Flag suspicious sessions for manual review
- Implement progressive friction (CAPTCHA after N sessions from same IP)

### Phase 4: Network Hardening (Medium-term)

- Implement Cloudflare or similar CDN/WAF
- Geo-blocking (if demo is Taiwan-only)
- DDoS protection

### Phase 5: Audit Logging (Long-term)

- Log all session creation events with IP, user agent, timestamp
- Alert on anomaly patterns (e.g., 100 sessions from one IP in 1 hour)
- Retain logs for 90 days

---

> Next: [`12-monitoring-alerting.md`](12-monitoring-alerting.md)

(End of file)
