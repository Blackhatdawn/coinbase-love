# CryptoVault - Product Requirements Document

## Project Overview
- **Application**: CryptoVault - Enterprise Cryptocurrency Trading Platform
- **Frontend**: React + Vite + TypeScript → Vercel (https://www.cryptovault.financial)
- **Backend**: FastAPI + Python + MongoDB Atlas → **Fly.io** (https://coinbase-love.fly.dev)
- **Real-time**: Socket.IO + CoinCap WebSocket
- **Database**: MongoDB Atlas (cloud-hosted)
- **Cache**: Upstash Redis (cloud-hosted)

---

## Latest Updates (January 25, 2026)

### Complete Fly.io Migration ✅

#### What Was Done:
1. **Removed ALL Render References**
   - Deleted `render.yaml`
   - Updated CSP headers → fly.dev domains
   - Updated Sentry trace propagation → fly.dev
   - Updated fallback URLs → coinbase-love.fly.dev
   - Cleaned up legacy documentation

2. **Enterprise Fly.io Configuration**
   - `fly.toml` - Production config for `coinbase-love` app
   - `Dockerfile.fly` - Optimized multi-stage build
   - Auto-scaling: 1-3 instances based on connections
   - Health checks at `/health`

3. **Version Sync System** (Prevents Frontend-Backend Mismatches)
   - `GET /api/version` - Server version info
   - `GET /api/version/check` - Client compatibility check
   - `GET /api/version/features` - Feature flags
   - `GET /api/version/deployment` - Fly.io deployment info
   - Frontend hook: `useVersionSync()` - Automatic sync

4. **Production Environment**
   - All secrets configured for Fly.io
   - CORS includes Fly.io domains
   - CSP headers updated for Fly.io
   - Firebase credentials configured

---

## Architecture

### Communication Flow
```
Frontend (Vercel) ─── HTTPS ───> Vercel Rewrites
                                      │
                                      ▼
                              Fly.io Backend
                              (coinbase-love.fly.dev)
                                      │
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
              MongoDB Atlas    Upstash Redis    CoinCap API
```

### Version Sync Flow
```
Frontend (on load/tab focus)
         │
         ▼
GET /api/version/check?client_version=1.0.0
         │
         ▼
Backend validates compatibility
         │
         ├── Compatible ──> Continue
         │
         └── Incompatible ──> Show refresh toast
```

---

## Deployment

### Backend (Fly.io)

**Step 1: Set Secrets**
```bash
flyctl secrets set \
  MONGO_URL="mongodb+srv://..." \
  JWT_SECRET="..." \
  CSRF_SECRET="..." \
  SENDGRID_API_KEY="..." \
  COINCAP_API_KEY="..." \
  NOWPAYMENTS_API_KEY="..." \
  NOWPAYMENTS_IPN_SECRET="..." \
  UPSTASH_REDIS_REST_URL="..." \
  UPSTASH_REDIS_REST_TOKEN="..." \
  SENTRY_DSN="..." \
  CORS_ORIGINS='["https://www.cryptovault.financial","https://cryptovault.financial","https://coinbase-love.fly.dev"]' \
  --app coinbase-love
```

**Step 2: Deploy**
```bash
cd /app/backend
flyctl deploy --app coinbase-love
```

**Step 3: Verify**
```bash
curl https://coinbase-love.fly.dev/health
curl https://coinbase-love.fly.dev/api/version
```

### Frontend (Vercel)
```bash
# Environment Variables in Vercel Dashboard:
VITE_API_BASE_URL=https://coinbase-love.fly.dev
```

---

## API Endpoints

### Core
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/health` | GET | API health with DB status |
| `/ping` | GET | Keep-alive ping |

### Version (NEW)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/version` | GET | Server version info |
| `/api/version/check` | GET | Compatibility check |
| `/api/version/features` | GET | Feature flags |
| `/api/version/deployment` | GET | Fly.io deployment info |

### Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fly/status` | GET | Fly.io machine info |
| `/api/fly/region` | GET | Current region |
| `/api/optimization/metrics` | GET | Cache & security stats |

---

## Features

### Core Features ✅
- [x] User authentication (JWT + cookies)
- [x] 2FA with TOTP
- [x] Cryptocurrency trading
- [x] Portfolio management
- [x] Wallet operations
- [x] P2P transfers
- [x] Price alerts
- [x] Admin dashboard

### Infrastructure ✅
- [x] Fly.io deployment
- [x] Auto-scaling (1-3 instances)
- [x] Version sync system
- [x] Feature flags
- [x] Redis caching
- [x] Sentry monitoring
- [x] Rate limiting
- [x] CORS + CSP security

---

## Test Reports
- Latest: `/app/test_reports/iteration_15.json`
- Status: 100% pass rate (9/9 tests)

---

*Last Updated: January 25, 2026*
*Platform: Fly.io (coinbase-love)*
