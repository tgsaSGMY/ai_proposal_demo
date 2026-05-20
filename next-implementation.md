# Next Implementation Plan — AI Proposal Demo (Lead Generation)

> **Version:** 1.0.0-demo  
> **Last Updated:** 2026-05-18  
> **Purpose:** Step-by-step implementation guide for converting the AI Proposal Platform into a free-access demo with hard limits and seamless signup migration.

---

## Table of Contents

1. [Phase 0: Environment & Configuration](#phase-0-environment--configuration)
2. [Phase 1: Database Layer](#phase-1-database-layer)
3. [Phase 2: Backend — Demo Router & Middleware](#phase-2-backend--demo-router--middleware)
4. [Phase 3: Backend — Limit Enforcement](#phase-3-backend--limit-enforcement)
5. [Phase 4: Backend — .docx Generation for Demo](#phase-4-backend--docx-generation-for-demo)
6. [Phase 5: Frontend — Demo Chat Page (No Landing Page)](#phase-5-frontend--demo-chat-page)
7. [Phase 6: Frontend — DemoChatbox Component](#phase-6-frontend--demochatbox-component)
8. [Phase 7: Frontend — Session Management](#phase-7-frontend--session-management)
9. [Phase 8: Frontend — Upsell & CTA](#phase-8-frontend--upsell--cta)
10. [Phase 9: Migration Flow](#phase-9-migration-flow)
11. [Phase 10: Testing & Verification](#phase-10-testing--verification)
12. [Phase 11: Documentation & Deployment](#phase-11-documentation--deployment)
13. [Appendix A: File Inventory](#appendix-a-file-inventory)

---

## Phase 0: Environment & Configuration

### 0.1 Backend Environment Variables

**File:** `backend/.env` (add to existing, DO NOT commit)

```env
# ============================================
# DEMO MODE CONFIGURATION
# ============================================
DEMO_MODE=true
DEMO_TEMPLATE_ID=sbir_p1
DEMO_MAX_PROMPTS_PER_SESSION=15
DEMO_MAX_GENERATIONS_PER_SESSION=1
DEMO_MAX_TOKENS_PER_SESSION=100000
DEMO_SESSION_EXPIRY_DAYS=30
DEMO_IP_HOURLY_LIMIT=3
DEMO_IP_DAILY_LIMIT=5

# URLs
DEMO_FRONTEND_URL=https://demo-aiproposal.tgsa.com.tw
FULL_PLATFORM_URL=https://aiproposal.tgsa.com.tw

# Internal service key for migration endpoint (generate strong random string)
DEMO_MIGRATION_SERVICE_KEY=your-random-secret-key-here-change-in-production
```

### 0.2 Frontend Environment Variables

**File:** `frontend/.env` (add to existing, DO NOT commit)

```env
# ============================================
# DEMO MODE CONFIGURATION
# ============================================
NUXT_PUBLIC_IS_DEMO_MODE=true
NUXT_PUBLIC_DEMO_MAX_PROMPTS=15
NUXT_PUBLIC_DEMO_MAX_GENERATIONS=1
NUXT_PUBLIC_FULL_PLATFORM_URL=https://aiproposal.tgsa.com.tw
NUXT_PUBLIC_DEMO_TEMPLATE_ID=sbir_p1
```

### 0.3 Backend Config Constants

**File:** `backend/app/config.py` (append to existing)

```python
# ============================================
# Demo Mode Configuration
# ============================================
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in {"1", "true", "yes"}
DEMO_TEMPLATE_ID = os.getenv("DEMO_TEMPLATE_ID", "sbir_p1")
DEMO_MAX_PROMPTS_PER_SESSION = int(os.getenv("DEMO_MAX_PROMPTS_PER_SESSION", "15"))
DEMO_MAX_GENERATIONS_PER_SESSION = int(os.getenv("DEMO_MAX_GENERATIONS_PER_SESSION", "1"))
DEMO_MAX_TOKENS_PER_SESSION = int(os.getenv("DEMO_MAX_TOKENS_PER_SESSION", "100000"))
DEMO_SESSION_EXPIRY_DAYS = int(os.getenv("DEMO_SESSION_EXPIRY_DAYS", "30"))
DEMO_IP_HOURLY_LIMIT = int(os.getenv("DEMO_IP_HOURLY_LIMIT", "3"))
DEMO_IP_DAILY_LIMIT = int(os.getenv("DEMO_IP_DAILY_LIMIT", "5"))
DEMO_FRONTEND_URL = os.getenv("DEMO_FRONTEND_URL", "https://demo-aiproposal.tgsa.com.tw")
FULL_PLATFORM_URL = os.getenv("FULL_PLATFORM_URL", "https://aiproposal.tgsa.com.tw")
```

### 0.4 Frontend Runtime Config

**File:** `frontend/nuxt.config.ts` (modify existing)

```typescript
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxtjs/tailwindcss", "@nuxt/icon", "nuxt-color-picker"],
  icon: {
    localApiEndpoint: "/_nuxt_icon",
  },
  runtimeConfig: {
    public: {
      apiBaseUrl: process.env.NUXT_PUBLIC_API_BASE_URL || "",
      platformHomeUrl:
        process.env.NUXT_PUBLIC_PLATFORM_HOME_URL ||
        "https://portal.tgsaapp.com/",
      supabaseUrl: process.env.SUPABASE_URL || "",
      supabaseAnonKey: process.env.SUPABASE_ANON_KEY || "",
      
      // --- NEW: Demo Mode Config ---
      isDemoMode: process.env.NUXT_PUBLIC_IS_DEMO_MODE === "true",
      demoMaxPrompts: parseInt(process.env.NUXT_PUBLIC_DEMO_MAX_PROMPTS || "15"),
      demoMaxGenerations: parseInt(process.env.NUXT_PUBLIC_DEMO_MAX_GENERATIONS || "1"),
      fullPlatformUrl: process.env.NUXT_PUBLIC_FULL_PLATFORM_URL || "https://aiproposal.tgsa.com.tw",
      demoTemplateId: process.env.NUXT_PUBLIC_DEMO_TEMPLATE_ID || "sbir_p1",
    },
  },
  routeRules: {
    "/projects/**": { ssr: false },
    "/demo/**": { ssr: false },   // <-- ADD THIS
    "/": { ssr: false },
  },
});
```

### 0.5 Main.py — Router Reconstruction (CRITICAL)

**File:** `backend/app/main.py` (modify existing)

**REMOVE these routers entirely:**
- `auth` — Demo is anonymous, no login status checks
- `external_auth` — No OAuth in demo
- `projects` — Demo uses `demo_sessions` table, not `projects` table
- `datasets` — No dataset governance in demo
- `generate` — Demo uses `/api/demo/*` endpoints exclusively (original endpoints write to `projects`/`execution_logs`)

**KEEP only:**
- `config` — Read-only grant/template config (safe)
- `demo` — All demo endpoints + WebSocket

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# === NEW: Only import routers needed for demo ===
from app.api import (
    config as api_config,  # Keep: reads grant/template config
    demo as demo_router,   # NEW: demo endpoints + /ws/demo_chat
)
# REMOVED: generate, auth, external_auth, projects, datasets

from app.core.lifecycle import startup_event_handler, shutdown_event_handler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Proposal Platform API — Demo Edition",
    description="Anonymous demo API for SBIR Phase 1 proposal generation.",
    version="1.0.0-demo"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://demo-aiproposal.tgsa.com.tw",
        "https://aiproposal.tgsa.com.tw",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await startup_event_handler(app)

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_event_handler(app)

# === NEW: Only register demo-safe routers ===
app.include_router(demo_router.router)      # All /api/demo/* + /ws/demo_chat
app.include_router(api_config.router)       # /api/config, /api/plan_templates

# REMOVED: app.include_router(generate.router)
# REMOVED: app.include_router(projects.router)
# REMOVED: app.include_router(datasets.router)
# REMOVED: app.include_router(auth.router)
# REMOVED: app.include_router(external_auth.router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "AI Proposal Platform Demo API"}
```

> ⚠️ **IMPORTANT:** Do NOT register the original `generate.router` in demo mode. Its endpoints (`/api/generate_plan`, etc.) expect authenticated users and write to `projects`/`execution_logs` tables. The demo uses `/api/demo/*` endpoints exclusively.

### 0.6 Database Write Protection (CRITICAL)

**Problem:** The original `generate.py` endpoints (`/api/generate_plan`, `/api/revise_plan_version`, WebSocket `/ws/chat_guidance`) call:
- `supabase_service.update_project_record()` → writes to **`projects`** table
- `supabase_service.log_execution_event()` → writes to **`execution_logs`** table
- `supabase_service.log_usage()` → writes to **`usage_logs`** table

If a demo user triggers these, it pollutes the production database with anonymous data.

**Solution:** In demo mode, these endpoints are **not registered** in `main.py`. The demo uses only `/api/demo/*` endpoints which write exclusively to `demo_sessions` table.

**Verification:**

```bash
# 1. Verify backend config loads
python -c "from app.config import DEMO_MODE, DEMO_TEMPLATE_ID; print(DEMO_MODE, DEMO_TEMPLATE_ID)"

# 2. Verify removed endpoints return 404
curl http://localhost:8000/api/projects
# Expected: {"detail":"Not Found"}

curl http://localhost:8000/api/auth/me
# Expected: {"detail":"Not Found"}

curl http://localhost:8000/api/datasets
# Expected: {"detail":"Not Found"}

# 3. Verify demo endpoints exist
curl -X POST http://localhost:8000/api/demo/init
# Expected: {"session_id":"...","template_id":"..."}

# 4. Frontend build check
npm run build
# Check if runtimeConfig.public.isDemoMode is true in generated output
```

---

## Phase 1: Database Layer

> **Owner:** Colleague (DB schema)  
> **Integration:** You (backend API integration)

### 1.1 SQL Migration Script

**File:** `database-migrations/001_demo_tables.sql` (create new)

Run this in Supabase SQL Editor:

```sql
-- ============================================
-- 1. demo_sessions — Core Anonymous Session State
-- ============================================
CREATE TABLE IF NOT EXISTS demo_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          TEXT UNIQUE NOT NULL,
    ip_address          INET,
    grant_id            TEXT NOT NULL DEFAULT 'sbir',
    template_id         TEXT NOT NULL DEFAULT 'sbir_p1',
    
    -- Usage Limits
    prompt_count        INT DEFAULT 0,
    total_tokens_used   INT DEFAULT 0,
    has_generated_docx  BOOLEAN DEFAULT FALSE,
    
    -- Content Mirrors (JSONB)
    chat_history        JSONB DEFAULT '[]',
    stored_answers      JSONB DEFAULT '{}',
    generated_sections  JSONB DEFAULT '[]',
    execution_timeline  JSONB DEFAULT '[]',
    
    -- Metadata
    status              TEXT DEFAULT 'active',
    created_at          TIMESTAMPTZ DEFAULT now(),
    expires_at          TIMESTAMPTZ DEFAULT (now() + interval '30 days'),
    
    -- Migration
    migrated_to_project_id  UUID REFERENCES projects(id) ON DELETE SET NULL,
    migrated_at             TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_demo_sessions_session_id ON demo_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_demo_sessions_ip_created ON demo_sessions(ip_address, created_at);
CREATE INDEX IF NOT EXISTS idx_demo_sessions_expires ON demo_sessions(expires_at) 
    WHERE status IN ('active', 'generated');

-- ============================================
-- 2. demo_ip_limits — Rate Limit Counter
-- ============================================
CREATE TABLE IF NOT EXISTS demo_ip_limits (
    ip_address      INET NOT NULL,
    window_start    TIMESTAMPTZ NOT NULL,
    window_type     TEXT NOT NULL,
    session_count   INT DEFAULT 0,
    PRIMARY KEY (ip_address, window_start, window_type)
);

-- ============================================
-- 3. Migration Stored Procedure
-- ============================================
CREATE OR REPLACE FUNCTION migrate_demo_to_project(
    p_demo_session_id TEXT,
    p_new_user_id UUID
)
RETURNS UUID AS $$
DECLARE
    v_demo_record RECORD;
    v_project_id UUID;
BEGIN
    SELECT * INTO v_demo_record
    FROM demo_sessions
    WHERE session_id = p_demo_session_id
      AND status = 'generated'
    FOR UPDATE;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Demo session not found or not ready for migration';
    END IF;
    
    INSERT INTO projects (
        user_id, title, description,
        grant_id, template_id,
        saved_plan, stored_answer, conversation_history,
        created_at
    ) VALUES (
        p_new_user_id,
        COALESCE(v_demo_record.stored_answers->>'plan_name', 'Migrated Demo Project'),
        COALESCE(v_demo_record.stored_answers->>'plan_summary', 'Imported from demo session'),
        v_demo_record.grant_id,
        v_demo_record.template_id,
        v_demo_record.generated_sections,
        v_demo_record.stored_answers,
        v_demo_record.chat_history,
        now()
    )
    RETURNING id INTO v_project_id;
    
    INSERT INTO execution_logs (project_id, user_id, event_type, payload, created_at)
    SELECT 
        v_project_id, p_new_user_id,
        (event->>'event_type')::TEXT,
        event->>'payload',
        COALESCE((event->>'created_at')::TIMESTAMPTZ, now())
    FROM jsonb_array_elements(v_demo_record.execution_timeline) AS event;
    
    UPDATE demo_sessions
    SET status = 'migrated',
        migrated_to_project_id = v_project_id,
        migrated_at = now()
    WHERE session_id = p_demo_session_id;
    
    RETURN v_project_id;
END;
$$ LANGUAGE plpgsql;
```

### 1.2 Daily Cleanup Cron (Supabase Edge Function or Backend Startup)

**Option A:** Supabase Edge Function (recommended)

```typescript
// supabase/functions/cleanup-demo-sessions/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );
  
  const { error } = await supabase
    .from("demo_sessions")
    .delete()
    .lt("expires_at", new Date().toISOString())
    .not("status", "in", "('migrated')");
  
  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 });
  }
  
  return new Response(JSON.stringify({ success: true }), { status: 200 });
});
```

**Option B:** Backend startup check (simpler, runs on every container start)

Add to `backend/app/core/lifecycle.py` in `startup_event_handler()`:

```python
async def cleanup_expired_demo_sessions(supabase_service):
    """Delete expired demo sessions that were not migrated."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    result = supabase_service.client.table("demo_sessions")\
        .delete()\
        .lt("expires_at", now)\
        .not_.in_("status", ["migrated"])\
        .execute()
    logger.info(f"Cleaned up {len(result.data)} expired demo sessions")
```

### Verification

```sql
-- Check tables exist
SELECT * FROM demo_sessions LIMIT 0;
SELECT * FROM demo_ip_limits LIMIT 0;

-- Test migration function (with dummy data)
INSERT INTO demo_sessions (session_id, status, generated_sections, stored_answers)
VALUES ('test-session-123', 'generated', '[]', '{"plan_name": "Test"}');

SELECT migrate_demo_to_project('test-session-123', '00000000-0000-0000-0000-000000000001'::UUID);

-- Cleanup test
DELETE FROM demo_sessions WHERE session_id = 'test-session-123';
```

---

## Phase 2: Backend — Demo Router & Middleware

### 2.1 IP Extraction Utility

**File:** `backend/app/utils/ip_extractor.py` (create new)

```python
"""
Extract real client IP from request, handling X-Forwarded-For behind nginx.
"""
from fastapi import Request
from typing import Optional

def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract client IP from request headers.
    Priority: X-Forwarded-For → X-Real-IP → request.client.host
    """
    # X-Forwarded-For can be a comma-separated list
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # First IP is typically the original client
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return None
```

### 2.2 Rate Limiting Utility

**File:** `backend/app/utils/demo_rate_limiter.py` (create new)

```python
"""
IP-based rate limiting for demo sessions.
3 sessions per hour, 5 sessions per day per IP.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional
from app.services.supabase_service import SupabaseService
from app.config import DEMO_IP_HOURLY_LIMIT, DEMO_IP_DAILY_LIMIT
import logging

logger = logging.getLogger(__name__)

class DemoRateLimiter:
    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service.client
    
    async def check_limits(self, ip_address: str) -> dict:
        """
        Check if IP has exceeded demo session limits.
        Returns: { "allowed": bool, "reason": str|None, "retry_after": int|None }
        """
        now = datetime.now(timezone.utc)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Check hourly limit
        hour_result = self.supabase.table("demo_ip_limits")\
            .select("session_count")\
            .eq("ip_address", ip_address)\
            .eq("window_start", hour_start.isoformat())\
            .eq("window_type", "hour")\
            .single()\
            .execute()
        
        hour_count = hour_result.data["session_count"] if hour_result.data else 0
        
        if hour_count >= DEMO_IP_HOURLY_LIMIT:
            next_hour = hour_start + timedelta(hours=1)
            retry_seconds = int((next_hour - now).total_seconds())
            return {
                "allowed": False,
                "reason": f"Hourly limit exceeded ({DEMO_IP_HOURLY_LIMIT} sessions/hour)",
                "retry_after": retry_seconds
            }
        
        # Check daily limit
        day_result = self.supabase.table("demo_ip_limits")\
            .select("session_count")\
            .eq("ip_address", ip_address)\
            .eq("window_start", day_start.isoformat())\
            .eq("window_type", "day")\
            .single()\
            .execute()
        
        day_count = day_result.data["session_count"] if day_result.data else 0
        
        if day_count >= DEMO_IP_DAILY_LIMIT:
            next_day = day_start + timedelta(days=1)
            retry_seconds = int((next_day - now).total_seconds())
            return {
                "allowed": False,
                "reason": f"Daily limit exceeded ({DEMO_IP_DAILY_LIMIT} sessions/day)",
                "retry_after": retry_seconds
            }
        
        return { "allowed": True, "reason": None, "retry_after": None }
    
    async def increment_counter(self, ip_address: str) -> None:
        """Increment both hour and day counters for an IP."""
        now = datetime.now(timezone.utc)
        hour_start = now.replace(minute=0, second=0, microsecond=0)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for window_start, window_type in [(hour_start, "hour"), (day_start, "day")]:
            # Upsert: increment if exists, insert if not
            existing = self.supabase.table("demo_ip_limits")\
                .select("session_count")\
                .eq("ip_address", ip_address)\
                .eq("window_start", window_start.isoformat())\
                .eq("window_type", window_type)\
                .single()\
                .execute()
            
            if existing.data:
                self.supabase.table("demo_ip_limits")\
                    .update({"session_count": existing.data["session_count"] + 1})\
                    .eq("ip_address", ip_address)\
                    .eq("window_start", window_start.isoformat())\
                    .eq("window_type", window_type)\
                    .execute()
            else:
                self.supabase.table("demo_ip_limits")\
                    .insert({
                        "ip_address": ip_address,
                        "window_start": window_start.isoformat(),
                        "window_type": window_type,
                        "session_count": 1
                    })\
                    .execute()
```

### 2.3 Demo Session Dependency

**File:** `backend/app/core/demo_dependencies.py` (create new)

```python
"""
FastAPI dependencies for demo session management.
Extracts or creates demo session from x-demo-session-id header.
"""
from fastapi import Request, Header, HTTPException
from typing import Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from app.config import DEMO_SESSION_EXPIRY_DAYS, DEMO_TEMPLATE_ID
from app.services.supabase_service import SupabaseService
from app.utils.ip_extractor import get_client_ip
from app.utils.demo_rate_limiter import DemoRateLimiter
import logging

logger = logging.getLogger(__name__)

async def get_or_create_demo_session(
    request: Request,
    x_demo_session_id: Optional[str] = Header(None),
    supabase_service: SupabaseService = None,  # Injected via Depends
) -> Dict[str, Any]:
    """
    Extract demo session from header, or create new one.
    Returns demo session record from database.
    """
    supabase = supabase_service.client if supabase_service else request.app.state.supabase_service.client
    
    session_id = x_demo_session_id
    
    # Try to find existing session
    if session_id:
        result = supabase.table("demo_sessions")\
            .select("*")\
            .eq("session_id", session_id)\
            .single()\
            .execute()
        
        if result.data:
            # Check expiry
            expires_at = datetime.fromisoformat(result.data["expires_at"].replace("Z", "+00:00"))
            if expires_at > datetime.now(timezone.utc):
                return result.data
            # Session expired, create new one below
            logger.info(f"Demo session {session_id} expired, creating new one")
    
    # Create new session
    new_session_id = str(uuid4())
    ip_address = get_client_ip(request)
    expires_at = datetime.now(timezone.utc) + timedelta(days=DEMO_SESSION_EXPIRY_DAYS)
    
    result = supabase.table("demo_sessions")\
        .insert({
            "session_id": new_session_id,
            "ip_address": ip_address,
            "template_id": DEMO_TEMPLATE_ID,
            "expires_at": expires_at.isoformat(),
        })\
        .execute()
    
    return result.data[0]

async def require_demo_session(
    request: Request,
    x_demo_session_id: Optional[str] = Header(None),
) -> Dict[str, Any]:
    """
    Require existing demo session (returns 401 if not provided).
    Used for endpoints that require an active session.
    """
    if not x_demo_session_id:
        raise HTTPException(status_code=401, detail="Demo session ID required")
    
    supabase = request.app.state.supabase_service.client
    result = supabase.table("demo_sessions")\
        .select("*")\
        .eq("session_id", x_demo_session_id)\
        .single()\
        .execute()
    
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid demo session")
    
    # Check expiry
    expires_at = datetime.fromisoformat(result.data["expires_at"].replace("Z", "+00:00"))
    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Demo session expired")
    
    return result.data
```

### 2.4 Demo API Router Scaffold

**File:** `backend/app/api/demo.py` (create new)

```python
"""
Demo API endpoints for anonymous users.
All endpoints use x-demo-session-id header instead of auth tokens.
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Header
from typing import Dict, Any, Optional
from app.core.demo_dependencies import get_or_create_demo_session, require_demo_session
from app.services.supabase_service import SupabaseService
from app.services.llm_service import LLMService
from app.api.dependencies import get_supabase_service, get_llm_service
from app.config import (
    DEMO_MAX_PROMPTS_PER_SESSION,
    DEMO_MAX_TOKENS_PER_SESSION,
    DEMO_MAX_GENERATIONS_PER_SESSION,
    FULL_PLATFORM_URL,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/demo", tags=["Demo"])

# ============================================
# Session Management
# ============================================

@router.post("/init")
async def demo_init(
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    Initialize a new demo session.
    Returns session_id to be stored in browser localStorage/cookie.
    """
    # TODO: Implement IP rate limiting check here
    session = await get_or_create_demo_session(request, None, supabase_service)
    return {
        "session_id": session["session_id"],
        "template_id": session["template_id"],
        "expires_at": session["expires_at"],
    }

@router.get("/status")
async def demo_status(
    session: Dict[str, Any] = Depends(require_demo_session),
):
    """
    Return current demo session usage and limits.
    Frontend polls this to update the DemoLimitBar.
    """
    prompts_remaining = max(0, DEMO_MAX_PROMPTS_PER_SESSION - session["prompt_count"])
    tokens_remaining = max(0, DEMO_MAX_TOKENS_PER_SESSION - session["total_tokens_used"])
    can_generate = not session["has_generated_docx"]
    
    return {
        "session_id": session["session_id"],
        "status": session["status"],
        "prompts_used": session["prompt_count"],
        "prompts_remaining": prompts_remaining,
        "prompts_total": DEMO_MAX_PROMPTS_PER_SESSION,
        "tokens_used": session["total_tokens_used"],
        "tokens_remaining": tokens_remaining,
        "tokens_total": DEMO_MAX_TOKENS_PER_SESSION,
        "has_generated": session["has_generated_docx"],
        "can_generate": can_generate,
        "expires_at": session["expires_at"],
    }

# ============================================
# Chat & Generation
# ============================================

@router.post("/chat")
async def demo_chat(
    request: Request,
    message: Dict[str, str],
    session: Dict[str, Any] = Depends(require_demo_session),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Send a chat message in demo mode.
    Increments prompt_count, accumulates tokens, appends to chat_history.
    """
    # TODO: Check prompt limit
    # TODO: Call LLM service
    # TODO: Update session counters
    # TODO: Return streaming response
    pass

@router.post("/generate-section")
async def demo_generate_section(
    request: Request,
    section_req: Dict[str, Any],
    session: Dict[str, Any] = Depends(require_demo_session),
    supabase_service: SupabaseService = Depends(get_supabase_service),
    llm_service: LLMService = Depends(get_llm_service),
):
    """
    Generate a single section content for demo session.
    """
    pass

# ============================================
# Finalize & .docx
# ============================================

@router.post("/finalize")
async def demo_finalize(
    request: Request,
    session: Dict[str, Any] = Depends(require_demo_session),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    Generate .docx report from demo session data.
    Sets has_generated_docx = true (one-time only).
    """
    pass

@router.get("/preview-docx")
async def demo_preview_docx(
    session: Dict[str, Any] = Depends(require_demo_session),
):
    """
    Return .docx preview data (HTML/JSON representation for iframe rendering).
    """
    pass

# ============================================
# Migration (Internal — called by full platform)
# ============================================

@router.post("/migrate")
async def demo_migrate(
    request: Request,
    payload: Dict[str, str],
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    Migrate demo session to full platform user account.
    Called by full platform backend after successful signup.
    Protected by X-Internal-Service-Key header.
    """
    import os
    internal_key = request.headers.get("X-Internal-Service-Key")
    expected_key = os.getenv("DEMO_MIGRATION_SERVICE_KEY")
    
    if not internal_key or internal_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid service key")
    
    demo_session_id = payload.get("demo_session_id")
    new_user_id = payload.get("new_user_id")
    
    if not demo_session_id or not new_user_id:
        raise HTTPException(status_code=400, detail="Missing parameters")
    
    # Call PostgreSQL function
    supabase = supabase_service.client
    result = supabase.rpc(
        "migrate_demo_to_project",
        {"p_demo_session_id": demo_session_id, "p_new_user_id": new_user_id}
    ).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Migration failed")
    
    return {
        "project_id": result.data,
        "message": "Demo session migrated successfully"
    }

# ============================================
# WebSocket Endpoint — /ws/demo_chat
# ============================================

@router.websocket("/ws/demo_chat")
async def websocket_demo_chat(websocket: WebSocket):
    """
    WebSocket for demo chat — anonymous, session-based.
    Accepts ?session_id=xxx in query parameter.
    Writes ONLY to demo_sessions.chat_history JSONB.
    NEVER writes to projects or execution_logs tables.
    """
    await websocket.accept()
    
    # TODO: Extract session_id from query param ?session_id=xxx
    # TODO: Validate session exists and not expired
    # TODO: Load chat_history from demo_sessions
    # TODO: Handle incoming messages, call LLM service
    # TODO: Append assistant response to chat_history
    # TODO: Increment prompt_count
    # TODO: Check limits at each step
    # TODO: Return streamed response to client
    pass
```

### 2.5 Register Demo Router

**File:** `backend/app/main.py` (modify)

```python
# Add import:
from app.api import demo as demo_router

# Add in app creation:
app.include_router(demo_router.router)
```

### Verification

```bash
curl -X POST http://localhost:8000/api/demo/init
curl -H "x-demo-session-id: <session_id>" http://localhost:8000/api/demo/status
```

---

## Phase 3: Backend — Limit Enforcement

### 3.1 Prompt Limit Check

**Location:** Every chat endpoint (`POST /api/demo/chat`, WebSocket receive)

```python
async def check_prompt_limit(session: Dict[str, Any]) -> None:
    """Raise 429 if prompt limit exceeded."""
    if session["prompt_count"] >= DEMO_MAX_PROMPTS_PER_SESSION:
        raise HTTPException(
            status_code=429,
            detail="DEMO_PROMPT_LIMIT_REACHED",
            headers={
                "X-Demo-Status": "prompt_limit",
                "X-Prompts-Remaining": "0",
            }
        )
```

### 3.2 Token Accumulation

**Location:** After every LLM call in demo endpoints

```python
async def accumulate_tokens(
    session_id: str,
    tokens_used: int,
    supabase_service: SupabaseService,
) -> None:
    """
    Add tokens to session accumulator.
    Check if 100K limit exceeded.
    """
    supabase = supabase_service.client
    
    # Get current total
    result = supabase.table("demo_sessions")\
        .select("total_tokens_used")\
        .eq("session_id", session_id)\
        .single()\
        .execute()
    
    current_total = result.data["total_tokens_used"] if result.data else 0
    new_total = current_total + tokens_used
    
    # Update
    supabase.table("demo_sessions")\
        .update({"total_tokens_used": new_total})\
        .eq("session_id", session_id)\
        .execute()
    
    if new_total >= DEMO_MAX_TOKENS_PER_SESSION:
        raise HTTPException(
            status_code=429,
            detail="DEMO_TOKEN_LIMIT_REACHED",
            headers={"X-Demo-Status": "token_limit"}
        )
```

**Token counting strategy:**

| Provider | Source | Fallback |
|----------|--------|----------|
| OpenAI | `response.usage.total_tokens` | — |
| Gemini | `usageMetadata.totalTokenCount` | — |
| Ollama/Other | — | `len(prompt + response) // 4` (rough heuristic) |

### 3.3 .docx Generation Limit

**Location:** `POST /api/demo/finalize`

```python
async def check_generation_limit(session: Dict[str, Any]) -> None:
    """Raise 403 if .docx already generated."""
    if session["has_generated_docx"]:
        raise HTTPException(
            status_code=403,
            detail="DEMO_GENERATION_ALREADY_USED",
            headers={"X-Demo-Status": "generation_used"}
        )
```

### 3.4 IP Rate Limit Enforcement

**Location:** `POST /api/demo/init` (session creation)

```python
from app.utils.demo_rate_limiter import DemoRateLimiter

@router.post("/init")
async def demo_init(
    request: Request,
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    ip_address = get_client_ip(request)
    
    limiter = DemoRateLimiter(supabase_service)
    check = await limiter.check_limits(ip_address)
    
    if not check["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=check["reason"],
            headers={"Retry-After": str(check["retry_after"])}
        )
    
    # Create session
    session = await get_or_create_demo_session(request, None, supabase_service)
    
    # Increment IP counters
    await limiter.increment_counter(ip_address)
    
    return { "session_id": session["session_id"], ... }
```

### Verification

```bash
# Test prompt limit
curl -H "x-demo-session-id: <sid>" -X POST http://localhost:8000/api/demo/chat -d '{"message":"test"}'
# Repeat 15 times, 16th should return 429

# Test generation limit
curl -H "x-demo-session-id: <sid>" -X POST http://localhost:8000/api/demo/finalize
# Second call should return 403
```

---

## Phase 4: Backend — .docx Generation for Demo

### 4.1 Reuse Strategy

The existing full platform has Word export logic (likely in `utils/exportToWord.ts` or backend equivalent). For the demo:

1. **Backend assembles content** from `demo_sessions.generated_sections` JSONB
2. **Calls existing DOCX generation utility** with the assembled data
3. **Stores file in Supabase Storage** (temporary bucket)
4. **Returns public URL** for preview + download

### 4.2 Implementation Outline

```python
@router.post("/finalize")
async def demo_finalize(
    request: Request,
    session: Dict[str, Any] = Depends(require_demo_session),
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    # 1. Check generation limit
    await check_generation_limit(session)
    
    # 2. Assemble sections from generated_sections JSONB
    sections = session.get("generated_sections", [])
    if not sections:
        raise HTTPException(status_code=400, detail="No sections generated yet")
    
    # 3. Generate .docx using existing utility
    # TODO: Adapt existing Word export to accept JSONB data instead of project_id
    docx_bytes = await generate_docx_from_sections(sections, template_id=session["template_id"])
    
    # 4. Upload to Supabase Storage (temporary bucket)
    file_path = f"demo-reports/{session['session_id']}/report.docx"
    supabase_service.client.storage.from_("demo-reports").upload(
        file_path, docx_bytes, {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    )
    
    # 5. Get public URL
    public_url = supabase_service.client.storage.from_("demo-reports").get_public_url(file_path)
    
    # 6. Mark as generated
    supabase_service.client.table("demo_sessions")\
        .update({"has_generated_docx": True, "status": "generated"})\
        .eq("session_id", session["session_id"])\
        .execute()
    
    return {
        "download_url": public_url,
        "preview_url": f"/api/demo/preview-docx?session_id={session['session_id']}",
        "message": "Report generated successfully. Sign up to continue editing!"
    }
```

### 4.3 Supabase Storage Bucket Setup

Run in Supabase SQL Editor or Dashboard:

```sql
-- Create bucket for demo reports (if not exists via dashboard)
-- Set bucket to public with 30-day object TTL
-- RLS policy: allow public read (since these are anonymous demo reports)
```

Or via Supabase Management API:

```bash
curl -X POST "https://<project>.supabase.co/storage/v1/bucket" \
  -H "Authorization: Bearer <service_key>" \
  -H "Content-Type: application/json" \
  -d '{"id":"demo-reports","name":"demo-reports","public":true}'
```

---

## Phase 5: Frontend — Demo Chat Page (No Landing Page)

> **Note:** There is NO landing page (`/demo.vue`). External lead pages link directly to `/demo/chat`.

### 5.1 Modify Auth Middleware

**File:** `frontend/middleware/auth.ts` (modify)

```typescript
/**
 * Auth Middleware — protects authenticated pages, allows demo routes
 */
import { authenticatedFetch, getAppSession } from "~/composables/useAppAuth";

export default defineNuxtRouteMiddleware(async (to, from) => {
  // Allow all demo routes without authentication
  if (to.path.startsWith("/demo")) return;
  
  if (to.path === "/login") return;
  if (process.server) return;

  try {
    const session = await getAppSession();
    if (!session.isAuthenticated) {
      return navigateTo("/login");
    }
    return;
  } catch (error) {
    console.error("Auth middleware error:", error);
    return navigateTo("/login");
  }
});
```

### 5.2 Create Demo Chat Workspace

**File:** `frontend/pages/demo/chat.vue` (create new)

```vue
<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- === STRIPPED HEADER: Logo + {Demo} Watermark Only === -->
    <header class="bg-white border-b border-slate-200 px-4 py-3">
      <div class="max-w-6xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-3">
          <!-- Logo -->
          <span
            class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#ffb067] via-[#ff7a66] to-[#ff4b5c] text-sm font-semibold text-white"
          >
            AI
          </span>
          <div>
            <p class="text-base font-semibold text-slate-900">補助引擎</p>
            <p class="text-xs text-slate-500">{{ templateName }}</p>
          </div>
          <!-- Demo Watermark -->
          <span
            class="ml-2 inline-flex items-center rounded-lg bg-amber-50 px-2 py-1 text-xs font-bold text-amber-600 border border-amber-200"
          >
            {Demo}
          </span>
        </div>
      </div>
    </header>
    
    <!-- === LIMIT BAR === -->
    <DemoLimitBar
      :prompts-used="promptsUsed"
      :prompts-total="maxPrompts"
      :tokens-used="tokensUsed"
      :tokens-total="maxTokens"
      :has-generated="hasGenerated"
    />
    
    <!-- === CHAT WORKSPACE === -->
    <div class="flex-1 overflow-hidden">
      <DemoChatbox
        :session-id="demoSessionId"
        :template-id="templateId"
        :messages="chatMessages"
        @send="handleSendMessage"
        @limit-reached="showUpsell"
        @generate-section="handleGenerateSection"
      />
    </div>
    
    <!-- === GENERATE REPORT CTA (when ready) === -->
    <div v-if="canGenerateReport" class="p-4 bg-white border-t">
      <button
        @click="generateReport"
        :disabled="isGenerating"
        class="w-full bg-gradient-to-r from-[#ff9b6d] to-[#ff4b6b] text-white font-bold py-3 rounded-2xl shadow-lg hover:shadow-xl transition disabled:opacity-50"
      >
        {{ isGenerating ? "生成中..." : "✨ 完成並生成 .docx 報告" }}
      </button>
    </div>
    
    <!-- === PERSISTENT SIGNUP CTA === -->
    <PersistentSignupCTA
      v-if="showPersistentCTA"
      :session-id="demoSessionId"
    />
    
    <!-- === UPSELL MODAL === -->
    <UpsellModal
      v-if="showUpsellModal"
      :preview-url="docxPreviewUrl"
      :download-url="docxDownloadUrl"
      :session-id="demoSessionId"
      @dismiss="showUpsellModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useDemoSession } from "~/composables/useDemoSession";
import { demoFetch } from "~/composables/useDemoFetch";
import { useRuntimeConfig } from "#app";

// State
const { demoSessionId, initSession } = useDemoSession();
const config = useRuntimeConfig();
const templateId = config.public.demoTemplateId;
const templateName = "SBIR Phase 1"; // Could be fetched from /api/config
const maxPrompts = config.public.demoMaxPrompts;
const maxTokens = 100000;

const chatMessages = ref([]);
const promptsUsed = ref(0);
const tokensUsed = ref(0);
const hasGenerated = ref(false);
const isGenerating = ref(false);
const showUpsellModal = ref(false);
const showPersistentCTA = ref(false);
const docxPreviewUrl = ref("");
const docxDownloadUrl = ref("");

// Computed
const canGenerateReport = computed(() => {
  return chatMessages.value.length >= 3 && !hasGenerated.value;
});

// Lifecycle
onMounted(async () => {
  if (!demoSessionId.value) {
    await initSession();
  }
  await loadSessionStatus();
  
  // Auto-start chat with welcome message
  if (chatMessages.value.length === 0) {
    chatMessages.value.push({
      id: "welcome",
      role: "assistant",
      content: "您好！我是您的 SBIR Phase 1 計畫書智能助手。請告訴我您的專案構想，我們一起完成這份計畫書。",
      type: "text",
    });
  }
});

// Methods
async function loadSessionStatus() {
  try {
    const response = await demoFetch("/status");
    const data = await response.json();
    promptsUsed.value = data.prompts_used;
    tokensUsed.value = data.tokens_used;
    hasGenerated.value = data.has_generated;
  } catch (error) {
    console.error("Failed to load session status:", error);
  }
}

async function handleSendMessage(message: string) {
  // Append user message
  chatMessages.value.push({
    id: `user-${Date.now()}`,
    role: "user",
    content: message,
    type: "text",
  });
  
  try {
    const response = await demoFetch("/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    
    if (response.status === 429) {
      showUpsellModal.value = true;
      return;
    }
    
    const data = await response.json();
    
    // Append AI response
    chatMessages.value.push({
      id: `ai-${Date.now()}`,
      role: "assistant",
      content: data.content,
      type: "text",
    });
    
    // Update counters
    promptsUsed.value = data.prompts_used || promptsUsed.value + 1;
    tokensUsed.value = data.tokens_used || tokensUsed.value;
    
    // Show persistent CTA after first prompt
    if (promptsUsed.value >= 1) {
      showPersistentCTA.value = true;
    }
  } catch (error) {
    console.error("Chat error:", error);
  }
}

async function handleGenerateSection(sectionId: string) {
  try {
    const response = await demoFetch("/generate-section", {
      method: "POST",
      body: JSON.stringify({ section_id: sectionId }),
    });
    const data = await response.json();
    // Update sections data
  } catch (error) {
    console.error("Generate section error:", error);
  }
}

async function generateReport() {
  isGenerating.value = true;
  try {
    const response = await demoFetch("/finalize", { method: "POST" });
    const data = await response.json();
    
    docxPreviewUrl.value = data.preview_url;
    docxDownloadUrl.value = data.download_url;
    hasGenerated.value = true;
    showUpsellModal.value = true;
  } catch (error) {
    console.error("Finalize error:", error);
  } finally {
    isGenerating.value = false;
  }
}

function showUpsell() {
  showUpsellModal.value = true;
}
</script>
```

### 5.3 Header Differences from Full Platform

| Element | Full Platform `projects/[id].vue` | Demo `demo/chat.vue` |
|---------|-----------------------------------|----------------------|
| **Breadcrumb** | "首頁 > Project Title" | ❌ **Removed** |
| **Project title `<h1>`** | User-defined | ❌ **Removed** — hardcoded in logo area |
| **Description** | User input | ❌ **Removed** |
| **Mode badge** | "互動模式" label | ❌ **Removed** |
| **Model toggle** | Internal/External switch | ❌ **Removed** |
| **"返回首頁" button** | Links to `/` | ❌ **Removed** |
| **Read-only banner** | Amber warning for locked projects | ❌ **Removed** |
| **Sidebar** | `ChatSidebar` with Q&A items | ❌ **Removed entirely** |
| **Modals** | 5 modals (including RecommendName) | ✅ **4 modals** (RecommendName removed) |
| **Project ID** | From route params | ❌ Not used — uses `demoSessionId` |
| **API calls** | `authenticatedFetch` | ✅ `demoFetch` with `x-demo-session-id` |

---

## Phase 6: Frontend — DemoChatbox Component

### 6.1 DemoChatbox.vue (New Component)

**Base:** Copy `components/chat/Chatbox.vue` → `components/demo/DemoChatbox.vue`

**Strategy:** Create a **new** component rather than modifying the existing `Chatbox.vue`. This is a hard fork — zero risk of breaking the full platform.

**Modifications from original:**
1. Replace `authenticatedFetch` with `demoFetch`
2. Remove `supabase` client direct calls (or adapt for demo)
3. Remove `RecommendNameModal` import and usage
4. Replace `projectId` prop with `sessionId`
5. Remove `isReadOnly` logic — demo has no read-only state
6. Change WebSocket from `/ws/chat_guidance?token=xxx` to `/ws/demo_chat?session_id=xxx`
7. Ensure all API calls go to `/api/demo/*` endpoints
8. Remove sidebar references entirely

**Props Interface:**

```typescript
const props = defineProps({
  sessionId: { type: String, required: true },       // Replaces projectId
  templateId: { type: String, default: "" },
  grantId: { type: String, default: "sbir" },
  grantName: { type: String, default: "SBIR Phase 1" },
  templateName: { type: String, default: "SBIR Phase 1" },
  sections: { type: Array, default: () => [] },
  isGenerating: { type: Boolean, default: false },
  // REMOVED: projectId, savedPlanVersions, selectedModel, isReadOnly, showSidebar
});
```

**Kept Modals (4 of 5):**
- ✅ `PlanCandidateSelector` — Shows AI-generated section candidates
- ✅ `PlanVersionModal` — Shows version history, timeline, export
- ✅ `FieldFileImportModal` — Upload file to auto-fill chat input
- ✅ `EditFieldModal` — Edit previously answered field
- ❌ `RecommendNameModal` — **Removed** (no project naming in demo)

### 6.2 Demo Limit Bar

**File:** `frontend/components/demo/DemoLimitBar.vue` (create new)

```vue
<template>
  <div class="bg-white border-b border-slate-200 px-4 py-3">
    <div class="max-w-4xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-6">
        <!-- Prompts -->
        <div class="flex items-center gap-2">
          <span class="text-sm font-semibold" :class="promptsTextColor">
            {{ promptsRemaining }}/{{ promptsTotal }}
          </span>
          <span class="text-xs text-slate-500">對話剩餘</span>
          <div class="w-24 h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              class="h-full rounded-full transition-all duration-500"
              :class="promptsBarColor"
              :style="{ width: `${(promptsRemaining / promptsTotal) * 100}%` }"
            />
          </div>
        </div>
        
        <!-- Tokens -->
        <div class="flex items-center gap-2">
          <span class="text-xs text-slate-500">
            {{ formatTokens(tokensUsed) }} / {{ formatTokens(tokensTotal) }}
          </span>
        </div>
        
        <!-- Generation Status -->
        <div class="flex items-center gap-2">
          <span
            class="text-xs font-semibold px-2 py-1 rounded-full"
            :class="hasGenerated ? 'bg-slate-100 text-slate-500' : 'bg-rose-100 text-rose-600'"
          >
            {{ hasGenerated ? "已產生報告" : "可產生報告" }}
          </span>
        </div>
      </div>
      
      <!-- Signup CTA -->
      <a
        :href="signupUrl"
        target="_blank"
        class="text-sm font-semibold text-rose-500 hover:text-rose-600 underline"
      >
        註冊繼續使用 →
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRuntimeConfig } from "#app";

const props = defineProps<{
  promptsUsed: number;
  promptsTotal: number;
  tokensUsed: number;
  tokensTotal: number;
  hasGenerated: boolean;
}>();

const config = useRuntimeConfig();

const promptsRemaining = computed(() => Math.max(0, props.promptsTotal - props.promptsUsed));

const promptsTextColor = computed(() => {
  if (promptsRemaining.value <= 3) return "text-red-500";
  if (promptsRemaining.value <= 8) return "text-amber-500";
  return "text-slate-700";
});

const promptsBarColor = computed(() => {
  if (promptsRemaining.value <= 3) return "bg-red-500";
  if (promptsRemaining.value <= 8) return "bg-amber-500";
  return "bg-green-500";
});

const signupUrl = computed(() => {
  const base = config.public.fullPlatformUrl;
  // TODO: Append demo session ID for migration
  return `${base}/signup`;
});

function formatTokens(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return `${n}`;
}
</script>
```

### 6.2 Upsell Modal

**File:** `frontend/components/demo/UpsellModal.vue` (create new)

```vue
<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="$emit('dismiss')" />
      
      <!-- Modal -->
      <div class="relative bg-white rounded-3xl shadow-2xl max-w-2xl w-full overflow-hidden">
        <!-- Header -->
        <div class="bg-gradient-to-r from-rose-500 to-rose-600 p-6 text-white text-center">
          <h2 class="text-2xl font-bold mb-2">🎉 您的 SBIR Phase 1 草稿已完成！</h2>
          <p class="text-rose-100">
            對我們的 AI 系統印象深刻嗎？
          </p>
        </div>
        
        <!-- Content -->
        <div class="p-6 space-y-6">
          <!-- Preview Area -->
          <div class="border border-slate-200 rounded-xl overflow-hidden">
            <div class="bg-slate-50 px-4 py-2 border-b border-slate-200 flex items-center gap-2">
              <span class="text-xs font-semibold text-slate-500">報告預覽</span>
            </div>
            <div class="p-4">
              <iframe
                v-if="previewUrl"
                :src="previewUrl"
                class="w-full h-64 border-0"
              />
              <p v-else class="text-sm text-slate-400 text-center py-8">
                預覽載入中...
              </p>
            </div>
          </div>
          
          <!-- Benefits -->
          <div class="grid grid-cols-2 gap-3 text-sm">
            <div class="flex items-center gap-2 text-slate-700">
              <span class="text-green-500">✓</span>
              無限制 AI 對話
            </div>
            <div class="flex items-center gap-2 text-slate-700">
              <span class="text-green-500">✓</span>
              多種補助計畫模板
            </div>
            <div class="flex items-center gap-2 text-slate-700">
              <span class="text-green-500">✓</span>
              無限制報告生成
            </div>
            <div class="flex items-center gap-2 text-slate-700">
              <span class="text-green-500">✓</span>
              匯出 Word / PDF
            </div>
          </div>
          
          <!-- CTA Buttons -->
          <div class="space-y-3">
            <a
              :href="signupUrl"
              target="_blank"
              class="block w-full bg-rose-500 hover:bg-rose-600 text-white font-bold py-4 rounded-2xl text-center transition shadow-lg shadow-rose-200"
            >
              🔥 免費註冊，繼續編輯您的計畫書
            </a>
            
            <button
              @click="$emit('dismiss')"
              class="block w-full text-slate-500 hover:text-slate-700 font-medium py-2 text-center transition"
            >
              稍後再說
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRuntimeConfig } from "#app";

const props = defineProps<{
  previewUrl: string;
  downloadUrl: string;
  sessionId: string;
}>();

defineEmits(["dismiss"]);

const config = useRuntimeConfig();

const signupUrl = computed(() => {
  const base = config.public.fullPlatformUrl;
  return `${base}/signup?demo_sid=${props.sessionId}&redirect_to=/projects/new`;
});
</script>
```

### 6.3 Persistent Signup CTA

**File:** `frontend/components/demo/PersistentSignupCTA.vue` (create new)

```vue
<template>
  <div class="fixed bottom-6 right-6 z-40">
    <a
      :href="signupUrl"
      target="_blank"
      class="group flex items-center gap-2 bg-rose-500 hover:bg-rose-600 text-white font-bold px-6 py-3 rounded-full shadow-lg shadow-rose-200 hover:shadow-rose-300 transition transform hover:-translate-y-1"
    >
      <span class="text-lg">🔥</span>
      <span class="text-sm">免費註冊，繼續使用</span>
      <span class="text-lg group-hover:translate-x-1 transition">→</span>
    </a>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRuntimeConfig } from "#app";

const props = defineProps<{
  sessionId: string;
}>();

const config = useRuntimeConfig();

const signupUrl = computed(() => {
  const base = config.public.fullPlatformUrl;
  return `${base}/signup?demo_sid=${props.sessionId}&redirect_to=/projects/new`;
});
</script>
```

---

## Phase 7: Frontend — Session Management

### 7.1 Demo Session Composable

**File:** `frontend/composables/useDemoSession.ts` (create new)

```typescript
"""
Composable for managing demo session ID in browser storage.
Session ID is stored in both localStorage (primary) and cookie (fallback).
"""
import { ref, onMounted } from "vue";

const DEMO_SESSION_KEY = "demo_session_id";
const DEMO_COOKIE_NAME = "demo_sid";

export function useDemoSession() {
  const demoSessionId = ref<string>("");
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  onMounted(() => {
    // Try to restore from localStorage
    const stored = localStorage.getItem(DEMO_SESSION_KEY);
    if (stored) {
      demoSessionId.value = stored;
      return;
    }
    
    // Fallback: try cookie
    const cookieMatch = document.cookie.match(
      new RegExp(`${DEMO_COOKIE_NAME}=([^;]+)`)
    );
    if (cookieMatch) {
      demoSessionId.value = cookieMatch[1];
      localStorage.setItem(DEMO_SESSION_KEY, demoSessionId.value);
    }
  });

  async function initSession(): Promise<void> {
    if (demoSessionId.value) return;
    
    isLoading.value = true;
    error.value = null;
    
    try {
      const config = useRuntimeConfig();
      const response = await fetch(
        `${config.public.apiBaseUrl}/demo/init`,
        { method: "POST" }
      );
      
      if (!response.ok) {
        throw new Error(`Failed to init session: ${response.status}`);
      }
      
      const data = await response.json();
      demoSessionId.value = data.session_id;
      
      // Store in both localStorage and cookie
      localStorage.setItem(DEMO_SESSION_KEY, data.session_id);
      document.cookie = `${DEMO_COOKIE_NAME}=${data.session_id}; path=/; max-age=2592000`; // 30 days
    } catch (err: any) {
      error.value = err.message || "Failed to initialize demo session";
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  function clearSession(): void {
    demoSessionId.value = "";
    localStorage.removeItem(DEMO_SESSION_KEY);
    document.cookie = `${DEMO_COOKIE_NAME}=; path=/; max-age=0`;
  }

  return {
    demoSessionId,
    isLoading,
    error,
    initSession,
    clearSession,
  };
}
```

### 7.2 Demo Fetch Utility

**File:** `frontend/composables/useDemoFetch.ts` (create new)

```typescript
"""
Fetch wrapper for demo API calls.
Automatically injects x-demo-session-id header.
"""
import { useDemoSession } from "./useDemoSession";

export async function demoFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const { demoSessionId } = useDemoSession();
  const config = useRuntimeConfig();
  
  if (!demoSessionId.value) {
    throw new Error("Demo session not initialized");
  }
  
  const url = `${config.public.apiBaseUrl}/demo${endpoint}`;
  
  const headers = {
    "Content-Type": "application/json",
    "x-demo-session-id": demoSessionId.value,
    ...(options.headers || {}),
  };
  
  return fetch(url, {
    ...options,
    headers,
  });
}
```

---

## Phase 8: Frontend — Upsell & CTA

### 8.1 Signup URL Construction

The signup URL must include the demo session ID so the full platform can migrate data:

```typescript
function buildSignupUrl(sessionId: string, fullPlatformUrl: string): string {
  const params = new URLSearchParams({
    demo_sid: sessionId,
    redirect_to: "/projects/new",  // After signup, redirect to project list
  });
  return `${fullPlatformUrl}/signup?${params.toString()}`;
}
```

### 8.2 Upsell Trigger Conditions

| Condition | Action |
|-----------|--------|
| Prompt count reaches 15 | Show upsell modal immediately after last AI response |
| User clicks "Generate Report" | Generate .docx, then show upsell modal with preview |
| User manually clicks "Continue for FREE" CTA | Open signup in new tab |
| User dismisses upsell modal | Persistent CTA remains visible; demo still usable if prompts remain |

### 8.3 Tracking (Optional)

Add query parameters to track demo-to-signup conversion:

```
aiproposal.tgsa.com.tw/signup?demo_sid=xxx&utm_source=demo&utm_medium=upsell_modal&utm_campaign=sbir_p1_demo
```

---

## Phase 9: Migration Flow

### 9.1 Full Platform Signup Handler

**Location:** Full platform codebase (separate repo) — `frontend/pages/signup.vue` or equivalent

```typescript
// On signup page load, check for demo_sid in URL
const route = useRoute();
const demoSid = route.query.demo_sid as string | undefined;

// Store demo_sid in localStorage temporarily
if (demoSid) {
  localStorage.setItem("pending_demo_migration", demoSid);
}

// After successful signup (OAuth callback or form submission):
async function onSignupComplete(userId: string) {
  const pendingDemoSid = localStorage.getItem("pending_demo_migration");
  
  if (pendingDemoSid) {
    try {
      // Call demo backend migration endpoint
      const response = await fetch(
        `${DEMO_BACKEND_URL}/api/demo/migrate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${INTERNAL_SERVICE_KEY}`,
          },
          body: JSON.stringify({
            demo_session_id: pendingDemoSid,
            new_user_id: userId,
          }),
        }
      );
      
      if (response.ok) {
        const { project_id } = await response.json();
        localStorage.removeItem("pending_demo_migration");
        // Redirect to migrated project
        navigateTo(`/projects/${project_id}`);
        return;
      }
    } catch (error) {
      console.error("Migration failed:", error);
    }
  }
  
  // Fallback: redirect to dashboard
  navigateTo("/projects");
}
```

### 9.2 Demo Backend Migration Endpoint

**File:** `backend/app/api/demo.py` — complete the `/migrate` endpoint:

```python
@router.post("/migrate")
async def demo_migrate(
    request: Request,
    payload: Dict[str, str],
    supabase_service: SupabaseService = Depends(get_supabase_service),
):
    """
    Migrate demo session to full platform user.
    Protected by internal service API key (not user auth).
    """
    # 1. Verify internal service key
    internal_key = request.headers.get("X-Internal-Service-Key")
    expected_key = os.getenv("DEMO_MIGRATION_SERVICE_KEY")
    
    if not internal_key or internal_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid service key")
    
    demo_session_id = payload.get("demo_session_id")
    new_user_id = payload.get("new_user_id")
    
    if not demo_session_id or not new_user_id:
        raise HTTPException(status_code=400, detail="Missing demo_session_id or new_user_id")
    
    # 2. Call PostgreSQL migration function
    supabase = supabase_service.client
    
    result = supabase.rpc(
        "migrate_demo_to_project",
        {
            "p_demo_session_id": demo_session_id,
            "p_new_user_id": new_user_id,
        }
    ).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Migration failed")
    
    return {
        "project_id": result.data,
        "message": "Demo session migrated successfully"
    }
```

### 9.3 Environment Variable for Migration Key

**File:** `backend/.env` (add)

```env
DEMO_MIGRATION_SERVICE_KEY=your-random-secret-key-here-change-in-production
```

**File:** `frontend/.env` on full platform (add)

```env
NUXT_PUBLIC_DEMO_BACKEND_URL=https://demo-aiproposal.tgsa.com.tw
DEMO_MIGRATION_SERVICE_KEY=your-random-secret-key-here-change-in-production
```

---

## Phase 10: Testing & Verification

### 10.1 Unit Tests

**Backend tests to write:**

| Test | File | Description |
|------|------|-------------|
| IP rate limit | `tests/test_demo_rate_limiter.py` | 3/hr, 5/day enforcement |
| Session creation | `tests/test_demo_init.py` | New session returns UUID, stored in DB |
| Prompt limit | `tests/test_demo_chat.py` | 16th prompt returns 429 |
| Token limit | `tests/test_demo_chat.py` | Accumulation stops at 100K |
| Generation limit | `tests/test_demo_finalize.py` | 2nd finalize returns 403 |
| Migration | `tests/test_demo_migrate.py` | SQL function creates project + logs |
| Session expiry | `tests/test_demo_session.py` | Expired session returns 401 |

**Frontend tests to write:**

| Test | File | Description |
|------|------|-------------|
| Session persistence | `tests/composables/useDemoSession.spec.ts` | localStorage + cookie roundtrip |
| Limit bar rendering | `tests/components/DemoLimitBar.spec.ts` | Shows correct colors at thresholds |
| Upsell modal | `tests/components/UpsellModal.spec.ts` | Opens at limit, has correct signup URL |
| CTA visibility | `tests/components/PersistentSignupCTA.spec.ts` | Appears after first prompt |

### 10.2 Integration Tests

```bash
# 1. Start full stack
docker compose -f docker-compose.beta.yml up -d

# 2. Run backend tests
pytest tests/test_demo_*.py -v

# 3. Run frontend tests (if using Vitest)
cd frontend && npx vitest run

# 4. Manual E2E test script
# Open browser directly to http://localhost:3000/demo/chat
# Should auto-create session and show welcome message
# Send 15 messages → 16th should show upsell modal
# Click "Generate Report" → should produce .docx
# Click "註冊繼續使用" CTA → should open full platform in new tab
# Sign up on full platform → should find migrated project
```

### 10.3 Verification Checklist

| # | Test | Expected Result |
|---|------|-----------------|
| 1 | Open `/demo/chat` directly (no login) | Auto-creates session, loads chat with welcome message |
| 2 | Inspect header | Shows logo + "補助引擎" + template name + `{Demo}` badge only |
| 3 | Inspect sidebar | **No sidebar visible** |
| 4 | Send chat message | AI responds, prompt count increases |
| 5 | Refresh page | Session persists, chat history restored |
| 6 | Send 16th message | Upsell modal appears, no AI response |
| 7 | Click "Generate Report" | .docx generates, preview shows, upsell appears |
| 8 | Click generate again | Button disabled or error message |
| 9 | Click "註冊繼續使用" CTA | Opens `aiproposal.tgsa.com.tw/signup?demo_sid=xxx` in new tab |
| 10 | Open incognito | New session starts (fresh 15 prompts) |
| 11 | Open 4th session from same IP | 429 Too Many Requests |
| 12 | Sign up on full platform | Migrated project appears with demo chat history |
| 13 | Try `/api/projects` | **404 Not Found** (router removed) |
| 14 | Try `/api/auth/me` | **404 Not Found** (router removed) |
| 15 | Try `/api/datasets` | **404 Not Found** (router removed) |
| 16 | Wait 30 days, revisit old session | New session created, old data gone |
| 17 | Clear browser storage, revisit | New session created |

---

## Phase 11: Documentation & Deployment

### 11.1 README Rewrite

**File:** `README.md` (rewrite for demo context)

Structure:
1. Project overview (demo purpose, not full platform)
2. Quick start (docker compose up)
3. Environment variables table (demo-specific)
4. API endpoints (demo-only)
5. Limitations & hard limits table
6. Migration flow diagram
7. Deployment instructions (subdomain, nginx)
8. Anti-abuse configuration
9. Link to full platform repo

### 11.2 API Documentation Update

**File:** `API文件.md` (append demo endpoints)

Add section:
- Demo API Group (`/api/demo/*`)
- Request/response schemas for each endpoint
- Error codes (`DEMO_PROMPT_LIMIT_REACHED`, `DEMO_TOKEN_LIMIT`, etc.)
- WebSocket spec for `/ws/demo_chat`

### 11.3 Deployment Checklist

| Step | Command / Action | Verify |
|------|-----------------|--------|
| 1. Set environment variables | Edit `.env` files | `DEMO_MODE=true` |
| 2. Run DB migration | Execute `001_demo_tables.sql` in Supabase | Tables visible in Studio |
| 3. Create Storage bucket | Supabase Dashboard → Storage → New bucket | `demo-reports` bucket exists, public |
| 4. Build Docker images | `docker compose build` | No errors |
| 5. Deploy to Dev VPS | GitHub Actions push to `dev` branch | Actions green |
| 6. Configure DNS | Add `demo-aiproposal.tgsa.com.tw` A record | `dig demo-aiproposal.tgsa.com.tw` resolves |
| 7. Configure nginx | Add server block for demo subdomain | `curl -I demo-aiproposal.tgsa.com.tw` returns 200 |
| 8. Configure SSL | Certbot / Let's Encrypt | HTTPS works, no certificate warnings |
| 9. Configure CORS | Add demo domain to `main.py` | Preflight requests succeed |
| 10. Test end-to-end | Manual browser test | All 13 verification checks pass |
| 11. Monitor logs | `docker compose logs -f fastapi-backend` | No errors, limits enforced |
| 12. Set up alerts | Configure 429 rate in monitoring | Alert if > 100 429s/hour (possible abuse) |

### 11.4 GitHub Actions CI/CD

**File:** `.github/workflows/deploy-demo.yml` (create new, or modify existing)

Key steps:
1. Inject build-time secrets (`NUXT_PUBLIC_*`)
2. Build frontend (`npm run build`)
3. Build backend Docker image
4. Push to Docker Hub (`tgsataiwan/ai-proposal-demo:dev`)
5. SSH to Dev VPS, pull, restart

---

## Appendix A: File Inventory

### New Files to Create

| # | Path | Phase | Purpose |
|---|------|-------|---------|
| 1 | `backend/app/utils/ip_extractor.py` | 2 | Extract real client IP |
| 2 | `backend/app/utils/demo_rate_limiter.py` | 2 | IP-based rate limiting |
| 3 | `backend/app/core/demo_dependencies.py` | 2 | Demo session FastAPI dependencies |
| 4 | `backend/app/api/demo.py` | 2 | Demo API router (7 REST endpoints + `/ws/demo_chat` WebSocket) |
| 5 | `frontend/pages/demo/chat.vue` | 5 | **Only demo page** — no landing page, auto-init session |
| 6 | `frontend/components/demo/DemoChatbox.vue` | 6 | **New component** — copies Chatbox.vue logic, demo-safe (no auth deps) |
| 7 | `frontend/components/demo/DemoLimitBar.vue` | 6 | Usage indicator bar (prompts, tokens, generation status) |
| 8 | `frontend/components/demo/UpsellModal.vue` | 6 | Limit reached + .docx preview + signup CTA modal |
| 9 | `frontend/components/demo/PersistentSignupCTA.vue` | 6 | Floating "Continue for FREE" button |
| 10 | `frontend/composables/useDemoSession.ts` | 7 | Session cookie + localStorage management |
| 11 | `frontend/composables/useDemoFetch.ts` | 7 | Fetch wrapper with `x-demo-session-id` header |
| 12 | `database-migrations/001_demo_tables.sql` | 1 | Database schema (`demo_sessions`, `demo_ip_limits`, migration function) |
| 13 | `README.md` | 11 | Rewritten for demo context |
| 14 | `.github/workflows/deploy-demo.yml` | 11 | CI/CD for demo deployment |

### Files to Modify

| # | Path | Phase | Change |
|---|------|-------|--------|
| 1 | `backend/app/config.py` | 0 | Add `DEMO_*` constants + `DEMO_MIGRATION_SERVICE_KEY` |
| 2 | `backend/app/main.py` | 0, 2 | **CRITICAL**: Remove 5 routers, register only `demo` + `config` |
| 3 | `frontend/nuxt.config.ts` | 0 | Add demo public runtime config, `/demo/**` route rule |
| 4 | `frontend/middleware/auth.ts` | 5 | Bypass `/demo/*` routes |
| 5 | `.github/workflows/deploy-dev.yml` | 0 | Inject new build-time secrets (`NUXT_PUBLIC_*`) |

### Backend Routers REMOVED from `main.py` (Dead Code Elimination)

| Router | File | Why Removed |
|--------|------|-------------|
| `auth` | `backend/app/api/auth.py` | Demo is anonymous — no login status checks |
| `external_auth` | `backend/app/api/external_auth.py` | No OAuth in demo |
| `projects` | `backend/app/api/projects.py` | Demo uses `demo_sessions` table, not `projects` table |
| `datasets` | `backend/app/api/datasets.py` | No dataset governance in demo |
| `generate` | `backend/app/api/generate.py` | Original endpoints write to `projects`/`execution_logs`. Demo uses `/api/demo/*` |

> **Note:** The `.py` files can stay in repo for reference, but must be **removed from `main.py`** so endpoints are not exposed.

---

## Appendix B: Error Codes Reference

| Code | HTTP Status | Trigger | Frontend Action |
|------|-------------|---------|-----------------|
| `DEMO_PROMPT_LIMIT_REACHED` | 429 | 16th chat message | Show upsell modal |
| `DEMO_TOKEN_LIMIT_REACHED` | 429 | Token accumulator ≥ 100K | Show upsell modal |
| `DEMO_GENERATION_ALREADY_USED` | 403 | 2nd finalize call | Disable generate button |
| `DEMO_HOURLY_LIMIT_EXCEEDED` | 429 | 4th session from same IP in 1hr | Show "try later" message |
| `DEMO_DAILY_LIMIT_EXCEEDED` | 429 | 6th session from same IP in 1 day | Show "try tomorrow" message |
| `DEMO_SESSION_EXPIRED` | 401 | Session past 30 days | Auto-create new session |
| `DEMO_SESSION_INVALID` | 401 | Session ID not found | Auto-create new session |

---

## Appendix C: Security Checklist

- [ ] `DEMO_MIGRATION_SERVICE_KEY` is strong random string (≥ 32 chars)
- [ ] `DEMO_MIGRATION_SERVICE_KEY` is not committed to git (in `.env` only)
- [ ] IP extraction uses `X-Forwarded-For` correctly (first IP, not last)
- [ ] nginx strips spoofed `X-Forwarded-For` from external requests
- [ ] `demo_ip_limits` table has appropriate RLS policies (or is service-role only)
- [ ] `demo_sessions` table does not expose sensitive data via RLS
- [ ] Supabase Storage `demo-reports` bucket has 30-day TTL or cleanup
- [ ] `.docx` files in storage are not guessable (UUID path)
- [ ] Rate limits are enforced in backend (not frontend-only)
- [ ] Token counts are accumulated server-side (not client-reported)
- [ ] CAPTCHA integration is planned for next phase

---

> **End of Implementation Plan**
> 
> Begin with **Phase 0** (environment setup), then proceed sequentially.
> Parallel work: Database migration (Phase 1) can be done by colleague while you implement backend router (Phase 2).
