# 14 — Migration Guide

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Database Migrations](#database-migrations)
2. [Code Migrations](#code-migrations)
3. [Environment Migrations](#environment-migrations)
4. [Rollback Procedures](#rollback-procedures)
5. [Version Upgrade Guide](#version-upgrade-guide)

---

## Database Migrations

### Migration Files

All migrations are in `database-migrations/` and are **idempotent** (safe to run multiple times).

```
database-migrations/
├── 001_demo_claim_columns.sql
├── 002_demo_download_count.sql
└── 003_demo_schema_update.sql
```

### 001 — Claim Columns

**File:** `database-migrations/001_demo_claim_columns.sql`

**Purpose:** Add claim tracking columns to the `demo` table.

**Changes:**
- `status` — `TEXT` with `CHECK (status IN ('active', 'claimed', 'expired'))`
- `claimed_by_user_id` — `UUID` FK to `users`
- `claimed_project_id` — `UUID` FK to `projects`
- `claimed_at` — `TIMESTAMPTZ`
- `idx_demo_active` — Partial index on `session_id WHERE status = 'active'`

**Run:**
```bash
psql "$DATABASE_URL" -f database-migrations/001_demo_claim_columns.sql
```

**Verify:**
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'demo' AND table_schema = 'ai_proposal_platform'
ORDER BY ordinal_position;
```

---

### 002 — Download Count

**File:** `database-migrations/002_demo_download_count.sql`

**Purpose:** Add download tracking columns.

**Changes:**
- `has_generated_docx` — `BOOLEAN NOT NULL DEFAULT FALSE`
- `download_count` — `INT NOT NULL DEFAULT 0`

**Run:**
```bash
psql "$DATABASE_URL" -f database-migrations/002_demo_download_count.sql
```

**Verify:**
```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'demo' 
  AND column_name IN ('has_generated_docx', 'download_count');
```

---

### 003 — Schema Update & Migration Function

**File:** `database-migrations/003_demo_schema_update.sql`

**Purpose:** Add `section_versions` and complete `migrate_demo_to_project()` function.

**Changes:**
- `section_versions` — `JSONB` (nullable)
- `idx_demo_section_versions_null` — Partial index for optimization
- `migrate_demo_to_project()` — Complete migration function

**Run:**
```bash
psql "$DATABASE_URL" -f database-migrations/003_demo_schema_update.sql
```

**Verify:**
```sql
-- Check column
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'demo' AND column_name = 'section_versions';

-- Check function
SELECT proname, prosrc 
FROM pg_proc 
WHERE proname = 'migrate_demo_to_project';

-- Test function (dry run)
SELECT ai_proposal_platform.migrate_demo_to_project(
  'test-session-id',
  '00000000-0000-0000-0000-000000000001'::UUID
);
```

---

### Migration Order

```
001_demo_claim_columns.sql
        ↓
002_demo_download_count.sql
        ↓
003_demo_schema_update.sql
```

**All migrations must be run in order.** Each migration is idempotent and can be re-run safely.

---

### Future Migrations

When adding new columns to the `demo` table:

```sql
-- 004_feature_xyz.sql
BEGIN;

ALTER TABLE ai_proposal_platform.demo
  ADD COLUMN IF NOT EXISTS new_feature JSONB;

CREATE INDEX IF NOT EXISTS idx_demo_new_feature 
  ON ai_proposal_platform.demo (new_feature) 
  WHERE new_feature IS NOT NULL;

COMMIT;
```

**Naming convention:** `###_description.sql` (zero-padded, sequential)

---

## Code Migrations

### Backend Migration Patterns

#### Adding a New Endpoint

1. Add route in `app/api/<router>.py`
2. Add test in `backend/tests/test_<feature>.py`
3. Update `docs/05-api-endpoints.md`
4. Update `STATUS.md` — mark as completed

#### Changing a Database Column

1. Create migration file `database-migrations/###_description.sql`
2. Update `app/services/supabase_service.py` — add getter/setter
3. Update `app/api/<router>.py` — use new column
4. Update tests
5. Update `docs/04-database-schema.md`

#### Removing a Feature

1. Mark as deprecated in `STATUS.md`
2. Remove code from routers
3. Remove code from frontend
4. Add test in `test_dead_routers.py`
5. Clean up database columns (optional — backward compatibility)

---

### Frontend Migration Patterns

#### Adding a New Component

1. Create component in `frontend/components/<category>/<Component>.vue`
2. Add test in `frontend/tests/components/<Component>.spec.ts`
3. Update `docs/07-frontend-components.md`
4. Update `STATUS.md`

#### Changing a Composable

1. Update `frontend/composables/<composable>.ts`
2. Update all consumers
3. Add test in `frontend/tests/composables/<composable>.spec.ts`
4. Update `docs/07-frontend-components.md`

---

## Environment Migrations

### Adding a New Environment Variable

1. Add to `backend/.env.example` (if exists)
2. Add to `frontend/.env.example` (if exists)
3. Add to `backend/app/config.py` — read and validate
4. Add to `frontend/nuxt.config.ts` — expose to runtimeConfig
5. Update `docs/08-environment-variables.md`
6. Update all deployment environments (dev, prod)
7. Update `STATUS.md`

### Changing Environment Values

| Environment | How to Update |
|-------------|---------------|
| Local dev | Edit `backend/.env` and `frontend/.env` |
| Dev VPS | SSH to server, edit `.env` files, restart containers |
| Production | Edit `.env` files, restart containers, or use secrets manager |

---

## Rollback Procedures

### Database Rollback

#### Rollback 003

```sql
BEGIN;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS section_versions;
DROP INDEX IF EXISTS ai_proposal_platform.idx_demo_section_versions_null;
DROP FUNCTION IF EXISTS ai_proposal_platform.migrate_demo_to_project(TEXT, UUID);
COMMIT;
```

#### Rollback 002

```sql
BEGIN;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS has_generated_docx;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS download_count;
COMMIT;
```

#### Rollback 001

```sql
BEGIN;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS status;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS claimed_by_user_id;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS claimed_project_id;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS claimed_at;
DROP INDEX IF EXISTS ai_proposal_platform.idx_demo_active;
COMMIT;
```

### Code Rollback

```bash
# Rollback to previous commit
git log --oneline -10
git checkout <previous-commit>

# Rebuild and restart
docker compose build --no-cache
docker compose up -d

# If using Docker images
docker pull tgsataiwan/ai-proposal-demo:backend-<previous-tag>
docker pull tgsataiwan/ai-proposal-demo:frontend-<previous-tag>
docker compose up -d
```

### Emergency Rollback

```bash
# Stop all services
docker compose down

# Revert to last known good image
docker tag tgsataiwan/ai-proposal-demo:backend-<last-good> tgsataiwan/ai-proposal-demo:backend-dev
docker tag tgsataiwan/ai-proposal-demo:frontend-<last-good> tgsataiwan/ai-proposal-demo:frontend-dev

# Restart
docker compose up -d
```

---

## Version Upgrade Guide

### v1.0.0-demo → v1.1.0-demo (Future)

**Planned changes:**
- Enable IP rate limiting
- Add CAPTCHA
- Multi-template demo support
- A/B testing framework

**Upgrade steps:**
1. Update `.env` with new variables
2. Run database migrations
3. Update `demo_rate_limiter.py` (uncomment enforcement)
4. Deploy new images
5. Monitor for 24 hours

### v1.0.0-demo → v2.0.0 (Hypothetical)

If merging back into full platform:
1. Audit all changes
2. Resolve conflicts
3. Test auth flow integration
4. Run full platform test suite
5. Staged rollout (10% → 50% → 100%)

---

## Migration Checklist

### Before Migration

- [ ] Backup database
- [ ] Review migration files
- [ ] Test on dev environment
- [ ] Notify team
- [ ] Schedule maintenance window

### During Migration

- [ ] Run migrations in order
- [ ] Verify each migration succeeded
- [ ] Test API endpoints
- [ ] Test WebSocket
- [ ] Test frontend

### After Migration

- [ ] Monitor error rates
- [ ] Monitor API cost
- [ ] Check conversion rate
- [ ] Update documentation
- [ ] Update `STATUS.md`
- [ ] Notify team

---

> Next: [`15-demo-to-platform-handoff.md`](15-demo-to-platform-handoff.md)

(End of file)
