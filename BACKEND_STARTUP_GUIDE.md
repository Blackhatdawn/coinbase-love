# CryptoVault Backend - Startup & API Verification Guide

## 🎯 Overview

This guide shows you how to:
1. Install backend dependencies
2. Start the backend server
3. Verify all API endpoints work correctly
4. Test frontend-backend connectivity

---

## 📦 Step 1: Install Dependencies

### First Time Setup

```bash
# Install all backend dependencies from requirements.txt
pip install -r backend/requirements.txt

# Expected output:
# Successfully installed fastapi-0.110.1 uvicorn[standard]-0.25.0 ...
```

### Verify Installation

```bash
# Check key packages are installed
pip list | grep -E "fastapi|uvicorn|pydantic"

# Expected output:
# fastapi                0.110.1
# uvicorn               0.25.0
# pydantic              2.12.5
# pydantic-settings     2.12.0
```

---

## ⚙️ Step 2: Configure Environment

### Option A: Using .env File (Recommended for Development)

The file `backend/.env` already contains your production configuration. For **development**, you might want to use simpler values:

```bash
# Edit backend/.env and update for development:
ENVIRONMENT=development
MONGO_URL=mongodb://localhost:27017/cryptovault  # Local MongoDB (optional)
JWT_SECRET=dev-secret-change-me
CSRF_SECRET=dev-secret-change-me
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
USE_REDIS=false  # Disable Redis for development (optional)
```

The backend will automatically load from `backend/.env`.

### Option B: Environment Variables

```bash
# Set environment variables in your terminal
export ENVIRONMENT=development
export MONGO_URL=mongodb://localhost:27017/cryptovault
export JWT_SECRET=dev-secret-change-me
export CSRF_SECRET=dev-secret-change-me
export CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Option C: Production Configuration

Use your production `.env` with real credentials for testing against production databases:

```bash
# .env already has your production values
# Just start the server and it will load them
```

---

## 🚀 Step 3: Start Backend Server

### Method 1: Using run_server.py (Recommended)

```bash
python run_server.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8001
✅ Environment Validated
✅ Database indexes ensured
✅ Real-time price stream service started
✅ WebSocket price feed started
✅ Server startup complete!
```

### Method 2: Direct Uvicorn Command

```bash
uvicorn backend.server:socket_app --host 0.0.0.0 --port 8001 --reload
```

### Method 3: Gunicorn (Production)

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.server:socket_app --bind 0.0.0.0:8001
```

---

## ✅ Step 4: Verify Backend is Running

### Quick Health Check

```bash
# In a new terminal, test if backend is responsive
curl http://localhost:8001/ping

# Expected response:
# {"status":"ok","message":"pong","timestamp":"2025-01-21T...","version":"1.0.0"}
```

### Full Health Status

```bash
curl http://localhost:8001/health

# Expected response:
# {"status":"healthy","api":"running","environment":"development","database":"connected"...}
```

### Check Configuration

```bash
curl http://localhost:8001/api/config

# Expected response:
# {
#   "appUrl": "http://localhost:3000",
#   "apiBaseUrl": "",
#   "preferRelativeApi": true,
#   "wsBaseUrl": "ws://localhost:8001",
#   "environment": "development",
#   "version": "1.0.0"
# }
```

---

## 🔌 Step 5: Test API Endpoints

### Test Crypto Data Endpoint

```bash
curl http://localhost:8001/api/crypto

# Expected response:
# {
#   "cryptocurrencies": [
#     {
#       "id": "bitcoin",
#       "symbol": "btc",
#       "name": "Bitcoin",
#       "price": "...",
#       ...
#     }
#   ]
# }
```

### Test CSRF Token Endpoint

```bash
curl -c cookies.txt http://localhost:8001/csrf

# Expected response:
# {
#   "csrf_token": "...",
#   "expires_in": 3600,
#   "message": "New token generated"
# }
```

### Test with CORS Headers

```bash
curl -i http://localhost:8001/api/crypto \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json"

# Should include in response headers:
# access-control-allow-origin: http://localhost:3000
# access-control-allow-credentials: true
```

---

## 🧪 Step 6: Frontend-Backend Integration Test

### Start Frontend (in new terminal)

```bash
cd frontend && yarn dev

# Expected output:
# VITE v5.4.21 ready in XXX ms
# ➜ Local: http://localhost:3000/
# [Vite] Backend proxy configured for: http://localhost:8001
```

### Test API Call Through Frontend Proxy

```bash
# Call from browser console at http://localhost:3000
fetch('/api/ping')
  .then(r => r.json())
  .then(d => console.log('API Response:', d))

# Expected console output:
# API Response: { status: "ok", message: "pong", ... }
```

### Check Network in Browser DevTools

1. Open http://localhost:3000 in browser
2. Open DevTools (F12)
3. Go to "Network" tab
4. Perform any action that makes an API call
5. Look for requests to `/api/*`
6. Should show Status: 200 (not error)
7. Response tab should show JSON data

---

## 🔐 Step 7: WebSocket Connection Test

### From Browser Console

```javascript
// Open browser console at http://localhost:3000

// Test WebSocket connection to Socket.IO
const socket = io('http://localhost:8001', {
  path: '/socket.io/',
  reconnection: true
});

socket.on('connect', () => {
  console.log('✓ WebSocket connected');
});

socket.on('disconnect', () => {
  console.log('✗ WebSocket disconnected');
});

socket.on('price_update', (data) => {
  console.log('Price update:', data);
});

socket.on('error', (err) => {
  console.error('Socket error:', err);
});
```

### Check WebSocket in DevTools

1. DevTools → Network tab
2. Filter: WS (WebSocket)
3. Should see connection to `ws://localhost:8001/socket.io/`
4. Status: 101 (Switching Protocols)

---

## 📝 Configuration Validation

### Run Configuration Test

```bash
python -m backend.config

# Expected output:
# ======================================================================
# CRYPTOVAULT CONFIGURATION TEST
# ======================================================================
# 
# Application:
#   Name: CryptoVault
#   Version: 2.0.0
#   Environment: development
#   Debug: false
#   Frontend URL: http://localhost:3000
# 
# Server:
#   Host: 0.0.0.0
#   Port: 8001
#   Workers: 4
# 
# Database (MongoDB):
#   URL: mongodb://localhost:27017/cryptovault
#   Database: cryptovault
# 
# ... [more config details]
```

---

## 🔍 Troubleshooting

### Issue 1: "Address already in use" Error

```
OSError: [Errno 48] Address already in use
```

**Solution:** Port 8001 is already in use.

```bash
# Find what's using port 8001
lsof -i :8001

# Kill the process (if safe)
kill -9 <PID>

# Or use different port
python run_server.py --port 8002
```

### Issue 2: "ModuleNotFoundError: No module named 'pydantic_settings'"

```
ModuleNotFoundError: No module named 'pydantic_settings'
```

**Solution:** Install missing dependency

```bash
pip install pydantic-settings
```

### Issue 3: "Database connection failed"

```
ServerSelectionTimeoutError: No servers available
```

**Solutions:**
- Option A: Disable Redis in .env (set `USE_REDIS=false`)
- Option B: Skip database connection in development
- Option C: Set up local MongoDB instance
- Option D: Use production database URL in .env

### Issue 4: API Endpoint Returns 500

Check backend logs for error message. Common causes:
- Missing environment variables
- Database connection failed
- External API error (CoinCap, etc.)
- Missing required Python package

**Solution:**
```bash
# Check logs in terminal where backend is running
# Look for red error messages
# Run configuration test:
python -m backend.config
# Should show any missing configuration
```

### Issue 5: CORS Error in Browser Console

```
Access to XMLHttpRequest blocked by CORS policy
```

**Solution:**
1. Check `CORS_ORIGINS` in .env includes `http://localhost:3000`
2. Restart both backend and frontend
3. Check Vite proxy is configured (in vite.config.ts)
4. Clear browser cache and cookies

```bash
# Verify CORS headers
curl -i http://localhost:8001/api/crypto \
  -H "Origin: http://localhost:3000"

# Should include: access-control-allow-origin: http://localhost:3000
```

---

## 📊 Full API Test Suite

Run these tests in order:

```bash
#!/bin/bash
# Test Backend Startup

echo "1. Ping Test..."
curl -s http://localhost:8001/ping | python -m json.tool

echo -e "\n2. Health Check..."
curl -s http://localhost:8001/health | python -m json.tool

echo -e "\n3. Configuration..."
curl -s http://localhost:8001/api/config | python -m json.tool

echo -e "\n4. Crypto Data..."
curl -s http://localhost:8001/api/crypto | python -m json.tool | head -30

echo -e "\n5. CSRF Token..."
curl -s -c cookies.txt http://localhost:8001/csrf | python -m json.tool

echo -e "\n✅ All tests completed!"
```

Save as `test_api.sh` and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## 🎯 Verification Checklist

After starting backend:

- [ ] Backend starts without errors
- [ ] See "✅ Environment Validated" in logs
- [ ] `/ping` returns { "status": "ok" }
- [ ] `/health` returns { "status": "healthy" }
- [ ] `/api/config` returns configuration object
- [ ] `/api/crypto` returns cryptocurrency data
- [ ] CORS headers present in responses
- [ ] Frontend can make API calls (Network tab shows 200)
- [ ] WebSocket connects (Network tab shows WS connection)
- [ ] No red errors in browser console

---

## 🚀 Production Backend Startup

For production on Render:

```bash
# Build command (in Render dashboard):
pip install -r backend/requirements.txt

# Start command (in Render dashboard):
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.server:socket_app --bind 0.0.0.0:$PORT

# Environment variables: (Set in Render dashboard)
ENVIRONMENT=production
MONGO_URL=<production-mongodb-url>
JWT_SECRET=<production-jwt-secret>
CSRF_SECRET=<production-csrf-secret>
CORS_ORIGINS=https://www.cryptovault.financial,http://localhost:3000
# ... (other env vars from backend/.env)
```

---

## 📝 Logs to Monitor

### Good Signs ✅
```
INFO:     Uvicorn running on http://0.0.0.0:8001
✅ Environment Validated
✅ Database indexes ensured
✅ Real-time price stream service started
✅ WebSocket price feed started
✅ Server startup complete!
```

### Issues to Watch ⚠️
```
❌ STARTUP FAILED: Critical environment variables not configured
❌ Database connection timeout
⚠️ Price stream service failed to start (non-critical)
ERROR: Failed to fetch cryptocurrency prices
```

---

## 🔑 Quick Reference

| Command | Purpose |
|---------|---------|
| `python run_server.py` | Start backend |
| `python -m backend.config` | Validate config |
| `curl http://localhost:8001/health` | Check health |
| `curl http://localhost:8001/api/ping` | Ping backend |
| `kill %1` | Stop backend |

---

## ✨ You're Ready!

Once you see "✅ Server startup complete!", your backend is ready to:
- Serve API requests
- Connect to frontend
- Handle WebSocket connections
- Process real-time price updates

**Start testing!** 🚀
