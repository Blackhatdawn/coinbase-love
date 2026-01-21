# CryptoVault - Enterprise-Grade Production Setup

## Overview

This document describes the production-ready, enterprise-grade configuration for CryptoVault's full-stack deployment with zero hardcoded secrets and environment-driven configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Vercel (Frontend + CDN)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React/Vite Frontend                                     │   │
│  │  - Relative API paths (/api/*)                           │   │
│  │  - Vercel rewrites proxy to backend                      │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────┬────────────────────────────────────────────┘
                       │ Vercel Rewrites
                       │ (vercel.json)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Production Backend (Render/Railway)                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Backend (Python)                                │   │
│  │  - Dynamic CORS from environment                         │   │
│  │  - pydantic-settings for config validation              │   │
│  │  - Startup environment validation                       │   │
│  │  - Health checks & monitoring                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration System

### Backend Configuration (pydantic-settings)

The backend uses **pydantic-settings** for production-grade configuration:

```python
from config import settings, validate_startup_environment

# Automatic startup validation
@app.on_event("startup")
async def startup():
    validate_startup_environment()  # Crash-safe validation
```

**Key Features:**
- ✅ Type validation for all environment variables
- ✅ Secure handling of secrets (SecretStr)
- ✅ Environment-specific defaults
- ✅ Startup crash-safety (fail fast if misconfigured)
- ✅ Zero hardcoding of sensitive values

### Environment Variables

#### Required (Production)

```bash
# Security
JWT_SECRET=<generate-secure-random-string>
CSRF_SECRET=<generate-secure-random-string>

# Database
DATABASE_URL=mongodb+srv://user:pass@cluster.mongodb.net/cryptovault

# Cache
REDIS_URL=redis://user:pass@redis.example.com:6379/0

# CORS (comma-separated)
CORS_ORIGINS=https://cryptovault.com,https://app.cryptovault.com

# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
```

#### Optional (Recommended)

```bash
# Error Tracking
SENTRY_DSN=https://key@sentry.io/project-id
SENTRY_ENVIRONMENT=production

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=<sendgrid-api-key>
EMAIL_FROM=noreply@cryptovault.com

# External Services
CRYPTO_API_KEY=<api-key>
ETH_RPC_URL=https://mainnet.infura.io/v3/<key>

# Feature Flags
FEATURE_2FA_ENABLED=true
FEATURE_TRADING_ENABLED=true
FEATURE_STAKING_ENABLED=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Development Setup

### Prerequisites

```bash
# Backend dependencies
pip install -r backend/requirements.txt

# Frontend dependencies
cd frontend && yarn install
```

### Local Development

**Terminal 1 - Backend:**
```bash
# Set development environment variables
export ENVIRONMENT=development
export CORS_ORIGINS=http://localhost:3000,http://localhost:5173
export JWT_SECRET=dev-key-change-in-production
export CSRF_SECRET=dev-key-change-in-production

# Start backend (auto-reload with reload_dirs)
python run_server.py
# Backend runs on http://localhost:8001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn dev
# Frontend runs on http://localhost:3000
# Automatically proxies /api/* to http://localhost:8001
```

### Configuration Validation

Test configuration at startup:
```bash
python -m backend.config
```

This displays:
- ✅ Application settings
- ✅ Server configuration
- ✅ Database & Cache connectivity
- ✅ Security settings
- ✅ Feature flags
- ✅ Monitoring status

## Production Deployment

### Render.com (Recommended)

1. **Create Backend Service**
   ```
   Build Command: pip install -r backend/requirements.txt
   Start Command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.server:socket_app --bind 0.0.0.0:$PORT
   ```

2. **Set Environment Variables** (in Render dashboard)
   ```
   ENVIRONMENT=production
   JWT_SECRET=<generate-secure-value>
   CSRF_SECRET=<generate-secure-value>
   DATABASE_URL=<mongodb-connection-string>
   REDIS_URL=<redis-connection-string>
   CORS_ORIGINS=https://cryptovault.com
   SENTRY_DSN=<sentry-dsn>
   ```

3. **Note the Backend URL** (e.g., `https://cryptovault-api.onrender.com`)

### Vercel (Frontend)

1. **Connect Git Repository**
   ```
   Framework: Vite
   Build Command: cd frontend && yarn install && yarn build
   Output Directory: frontend/dist
   ```

2. **Set Environment Variables**
   ```
   VITE_API_BASE_URL=  (leave empty - uses relative paths via rewrites)
   ```

3. **Update vercel.json**
   Replace `https://cryptovault-api.onrender.com` with your backend URL:
   ```json
   {
     "source": "/api/:path*",
     "destination": "https://<your-backend-url>/api/:path*"
   }
   ```

## Reverse Proxy Architecture

### How It Works

**Development (Vite Dev Server):**
```
Browser Request: GET /api/crypto/list
           ↓
Vite Dev Server (port 3000)
           ↓
Configured Proxy
           ↓
FastAPI Backend (port 8001)
```

**Production (Vercel Rewrites):**
```
Browser Request: GET /api/crypto/list
           ↓
Vercel Edge Network
           ↓
Rewrite Rule in vercel.json
           ↓
Production Backend (Render/Railway)
```

### Frontend API Client

The frontend API client automatically:
1. Uses **relative paths** in development (`/api/*`)
2. Falls back to **absolute URLs** from `VITE_API_BASE_URL` if set
3. Loads **runtime config** from `/api/config` endpoint

```typescript
// frontend/src/lib/apiClient.ts
const resolveBaseUrl = () => resolveApiBaseUrl();
const BASE_URL = resolveBaseUrl();  // Empty string = relative paths

// All requests use: GET /api/crypto/list
// Proxy or rewrite sends to: https://backend.example.com/api/crypto/list
```

## Security Features

### Environment Validation (Crash-Safe)

```python
from config import validate_startup_environment

@app.on_event("startup")
async def startup():
    # Validates all critical env vars before server starts
    validate_startup_environment()
    # If validation fails, server crashes immediately (fail-fast)
```

### Dynamic CORS

```python
# From config.py with environment override
cors_origins = settings.get_cors_origins_list()

# Backend verifies origin at request time
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Dynamic from CORS_ORIGINS env
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
```

### CSRF Protection

```python
# HTTP-only cookies with SameSite=Lax
response.set_cookie(
    key="csrf_token",
    value=csrf_token,
    httponly=True,      # Prevent XSS access
    secure=True,        # HTTPS only (production)
    samesite="lax",     # CSRF protection
    max_age=3600,       # 1 hour rotation
)
```

### Secure Secret Handling

```python
from pydantic import SecretStr

class Settings(BaseSettings):
    jwt_secret: SecretStr = Field(...)
    csrf_secret: SecretStr = Field(...)
    
# Access: settings.jwt_secret.get_secret_value()
# Hides value in logs and repr()
```

## Monitoring & Health Checks

### Health Check Endpoints

```bash
# Simple ping (no dependencies)
GET /ping

# Full health check
GET /health
# Returns: { "status": "healthy", "database": "connected", ... }

# API documentation
GET /api/docs      # Swagger UI
GET /api/redoc     # ReDoc
GET /api/openapi.json  # OpenAPI spec
```

### Rate Limiting

```bash
# Headers show current limit status
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1234567890
```

### Sentry Error Tracking

If `SENTRY_DSN` is configured:
```python
# Automatic error tracking
# - Unhandled exceptions logged
# - Request IDs for tracing
# - Environment segmentation
# - Sample-based tracing (0.1 by default)
```

## Debugging Production Issues

### Check Backend Connectivity

```bash
# From Vercel/frontend
curl https://cryptovault-api.onrender.com/ping
# Should return: { "status": "ok", "message": "pong" }

# Check health
curl https://cryptovault-api.onrender.com/health
# Should return detailed health status
```

### Check Configuration

```bash
# In backend service logs
# Look for: "✅ Environment Validated"
# Should show all critical settings loaded

# If missing:
# "❌ STARTUP FAILED: Critical environment variables not configured"
```

### WebSocket Issues

If Socket.IO isn't connecting:
```bash
# Check WebSocket proxy in Vercel
curl https://cryptovault.com/socket.io/
# Should proxies to backend WebSocket
```

## Zero Hardcoding Checklist

- ✅ Backend URLs are environment variables (Render/Railway configurable)
- ✅ Frontend uses relative paths (Vercel rewrites handle routing)
- ✅ CORS origins configurable via `CORS_ORIGINS` env var
- ✅ API keys/secrets use `SecretStr` from pydantic
- ✅ Database URLs from environment only
- ✅ Feature flags configurable at deployment
- ✅ Rate limits configurable per environment
- ✅ Error tracking DSN optional, environment-driven
- ✅ Email SMTP credentials from environment
- ✅ No API URLs in frontend code (runtime discovery)

## Performance Optimization

### Frontend Build

- ✅ Code splitting per page/component
- ✅ Vendor chunks separated
- ✅ Automatic tree-shaking
- ✅ Terser minification
- ✅ Source maps for error tracking

### Backend Performance

- ✅ Connection pooling (MongoDB, Redis)
- ✅ Async/await throughout
- ✅ GZip compression
- ✅ Request timeouts (30s default)
- ✅ Rate limiting
- ✅ Health checks for load balancer

### Caching Strategy

```
Assets (.js, .css):     1 week (stale-while-revalidate)
Images:                 1 day
Fonts:                  30 days (immutable)
HTML:                   No cache (always fresh)
API responses:          Redis with TTL
```

## Troubleshooting

### Backend not responding to Vercel

1. Check backend is running: `curl https://backend-url/health`
2. Verify `CORS_ORIGINS` includes Vercel domain
3. Check `vercel.json` rewrites point to correct backend URL
4. Review backend logs for errors

### CORS errors in browser console

1. Frontend domain must be in `CORS_ORIGINS`
2. Credentials setting must match (`allow_credentials=true`)
3. Wildcard `*` can't be used with credentials
4. Check Content-Security-Policy headers

### WebSocket connection failed

1. WebSocket proxy in `vercel.json` must include `/socket.io/:path*`
2. Backend must have Socket.IO mounted
3. Check browser DevTools → Network → WS tab

### Rate limiting issues

1. Adjust `RATE_LIMIT_REQUESTS_PER_MINUTE` env var
2. Check `X-RateLimit-*` headers in response
3. Rate limiting is per-user (from token) or per-IP

## Additional Resources

- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Pydantic Settings:** https://docs.pydantic.dev/latest/api/pydantic_settings/
- **Vercel Rewrites:** https://vercel.com/docs/concepts/projects/project-configuration#rewrites
- **Render.com Deployment:** https://render.com/docs
- **Socket.IO:** https://socket.io/docs/v4/

## Support

For deployment issues:
1. Check logs in Render/Vercel dashboard
2. Verify environment variables are set
3. Run configuration test locally: `python -m backend.config`
4. Check `/health` endpoint on backend
5. Review error tracking in Sentry (if configured)
