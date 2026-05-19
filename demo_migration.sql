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

    -- Demo-only: track the 10-interaction limit before prompting registration.
    interaction_count    INTEGER      NOT NULL DEFAULT 0,

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
