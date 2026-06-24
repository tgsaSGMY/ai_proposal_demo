# 09 — Deployment Guide

> **Scope:** AI Proposal Demo (Lead Generation Edition)  
> **Last Updated:** 2026-06-24

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Compose Deployment](#docker-compose-deployment)
3. [Nginx Configuration](#nginx-configuration)
4. [SSL/TLS Setup](#ssltls-setup)
5. [Environment Setup](#environment-setup)
6. [Database Migrations](#database-migrations)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Rollback Procedure](#rollback-procedure)
9. [Health Checks](#health-checks)

---

## Prerequisites

### Server Requirements

| Environment | CPU | RAM | Disk | OS |
|-------------|-----|-----|------|-----|
| Dev VPS | 1 vCPU | 2 GB | 20 GB | Ubuntu 22.04 LTS |
| Production | 2 vCPU | 4 GB | 50 GB | Ubuntu 22.04 LTS |

### Software Requirements

- Docker Engine 24.0+
- Docker Compose v2.20+
- Git
- SSH access
- Nginx (or Nginx Proxy Manager)

### Domain Requirements

- **Demo:** `demo-aiproposal.tgsa.com.tw`
- **Full Platform:** `aiproposal.tgsa.com.tw`
- DNS A record pointing to server IP

---

## Docker Compose Deployment

### Production (`docker-compose.yml`)

```yaml
version: "3.8"

services:
  fastapi-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fastapi-backend
    restart: unless-stopped
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nuxt-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: nuxt-frontend
    restart: unless-stopped
    env_file:
      - ./frontend/.env
    ports:
      - "3000:3000"
    networks:
      - app-network
    depends_on:
      - fastapi-backend

  nginx-proxy:
    build:
      context: ./nginx
      dockerfile: Dockerfile
    container_name: nginx-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - app-network
    depends_on:
      - fastapi-backend
      - nuxt-frontend

networks:
  app-network:
    driver: bridge
```

### Dev VPS (`docker-compose.beta.yml`)

```yaml
version: "3.8"

services:
  fastapi-backend:
    image: tgsataiwan/ai-proposal-demo:backend-dev
    container_name: fastapi-backend
    restart: unless-stopped
    env_file:
      - ./backend/.env
    ports:
      - "8000:8000"
    networks:
      - app-network

  nuxt-frontend:
    image: tgsataiwan/ai-proposal-demo:frontend-dev
    container_name: nuxt-frontend
    restart: unless-stopped
    env_file:
      - ./frontend/.env
    ports:
      - "3000:3000"
    networks:
      - app-network

  nginx-proxy:
    image: jc21/nginx-proxy-manager:latest
    container_name: nginx-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "81:81"  # NPM admin UI
    volumes:
      - npm-data:/data
      - npm-letsencrypt:/etc/letsencrypt
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  npm-data:
  npm-letsencrypt:
```

### Deploy Steps

```bash
# 1. Clone repository
git clone https://github.com/tgsaSGMY/ai_proposal_demo.git
cd ai_proposal_demo

# 2. Create environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit both files with your values

# 3. Build and start
 docker compose up -d

# 4. Verify
 docker compose ps
 docker compose logs -f --tail=200

# 5. Health check
curl https://demo-aiproposal.tgsa.com.tw/api/demo
curl https://demo-aiproposal.tgsa.com.tw/api/config
```

---

## Nginx Configuration

### Production (`nginx/nginx.conf`)

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript;

    # Rate limiting (optional)
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=ws:10m rate=5r/s;

    upstream frontend {
        server nuxt-frontend:3000;
    }

    upstream backend {
        server fastapi-backend:8000;
    }

    server {
        listen 80;
        server_name demo-aiproposal.tgsa.com.tw;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name demo-aiproposal.tgsa.com.tw;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # Timeouts for LLM calls
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
            proxy_send_timeout 300s;
        }

        # WebSocket
        location /ws/ {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400s;
        }

        # Icon endpoint
        location /_nuxt_icon/ {
            proxy_pass http://frontend;
        }
    }
}
```

### Dev VPS (`nginx/nginx.dev.conf`)

For Dev VPS using Nginx Proxy Manager, configure via the web UI (port 81):

1. **Proxy Hosts:**
   - Domain: `demo-dev.172.233.79.222.nip.io`
   - Forward Hostname/IP: `nuxt-frontend`
   - Forward Port: `3000`
   - Block Common Exploits: ✅
   - Cache Assets: ✅

2. **Custom Locations:**
   - Location: `/api/`
   - Forward Hostname/IP: `fastapi-backend`
   - Forward Port: `8000`

   - Location: `/ws/`
   - Forward Hostname/IP: `fastapi-backend`
   - Forward Port: `8000`
   - WebSocket Support: ✅

3. **SSL:**
   - SSL Certificate: Request a new certificate (Let's Encrypt)
   - Force SSL: ✅
   - HTTP/2 Support: ✅

---

## SSL/TLS Setup

### Production (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d demo-aiproposal.tgsa.com.tw

# Copy to nginx ssl directory
sudo cp /etc/letsencrypt/live/demo-aiproposal.tgsa.com.tw/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/demo-aiproposal.tgsa.com.tw/privkey.pem ./nginx/ssl/

# Auto-renewal
sudo crontab -e
# Add: 0 3 * * * /usr/bin/certbot renew --quiet && docker compose restart nginx-proxy
```

### Dev VPS (NPM Let's Encrypt)

1. Open Nginx Proxy Manager admin UI (`https://<ip>:81`)
2. Go to **SSL Certificates** → **Add SSL Certificate**
3. Select **Let's Encrypt**
4. Enter domain: `demo-dev.172.233.79.222.nip.io`
5. Click **Save**

---

## Environment Setup

### Pre-Deployment Checklist

- [ ] Server provisioned with Docker & Docker Compose
- [ ] DNS A record points to server IP
- [ ] Firewall allows ports 80, 443, 22
- [ ] `.env` files created with correct values
- [ ] Supabase project created and schema migrated
- [ ] API keys (OpenAI, Gemini) are valid and have quota
- [ ] `demo` table exists in `ai_proposal_platform` schema
- [ ] `demo_ip_limits` table exists
- [ ] `migrate_demo_to_project()` function exists

### Post-Deployment Verification

```bash
# 1. Container health
docker compose ps

# 2. Backend health
curl -f https://demo-aiproposal.tgsa.com.tw/
# Expected: {"message":"AI Proposal Demo API — unauthenticated, cookie-scoped."}

# 3. API endpoints
curl -f https://demo-aiproposal.tgsa.com.tw/api/config

# 4. Session creation
curl -c cookies.txt -f https://demo-aiproposal.tgsa.com.tw/api/demo

# 5. WebSocket (using wscat)
npm install -g wscat
wscat -c "wss://demo-aiproposal.tgsa.com.tw/ws/chat_guidance" \
  -H "Cookie: demo_session_id=<uuid>"

# 6. Frontend loads
curl -f https://demo-aiproposal.tgsa.com.tw/
```

---

## Database Migrations

### Run Migrations on Production

```bash
# Connect to Supabase SQL Editor or use psql
psql "postgresql://..." -f database-migrations/001_demo_claim_columns.sql
psql "postgresql://..." -f database-migrations/002_demo_download_count.sql
psql "postgresql://..." -f database-migrations/003_demo_schema_update.sql
```

### Verify Migration

```sql
-- Check tables exist
SELECT * FROM ai_proposal_platform.demo LIMIT 0;
SELECT * FROM ai_proposal_platform.demo_ip_limits LIMIT 0;

-- Check function exists
SELECT proname FROM pg_proc WHERE proname = 'migrate_demo_to_project';

-- Check indexes
SELECT indexname FROM pg_indexes WHERE tablename = 'demo';
```

---

## CI/CD Pipeline

### GitHub Actions (`.github/workflows/deploy-dev.yml`)

```yaml
name: Deploy to Dev VPS

on:
  push:
    branches: [dev]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: tgsataiwan/ai-proposal-demo:backend-dev

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: tgsataiwan/ai-proposal-demo:frontend-dev

      - name: Deploy to VPS
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USERNAME }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/ai-proposal-demo
            docker compose pull
            docker compose up -d
            docker compose ps
            docker system prune -f
```

---

## Rollback Procedure

### 1. Rollback to Previous Image

```bash
# List available images
docker images | grep ai-proposal-demo

# Re-tag previous image
docker tag tgsataiwan/ai-proposal-demo:backend-dev-<previous> tgsataiwan/ai-proposal-demo:backend-dev

# Restart
docker compose up -d
```

### 2. Rollback Database (if migration failed)

```sql
-- Revert 003 migration
BEGIN;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS section_versions;
DROP INDEX IF EXISTS ai_proposal_platform.idx_demo_section_versions_null;
COMMIT;

-- Revert 002 migration
BEGIN;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS has_generated_docx;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS download_count;
COMMIT;

-- Revert 001 migration
BEGIN;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS status;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS claimed_by_user_id;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS claimed_project_id;
ALTER TABLE ai_proposal_platform.demo DROP COLUMN IF EXISTS claimed_at;
DROP INDEX IF EXISTS ai_proposal_platform.idx_demo_active;
COMMIT;
```

### 3. Emergency Stop

```bash
# Stop all services
docker compose down

# Or scale to zero
docker compose up -d --scale fastapi-backend=0 --scale nuxt-frontend=0
```

---

## Health Checks

### Backend Health

```bash
curl -f http://localhost:8000/
# Expected: {"message":"AI Proposal Demo API — unauthenticated, cookie-scoped."}
```

### Frontend Health

```bash
curl -f http://localhost:3000/
# Expected: HTML page with 200 status
```

### Database Health

```bash
# Check connection
psql "$DATABASE_URL" -c "SELECT 1;"

# Check active sessions
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ai_proposal_platform.demo WHERE status = 'active';"

# Check expired sessions
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ai_proposal_platform.demo WHERE expires_at < NOW();"
```

### Log Monitoring

```bash
# Real-time logs
docker compose logs -f --tail=200

# Error only
docker compose logs -f --tail=200 | grep -i error

# Specific service
docker compose logs -f --tail=200 fastapi-backend
```

---

> Next: [`10-testing-strategy.md`](10-testing-strategy.md)

(End of file)
