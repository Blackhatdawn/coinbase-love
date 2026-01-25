# CryptoVault - Product Requirements Document

## Project Overview
- **Frontend**: React + Vite + TypeScript → Vercel (https://www.cryptovault.financial)
- **Backend**: FastAPI + Python + MongoDB Atlas → **Fly.io** (https://cryptovault-api.fly.dev)
- **Real-time**: Socket.IO + CoinCap WebSocket
- **Database**: MongoDB Atlas (cloud-hosted)
- **Cache**: Upstash Redis (cloud-hosted)
- **Admin**: Full admin control panel at /admin

---

## Latest Updates (January 25, 2026)

### Render → Fly.io Migration Complete ✅

#### What Was Done:
1. **Deep Investigation & Audit** of all frontend↔backend communication paths
2. **Created Fly.io Configuration**:
   - `fly.toml` - Production-ready Fly.io deployment config
   - `Dockerfile.fly` - Optimized multi-stage Docker build
   - `deploy-fly.sh` - Automated deployment script
   - `.env.fly.template` - Secrets template for Fly.io
3. **Updated Frontend Configuration**:
   - `vercel.json` - Rewrites now point to `cryptovault-api.fly.dev`
   - `.env.production` - Updated `VITE_API_BASE_URL`
4. **Updated Backend Configuration**:
   - `.env` - Added `PUBLIC_API_URL` and `PUBLIC_WS_URL` for Fly.io
   - Added Fly.io URL to `CORS_ORIGINS`
5. **Full Technical Report** at `/app/FLY_IO_MIGRATION_REPORT.md`

#### Key Configuration Changes:
| File | Change |
|------|--------|
| `vercel.json` | Rewrites point to `https://cryptovault-api.fly.dev` |
| `.env.production` | `VITE_API_BASE_URL=https://cryptovault-api.fly.dev` |
| `backend/.env` | Added `PUBLIC_API_URL`, `PUBLIC_WS_URL`, updated `CORS_ORIGINS` |
| `fly.toml` | New Fly.io deployment configuration |
| `Dockerfile.fly` | Optimized for Fly.io with multi-stage build |

---

## Architecture

### Communication Flow
```
Frontend (Vercel)
    ↓ HTTPS
Vercel Rewrites → /api/* 
    ↓
Backend (Fly.io) → FastAPI + Socket.IO
    ↓
MongoDB Atlas | Upstash Redis | CoinCap API
```

### Core Technologies
- **Frontend**: React 18, Vite, TypeScript, TailwindCSS, Shadcn UI
- **Backend**: FastAPI, Python 3.11, Motor (MongoDB), Socket.IO
- **Authentication**: JWT + HTTP-only cookies + CSRF protection
- **Real-time**: Socket.IO with WebSocket + polling fallback
- **Caching**: Upstash Redis REST API
- **Monitoring**: Sentry (error tracking), structured JSON logging

---

## What's Been Implemented

### Core Features ✅
- User authentication (signup, login, logout, email verification)
- 2FA authentication with TOTP
- Password reset flow
- Portfolio management
- Cryptocurrency price tracking (20+ coins)
- Trading interface with order management
- Wallet management (deposit, withdraw, P2P transfer)
- Price alerts
- Transaction history
- Admin dashboard with user management

### Infrastructure ✅
- Enterprise-grade CORS configuration
- Rate limiting (60 req/min per user)
- Request ID correlation for tracing
- Structured JSON logging in production
- Security headers middleware
- CSRF protection
- Health check endpoints
- WebSocket real-time updates

---

## Deployment Guide

### Backend (Fly.io)
```bash
# 1. Install flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login to Fly.io
flyctl auth login

# 3. Set secrets
flyctl secrets set \
  MONGO_URL="mongodb+srv://..." \
  JWT_SECRET="..." \
  CSRF_SECRET="..." \
  SENDGRID_API_KEY="..." \
  UPSTASH_REDIS_REST_URL="..." \
  UPSTASH_REDIS_REST_TOKEN="..." \
  COINCAP_API_KEY="..." \
  SENTRY_DSN="..."

# 4. Deploy
cd /app/backend
./deploy-fly.sh production
```

### Frontend (Vercel)
```bash
# Update Vercel environment variables:
VITE_API_BASE_URL=https://cryptovault-api.fly.dev

# Deploy
vercel --prod
```

---

## P0/P1/P2 Features

### P0 (Critical) ✅
- [x] User authentication
- [x] Cryptocurrency prices
- [x] Wallet management
- [x] Trading interface

### P1 (Important) ✅
- [x] Admin dashboard
- [x] Price alerts
- [x] 2FA authentication
- [x] Email notifications

### P2 (Nice to Have)
- [ ] Mobile app (React Native)
- [ ] Advanced charting
- [ ] Social trading features
- [ ] Multi-language support

---

## Next Tasks
1. **Deploy to Fly.io** - Run `./deploy-fly.sh` in backend directory
2. **Update Vercel env vars** - Set `VITE_API_BASE_URL` in Vercel dashboard
3. **Test production** - Validate all endpoints work on Fly.io
4. **Monitor** - Check Sentry and Fly.io logs for 24-48 hours
5. **Custom domain** - Add custom domain to Fly.io if needed

---

*Last Updated: January 25, 2026*
*Migration Report: /app/FLY_IO_MIGRATION_REPORT.md*
*Test Report: /app/test_reports/iteration_13.json*
