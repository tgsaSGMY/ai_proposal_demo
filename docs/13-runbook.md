# 13 — Runbook (Troubleshooting Guide)

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Demo Cannot Load](#demo-cannot-load)
2. [WebSocket Connection Fails](#websocket-connection-fails)
3. [Plan Generation Fails](#plan-generation-fails)
4. [Session Migration Fails](#session-migration-fails)
5. [High API Cost](#high-api-cost)
6. [Database Connection Errors](#database-connection-errors)
7. [Rate Limit False Positives](#rate-limit-false-positives)
8. [Common Queries](#common-queries)

---

## Demo Cannot Load

### Symptoms

- Browser shows "無法載入體驗" (Cannot load experience)
- Blank page after loading
- 502 Bad Gateway
- 504 Gateway Timeout

### Troubleshooting Steps

#### Step 1: Check Container Status

```bash
docker compose ps
```

**Expected:** All containers `Up` and `healthy`.

**If not:**
```bash
docker compose logs -f --tail=200
# Check for startup errors
docker compose restart fastapi-backend
```

#### Step 2: Check Backend Health

```bash
curl -f http://localhost:8000/
```

**Expected:** `{"message":"AI Proposal Demo API — unauthenticated, cookie-scoped."}`

**If not:**
- Check backend logs: `docker compose logs -f fastapi-backend`
- Check `.env` file exists and is valid
- Check Supabase connection: `python backend/check_db.py`

#### Step 3: Check Frontend Health

```bash
curl -f http://localhost:3000/
```

**Expected:** HTML page with 200 status.

**If not:**
- Check frontend logs: `docker compose logs -f nuxt-frontend`
- Check if `npm run build` succeeded

#### Step 4: Check Nginx

```bash
curl -f http://localhost/
```

**If Nginx is not responding:**
```bash
docker compose logs -f nginx-proxy
docker compose restart nginx-proxy
```

**If Nginx returns 502:**
- Backend is down or not reachable
- Check backend container is running
- Check backend port is correct (8000)

#### Step 5: Check DNS

```bash
nslookup demo-aiproposal.tgsa.com.tw
```

**Expected:** Resolves to server IP.

**If not:** Check DNS A record.

---

## WebSocket Connection Fails

### Symptoms

- Chat shows "AI 正在構思..." indefinitely
- "WebSocket connection failed" error
- Messages not sending
- No AI response

### Troubleshooting Steps

#### Step 1: Check WebSocket Handshake

```bash
# Test with curl (HTTP upgrade)
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  http://localhost:8000/ws/chat_guidance
```

**Expected:** `101 Switching Protocols`

**If 404:**
- Router not registered in `main.py`
- Check `app.include_router(generate.router)`

#### Step 2: Check Cookie

```bash
# Test with wscat
npm install -g wscat

# First, get a cookie
curl -c cookies.txt -b cookies.txt http://localhost:8000/api/demo

# Then connect with cookie
wscat -c "ws://localhost:8000/ws/chat_guidance" \
  -H "Cookie: $(grep demo_session_id cookies.txt | awk '{print $7}')"
```

**If connection fails:**
- Cookie not sent → Check `credentials: "include"` in frontend
- Cookie invalid → Check `demo_session_id` format (UUID)

#### Step 3: Check Nginx WebSocket Config

```nginx
# In nginx.conf
location /ws/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400s;
}
```

**Common mistakes:**
- Missing `proxy_set_header Upgrade`
- Missing `proxy_set_header Connection`
- `proxy_read_timeout` too short (causes disconnects)

#### Step 4: Check Backend Logs

```bash
docker compose logs -f fastapi-backend | grep -i websocket
```

**Look for:**
- `missing demo_session_id cookie`
- `supabase unavailable`
- `Stream error`

#### Step 5: Check LLM Service

```bash
docker compose logs -f fastapi-backend | grep -i "llm\|openai\|gemini"
```

**If LLM errors:**
- Check API key validity: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`
- Check API quota: OpenAI dashboard
- Check model availability: `model_registry` at startup

---

## Plan Generation Fails

### Symptoms

- "生成計畫書失敗" error
- Empty candidates
- 429 error
- 500 error

### Troubleshooting Steps

#### Step 1: Check Session Status

```bash
curl -b cookies.txt http://localhost:8000/api/demo/status
```

**If `has_generated_docx: true`:**
- Session already generated — return 429
- User needs to register or reset session

#### Step 2: Check Template Config

```bash
curl http://localhost:8000/api/config
```

**Expected:** `grants` array with `templates` containing `sections`.

**If empty:**
- Supabase `grants` / `plan_templates` / `sections` tables empty
- Run `POST /api/config/refresh`
- Check `app.state.all_grants_config` at startup

#### Step 3: Check LLM Provider

```bash
docker compose logs -f fastapi-backend | grep -i "generate_plan\|section\|candidate"
```

**Common errors:**
- `Template X not found in Grant Y` → Check `grant_id` / `template_id` match
- `No sections found` → Template has no sections configured
- `Model not configured` → `model_registry` empty at startup
- `Rate limit` → LLM provider quota exceeded

#### Step 4: Check Specific Section

```bash
# Generate with only one section for debugging
curl -X POST http://localhost:8000/api/generate_plan \
  -b cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"grant":"sbir","template":"sbir_p1","user_input":"test","num_candidates":1}'
```

**If specific section fails:**
- Check section `json_schema` is valid
- Check section `prompt` is not empty
- Check LLM can handle the prompt length

---

## Session Migration Fails

### Symptoms

- User clicks "免費註冊" but lands on empty project
- Demo data not showing in full platform
- `status` remains `active` after signup
- Error in full platform logs

### Troubleshooting Steps

#### Step 1: Check Demo Session Status

```sql
SELECT session_id, status, claimed_by, claimed_at, claimed_project_id
FROM ai_proposal_platform.demo
WHERE session_id = '<session_id>';
```

**Expected:** `status = 'claimed'`, `claimed_by` = user UUID, `claimed_project_id` = project UUID.

**If `status = 'active'`:**
- Migration was not triggered
- Check full platform OAuth callback
- Check `pending_demo_claim` cookie

#### Step 2: Check Full Platform Callback

```bash
# In full platform logs
grep -i "claim_demo_session\|pending_demo_claim" /var/log/ai-proposal-platform/*.log
```

**Look for:**
- `claim_demo_session called with ref=<session_id>`
- `Migration failed: Demo session not found`
- `Migration failed: already_claimed`

#### Step 3: Check SQL Function

```sql
-- Test migration manually
SELECT ai_proposal_platform.migrate_demo_to_project(
  '<session_id>',
  '<user_id>'::UUID
);
```

**If error:**
- `Demo session not found` → Session expired or deleted
- `already claimed` → Another user claimed it
- Column mismatch → `projects` schema changed

#### Step 4: Check Field Mapping

```sql
-- Verify data exists in demo row
SELECT 
  saved_plan IS NOT NULL as has_plan,
  stored_answer IS NOT NULL as has_answers,
  conversation_history IS NOT NULL as has_history,
  title,
  section_versions IS NOT NULL as has_versions
FROM ai_proposal_platform.demo
WHERE session_id = '<session_id>';
```

**If all NULL:**
- User did not generate a plan or chat
- Migration creates empty project (expected behavior)

#### Step 5: Check Cross-Domain Cookie

```bash
# On full platform domain
curl -I https://aiproposal.tgsa.com.tw/api/external-auth/redirect?ref=<session_id>
```

**Check `Set-Cookie` header:**
```
Set-Cookie: pending_demo_claim=<session_id>; Max-Age=900; HttpOnly; SameSite=Lax; Path=/
```

**If missing:**
- Full platform callback not setting cookie
- Check `external-auth` router implementation

---

## High API Cost

### Symptoms

- Daily API cost > $100
- Unusual token usage spikes
- Many sessions with high `total_tokens_used`

### Troubleshooting Steps

#### Step 1: Identify Top Sessions

```sql
SELECT 
  session_id,
  ip_address,
  interaction_count,
  total_tokens_used,
  created_at
FROM ai_proposal_platform.demo
WHERE status = 'active'
ORDER BY total_tokens_used DESC
LIMIT 20;
```

#### Step 2: Identify Top IPs

```sql
SELECT 
  ip_address,
  COUNT(*) as session_count,
  SUM(interaction_count) as total_prompts,
  SUM(total_tokens_used) as total_tokens
FROM ai_proposal_platform.demo
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY ip_address
ORDER BY total_tokens DESC
LIMIT 20;
```

#### Step 3: Check for Bots

```sql
-- Sessions with many prompts but few fields filled
SELECT 
  session_id,
  ip_address,
  interaction_count,
  jsonb_array_length(conversation_history) as messages,
  jsonb_object_keys(stored_answer->'chat_answers') as fields
FROM ai_proposal_platform.demo
WHERE interaction_count > 15
  AND jsonb_object_keys(stored_answer->'chat_answers') IS NULL;
```

#### Step 4: Mitigation

1. **Enable IP rate limiting** (uncomment in `demo_rate_limiter.py`)
2. **Block specific IPs** (if identified):
   ```sql
   -- Not recommended long-term, but useful for immediate stop
   -- Use firewall instead
   ```
3. **Lower token cap** temporarily:
   ```env
   DEMO_MAX_TOKENS_PER_SESSION=50000
   ```
4. **Add CAPTCHA** (long-term solution)

---

## Database Connection Errors

### Symptoms

- "無法載入體驗" (Cannot load experience)
- Backend logs show `connection refused` or `timeout`
- `check_db.py` fails

### Troubleshooting Steps

#### Step 1: Check Database URL

```bash
python backend/check_db.py
```

**Expected:** `Database connection OK`

**If fails:**
- Check `DATABASE_URL` format
- Check network connectivity to Supabase
- Check Supabase project status

#### Step 2: Check Supabase Status

```bash
curl -I https://<project>.supabase.co
```

**If 503:** Supabase is down. Check status page.

#### Step 3: Check Connection Pool

```sql
-- In Supabase SQL Editor
SELECT 
  count(*) as active_connections,
  max_connections
FROM pg_stat_activity, pg_settings
WHERE name = 'max_connections';
```

**If near max:** Increase pool size or check for connection leaks.

#### Step 4: Check Schema Exists

```sql
SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ai_proposal_platform';
```

**If missing:**
- Run migrations: `database-migrations/*.sql`
- Check Supabase project settings

---

## Rate Limit False Positives

### Symptoms

- Legitimate users blocked with 429
- "無法建立新的體驗會話" error
- Users behind corporate VPN blocked

### Troubleshooting Steps

#### Step 1: Check IP Limit Status

```sql
SELECT 
  ip_address,
  window_type,
  window_start,
  session_count
FROM ai_proposal_platform.demo_ip_limits
WHERE ip_address = '<user_ip>'::inet
ORDER BY window_start DESC
LIMIT 10;
```

#### Step 2: Check User Pattern

```sql
SELECT 
  session_id,
  created_at,
  interaction_count
FROM ai_proposal_platform.demo
WHERE ip_address = '<user_ip>'::inet
ORDER BY created_at DESC
LIMIT 10;
```

**If many sessions with 0 interaction:**
- User refreshing page repeatedly
- Bot creating sessions without using them

#### Step 3: Adjust Limits

```env
# Increase limits temporarily
DEMO_IP_HOURLY_LIMIT=10
DEMO_IP_DAILY_LIMIT=20
```

**Or whitelist specific IPs:**
```python
# In dependencies.py
if ip in WHITELISTED_IPS:
    return new_id  # Skip rate limiting
```

#### Step 4: Consider Progressive Friction

Instead of hard blocking:
1. First 3 sessions: no friction
2. Sessions 4–5: show warning
3. Sessions 6+: require CAPTCHA

---

## Common Queries

### Daily Session Report

```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) as sessions_created,
  COUNT(*) FILTER (WHERE status = 'claimed') as converted,
  COUNT(*) FILTER (WHERE has_generated_docx) as generated,
  AVG(interaction_count) as avg_prompts,
  SUM(total_tokens_used) as total_tokens
FROM ai_proposal_platform.demo
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Top Abusers

```sql
SELECT 
  ip_address,
  COUNT(*) as sessions,
  SUM(interaction_count) as prompts,
  SUM(total_tokens_used) as tokens,
  MAX(created_at) as last_seen
FROM ai_proposal_platform.demo
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY ip_address
HAVING COUNT(*) > 5
ORDER BY sessions DESC;
```

### Expired Sessions Cleanup

```sql
-- Count expired sessions
SELECT COUNT(*) 
FROM ai_proposal_platform.demo 
WHERE expires_at < NOW() 
  AND status NOT IN ('claimed', 'expired');

-- Mark as expired (dry run)
UPDATE ai_proposal_platform.demo 
SET status = 'expired'
WHERE expires_at < NOW() 
  AND status NOT IN ('claimed', 'expired')
RETURNING session_id, expires_at;

-- Delete expired sessions (caution!)
DELETE FROM ai_proposal_platform.demo 
WHERE status = 'expired' 
  AND expires_at < NOW() - INTERVAL '30 days';
```

### Migration Success Rate

```sql
SELECT 
  DATE(created_at) as date,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE status = 'claimed') as claimed,
  ROUND(
    COUNT(*) FILTER (WHERE status = 'claimed') * 100.0 / COUNT(*), 
    2
  ) as conversion_rate
FROM ai_proposal_platform.demo
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

---

## Emergency Contacts

| Role | Contact | When to Contact |
|------|---------|----------------|
| DevOps | devops@tgsa.com.tw | Infrastructure issues |
| Backend Lead | backend@tgsa.com.tw | API errors, database issues |
| Frontend Lead | frontend@tgsa.com.tw | UI bugs, WebSocket issues |
| Database Admin | dba@tgsa.com.tw | Schema issues, migrations |
| Security | security@tgsa.com.tw | Abuse, breaches |

---

> Next: [`14-migration-guide.md`](14-migration-guide.md)

(End of file)
