# 12 — Monitoring & Alerting

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Monitoring Philosophy](#monitoring-philosophy)
2. [Key Metrics](#key-metrics)
3. [Log Format](#log-format)
4. [Alerting Rules](#alerting-rules)
5. [Dashboards](#dashboards)
6. [Log Aggregation](#log-aggregation)

---

## Monitoring Philosophy

The demo is a **public-facing lead generation tool**. Monitoring focuses on:

1. **Availability** — Is the demo accessible?
2. **Conversion** — Are visitors signing up?
3. **Cost** — Is API usage within budget?
4. **Abuse** — Are bots draining the API?
5. **Error rates** — Are users hitting errors?

---

## Key Metrics

### 1. Business Metrics

| Metric | Source | Target | Alert Threshold |
|--------|--------|--------|-----------------|
| **Active sessions** | `SELECT COUNT(*) FROM demo WHERE status = 'active'` | > 100/day | — |
| **Conversion rate** | `claimed` / `active` | > 5% | < 2% |
| **Average session duration** | `expires_at - created_at` | 3–5 min | < 1 min |
| **Plan generation rate** | `has_generated_docx = true` / total | > 30% | < 10% |
| **Average fields filled** | `len(chat_answers)` | > 5 | < 2 |

### 2. Technical Metrics

| Metric | Source | Target | Alert Threshold |
|--------|--------|--------|-----------------|
| **API availability** | HTTP probe on `/api/demo` | 99.9% | < 99% |
| **WebSocket availability** | WS probe on `/ws/chat_guidance` | 99.5% | < 95% |
| **API latency (p95)** | `GET /api/demo` | < 500ms | > 2s |
| **Generation latency (p95)** | `POST /api/generate_plan` | < 30s | > 60s |
| **Error rate** | HTTP 5xx / total requests | < 0.1% | > 1% |
| **WebSocket disconnect rate** | Disconnects / connections | < 5% | > 10% |

### 3. Cost Metrics

| Metric | Source | Target | Alert Threshold |
|--------|--------|--------|-----------------|
| **Daily API cost** | Sum of `usage_logs.cost` | < $50/day | > $100/day |
| **Cost per session** | `cost` / `session_count` | < $0.50 | > $1.00 |
| **Token usage** | `SUM(input_token + output_token)` | < 1M/day | > 2M/day |

### 4. Abuse Metrics

| Metric | Source | Target | Alert Threshold |
|--------|--------|--------|-----------------|
| **Sessions per IP** | `demo_ip_limits` | < 3/hr | > 5/hr |
| **Failed rate limits** | 429 responses | — | > 10/hr |
| **Bot-like sessions** | Sessions with < 2 fields filled | < 20% | > 50% |

---

## Log Format

### Backend Logs

FastAPI uses Python's standard `logging` module with this format:

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
```

**Example log entries:**

```
2026-06-24 06:30:00,123 - app.api.projects - INFO - Created demo session: 550e8400-e29b-41d4-a716-446655440000
2026-06-24 06:30:05,456 - app.api.generate - INFO - Generated plan for session: 550e8400-e29b-41d4-a716-446655440000, sections: 5
2026-06-24 06:30:10,789 - app.utils.demo_rate_limiter - WARNING - Rate limit exceeded for IP: 203.0.113.42
2026-06-24 06:30:15,012 - app.services.llm_service - ERROR - OpenAI API error: Rate limit exceeded
2026-06-24 06:30:20,345 - app.api.dependencies - ERROR - Database connection failed
```

### Structured Logging (Recommended)

For production, consider switching to JSON structured logging:

```json
{
  "timestamp": "2026-06-24T06:30:00.123Z",
  "level": "INFO",
  "logger": "app.api.projects",
  "message": "Created demo session",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0...",
  "request_id": "req-abc123"
}
```

### Request ID

Add a `X-Request-ID` header to all requests for tracing:

```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

---

## Alerting Rules

### P1 — Critical (Immediate Response)

| Condition | Action | Notification |
|-----------|--------|--------------|
| API down > 5 min | Escalate to on-call | Slack + PagerDuty |
| Error rate > 5% | Investigate immediately | Slack |
| Daily API cost > $200 | Check for abuse | Slack + Email |
| Database connection failures | Check Supabase status | Slack |

### P2 — High (Respond within 1 hour)

| Condition | Action | Notification |
|-----------|--------|--------------|
| Conversion rate < 2% | Check UX flow | Slack |
| WebSocket disconnect rate > 10% | Check network/LLM | Slack |
| Generation latency > 60s | Check LLM provider | Slack |
| Rate limit 429s > 50/hr | Check if abuse or misconfig | Slack |

### P3 — Medium (Respond within 4 hours)

| Condition | Action | Notification |
|-----------|--------|--------------|
| Active sessions < 10/day | Check marketing campaigns | Email |
| Average session duration < 1 min | Check AI quality | Email |
| Bot-like sessions > 30% | Consider enabling CAPTCHA | Email |

### P4 — Low (Respond within 24 hours)

| Condition | Action | Notification |
|-----------|--------|--------------|
| Expired sessions > 1000 | Run cleanup | Email |
| Disk usage > 80% | Clean logs | Email |

---

## Dashboards

### Recommended: Grafana + Prometheus

**Metrics to export:**

```python
# Using prometheus-client
from prometheus_client import Counter, Histogram, Gauge

# Business metrics
demo_sessions_created = Counter('demo_sessions_created_total', 'Total sessions created')
demo_sessions_claimed = Counter('demo_sessions_claimed_total', 'Total sessions migrated')
demo_sessions_expired = Counter('demo_sessions_expired_total', 'Total sessions expired')
demo_active_sessions = Gauge('demo_active_sessions', 'Currently active sessions')

# Technical metrics
http_requests = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['endpoint'])
websocket_connections = Counter('websocket_connections_total', 'Total WebSocket connections')
websocket_disconnects = Counter('websocket_disconnects_total', 'Total WebSocket disconnects', ['reason'])

# Cost metrics
llm_tokens_used = Counter('llm_tokens_used_total', 'Total LLM tokens used', ['model', 'provider'])
llm_cost = Counter('llm_cost_usd_total', 'Total LLM cost in USD', ['model', 'provider'])

# Abuse metrics
rate_limit_hits = Counter('rate_limit_hits_total', 'Rate limit hits', ['type', 'ip_address'])
```

### Dashboard Panels

```
┌─────────────────────────────────────────────────────────────────────┐
│  DEMO OVERVIEW                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Active       │  │ Converted    │  │ Avg Duration │  │ Cost     │ │
│  │ Sessions     │  │ Today        │  │ Today        │  │ Today    │ │
│  │  142         │  │  8 (5.6%)    │  │  4m 32s      │  │ $42.30   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│  API LATENCY (p95)                                                  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  GET /api/demo      │ ████████░░░░░░░░░░░░ │ 320ms           │  │
│  │  POST /generate     │ ████████████████████ │ 28s             │  │
│  │  WS /chat_guidance  │ ██████░░░░░░░░░░░░ │ 180ms           │  │
│  └─────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  ERROR RATE (24h)                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  5xx: 0.02%  │  429: 0.15%  │  400: 0.05%  │  200: 99.78%  │  │
│  └─────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│  TOP 10 IPs (Session Count)                                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  203.0.113.42  │  5 sessions  │  Normal                   │  │
│  │  198.51.100.7  │  3 sessions  │  Normal                   │  │
│  │  192.0.2.15    │  12 sessions │  ⚠️  Flagged              │  │
│  └─────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Log Aggregation

### Option 1: Docker Logs + Filebeat

```yaml
# docker-compose.yml (add to services)
filebeat:
  image: docker.elastic.co/beats/filebeat:8.11.0
  volumes:
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
```

### Option 2: CloudWatch (AWS)

```bash
# Install CloudWatch agent
docker run --log-driver=awslogs \
  --log-opt awslogs-region=ap-northeast-1 \
  --log-opt awslogs-group=ai-proposal-demo \
  --log-opt awslogs-stream=backend \
  tgsataiwan/ai-proposal-demo:backend
```

### Option 3: Supabase Log Drains

If hosting on Supabase, use the built-in log explorer:

```sql
-- Query logs in Supabase
SELECT timestamp, event_message
FROM postgres_logs
WHERE event_message LIKE '%demo%'
ORDER BY timestamp DESC
LIMIT 100;
```

### Recommended: Simple Log Aggregation

For the current scale, a simple approach is sufficient:

```bash
# Daily log rotation
docker compose logs -f --tail=200 > /var/log/ai-proposal-demo/$(date +%Y-%m-%d).log

# Weekly summary
# Run via cron every Sunday
grep -c "ERROR" /var/log/ai-proposal-demo/*.log
```

---

## Monitoring Checklist

### Post-Deployment

- [ ] HTTP probe on `/api/demo` returns 200
- [ ] WebSocket probe connects successfully
- [ ] Error logs are readable
- [ ] Alert channels are configured
- [ ] Dashboard is accessible
- [ ] On-call rotation is documented

### Weekly

- [ ] Review active session count
- [ ] Check conversion rate
- [ ] Review API cost
- [ ] Check error rate
- [ ] Review abuse metrics

### Monthly

- [ ] Review and adjust alert thresholds
- [ ] Update dashboards
- [ ] Rotate API keys
- [ ] Review and archive old logs

---

> Next: [`13-runbook.md`](13-runbook.md)

(End of file)
