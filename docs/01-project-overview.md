# 01 — Project Overview

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Vision

The AI Proposal Demo is a **free, anonymous, zero-friction entry point** into the AI Proposal Platform (補助引擎). It allows any visitor to experience the core value proposition — AI-powered grant proposal generation — without creating an account, downloading software, or providing any personal information.

The demo is deliberately **limited** (20 chat prompts, 1 report generation, 100K tokens) to:
1. Prevent API cost abuse
2. Create a natural conversion point to the full platform
3. Demonstrate the platform's value while leaving the user wanting more

---

## Target User

- **Small business owners** in Taiwan exploring SBIR grants
- **Startup founders** who want to test AI proposal quality before committing
- **Consultants** evaluating tools for their clients
- **Any visitor** from marketing campaigns, social media, or organic search

**Key characteristic:** They have **low intent** and **high friction tolerance** — they won't fill a long form, but they'll chat with an AI for 5 minutes.

---

## User Journey

### Step 1: Discovery (External)

The visitor arrives from:
- Marketing landing pages
- Social media ads
- Organic search results
- Direct links from sales materials

**No action required** — they simply click the link.

### Step 2: Instant Workspace (0 friction)

```
Visitor clicks link
  ↓
Browser loads https://demo-aiproposal.tgsa.com.tw/
  ↓
Frontend calls GET /api/demo → backend mints cookie
  ↓
WebSocket connects to /ws/chat_guidance
  ↓
AI greets user: "您好！我是您的 SBIR Phase 1 計畫書智能助手..."
```

**Total time to first interaction:** < 2 seconds.

### Step 3: Guided Conversation (Value delivery)

The AI asks questions about the user's project:
- Company overview
- Business model
- Target market
- Technology innovation
- Financial projections

The visitor answers in natural language. The AI:
- Extracts structured answers (hidden field format)
- Confirms understanding
- Asks the next most relevant question
- Shows progress (e.g., "還剩 8 題" — 8 questions remaining)

### Step 4: Plan Generation (Aha moment)

When enough fields are filled, the user clicks "輸出完整推演" (Generate Full Plan):
- Backend generates multi-candidate versions per section
- User selects the best candidate for each section
- Final plan is assembled and saved

### Step 5: Upsell & Migration (Conversion)

At any limit (20 prompts, 100K tokens, 1 generation, 1 download), the UI shows:
- "體驗次數已達上限，免費註冊以繼續使用"
- "報告生成次數已達上限，免費註冊以繼續使用"

Clicking the CTA redirects to:
```
https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<session_id>
```

After OAuth signup, all session data is migrated to the new account.

---

## Hard Limits

| Limit | Value | Purpose | User Experience |
|-------|-------|---------|----------------|
| **20 prompts** | Per session | Prevent API cost abuse | Chat shows remaining count implicitly; at limit shows registration CTA |
| **100K tokens** | Per session | Cap LLM usage | Backend-enforced; user sees same CTA as prompt limit |
| **1 generation** | Per session | Create scarcity | After generating, button is disabled; CTA shown |
| **1 download** | Per session | Prevent abuse | Download button disabled after first use |
| **7 days** | Session retention | Data hygiene | Expired sessions auto-cleaned; user starts fresh |
| **3/hour IP** | Session creation | Anti-bot (ready, not active) | Returns 429 with retry-after header |
| **5/day IP** | Session creation | Anti-bot (ready, not active) | Returns 429 with retry-after header |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Demo-to-signup conversion rate | > 5% | `claimed` rows / `active` rows (excluding expired) |
| Average session duration | 3–5 min | `expires_at - created_at` for active sessions |
| Average fields filled | > 5 | `len(chat_answers)` in `stored_answer` |
| Plan generation rate | > 30% | `has_generated_docx = true` / total sessions |
| API cost per session | < $0.50 | `usage_logs` cost aggregation (post-migration) |

---

## Scope Boundaries

### In Scope

- Single grant (SBIR Phase 1)
- Single template (configurable via `.env`)
- Anonymous cookie-based sessions
- WebSocket chat guidance
- Plan generation (multi-candidate)
- Plan revision
- Session migration to full platform
- IP rate limiting infrastructure

### Out of Scope

- User authentication (no login, no OAuth on demo)
- Multiple grants/templates (UI does not support selection)
- Admin management (`/_builder/*` pages removed)
- Dataset governance (no DPO/synthetic data generation)
- Model routing configuration (uses hardcoded defaults)
- Usage analytics dashboard (no admin access)
- Image generation (no Imagen calls in demo)
- File upload (no field file import)
- PDF export (only Word export via frontend)

---

## Business Model

The demo is a **lead generation tool**, not a standalone product. It exists solely to:

1. **Lower the barrier to entry** — visitors can try before registering
2. **Demonstrate value** — the AI quality is the sales pitch
3. **Collect warm leads** — sessions that migrate are highly qualified
4. **Reduce support burden** — users who try the demo understand the product before signing up

**Revenue model:** The full platform is a SaaS product with subscription tiers. The demo feeds the top of the funnel.

---

> Next: [`02-tech-stack.md`](02-tech-stack.md)

(End of file)
