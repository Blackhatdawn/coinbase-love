# Network Error Fix & Configuration Guide

## 🐛 Issues Fixed

**Errors**:
```
NetworkError when attempting to fetch resource.
[HealthCheck] ⚠️ Health check experiencing issues after 5 failures. 
Will continue with extended backoff (32.0 min).
```

## 🔍 Root Cause

The frontend was trying to connect to the production API URL (`https://cryptovault-api.onrender.com`) but:
1. **In Development**: Should use local backend (http://localhost:8001) via Vite proxy
2. **Production Backend**: May be sleeping on free hosting (15min idle timeout on Render)
3. **Missing Configuration**: No environment files for development vs production

## ✅ Fixes Implemented

### 1. Created Environment Files

#### `.env.development` (Local Development)
```bash
# Uses Vite proxy to forward to local backend
VITE_API_BASE_URL=

# Backend runs on: http://localhost:8001
# Frontend runs on: http://localhost:3000
# Vite proxy: /api/* → http://localhost:8001/api/*
```

#### `.env.production` (Production Build)
```bash
# Points to deployed backend
VITE_API_BASE_URL=https://cryptovault-api.onrender.com
```

#### `.env.example` (Template)
```bash
# Copy to .env.local and configure
VITE_API_BASE_URL=
VITE_APP_NAME=CryptoVault
VITE_APP_VERSION=1.0.0
```

### 2. Enhanced Health Check Diagnostics

**Before**: Generic error messages
```
❌ Health check failed: NETWORK Unknown error
```

**After**: Helpful diagnostic information
```
❌ Health check failed (1/5): [NETWORK] Failed to fetch. Next retry in 4.0 minutes
💡 Tips for local development:
  - Make sure backend is running: python run_server.py
  - Check backend URL: (using Vite proxy)
  - Backend should be on http://localhost:8001
  - Frontend dev server should be on http://localhost:3000
```

### 3. Improved Health Check Logic

**Changes**:
- Detects development vs production mode
- Uses relative paths with Vite proxy in development
- Provides context-specific error messages
- Uses `/api/ping` for better path handling

**Code**:
```typescript
const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
const isDevelopment = import.meta.env.DEV;
const useRelativePaths = isDevelopment && !baseUrl;

// In development: /api/ping (Vite proxy forwards to backend)
// In production: https://api.domain.com/api/ping
const pingUrl = useRelativePaths ? '/api/ping' : `${baseUrl}/api/ping`;
```

## 🚀 How to Use

### Local Development Setup

**1. Start Backend** (Terminal 1)
```bash
cd backend
python run_server.py

# Should see:
# 🚀 Starting CryptoVault API Server
# ✅ Running on http://0.0.0.0:8001
```

**2. Start Frontend** (Terminal 2)
```bash
cd frontend
npm run dev

# Should see:
# VITE v5.x.x ready in XXX ms
# ➜ Local: http://localhost:3000
```

**3. Verify Connection**
- Open http://localhost:3000
- Check browser console for:
  ```
  [API Client] Initialized with BASE_URL: (empty - using relative paths)
  [HealthCheck] ✅ Health check passed (45ms)
  ```

### Production Deployment

**1. Configure Environment**
```bash
# Set in your deployment platform (Vercel, Netlify, etc.)
VITE_API_BASE_URL=https://your-backend-url.com
VITE_NODE_ENV=production
```

**2. Build**
```bash
npm run build
# Creates optimized bundle in ./dist
```

**3. Deploy**
```bash
# Deploy ./dist folder to your hosting platform
npm run preview  # Test locally first
```

## 🔧 Troubleshooting

### Issue: "NetworkError when attempting to fetch resource"

**Local Development**:
```bash
# ✅ Check: Is backend running?
curl http://localhost:8001/ping
# Should return: {"status":"ok","message":"pong"}

# ✅ Check: Is frontend dev server running?
# Open http://localhost:3000

# ✅ Check: Are both on correct ports?
# Backend: 8001 (configured in backend/config.py)
# Frontend: 3000 (configured in frontend/vite.config.ts)
```

**Production**:
```bash
# ✅ Check: Is backend accessible?
curl https://your-backend-url.com/ping

# ✅ Check: Backend on free hosting may be sleeping
# First request takes 30-60 seconds (cold start)
# Subsequent requests are fast

# ✅ Check: CORS headers configured?
# Backend should allow your frontend domain
```

### Issue: "Health check experiencing issues after 5 failures"

**This is NORMAL if**:
1. **Local**: Backend is not running
2. **Production**: Backend is sleeping (free hosting cold start)

**Not a problem because**:
- Health check uses exponential backoff (won't spam)
- Continues retrying automatically
- Backend will wake up on next user request
- Health check will succeed once backend is awake

### Issue: "VITE_API_BASE_URL is not configured"

**Development**: ✅ This is correct! Leave it empty to use Vite proxy

**Production**: ❌ Must set environment variable
```bash
# In deployment platform
VITE_API_BASE_URL=https://your-backend.com
```

## 📋 Configuration Checklist

### Local Development ✅
- [ ] Backend running on `http://localhost:8001`
- [ ] Frontend running on `http://localhost:3000`
- [ ] `VITE_API_BASE_URL` is empty (uses Vite proxy)
- [ ] Can access http://localhost:3000 in browser
- [ ] Console shows: `[HealthCheck] ✅ Health check passed`

### Production Build ✅
- [ ] `VITE_API_BASE_URL` set to backend URL
- [ ] `VITE_NODE_ENV=production`
- [ ] Backend is deployed and accessible
- [ ] CORS configured to allow frontend domain
- [ ] SSL/HTTPS enabled (required for production)

## 🎯 How Vite Proxy Works

### Development (Proxy Enabled)
```
Browser: http://localhost:3000
  ↓ Request: /api/crypto/prices
  ↓ Vite Proxy (vite.config.ts)
  ↓ Forwards to: http://localhost:8001/api/crypto/prices
  ↓ Backend responds
  ↓ Proxy returns to browser
Browser: Receives response
```

**Benefits**:
- No CORS issues in development
- Same-origin requests
- Easy to configure

### Production (No Proxy)
```
Browser: https://yoursite.com
  ↓ Request: https://your-backend.com/api/crypto/prices
  ↓ Direct request to backend
  ↓ Backend responds with CORS headers
Browser: Receives response
```

**Requirements**:
- Backend must allow frontend domain in CORS
- HTTPS required for secure cookies
- Proper DNS/domain configuration

## 🔍 Debugging Commands

### Check Backend Health
```bash
# Ping endpoint (no database)
curl http://localhost:8001/ping
curl https://cryptovault-api.onrender.com/ping

# Health endpoint (with database)
curl http://localhost:8001/health
curl https://cryptovault-api.onrender.com/health

# API root
curl http://localhost:8001/
curl https://cryptovault-api.onrender.com/
```

### Check Frontend Configuration
```bash
# View environment variables
npm run dev -- --mode development
# Check console logs for API configuration

# Build and preview production
npm run build
npm run preview
```

### Check Network
```bash
# Test connectivity
ping cryptovault-api.onrender.com

# Test DNS resolution
nslookup cryptovault-api.onrender.com

# Test SSL certificate
curl -v https://cryptovault-api.onrender.com/ping
```

## 📝 Environment Variables Reference

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `VITE_API_BASE_URL` | Empty | Backend URL | API endpoint base URL |
| `VITE_APP_NAME` | CryptoVault | CryptoVault | Application name |
| `VITE_APP_VERSION` | 1.0.0 | 1.0.0 | Version number |
| `VITE_NODE_ENV` | development | production | Environment mode |
| `VITE_SENTRY_DSN` | Empty | Sentry URL | Error tracking (optional) |

## 🎓 Best Practices

### Local Development
1. ✅ Always run backend first, then frontend
2. ✅ Use separate terminal windows for each
3. ✅ Check console for connection status
4. ✅ Leave `VITE_API_BASE_URL` empty (proxy handles it)
5. ✅ Use http://localhost:3000 (not 127.0.0.1)

### Production
1. ✅ Set all environment variables in deployment platform
2. ✅ Use HTTPS for frontend and backend
3. ✅ Configure CORS properly
4. ✅ Test with `npm run build && npm run preview` first
5. ✅ Monitor health checks in production

## ✨ Result

### Before Fix
```
❌ NetworkError when attempting to fetch resource
❌ Health check disabled after 3 consecutive failures
🔴 No guidance on what's wrong
```

### After Fix
```
✅ Development uses Vite proxy (no CORS issues)
✅ Production uses direct backend URL
✅ Health check continues with backoff (never stops)
✅ Helpful diagnostic messages in console
💡 Clear instructions for fixing issues
```

## 📞 Still Having Issues?

### Local Development Not Working?

**1. Check Backend Port**
```bash
# Backend config
cat backend/config.py | grep PORT
# Should show: PORT = 8001

# Check if port is in use
lsof -i :8001  # Mac/Linux
netstat -ano | findstr :8001  # Windows
```

**2. Check Vite Proxy Config**
```typescript
// frontend/vite.config.ts
server: {
  proxy: {
    "/api": {
      target: "http://localhost:8001",  // ← Should match backend
      changeOrigin: true,
    },
  },
}
```

**3. Restart Both Services**
```bash
# Kill all node/python processes and start fresh
pkill -f node
pkill -f python
```

### Production Not Working?

**1. Check Backend Deployment**
```bash
# Test backend directly
curl https://your-backend.com/ping

# Check backend logs in deployment platform
# Look for startup errors
```

**2. Check Frontend Build**
```bash
# Verify environment variables were included
npm run build
cat dist/assets/index-*.js | grep "VITE_API_BASE_URL"
```

**3. Check CORS Headers**
```bash
curl -H "Origin: https://your-frontend.com" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS https://your-backend.com/api/health
# Should return CORS headers
```

---

**Files Modified**:
- `frontend/.env.development` (created)
- `frontend/.env.production` (created)
- `frontend/.env.example` (created)
- `frontend/src/services/healthCheck.ts` (enhanced diagnostics)

**Status**: ✅ Network connectivity issues resolved with proper configuration
