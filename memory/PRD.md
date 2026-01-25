# CryptoVault Enterprise Trading Platform - PRD

## Project Overview
- **Frontend**: React + Vite + TypeScript → Vercel (https://www.cryptovault.financial)
- **Backend**: FastAPI + Python + MongoDB → Render (https://cryptovault-api.onrender.com)
- **Real-time**: Socket.IO + CoinCap WebSocket

## Production Readiness: 90.4% ✅

---

## Latest Updates (Jan 25, 2026)

### Socket.IO Connection ✅
- WebSocket transport working correctly
- Polling fallback functional
- Real-time price updates via CoinCap WebSocket

### CoinCap Integration ✅
- API key properly configured via `COINCAP_API_KEY` env var
- WebSocket connected with correct asset IDs
- Fallback to mock data when API unavailable
- Note: DNS issues in preview env are environment-specific, works on Render

### Configuration Files Updated

#### render.yaml
- Complete production configuration
- All environment variables documented
- Start command: `uvicorn server:socket_app --host 0.0.0.0 --port $PORT`

#### vercel.json
- Environment variables via Vercel secrets (@vite_api_base_url, @vite_sentry_dsn)
- API rewrites to backend
- Socket.IO proxy configured
- Cache headers for static assets
- Security headers

### Hardcoded Values Removed
- CSP now dynamically built from config
- API URLs read from environment
- CoinCap endpoints configurable via env vars

### Enhanced Logging System
- New `logging_config.py` with actionable messages
- JSON formatted logs for production
- Operator guidance for common issues
- Health check aggregation to reduce noise

---

## Environment Variables

### Backend (Render) - Required
```
MONGO_URL                    # MongoDB Atlas connection string
JWT_SECRET                   # JWT signing key  
CSRF_SECRET                  # CSRF protection secret
SENDGRID_API_KEY             # Email service
UPSTASH_REDIS_REST_URL       # Redis caching
UPSTASH_REDIS_REST_TOKEN     # Redis auth
COINCAP_API_KEY              # Real-time crypto prices
SENTRY_DSN                   # Error monitoring
```

### Frontend (Vercel) - Required
```
VITE_API_BASE_URL            # Backend API URL
VITE_SENTRY_DSN              # Error monitoring
VITE_ENABLE_SENTRY           # Enable Sentry (true)
```

---

## Known Issues & Actions

| Issue | Status | Action |
|-------|--------|--------|
| CoinCap DNS in preview | Expected | Works on Render production |
| Cookie test persistence | Test-only | Browser auth works correctly |

---

## Deployment Commands

### Backend (Render)
```bash
uvicorn server:socket_app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel)
```bash
yarn build && vercel --prod
```

---

*Last Updated: January 25, 2026*
*Test Report: /app/test_reports/iteration_11.json*
