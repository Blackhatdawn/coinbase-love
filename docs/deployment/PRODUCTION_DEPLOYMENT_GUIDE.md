# CryptoVault Production Deployment Guide

This guide provides comprehensive instructions for deploying CryptoVault to production with Vercel (frontend) and Render (backend).

## 🎯 Quick Start Summary

| Component | Platform | URL | Status |
|-----------|----------|-----|--------|
| Frontend | Vercel | `https://coinbase-love.vercel.app` | 🟡 Production Candidate |
| Backend | Render | `https://coinbase-love.fly.dev` | 🟡 Production Candidate |

## 📋 Pre-Deployment Checklist

### Backend (Render) - Required Secrets

Set these in the Render Dashboard under **Environment** section:

```bash
# CRITICAL: Database
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/cryptovault

# CRITICAL: Authentication
JWT_SECRET=your-random-256-bit-secret-here
CSRF_SECRET=your-csrf-secret-different-from-jwt

# Email (SendGrid)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# External Services
COINCAP_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
TELEGRAM_BOT_TOKEN=1234567890:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
ADMIN_TELEGRAM_CHAT_ID=123456789

# Payments (NOWPayments)
NOWPAYMENTS_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
NOWPAYMENTS_IPN_SECRET=your-ipn-secret-here

# Cache (Upstash Redis)
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-redis-token

# Monitoring (Sentry)
SENTRY_DSN=https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@o123456.ingest.sentry.io/1234567
```

### Frontend (Vercel) - Environment Variables

Set these in Vercel Dashboard under **Settings > Environment Variables**:

```bash
VITE_API_BASE_URL=""  # Empty = use relative paths (Vercel rewrites)
VITE_SENTRY_DSN=https://xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@o123456.ingest.sentry.io/1234567
```

## 🚀 Deployment Steps

### 1. Deploy Backend to Render

```bash
# Option A: Git Push (Auto-deploy)
git push origin main

# Option B: Manual Deploy
# 1. Go to Render Dashboard
# 2. Click "New" → "Blueprint"
# 3. Connect your GitHub repo
# 4. Select `render.yaml`
# 5. Click "Apply"
```

**Verify Backend Deployment:**
```bash
curl https://coinbase-love.fly.dev/health
curl https://coinbase-love.fly.dev/api/config
```

Expected response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2026-02-10T14:30:00Z"
}
```

### 2. Deploy Frontend to Vercel

```bash
# Option A: Vercel CLI
vercel --prod

# Option B: Git Integration
# 1. Push to main branch
# 2. Vercel auto-deploys

# Option C: Manual
# 1. Go to vercel.com
# 2. Import GitHub repo
# 3. Select "Vite" framework
# 4. Root Directory: frontend
# 5. Set Install Command: pnpm install --frozen-lockfile
# 6. Set Build Command: pnpm run build:prod
# 7. Set Output Directory: dist
# 8. Deploy
```

> ⚠️ Keep a single source of truth for build settings: if `vercel.json` defines install/build/output, clear those fields in the Vercel dashboard to avoid conflicting overrides.

**Verify Frontend Deployment:**
1. Visit `https://coinbase-love.vercel.app`
2. Check browser console for errors
3. Test login flow
4. Verify WebSocket connection

## 📁 Updated Configuration Files

### Vercel Configuration (`vercel.json`)
- ✅ Production build with `pnpm run build:prod`
- ✅ Frozen lockfile for reproducible builds
- ✅ Service Worker routes for PWA
- ✅ Optimized CSP headers
- ✅ Long-term asset caching
- ✅ Security headers (HSTS, CSP, X-Frame-Options)

### Render Configuration (`render.yaml`)
- ✅ Enhanced build with pip upgrade and validation
- ✅ Optimized uvicorn with uvloop and proxy headers
- ✅ Health checks configured
- ✅ Environment variables structure
- ✅ Auto-deploy enabled
- ✅ Disk storage for logs

### Frontend Package.json
- ✅ `build:prod` - Production build
- ✅ `build:analyze` - Bundle analysis
- ✅ `lint:fix` - Auto-fix linting
- ✅ `type-check` - TypeScript validation
- ✅ `clean` - Clean dist folder

## 🔒 Security Hardening

### CORS Configuration
Backend (`render.yaml`):
```yaml
CORS_ORIGINS: '["https://www.cryptovault.financial","https://cryptovault.financial","https://coinbase-love.vercel.app"]'
USE_CROSS_SITE_COOKIES: "true"
COOKIE_SECURE: "true"
COOKIE_SAMESITE: "lax"
```

### CSP Headers (Vercel)
```http
Content-Security-Policy: default-src 'self'; 
  script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; 
  style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; 
  connect-src 'self' https://coinbase-love.fly.dev wss://coinbase-love.fly.dev;
  frame-ancestors 'none';
  upgrade-insecure-requests;
```

## 🏥 Health Checks & Monitoring

### Backend Health Endpoints
- `GET /health` - Overall health
- `GET /ping` - Simple ping
- `GET /api/health` - Detailed health with DB status

### Frontend Health Checks
- Runtime config loads from `/api/config`
- Service Worker registration
- Sentry error tracking

### Monitoring Setup
1. **Sentry** - Error tracking (already configured)
2. **Vercel Analytics** - Web vitals (already enabled)
3. **Render Metrics** - Server metrics in dashboard

## 🔄 Continuous Deployment

### Git Workflow
```bash
# Development
feature-branch → pull request → review → merge to main

# Deployment
main branch → auto-deploy to production
```

### Rollback Procedure
```bash
# Backend (Render)
1. Go to Render Dashboard
2. Select service
3. Click "Manual Deploy" → "Deploy latest commit" or choose specific commit

# Frontend (Vercel)
1. Go to Vercel Dashboard
2. Select project
3. Go to "Deployments"
4. Click on previous deployment
5. Click "Promote to Production"
```

## 📊 Performance Optimization

### Build Optimizations Applied
1. **Code Splitting** - Manual chunks in `vite.config.ts`
2. **Asset Optimization** - Hashed filenames, immutable caching
3. **Service Worker** - Offline support with multi-cache strategy
4. **Image Optimization** - Lazy loading, WebP/AVIF support
5. **Bundle Analysis** - `pnpm run build:analyze`

### Backend Optimizations
1. **Uvicorn wrapper** (`start_server.py`) with asyncio default, h11 HTTP, configurable workers
2. **Redis Caching** - Upstash for rate limiting and data caching
3. **Connection Pooling** - MongoDB with max 10 connections
4. **Rate Limiting** - 60 requests/minute per IP

## 🐛 Troubleshooting

### Common Issues

**1. CORS Errors**
```bash
# Symptom: "CORS policy" errors in browser
# Fix: Ensure CORS_ORIGINS includes exact Vercel URL
# Check: backend logs for rejected origins
```

**2. Cookie Not Sent**
```bash
# Symptom: 401 errors despite login
# Check: Cookie attributes in browser DevTools
# Fix: Ensure USE_CROSS_SITE_COOKIES=true and COOKIE_SECURE=true
```

**3. Socket.IO Connection Fails**
```bash
# Symptom: WebSocket errors
# Check: PUBLIC_SOCKET_IO_PATH has trailing slash
# Verify: /socket.io/ route in vercel.json rewrites
```

**4. Build Fails**
```bash
# Symptom: pnpm install fails on Vercel
# Fix: Ensure pnpm-lock.yaml is committed to git
# Check: Node version compatibility (use 18.x or 20.x)
```

### Debug Commands
```bash
# Check backend health
curl https://coinbase-love.fly.dev/health | jq .

# Check runtime config
curl https://coinbase-love.fly.dev/api/config | jq .

# Test CORS preflight
curl -X OPTIONS -H "Origin: https://coinbase-love.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  https://coinbase-love.fly.dev/api/auth/login

# Check response headers
curl -I https://coinbase-love.fly.dev/api/config
```

## 🎯 Production Checklist

Before announcing production readiness:

### Backend
- [ ] All secrets set in Render dashboard
- [ ] Database connected and migrations run
- [ ] Health endpoint returns 200
- [ ] Rate limiting active (test with 61 rapid requests)
- [ ] Email service configured (or set to mock)
- [ ] Sentry receiving errors
- [ ] Logs visible in Render dashboard

### Frontend
- [ ] Build succeeds with no errors
- [ ] All assets load (check Network tab)
- [ ] Login/logout works
- [ ] API calls succeed
- [ ] WebSocket connects
- [ ] Service Worker registers
- [ ] CSP headers valid (no console warnings)
- [ ] Sentry receiving errors

### Integration
- [ ] Frontend can call backend API
- [ ] Cookies set correctly (httpOnly, Secure, SameSite)
- [ ] CSRF tokens working
- [ ] Socket.IO real-time updates
- [ ] File uploads work (if applicable)

## 📞 Support

If deployment fails:
1. Check logs in Render/Vercel dashboard
2. Verify all environment variables are set
3. Test backend endpoints directly with curl
4. Check browser console for frontend errors
5. Review Sentry for error reports

## 📚 Related Documentation

- `FRONTEND_HARDENING_OPTIMIZATION_REVIEW.md` - Detailed security review
- `DEEP_INVESTIGATION_VERIFICATION_REPORT.md` - Integration verification
- `backend/config.py` - Configuration settings
- `frontend/vite.config.ts` - Build configuration

---

**Last Updated:** 2026-02-10  
**Version:** 2.0.0  
**Status:** Production Candidate (verify checklist before go-live) 🟡
