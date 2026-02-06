# CryptoVault - PRD & Investigation Report
## Date: 2026-02-06 (Updated)

## Production URLs
- **Frontend**: https://coinbase-love.vercel.app (Vercel)
- **Backend**: https://cryptovault-api.onrender.com (Render)
- **Database**: MongoDB Atlas (cryptovaultcluster)

## Architecture
- **Frontend**: React + Vite + TypeScript + Tailwind + shadcn/ui
- **Backend**: FastAPI + Python 3.11 + Motor (async MongoDB)
- **Database**: MongoDB Atlas
- **Auth**: JWT with httpOnly cookies + OTP for admin
- **WebSocket**: Socket.IO (python-socketio + ASGI) + Native WS for prices
- **Deployment**: Render (backend), Vercel (frontend)

## Session 1 Fixes (Container/Dev Environment)

### P0 - Service Crashers (Fixed)
1. Missing Python deps: pydantic-settings, pyotp, redis, python-socketio, psutil, slowapi
2. Invalid `packageManager: "pnpm@9.0.0"` in root & frontend package.json
3. Socket.IO ASGI app not exported (`app = socket_app`)
4. `PUBLIC_WS_URL` pointed to dead Fly.io (`wss://coinbase-love.fly.dev`)
5. `send_to_user` method missing on SocketIOManager

### P0 - Frontend-Backend Sync (Fixed)
6. Admin API endpoint mismatches (frontend vs backend paths)
7. AuthContext missing `token` field for WebSocket auth
8. Admin fetch used relative URLs without CSRF token
9. CSRF middleware blocked `/api/admin/login` and `/api/admin/verify-otp`
10. Admin router double-mounted (duplicate at `/api/api/admin/*`)
11. Runtime config pushed Render URL to dev frontend (CORS blocked)
12. WebSocket price hook had infinite reconnection loop
13. Vite proxy missing `/ws` path for native WebSocket
14. CSP headers referenced dead Fly.io URLs
15. COEP/CORP headers too strict (blocked cross-origin crypto images)

## Session 2 Findings (Production Review)

### Render Backend (LIVE)
- Health: healthy, DB connected
- CORS: Properly allows `coinbase-love.vercel.app`
- Crypto API: 20 cryptos loaded
- Config endpoint: Returns correct production config

### Render Backend Issues (Need Redeployment)
- **CSRF blocks admin login** — `/api/admin/login` not in CSRF skip paths
- **Socket.IO returns 404** — `socket_app` not exported as `app`
- **CSP references old Fly.io** in `connect-src`
- **COEP/CORP too strict** — blocks cross-origin resources

### Vercel Frontend Issues (Need Redeployment)
- **ALL sub-routes 404** — SPA catch-all regex pattern broken in vercel.json
- **Build uses pnpm** but `packageManager` field removed (changed to `yarn`)
- **Missing `/ws` rewrite** for native WebSocket price streaming
- **CORP header `same-origin`** blocks cross-origin resources

## Changes Made in This Session

### vercel.json (Critical for Vercel)
- Simplified SPA rewrite: `"/:path*" → "/index.html"` (was broken regex)
- Changed build/install commands from `pnpm` to `yarn`
- Added `/ws/:path*` rewrite for price WebSocket
- Added `coincap.io` to CSP connect-src
- Fixed COEP: `unsafe-none`, CORP: `cross-origin`, COOP: `same-origin-allow-popups`

### Backend Fixes (Need Render Redeploy)
- CSRF skip: Added `/api/admin/login` and `/api/admin/verify-otp`
- Socket.IO: `app = socket_app` for proper ASGI mount
- Removed admin router double-mount
- CSP updated from Fly.io to Render URLs
- DB pool uses .env config values

### Frontend Fixes (Need Vercel Redeploy)
- AdminLogin.tsx: Uses api client with CSRF handling
- AdminDashboard.tsx: Includes CSRF token + base URL
- runtimeConfig.ts: Prefers relative API in non-production environments
- usePriceWebSocket.ts: Fixed infinite reconnection loop
- AuthContext.tsx: Exposes access_token for WebSocket auth
- apiClient.ts: All admin endpoints aligned with backend routes

## Deployment Checklist

### To Deploy to Render:
1. Push updated backend code (server.py, middleware/security.py, socketio_server.py)
2. Ensure Render env has: `CORS_ORIGINS` including `coinbase-love.vercel.app`
3. Verify `PUBLIC_WS_URL=wss://cryptovault-api.onrender.com`

### To Deploy to Vercel:
1. Push updated frontend code + vercel.json
2. Set Vercel env: `VITE_API_BASE_URL=https://cryptovault-api.onrender.com`
3. Trigger redeploy

## Backlog
- P1: SendGrid integration for admin OTP emails
- P1: Redis cache for production token blacklisting
- P2: E2E admin dashboard test with real credentials
- P3: Rate limiting fine-tuning
