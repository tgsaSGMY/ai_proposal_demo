-- Apply against the existing Supabase project on the Dev VPS,
-- in the ai_proposal_platform schema. Idempotent.

CREATE TABLE IF NOT EXISTS ai_proposal_platform.demo (
    session_id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    expires_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW() + INTERVAL '30 days',

    -- What template this session is filling out
    -- (matches the existing projects.grant_id / template_id shape)
    grant_id             TEXT,
    template_id          TEXT,

    -- Hardcoded for the demo — the visitor never sees a "name your project"
    -- step, so we ship a placeholder title and lock the workspace into
    -- interactive (chat) mode. Both are editable on the parent platform
    -- after the visitor registers and the row is claimed.
    title                TEXT         NOT NULL DEFAULT 'AI 計畫書草稿',
    mode                 TEXT         NOT NULL DEFAULT 'interactive',

    -- Same JSONB shape as projects.conversation_history / stored_answer / saved_plan
    -- so the existing chat/generate logic ports over without restructuring.
    conversation_history JSONB        NOT NULL DEFAULT '[]'::jsonb,
    stored_answer        JSONB        NOT NULL DEFAULT '{}'::jsonb,
    saved_plan           JSONB,

    -- Demo-only counters and flags that gate the registration prompt.
    --   interaction_count  — chat turns vs DEMO_INTERACTION_LIMIT
    --   total_tokens_used  — running sum across LLM calls, vs the token cap
    --   has_generated_docx — set once a finalize/.docx flow runs (one-shot)
    interaction_count    INTEGER      NOT NULL DEFAULT 0,
    total_tokens_used    INTEGER      NOT NULL DEFAULT 0,
    has_generated_docx   BOOLEAN      NOT NULL DEFAULT FALSE,

    -- Lifecycle state machine. Independent of claimed_by so the demo backend
    -- can mark a row 'generated' (docx produced, no more finalize allowed)
    -- before — or without — the parent platform ever claims it.
    --   'active'    — visitor still mid-flow
    --   'generated' — .docx has been produced
    --   'claimed'   — parent set claimed_by/claimed_at on register handoff
    status               TEXT         NOT NULL DEFAULT 'active'
                                      CHECK (status IN ('active', 'generated', 'claimed')),

    -- Buffered audit data. The demo backend appends one entry per LLM call
    -- and per substantive event into these arrays; on claim, the parent
    -- platform drains them into ai_proposal_platform.usage_logs and
    -- ai_proposal_platform.execution_logs with the new user_id / project_id.
    -- Shape per entry: see SupabaseService.append_demo_usage_log /
    -- append_demo_execution_event in backend/app/services/supabase_service.py.
    pending_usage_logs       JSONB    NOT NULL DEFAULT '[]'::jsonb,
    pending_execution_events JSONB    NOT NULL DEFAULT '[]'::jsonb,

    -- Claim handoff: the parent platform's register endpoint sets these when
    -- migrating a demo session into a registered user account.
    -- FK is nullable; rows live unclaimed until (and unless) the visitor registers.
    claimed_by           UUID         REFERENCES ai_proposal_platform.users(id) ON DELETE SET NULL,
    claimed_at           TIMESTAMPTZ
);

-- Idempotent ALTER for re-runs: if the table already exists from a prior
-- apply of this migration, make sure the newer columns are present.
ALTER TABLE ai_proposal_platform.demo
    ADD COLUMN IF NOT EXISTS title TEXT NOT NULL DEFAULT 'AI 計畫書草稿';
ALTER TABLE ai_proposal_platform.demo
    ADD COLUMN IF NOT EXISTS mode  TEXT NOT NULL DEFAULT 'interactive';
ALTER TABLE ai_proposal_platform.demo
    ADD COLUMN IF NOT EXISTS pending_usage_logs JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE ai_proposal_platform.demo
    ADD COLUMN IF NOT EXISTS pending_execution_events JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE ai_proposal_platform.demo
    ADD COLUMN IF NOT EXISTS total_tokens_used INTEGER NOT NULL DEFAULT 0;
ALTER TABLE ai_proposal_platform.demo
    ADD COLUMN IF NOT EXISTS has_generated_docx BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE ai_proposal_platform.demo
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';

-- Re-create the status CHECK on every run so the allowed set stays in sync
-- with the CREATE TABLE definition when this migration is amended.
ALTER TABLE ai_proposal_platform.demo
    DROP CONSTRAINT IF EXISTS demo_status_check;
ALTER TABLE ai_proposal_platform.demo
    ADD CONSTRAINT demo_status_check
    CHECK (status IN ('active', 'generated', 'claimed'));

-- Row Level Security: lock the table down so only the backend (which uses
-- the service_role key) can touch demo rows. The frontend's anon key is
-- exposed in the JS bundle, and without RLS anyone with that key could
-- read every visitor's conversation_history / stored_answer via PostgREST.
-- RLS with no policies blocks anon/authenticated entirely; service_role
-- bypasses RLS by design, so the backend continues working unchanged.
ALTER TABLE ai_proposal_platform.demo ENABLE ROW LEVEL SECURITY;

-- Partial index for the cleanup cron (only scans unclaimed rows past expiry).
CREATE INDEX IF NOT EXISTS demo_expires_at_idx
    ON ai_proposal_platform.demo (expires_at)
    WHERE claimed_by IS NULL;

-- Partial index for the parent platform's "find a user's claimed demo session" lookup.
CREATE INDEX IF NOT EXISTS demo_claimed_by_idx
    ON ai_proposal_platform.demo (claimed_by)
    WHERE claimed_by IS NOT NULL;

-- Keep updated_at fresh on row mutation.
CREATE OR REPLACE FUNCTION ai_proposal_platform.demo_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS demo_touch_updated_at_trg ON ai_proposal_platform.demo;
CREATE TRIGGER demo_touch_updated_at_trg
    BEFORE UPDATE ON ai_proposal_platform.demo
    FOR EACH ROW
    EXECUTE FUNCTION ai_proposal_platform.demo_touch_updated_at();

-- ---------------------------------------------------------------------------
-- Auto-cleanup of expired demo rows.
--
-- Supabase ships with the pg_cron extension; enable it once per project,
-- then schedule a daily DELETE of unclaimed rows past their expires_at.
-- Claimed rows (claimed_by IS NOT NULL) are preserved as an audit trail —
-- delete those manually if/when you want to.
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Drop the prior schedule (if any) so re-running this migration is idempotent.
DO $$
DECLARE
    existing_jobid BIGINT;
BEGIN
    SELECT jobid INTO existing_jobid
    FROM cron.job
    WHERE jobname = 'demo_cleanup_expired';
    IF existing_jobid IS NOT NULL THEN
        PERFORM cron.unschedule(existing_jobid);
    END IF;
END$$;

-- Run daily at 03:15 UTC.
SELECT cron.schedule(
    'demo_cleanup_expired',
    '15 3 * * *',
    $$DELETE FROM ai_proposal_platform.demo
       WHERE claimed_by IS NULL AND expires_at < NOW()$$
);

-- Fallback if pg_cron is unavailable on this Supabase project: run this
-- statement from any external cron / scheduled task once a day instead.
--   DELETE FROM ai_proposal_platform.demo
--    WHERE claimed_by IS NULL AND expires_at < NOW();

-- ---------------------------------------------------------------------------
-- demo_ip_limits — IP-based rate-limit counters for /api/demo/init.
--
-- One row per (ip_address, window_start, window_type) with a running
-- session_count. The backend's rate limiter reads this on session creation
-- and rejects with 429 if the per-hour or per-day cap is breached. Hour and
-- day windows are stored side by side so a single IP has at most two live
-- rows at any moment.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_proposal_platform.demo_ip_limits (
    ip_address    INET         NOT NULL,
    window_start  TIMESTAMPTZ  NOT NULL,
    window_type   TEXT         NOT NULL,
    session_count INTEGER      NOT NULL DEFAULT 0,
    PRIMARY KEY (ip_address, window_start, window_type),
    CONSTRAINT demo_ip_limits_window_type_check
        CHECK (window_type IN ('hour', 'day'))
);

-- Service-role only — same threat model as the demo table itself.
ALTER TABLE ai_proposal_platform.demo_ip_limits ENABLE ROW LEVEL SECURITY;

-- Powers the cleanup cron below; the read path already hits the PK.
CREATE INDEX IF NOT EXISTS demo_ip_limits_window_start_idx
    ON ai_proposal_platform.demo_ip_limits (window_start);

-- ---------------------------------------------------------------------------
-- Auto-cleanup of stale rate-limit windows.
--
-- Windows older than 48h are out of scope for hourly and daily enforcement
-- and would otherwise accumulate without bound as new IPs hit the endpoint.
-- ---------------------------------------------------------------------------

DO $$
DECLARE
    existing_jobid BIGINT;
BEGIN
    SELECT jobid INTO existing_jobid
    FROM cron.job
    WHERE jobname = 'demo_ip_limits_cleanup';
    IF existing_jobid IS NOT NULL THEN
        PERFORM cron.unschedule(existing_jobid);
    END IF;
END$$;

-- Run daily at 03:20 UTC (5 min after demo_cleanup_expired).
SELECT cron.schedule(
    'demo_ip_limits_cleanup',
    '20 3 * * *',
    $$DELETE FROM ai_proposal_platform.demo_ip_limits
       WHERE window_start < NOW() - INTERVAL '2 days'$$
);

-- Fallback if pg_cron is unavailable:
--   DELETE FROM ai_proposal_platform.demo_ip_limits
--    WHERE window_start < NOW() - INTERVAL '2 days';
