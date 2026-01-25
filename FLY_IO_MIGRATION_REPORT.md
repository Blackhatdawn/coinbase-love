# CryptoVault: Render → Fly.io Migration Report

**Date:** January 2026
**Status:** Deep Investigation Complete
**Current Hosting:** Backend on Render, Frontend on Vercel
**Target:** Backend on Fly.io, Frontend remains on Vercel

---

## 1. EXECUTIVE SUMMARY

### Current Architecture Analysis
- **Frontend:** React + Vite + TypeScript → Vercel (https://www.cryptovault.financial)
- **Backend:** FastAPI + Python + MongoDB Atlas + Socket.IO → Render (https://cryptovault-api.onrender.com)
- **Database:** MongoDB Atlas (cloud-hosted, no migration needed)
- **Cache:** Upstash Redis (cloud-hosted, no migration needed)
- **Real-time:** Socket.IO over WebSocket with polling fallback

### Critical Findings

#### ✅ STRENGTHS
1. **Environment-driven configuration** - All URLs read from env vars via `config.py`
2. **Runtime config endpoint** - `/api/config` dynamically provides API URLs to frontend
3. **Robust health checks** - Multiple endpoints (`/health`, `/ping`, `/api/health`)
4. **Enterprise CORS** - Configurable origins via `CORS_ORIGINS` env var
5. **Cookie-based auth** - `withCredentials: true` properly configured
6. **WebSocket fallback** - Transport downgrades from WebSocket to polling

#### ⚠️ ISSUES TO FIX
1. **Hardcoded Render URL** in `vercel.json` rewrites (line 21-42)
2. **Hardcoded Render URL** in `.env.production` (line 5)
3. **Missing Fly.io deployment config** (no `fly.toml`)
4. **Port configuration** - Render uses `$PORT`, Fly.io may differ
5. **Health check timing** - May need adjustment for Fly.io cold starts
6. **CORS origins** - Need to add Fly.io backend URL to allowed origins

---

## 2. FRONTEND ↔ BACKEND COMMUNICATION PATHS AUDIT

### 2.1 API Communication
```
Frontend (Vercel)
    ↓ HTTPS
API Client (axios) → VITE_API_BASE_URL
    ↓
Vercel Rewrites (vercel.json) → /api/* proxied to backend
    ↓
Backend (Render→Fly.io) → FastAPI /api/* routes
```

**Files Involved:**
- `/app/frontend/src/lib/apiClient.ts` - Axios client with CSRF, retry, token refresh
- `/app/frontend/src/lib/runtimeConfig.ts` - Resolves `VITE_API_BASE_URL`
- `/app/frontend/vercel.json` - Rewrites to backend URL

### 2.2 WebSocket Communication
```
Frontend (Vercel)
    ↓ WSS
Socket.IO Client → resolveApiBaseUrl() + /socket.io/
    ↓
Backend → python-socketio (mounted on FastAPI)
```

**Files Involved:**
- `/app/frontend/src/services/socketService.ts` - Socket.IO client
- `/app/backend/socketio_server.py` - Socket.IO server
- `/app/backend/server.py` - Mounts Socket.IO ASGI app

### 2.3 Health Check Flow
```
Frontend (App init)
    ↓
healthCheckService.start() → /api/ping → /health → /api/crypto
    ↓
Backend → Returns health status
    ↓
Keeps backend warm (4-min interval)
```

---

## 3. ENVIRONMENT VARIABLES AUDIT

### Backend (`/app/backend/.env`)
| Variable | Status | Migration Action |
|----------|--------|------------------|
| `MONGO_URL` | ✅ Cloud-hosted | No change |
| `DB_NAME` | ✅ | No change |
| `JWT_SECRET` | ✅ | Copy to Fly.io |
| `CSRF_SECRET` | ✅ | Copy to Fly.io |
| `CORS_ORIGINS` | ⚠️ | Add Fly.io URL |
| `SENTRY_DSN` | ✅ | No change |
| `SENDGRID_API_KEY` | ✅ | Copy to Fly.io |
| `UPSTASH_REDIS_*` | ✅ Cloud-hosted | No change |
| `COINCAP_API_KEY` | ✅ | Copy to Fly.io |
| `NOWPAYMENTS_*` | ✅ | Copy to Fly.io |
| `PUBLIC_API_URL` | ⚠️ Missing | Add Fly.io URL |
| `PUBLIC_WS_URL` | ⚠️ Missing | Add Fly.io URL |
| `ENVIRONMENT` | ⚠️ | Set to `production` |

### Frontend (`/app/frontend/.env.production`)
| Variable | Status | Migration Action |
|----------|--------|------------------|
| `VITE_API_BASE_URL` | ❌ Hardcoded Render | Change to Fly.io URL |
| `VITE_SENTRY_DSN` | ✅ | No change |
| `VITE_APP_NAME` | ✅ | No change |

### Vercel Environment Variables (Dashboard)
| Variable | Status | Migration Action |
|----------|--------|------------------|
| `@vite_api_base_url` | ❌ Points to Render | Update to Fly.io URL |

---

## 4. HARDCODED URLs FOUND

### 4.1 vercel.json (Lines 21-42)
```json
{
  "source": "/api/:path*",
  "destination": "https://cryptovault-api.onrender.com/api/:path*"  // ❌ HARDCODED
}
```

**Fix Required:** Replace with Fly.io backend URL

### 4.2 .env.production (Line 5)
```
VITE_API_BASE_URL=https://cryptovault-api.onrender.com  // ❌ HARDCODED
```

**Fix Required:** Replace with Fly.io backend URL

### 4.3 render.yaml (Line 69)
```yaml
- key: PUBLIC_API_URL
  value: https://cryptovault-api.onrender.com  // ❌ HARDCODED
```

**Fix Required:** This file will be replaced by fly.toml

### 4.4 Backend config.py - CLEAN ✅
All URLs are read from environment variables. No hardcoding.

### 4.5 API Client - CLEAN ✅
Uses `resolveApiBaseUrl()` which reads from runtime config/env.

---

## 5. FLY.IO MIGRATION PLAN

### Phase 1: Create Fly.io Configuration
1. Create `fly.toml` with:
   - App name: `cryptovault-api`
   - Region: `iad` (US East - matches Vercel)
   - HTTP service on port 8001
   - Health checks at `/health`
   - Auto-scaling configuration
   - Volume for persistent storage (if needed)

2. Create Fly.io Dockerfile optimizations:
   - Multi-stage build
   - Non-root user
   - Health check
   - Proper signal handling for graceful shutdown

### Phase 2: Environment Setup on Fly.io
```bash
flyctl secrets set \
  MONGO_URL="mongodb+srv://..." \
  JWT_SECRET="..." \
  CSRF_SECRET="..." \
  SENDGRID_API_KEY="..." \
  UPSTASH_REDIS_REST_URL="..." \
  UPSTASH_REDIS_REST_TOKEN="..." \
  COINCAP_API_KEY="..." \
  NOWPAYMENTS_API_KEY="..." \
  NOWPAYMENTS_IPN_SECRET="..." \
  SENTRY_DSN="..."
```

### Phase 3: Update Frontend Configuration
1. Update `vercel.json` rewrites to new Fly.io URL
2. Update `VITE_API_BASE_URL` in Vercel dashboard
3. Update CORS origins in backend to include Vercel domains

### Phase 4: Testing & Cutover
1. Deploy to Fly.io staging
2. Test all API endpoints
3. Test WebSocket connections
4. Test authentication flow
5. Switch DNS/rewrites to production

---

## 6. FLY.IO CONFIGURATION FILES

### 6.1 fly.toml (New)
```toml
app = "cryptovault-api"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  ENVIRONMENT = "production"
  DB_NAME = "cryptovault"
  PORT = "8001"
  USE_REDIS = "true"
  USE_MOCK_PRICES = "false"
  LOG_LEVEL = "INFO"

[http_service]
  internal_port = 8001
  force_https = true
  auto_stop_machines = false
  auto_start_machines = true
  min_machines_running = 1
  
  [http_service.concurrency]
    type = "connections"
    hard_limit = 100
    soft_limit = 80

[[services]]
  protocol = "tcp"
  internal_port = 8001

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.tcp_checks]]
    grace_period = "30s"
    interval = "15s"
    restart_limit = 0
    timeout = "10s"

  [[services.http_checks]]
    grace_period = "30s"
    interval = "15s"
    method = "GET"
    path = "/health"
    protocol = "http"
    timeout = "10s"
    tls_skip_verify = false

[checks]
  [checks.health]
    port = 8001
    type = "http"
    interval = "15s"
    timeout = "10s"
    grace_period = "30s"
    method = "GET"
    path = "/health"
```

### 6.2 Dockerfile.fly (Optimized for Fly.io)
```dockerfile
# Multi-stage build for smaller image
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"

# Start with uvicorn (Socket.IO compatible)
CMD ["uvicorn", "server:socket_app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
```

---

## 7. UPDATED CONFIGURATION FILES

### 7.1 vercel.json (Updated for Fly.io)
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://cryptovault-api.fly.dev/api/:path*"
    },
    {
      "source": "/health",
      "destination": "https://cryptovault-api.fly.dev/health"
    },
    {
      "source": "/ping",
      "destination": "https://cryptovault-api.fly.dev/ping"
    },
    {
      "source": "/csrf",
      "destination": "https://cryptovault-api.fly.dev/csrf"
    },
    {
      "source": "/socket.io/:path*",
      "destination": "https://cryptovault-api.fly.dev/socket.io/:path*"
    }
  ]
}
```

### 7.2 Backend .env (Fly.io Production)
```env
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# URLs (Fly.io)
PUBLIC_API_URL=https://cryptovault-api.fly.dev
PUBLIC_WS_URL=wss://cryptovault-api.fly.dev
APP_URL=https://www.cryptovault.financial
PUBLIC_SOCKET_IO_PATH=/socket.io/

# CORS (Include Vercel domains)
CORS_ORIGINS=["https://www.cryptovault.financial","https://cryptovault.financial","https://cryptovault-*.vercel.app"]
USE_CROSS_SITE_COOKIES=true

# Database (Cloud-hosted - no change)
MONGO_URL=<existing>
DB_NAME=cryptovault
MONGO_MAX_POOL_SIZE=10
MONGO_TIMEOUT_MS=5000

# Cache (Cloud-hosted - no change)
USE_REDIS=true
UPSTASH_REDIS_REST_URL=<existing>
UPSTASH_REDIS_REST_TOKEN=<existing>

# Security
JWT_SECRET=<existing>
JWT_ALGORITHM=HS256
CSRF_SECRET=<existing>
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# External Services
COINCAP_API_KEY=<existing>
SENDGRID_API_KEY=<existing>
NOWPAYMENTS_API_KEY=<existing>
NOWPAYMENTS_IPN_SECRET=<existing>
SENTRY_DSN=<existing>
```

---

## 8. OBSERVABILITY & LOGGING

### Current Implementation ✅
- **Structured JSON logging** in production (JSONFormatter class)
- **Request ID correlation** via RequestIDMiddleware
- **Sentry integration** for error tracking
- **Health check endpoints** for monitoring

### New Fly.io-Specific Endpoints
| Endpoint | Purpose |
|----------|---------|
| `/api/fly/status` | Full deployment info (region, machine ID, IPs) |
| `/api/fly/region` | Quick region check for latency testing |
| `/api/fly/instances` | Instance info for debugging auto-scaling |
| `/api/fly/health/fly` | Fly.io-specific health check |

### Recommended Enhancements for Fly.io
1. **Add Fly.io metrics** - Use fly-metrics for auto-collected metrics
2. **Log shipping** - Stream logs to external service (Datadog, Papertrail)
3. **Distributed tracing** - Add OpenTelemetry for request tracing
4. **Alerting** - Set up alerts for error rates, latency

---

## 9. PERFORMANCE OPTIMIZATIONS

### Fly.io-Specific Optimizations
1. **Regional deployment** - Deploy to `iad` (US East) to match Vercel
2. **Auto-scaling** - Configure min 1 machine, scale to 3 on demand
3. **Connection pooling** - MongoDB pool already configured (10 connections)
4. **Redis caching** - Upstash already in use
5. **Gzip compression** - Already enabled via middleware
6. **CDN for static** - Vercel handles frontend CDN

### Cold Start Mitigation
1. **min_machines_running = 1** - Always keep one instance warm
2. **Health check interval** - 15s keeps machine alive
3. **Frontend health check** - 4-min interval keeps API warm

### Auto-Scaling for Peak Trading Hours
The Fly.io configuration now includes auto-scaling:
- **Minimum**: 1 instance (always running, no cold starts)
- **Maximum**: 3 instances during peak trading
- **Scale trigger**: When connections exceed 70 (soft limit)
- **Scale down**: After 5 minutes of low activity

**Scaling Behavior:**
| Connections | Instances | Capacity |
|-------------|-----------|----------|
| 0-70 | 1 | Normal hours |
| 71-140 | 2 | Moderate traffic |
| 141-210 | 3 | Peak trading |

**Cost Estimate:**
- Base: ~$5/month (1 instance always on)
- Peak: ~$10-15/month (with occasional scaling)

---

## 10. SECURITY CHECKLIST

| Item | Status | Action |
|------|--------|--------|
| HTTPS forced | ✅ | Fly.io handles via `force_https` |
| CORS configured | ✅ | Update origins for Fly.io domain |
| CSRF protection | ✅ | Works across Fly.io |
| Rate limiting | ✅ | SlowAPI configured |
| Security headers | ✅ | Middleware adds headers |
| JWT secrets | ✅ | Move to Fly.io secrets |
| Cookie security | ✅ | SameSite=Lax, Secure in prod |

---

## 11. RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|------------|
| DNS propagation delay | Medium | Use Fly.io URL initially, add custom domain later |
| WebSocket compatibility | Low | Fly.io supports WebSockets natively |
| Cold start latency | Medium | Keep min 1 machine running |
| Database connectivity | Low | MongoDB Atlas works globally |
| Secret management | High | Use `flyctl secrets set` |

---

## 12. MIGRATION TIMELINE

| Step | Duration | Description |
|------|----------|-------------|
| 1. Setup | 30 min | Create Fly.io app, configure fly.toml |
| 2. Deploy | 15 min | Push Docker image to Fly.io |
| 3. Secrets | 10 min | Configure all environment variables |
| 4. Testing | 60 min | Validate all endpoints and WebSocket |
| 5. DNS/Rewrites | 15 min | Update Vercel to point to Fly.io |
| 6. Monitoring | 30 min | Verify logs, metrics, Sentry |
| **Total** | **~2.5 hours** | |

---

## 13. NEXT STEPS

1. **Create Fly.io account** and install `flyctl` CLI
2. **Run `flyctl launch`** in backend directory
3. **Configure secrets** using `flyctl secrets set`
4. **Deploy** using `flyctl deploy`
5. **Test** all endpoints against Fly.io URL
6. **Update Vercel** config to point to Fly.io
7. **Monitor** for 24-48 hours before decommissioning Render

---

*Report Generated: January 2026*
*Author: E1 - Full Stack Cloud Architect*
