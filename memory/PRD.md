# CryptoVault - PRD & Investigation Report
## Date: 2026-02-06 (Session 3)

## Production URLs
- **Frontend**: https://coinbase-love.vercel.app (Vercel)
- **Backend**: https://cryptovault-api.onrender.com (Render)
- **Database**: MongoDB Atlas (cryptovaultcluster)

## Session 3 Fixes — Cross-Site Cookie, WebSocket, CORS

### Fix 1: Cookies — SameSite=None + Secure=True
- **Root cause**: `USE_CROSS_SITE_COOKIES=false` in backend .env
- Different domains (Vercel ↔ Render) = cross-site. Browser blocks cookies with SameSite=Lax.
- **Fixed**: Set `USE_CROSS_SITE_COOKIES=true`
- **Verified locally**: CSRF cookies, auth cookies (access_token, refresh_token), admin cookies all now have `SameSite=none; Secure`

### Fix 2: WebSocket — Socket.IO CORS + Transports
- Server already had `transports=['websocket', 'polling']`
- Client already had `transports: ['websocket', 'polling']`
- **Fixed**: Socket.IO `cors_allowed_origins` now includes Render public API URL
- **Verified locally**: Socket.IO handshake succeeds, price WebSocket streams data

### Fix 3: CORS — allow_credentials
- `CORSMiddleware` already had `allow_credentials=True`
- **Verified locally**: OPTIONS preflight returns `access-control-allow-credentials: true` for Vercel origin
- **Also fixed**: CSP `connect-src` now includes `coinbase-love.vercel.app`

### Additional Fixes (from previous sessions)
- CSRF middleware exempts `/api/admin/login` and `/api/admin/verify-otp`
- Socket.IO ASGI app properly exported as `app`
- Admin router double-mount removed
- `vercel.json` SPA rewrite fixed for all sub-routes
- Security headers (COEP/CORP) relaxed for cross-origin resources

## Local Verification Results (All Pass)
1. CSRF cookie: `SameSite=none` ✅
2. Auth cookie: `SameSite=none; Secure` ✅
3. CORS credentials: `allow-credentials: true` ✅
4. Socket.IO: Handshake succeeds ✅
5. Admin login: No CSRF block (returns 401 auth error) ✅
6. Login response: `access_token` present in body ✅

## Deployment Required
These fixes are in the container codebase. To go live:
1. Push code to GitHub → Render auto-deploys backend
2. Push code to GitHub → Vercel auto-deploys frontend
3. **Render env var**: Set `USE_CROSS_SITE_COOKIES=true` in Render dashboard

## Backlog
- P1: SendGrid for admin OTP emails
- P1: Redis for production token blacklisting
- P2: WebSocket reconnection resilience on production
