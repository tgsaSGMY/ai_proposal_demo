-- Phase 9: Demo Session Migration
-- Adds claim-tracking columns + a partial index to ai_proposal_platform.demo.
-- Run once against the shared Supabase database.

BEGIN;

ALTER TABLE ai_proposal_platform.demo
  ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active'
    CHECK (status IN ('active', 'claimed', 'expired'));

ALTER TABLE ai_proposal_platform.demo
  ADD COLUMN IF NOT EXISTS claimed_by_user_id UUID
    REFERENCES ai_proposal_platform.users(id);

ALTER TABLE ai_proposal_platform.demo
  ADD COLUMN IF NOT EXISTS claimed_project_id UUID
    REFERENCES ai_proposal_platform.projects(id);

ALTER TABLE ai_proposal_platform.demo
  ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_demo_active
  ON ai_proposal_platform.demo(session_id)
  WHERE status = 'active';

COMMIT;
