# 03 — System Architecture

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## System Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                               │
│                         (Anonymous, No Login)                           │
│                    https://demo-aiproposal.tgsa.com.tw                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Nginx Reverse Proxy                             │
│                    (TLS termination, routing, caching)                    │
│                                                                         │
│   Route: /                     →  Nuxt Frontend (localhost:3000)      │
│   Route: /api/*                →  FastAPI Backend (localhost:8000)    │
│   Route: /ws/chat_guidance     →  FastAPI Backend (WebSocket)          │
│   Route: /_nuxt_icon/*         →  Nuxt Frontend (icon endpoint)        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
┌─────────────────────────────┐         ┌─────────────────────────────┐
│      Nuxt 3 Frontend        │         │      FastAPI Backend        │
│      (Vue 3 + TypeScript)   │         │      (Python 3.10+)         │
│                             │         │                             │
│  pages/index.vue            │         │  app/api/generate.py        │
│  ├── DemoChatbox.vue        │         │  ├── /generate_plan         │
│  ├── DemoRegisterModal.vue  │         │  ├── /revise_plan_version   │
│  └── useDemoSession.ts      │         │  ├── /recommend_project_names│
│                             │         │  └── /ws/chat_guidance      │
│  composables/               │         │                             │
│  ├── useAppAuth.ts          │         │  app/api/projects.py        │
│  ├── usePlanGenerator.ts    │         │  ├── /api/demo (GET/PUT/DEL)│
│  └── useLoading.ts          │         │  ├── /api/demo/status       │
│                             │         │  ├── /api/demo/dynamic-fields│
│  utils/                     │         │  └── /api/demo/download     │
│  ├── exportToWord.ts        │         │                             │
│  └── supabaseClient.ts      │         │  app/api/config.py          │
│                             │         │  ├── /api/config            │
│                             │         │  └── /api/config/refresh    │
│                             │         │                             │
│                             │         │  app/services/              │
│                             │         │  ├── llm_service.py         │
│                             │         │  ├── supabase_service.py    │
│                             │         │  └── model_registry.py      │
│                             │         │                             │
│                             │         │  app/utils/                 │
│                             │         │  ├── ip_extractor.py        │
│                             │         │  └── demo_rate_limiter.py   │
│                             │         │                             │
│                             │         │  app/core/                  │
│                             │         │  └── lifecycle.py           │
└─────────────┬───────────────┘         └─────────────┬───────────────┘
              │                                       │
              │           ┌───────────────────────────┘
              │           │
              ▼           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Supabase PostgreSQL (Shared)                         │
│                    https://<project>.supabase.co                      │
│                                                                         │
│   Schema: ai_proposal_platform                                          │
│   ├── demo                        ← Demo sessions (anonymous)          │
│   ├── demo_ip_limits              ← Rate limiting counters             │
│   ├── users                       ← Full platform users                  │
│   ├── projects                    ← Full platform projects               │
│   ├── execution_logs              ← Execution audit trail                │
│   ├── usage_logs                  ← Token/cost tracking                  │
│   ├── grants                      ← Grant definitions                  │
│   ├── plan_templates              ← Template definitions               │
│   ├── sections                    ← Section schemas                    │
│   ├── dynamic_sections            ← Dynamic field definitions          │
│   ├── dynamic_fields              ← Dynamic field details              │
│   ├── models                      ← LLM model registry                 │
│   ├── routing_rules               ← Model routing rules                │
│   └── ... (other full platform tables)                                  │
│                                                                         │
│   Functions:                                                            │
│   └── migrate_demo_to_project()   ← Session → project migration         │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Full AI Proposal Platform (aiproposal.tgsa.com.tw)        │
│                                                                         │
│   • OAuth client (connects to assist_link portal)                     │
│   • claim_demo_session() — reads demo row, creates project row        │
│   • User dashboard, admin panel, analytics                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Component Diagram

### Frontend

```
┌─────────────────────────────────────────┐
│            pages/index.vue                │
│  (Root page — no landing page)           │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │      DemoChatbox.vue                ││
│  │  ┌─────────────────────────────┐   ││
│  │  │  Chat Area                  │   ││
│  │  │  • Message list (user/AI) │   ││
│  │  │  • Streaming chunks       │   ││
│  │  │  • Hidden field parsing   │   ││
│  │  └─────────────────────────────┘   ││
│  │  ┌─────────────────────────────┐   ││
│  │  │  Composer Footer            │   ││
│  │  │  • Text input               │   ││
│  │  │  • Limit notices            │   ││
│  │  │  • Send button              │   ││
│  │  └─────────────────────────────┘   ││
│  │  ┌─────────────────────────────┐   ││
│  │  │  PlanCandidateSelector      │   ││
│  │  │  (modal)                    │   ││
│  │  └─────────────────────────────┘   ││
│  │  ┌─────────────────────────────┐   ││
│  │  │  PlanVersionModal           │   ││
│  │  │  (modal)                    │   ││
│  │  └─────────────────────────────┘   ││
│  │  ┌─────────────────────────────┐   ││
│  │  │  EditFieldModal             │   ││
│  │  │  (modal)                    │   ││
│  │  └─────────────────────────────┘   ││
│  └─────────────────────────────────────┘│
│  ┌─────────────────────────────────────┐│
│  │      DemoRegisterModal.vue          ││
│  │  (Triggered at limits)              ││
│  │  • Progress summary                 ││
│  │  • Register CTA                     ││
│  │  • Project title input              ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
              │
              │ uses
              ▼
┌─────────────────────────────────────────┐
│           useDemoSession.ts             │
│  • Memoized GET /api/demo call          │
│  • Prevents parallel cookie minting     │
└─────────────────────────────────────────┘
              │
              │ uses
              ▼
┌─────────────────────────────────────────┐
│           useAppAuth.ts                 │
│  • No Bearer token in demo              │
│  • Cookie-based auth check              │
│  • demoFetch() wrapper                  │
└─────────────────────────────────────────┘
```

### Backend

```
┌─────────────────────────────────────────┐
│           app/main.py                   │
│  FastAPI entrypoint                     │
│  • CORS configuration                   │
│  • Router registration                  │
│  • Startup/shutdown lifecycle           │
└─────────────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│generate│ │projects│ │ config │
│ .py    │ │ .py    │ │ .py    │
└────────┘ └────────┘ └────────┘
    │         │         │
    │    ┌────┴────┐    │
    │    │         │    │
    ▼    ▼         ▼    ▼
┌─────────────────────────────────────────┐
│      app/services/llm_service.py        │
│  • stream_external_api()                │
│  • call_external_api()                  │
│  • generate_section_content()           │
│  • Model routing & fallback             │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│    app/services/supabase_service.py     │
│  • get_demo_session()                   │
│  • ensure_demo_session()                │
│  • update_demo_session()                │
│  • increment_demo_interaction()         │
│  • append_demo_usage_log()              │
│  • append_demo_execution_event()        │
│  • get_dynamic_fields_for_template()    │
│  • get_template_by_id()                   │
│  • Direct SQLAlchemy session (for       │
│    atomic rate limiter upsert)          │
└─────────────────────────────────────────┘
```

---

## Data Flow

### 1. Session Bootstrap

```
Browser ──GET /api/demo──> Nginx ──> FastAPI
                                │
                                ├──> dependencies.get_demo_session_id()
                                │    ├──> Check cookie
                                │    ├──> If missing/invalid: mint UUID
                                │    └──> Set cookie
                                │
                                └──> projects.py get_demo_session()
                                     ├──> supabase_service.ensure_demo_session()
                                     └──> Return row

FastAPI ──200 + Set-Cookie──> Nginx ──> Browser
```

### 2. WebSocket Chat

```
Browser ──WS /ws/chat_guidance──> Nginx ──> FastAPI
                                      │
                                      ├──> Accept connection
                                      ├──> Read cookie
                                      ├──> Load demo row from DB
                                      ├──> Wait for init message
                                      │
                                      └──> Message loop:
                                           ├──> Receive user_message
                                           ├──> Check limits
                                           ├──> If exceeded: send limit_reached
                                           ├──> If OK: call LLM
                                           │    ├──> stream_external_api()
                                           │    └──> Send chunks
                                           ├──> Parse hidden answers
                                           ├──> Save state to DB
                                           └──> Check limits again
```

### 3. Plan Generation

```
Browser ──POST /api/generate_plan──> Nginx ──> FastAPI generate.py
                                            │
                                            ├──> Check has_generated_docx
                                            ├──> Load template from app.state
                                            ├──> Filter sections by answered fields
                                            ├──> For each section:
                                            │    └──> generate_section_content()
                                            │         ├──> Build prompt
                                            │         ├──> call LLM
                                            │         └──> Parse JSON
                                            ├──> Aggregate results
                                            ├──> Update has_generated_docx
                                            └──> Return candidates
```

### 4. Migration (Demo → Platform)

```
Browser ──Click register──> Full platform /api/external-auth/redirect?ref=<sid>
                                │
                                ├──> Set pending_demo_claim cookie
                                ├──> Redirect to OAuth IdP
                                ├──> User registers
                                ├──> Redirect to /api/external-auth/callback
                                ├──> Read pending_demo_claim cookie
                                ├──> claim_demo_session(ref, user_id)
                                │    └──> SQL: migrate_demo_to_project()
                                │         ├──> Lock demo row
                                │         ├──> INSERT projects
                                │         ├──> INSERT execution_logs
                                │         ├──> INSERT usage_logs
                                │         └──> UPDATE demo SET status='claimed'
                                └──> Redirect to /projects/<id>
```

---

## Deployment Architecture

### Dev VPS

```
┌─────────────────────────────────────────┐
│           Docker Host                   │
│  (1 vCPU / 2GB RAM / 4GB swap)         │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  nginx-proxy (container)       │    │
│  │  • Port 80/443                  │    │
│  │  • TLS via Let's Encrypt        │    │
│  │  • Nginx Proxy Manager UI       │    │
│  └─────────────────────────────────┘    │
│           │                             │
│     ┌─────┴─────┐                       │
│     │           │                       │
│     ▼           ▼                       │
│  ┌──────┐  ┌──────┐                    │
│  │nuxt  │  │fastapi│                   │
│  │:3000 │  │:8000 │                   │
│  └──────┘  └──────┘                   │
│                                         │
└─────────────────────────────────────────┘
              │
              ▼
    Supabase (cloud)
```

### Production

```
┌─────────────────────────────────────────┐
│           Docker Host (TBD)               │
│                                         │
│  ┌─────────────────────────────────┐    │
│  │  nginx (container)             │    │
│  │  • Custom nginx.conf            │    │
│  │  • TLS via managed cert         │    │
│  └─────────────────────────────────┘    │
│           │                             │
│     ┌─────┴─────┐                       │
│     │           │                       │
│     ▼           ▼                       │
│  ┌──────┐  ┌──────┐                    │
│  │nuxt  │  │fastapi│                   │
│  │:3000 │  │:8000 │                   │
│  └──────┘  └──────┘                   │
│                                         │
└─────────────────────────────────────────┘
              │
              ▼
    Supabase (cloud, shared)
```

---

## Network Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Visitor   │────>│   Cloudflare│────>│   Nginx     │
│   Browser   │     │   (DNS/TLS) │     │   (VPS)     │
└─────────────┘     └─────────────┘     └─────────────┘
                                                │
                          ┌─────────────────────┘
                          │
                    ┌─────┴─────┐
                    │           │
                    ▼           ▼
              ┌────────┐  ┌────────┐
              │ Frontend│  │ Backend│
              │ :3000   │  │ :8000  │
              └────────┘  └────────┘
                    │           │
                    │           │
                    │    ┌──────┘
                    │    │
                    ▼    ▼
              ┌─────────────┐
              │  Supabase   │
              │ PostgreSQL  │
              └─────────────┘
                    │
                    │
                    ▼
              ┌─────────────┐
              │ Full Platform│
              │ (OAuth client)│
              └─────────────┘
                    │
                    │
                    ▼
              ┌─────────────┐
              │ assist_link │
              │ (OAuth IdP) │
              └─────────────┘
```

---

> Next: [`04-database-schema.md`](04-database-schema.md)

(End of file)
