# 07 — Frontend Components & Composables

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Pages](#pages)
2. [Components](#components)
3. [Composables](#composables)
4. [State Flow](#state-flow)
5. [Event Bus](#event-bus)

---

## Pages

### `pages/index.vue`

The **root page** and the entire demo experience. There is no separate landing page or sub-page.

**Responsibilities:**
- Bootstrap the demo session via `useDemoSession()`
- Load the grant/template catalog via `GET /api/config`
- Load dynamic fields (if available) or derive static questions from `json_schema`
- Manage the `DemoChatbox` component with all props and event handlers
- Handle plan generation, revision, and finalization
- Show the `DemoRegisterModal` when limits are reached

**Key Props Passed to `DemoChatbox`:**

| Prop | Type | Description |
|------|------|-------------|
| `grantId` | `string` | Selected grant ID (e.g., `sbir`) |
| `templateId` | `string` | Selected template ID (e.g., `sbir_p1`) |
| `grantName` | `string` | Display name of the grant |
| `templateName` | `string` | Display name of the template |
| `allQuestions` | `Question[]` | Array of all field questions |
| `sessionId` | `string` | Demo session ID |
| `interactionCount` | `number` | Current prompt count |
| `interactionLimit` | `number` | Max prompts (default 20) |
| `chatLimitReached` | `boolean` | Whether prompt limit is reached |
| `generationLimitReached` | `boolean` | Whether generation limit is reached |
| `downloadLimitReached` | `boolean` | Whether download limit is reached |
| `hasGeneratedDocx` | `boolean` | Whether plan has been generated |
| `conversationHistory` | `Message[]` | Chat messages array |
| `storedAnswers` | `Record<string, string>` | Field answers map |
| `registerUrl` | `string` | Registration redirect URL |
| `projectTitle` | `string` | User-editable project title |
| `projectSummary` | `string` | Project summary |
| `sections` | `Section[]` | Template sections array |
| `candidatePlan` | `Record<string, Candidate[]>` | Generated candidates |
| `finalPlanContent` | `Record<string, any>` | Final selected plan |
| `savedPlanVersions` | `PlanVersion[]` | Saved plan versions |
| `sectionVersions` | `Record<string, number>` | Section version map |

**Key Events from `DemoChatbox`:**

| Event | Payload | Description |
|-------|---------|-------------|
| `messages-updated` | `Message[]` | Chat messages changed |
| `question-answers-updated` | `Record<string, string>` | Field answers changed |
| `ai-response-complete` | — | AI finished responding |
| `generate-plan` | `{ grantId, templateId, prompt }` | User requested plan generation |
| `download-completed` | — | User downloaded the report |
| `update-project-title` | `string` | User changed project title |
| `finalize-candidates` | `{ selected, rejected }` | User selected candidates |
| `request-version-update` | `{ version }` | User requested version revision |
| `register` | — | User clicked registration CTA |

---

## Components

### `components/chat/DemoChatbox.vue`

The **core demo chat interface**. Replaces the full platform's `Chatbox.vue` with demo-specific adaptations.

**Features:**
- Real-time WebSocket chat with streaming AI responses
- Message list with user/assistant bubbles
- Hidden field answer parsing (automatic form population)
- Progress indicators ("AI 正在構思下一個提問...")
- Composer with send button and tips
- Limit notices (chat limit, generation limit, download limit)
- Plan generation trigger ("輸出完整推演" button)
- Plan candidate selector (modal)
- Plan version modal (modal)
- Edit field modal (modal)
- File import button (disabled in demo — shows "註冊後可使用")
- Project name recommendation button (modal)

**Props:**

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `grantId` | `string` | Yes | Grant identifier |
| `templateId` | `string` | Yes | Template identifier |
| `grantName` | `string` | Yes | Grant display name |
| `templateName` | `string` | Yes | Template display name |
| `allQuestions` | `Question[]` | Yes | All field questions |
| `sessionId` | `string` | Yes | Demo session ID |
| `interactionCount` | `number` | Yes | Current prompt count |
| `interactionLimit` | `number` | Yes | Max prompts |
| `chatLimitReached` | `boolean` | Yes | Chat limit reached flag |
| `generationLimitReached` | `boolean` | Yes | Generation limit reached flag |
| `downloadLimitReached` | `boolean` | Yes | Download limit reached flag |
| `hasGeneratedDocx` | `boolean` | Yes | Has generated flag |
| `conversationHistory` | `Message[]` | Yes | Initial messages |
| `storedAnswers` | `Record<string, string>` | Yes | Initial answers |
| `registerUrl` | `string` | Yes | Registration URL |
| `projectTitle` | `string` | Yes | Project title |
| `projectSummary` | `string` | Yes | Project summary |
| `sections` | `Section[]` | Yes | Template sections |
| `candidatePlan` | `Record<string, Candidate[]>` | No | Generated candidates |
| `finalPlanContent` | `Record<string, any>` | No | Final plan content |
| `savedPlanVersions` | `PlanVersion[]` | No | Saved versions |
| `sectionVersions` | `Record<string, number>` | No | Section versions |

**Events:**

| Event | Payload | Description |
|-------|---------|-------------|
| `messages-updated` | `Message[]` | Messages changed |
| `question-answers-updated` | `Record<string, string>` | Answers changed |
| `ai-response-complete` | — | AI response done |
| `generate-plan` | `{ grantId, templateId, prompt }` | Generate plan request |
| `download-completed` | — | Download done |
| `update-project-title` | `string` | Title changed |
| `finalize-candidates` | `{ selected, rejected }` | Candidates selected |
| `request-version-update` | `{ version }` | Revise request |
| `register` | — | Register CTA clicked |

**Internal State:**

| State | Type | Description |
|-------|------|-------------|
| `messages` | `Message[]` | Current chat messages |
| `draftMessage` | `string` | Composer input text |
| `isFetchingNextQuestion` | `boolean` | AI is thinking |
| `isGenerationComplete` | `boolean` | Generation finished |
| `isReadOnly` | `boolean` | Input disabled (when limit reached) |
| `isComposing` | `boolean` | IME composition active |
| `showPlanCandidateSelector` | `boolean` | Show candidate modal |
| `showPlanVersionModal` | `boolean` | Show version modal |
| `showEditFieldModal` | `boolean` | Show edit field modal |
| `showRecommendNameModal` | `boolean` | Show name recommendation modal |
| `showFieldFileImportModal` | `boolean` | Show file import modal |
| `selectedPlan` | `Record<string, Candidate>` | User's candidate selections |
| `activeSection` | `string` | Currently active section ID |
| `activeQuestion` | `Question` | Currently focused question |
| `currentAnswer` | `string` | Current answer being edited |
| `currentAnswerMeta` | `AnswerMeta` | Current answer metadata |
| `ws` | `WebSocket` | Active WebSocket connection |
| `wsReady` | `boolean` | WebSocket is ready |
| `wsReconnectAttempts` | `number` | Reconnection attempt count |

**WebSocket Lifecycle:**

```
1. onMounted → connectWebSocket()
2. WebSocket opens → send init message
3. Receive "ready" → set wsReady = true
4. Receive "chunk_start" → set isFetchingNextQuestion = true
5. Receive "chunk" → append to current message
6. Receive "done" → set isFetchingNextQuestion = false
7. Receive "filled" → update storedAnswers, emit question-answers-updated
8. Receive "limit_reached" → set isReadOnly = true, emit register
9. Receive "error" → show error, attempt reconnect
10. onBeforeUnmount → close WebSocket
```

**Composer Behavior:**

- Enter key sends message (unless Shift+Enter for newline)
- IME composition state tracked (don't send during composition)
- Disabled when `isReadOnly` or `chatLimitReached`
- Shows placeholder text when disabled

---

### `components/chat/helper/DemoRegisterModal.vue`

**Upsell modal** triggered when the user hits any limit.

**Features:**
- Shows current progress (how many questions answered, plan generated, etc.)
- Displays project title (editable in modal)
- Shows registration URL with `?ref=<session_id>`
- Has "close" button to dismiss (user can continue browsing but cannot chat/generate)

**Props:**

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `isOpen` | `boolean` | Yes | Modal visibility (v-model) |
| `interactionCount` | `number` | Yes | Current prompt count |
| `interactionLimit` | `number` | Yes | Max prompts |
| `registerUrl` | `string` | Yes | Registration URL |
| `sessionId` | `string` | Yes | Session ID |
| `projectTitle` | `string` | Yes | Project title |

**Events:**

| Event | Payload | Description |
|-------|---------|-------------|
| `close` | — | Modal dismissed |
| `update-title` | `string` | Title changed |

---

### Other Components (inherited from full platform)

| Component | File | Purpose | Status in Demo |
|-----------|------|---------|----------------|
| `PlanCandidateSelector` | `components/chat/helper/PlanCandidateSelector.vue` | Shows AI-generated candidates per section | ✅ Active |
| `PlanVersionModal` | `components/chat/helper/PlanVersionModal.vue` | Shows version history, timeline, export | ✅ Active |
| `EditFieldModal` | `components/chat/helper/EditFieldModal.vue` | Edit previously answered field | ✅ Active |
| `RecommendNameModal` | `components/chat/helper/RecommendNameModal.vue` | Project name recommendation | ✅ Active |
| `FieldFileImportModal` | `components/chat/helper/FieldFileImportModal.vue` | Upload file to auto-fill | ⚠️ Disabled in UI |
| `ChatSidebar` | `components/chat/ChatSidebar.vue` | Sidebar with Q&A items | ❌ Removed (not used in demo) |
| `GlobalLoading` | `components/global/GlobalLoading.vue` | Global loading overlay | ✅ Active |
| `GlobalNotifications` | `components/global/GlobalNotifications.vue` | Toast notifications | ✅ Active |
| `GlobalConfirm` | `components/global/GlobalConfirm.vue` | Confirm dialog | ✅ Active |

---

## Composables

### `composables/useDemoSession.ts`

**The single source of the visitor's demo session.**

**Problem it solves:** If multiple callers (page, layout, useCurrentUser) call `GET /api/demo` in parallel before the `Set-Cookie` lands, each creates a **separate session**. This causes the cookie the WebSocket uses to diverge from the ID the frontend keeps for registration.

**Solution:** Promise memoization. The first call creates a single promise that all concurrent callers await.

```typescript
let demoSessionPromise: Promise<Record<string, any> | null> | null = null;

export function useDemoSession() {
  const ensureDemoSession = (): Promise<Record<string, any> | null> => {
    if (typeof window === "undefined") return Promise.resolve(null);
    if (!demoSessionPromise) {
      const config = useRuntimeConfig();
      const apiBaseUrl = `${config.public.apiBaseUrl}/api`;
      demoSessionPromise = fetch(`${apiBaseUrl}/demo`, { credentials: "include" })
        .then((resp) => (resp.ok ? resp.json() : null))
        .catch((err) => {
          console.error("Failed to bootstrap demo session", err);
          demoSessionPromise = null;
          return null;
        });
    }
    return demoSessionPromise;
  };

  return { ensureDemoSession };
}
```

**Usage:**

```typescript
const { ensureDemoSession } = useDemoSession();
const demo = await ensureDemoSession();
if (!demo) {
  throw new Error("Session bootstrap failed");
}
const sessionId = demo.session_id;
```

**Important:**
- `ensureDemoSession()` must be called **before** any other API call or WebSocket connection
- It only works on the **client** (SSR returns `null`)
- After a transient failure, it resets the promise to allow retry

---

### `composables/useAppAuth.ts`

**Authentication helpers adapted for demo mode.**

**Key differences from full platform:**
- No Bearer token (no JWT)
- No `authenticatedFetch()` — uses standard `fetch()` with `credentials: "include"`
- No login/logout logic
- Session is entirely cookie-based

**Functions:**

| Function | Purpose | Demo Behavior |
|----------|---------|---------------|
| `getAppSession()` | Check auth status | Returns `{ isAuthenticated: false }` (always) |
| `authenticatedFetch()` | API call with auth | Not used in demo |
| `logout()` | Log out | Not used in demo |

**In demo mode, the frontend uses plain `fetch()`:**

```typescript
const response = await fetch(`${apiBaseUrl}/demo`, {
  credentials: "include",
});
```

---

### `composables/usePlanGenerator.ts`

**Plan generation flow orchestration.**

**Responsibilities:**
- Manage generation state (loading, error, success)
- Call `POST /api/generate_plan`
- Transform raw response into `candidatePlan` format
- Handle errors and show notifications

**Usage:**

```typescript
const {
  isGenerating,
  error,
  candidatePlan,
  generatePlan,
  revisePlan,
} = usePlanGenerator();

await generatePlan({
  grantId: "sbir",
  templateId: "sbir_p1",
  prompt: "We are a B2B SaaS company...",
});
```

---

### `composables/useLoading.ts`

**Global loading state.**

```typescript
const { show, hide } = useLoading();
show("正在生成計畫書...", true);  // show with spinner
hide();
```

---

### `composables/useNotifications.ts`

**Toast notifications.**

```typescript
const { success, error, info } = useNotifications();
success("計畫書草稿已生成！");
error("生成失敗: 未知錯誤");
```

---

## State Flow

```
┌─────────────────────────────────────────┐
│          Browser loads /                │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      useDemoSession.ensureDemoSession() │
│      ──> GET /api/demo (mint cookie)    │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│       Load catalog: GET /api/config       │
│       Load status: GET /api/demo/status   │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│       Load dynamic fields (optional)    │
│       GET /api/demo/dynamic-fields      │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│       WebSocket: /ws/chat_guidance      │
│       Send init message                 │
└─────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│       Chat loop (user <-> AI)             │
│       • User sends message              │
│       • AI streams response             │
│       • Hidden fields parsed            │
│       • Answers saved to DB             │
│       • Limits checked                  │
└─────────────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         ▼                   ▼
┌────────────────┐    ┌────────────────┐
│  Limit reached │    │  Generate plan │
│  (show modal)  │    │  (POST /api/    │
│                │    │   generate_plan)│
└────────────────┘    └────────────────┘
         │                   │
         │                   ▼
         │          ┌────────────────┐
         │          │ Select candidates│
         │          │ (modal)          │
         │          └────────────────┘
         │                   │
         │                   ▼
         │          ┌────────────────┐
         │          │ Finalize plan   │
         │          │ (PUT /api/demo) │
         │          └────────────────┘
         │                   │
         │                   ▼
         │          ┌────────────────┐
         │          │ Download Word   │
         │          │ (frontend util) │
         │          └────────────────┘
         │                   │
         └───────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│       Register CTA clicked              │
│       Redirect to full platform         │
│       with ?ref=<session_id>            │
└─────────────────────────────────────────┘
```

---

## Event Bus

The frontend uses **Vue's native event system** (emit/on) and **Nuxt's composable pattern** for state sharing. There is no global event bus.

**State sharing strategy:**
- **Page-level state** (index.vue) → passed down as props
- **Component events** → emitted up to parent
- **Global UI state** (loading, notifications) → shared composables
- **WebSocket state** → managed inside `DemoChatbox.vue`

---

> Next: [`08-environment-variables.md`](08-environment-variables.md)

(End of file)
