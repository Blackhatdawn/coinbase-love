# CryptoVault - PRD & Investigation Report
## Date: 2026-02-06

## Original Problem Statement
Deep investigate CryptoVault's entire codespace. Ensure frontend and backend are in perfect enterprise-grade production sync. Optimized CORS and WebSocket connection. Optimized production Database system. Fix admin dashboard loading issue. Full stack reads env from backend server hosted on Render.

## Architecture
- **Frontend**: React + Vite + TypeScript + Tailwind + shadcn/ui
- **Backend**: FastAPI + Python 3.11 + Motor (async MongoDB)
- **Database**: MongoDB (Atlas for prod, local for dev)
- **Auth**: JWT with httpOnly cookies + OTP for admin
- **WebSocket**: Socket.IO (python-socketio + ASGI)
- **Deployment**: Render (backend), Vercel (frontend)

## Critical Issues Found & Fixed

### P0 - Service Crashers
1. **Missing `pydantic-settings`** - Backend failed to start
2. **Missing `pyotp`** - Auth module crash
3. **Missing `redis`** - Blacklist module crash
4. **Missing `python-socketio`** - Socket.IO server crash
5. **Missing `psutil`** - Monitoring router crash
6. **Invalid `packageManager: "pnpm@9.0.0"`** in root & frontend package.json - Frontend couldn't start

### P0 - WebSocket Broken
7. **Socket.IO ASGI app not exported** - `uvicorn server:app` loaded raw FastAPI, not Socket.IO-wrapped app. Fixed by reassigning `app = socket_app`
8. **`PUBLIC_WS_URL` pointed to dead Fly.io** (`wss://coinbase-love.fly.dev`) - Changed to `wss://cryptovault-api.onrender.com`
9. **`send_to_user` method missing** on SocketIOManager - Admin router called it but only `broadcast_to_user` existed. Added alias.

### P1 - Frontend-Backend Sync
10. **Admin API endpoint mismatches** - Frontend called `/api/admin/stats` but backend has `/api/admin/dashboard/stats`. Realigned all admin API paths in `apiClient.ts`
11. **AuthContext missing `token` field** - SocketContext destructured `token` from `useAuth()` but it didn't exist. Added token storage from login response.
12. **Admin fetch used relative URLs** - `fetch('/api/admin...')` doesn't work in production. Added `VITE_API_BASE_URL` prefix.
13. **Vite dev server bound to 127.0.0.1** - Changed to `0.0.0.0` for container access
14. **Vite `allowedHosts` missing emergent preview domain** - Added `.preview.emergentagent.com`

### P1 - Database & CORS
15. **DB pool size hardcoded** - server.py ignored `.env` settings (MONGO_MAX_POOL_SIZE). Fixed to use config values.
16. **CORS origins missing preview URL** - Added emergent preview domain to allowed origins.
17. **Missing `__init__.py`** in middleware directory

## What's Implemented (Verified Working)
- Backend health check: healthy, database connected
- 20 cryptocurrencies loaded via /api/crypto
- Admin login page loads with OTP-based 2FA
- Socket.IO handshake succeeds with WebSocket upgrade
- Vite proxy correctly forwards /api/* to backend
- CORS properly configured for all environments
- All admin API endpoints properly secured (401 for unauth)

## Backlog / Future
- P1: SendGrid integration for admin OTP emails (currently mock)
- P1: Redis cache for production (currently using in-memory)
- P2: WebSocket reconnection resilience testing
- P2: Admin dashboard full E2E test with real admin credentials
- P3: Rate limiting fine-tuning for production load
