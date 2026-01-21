# CryptoVault Backend - Render Deployment Guide

## Your Verified Production Configuration

Your backend is running at: **https://cryptovault-api.onrender.com**  
Your frontend is at: **https://www.cryptovault.financial**

---

## Step 1: Prepare Render Environment Variables

### In Render Dashboard:
1. Go to **Services** → **cryptovault-api** → **Environment**
2. Add the following environment variables exactly as shown:

```bash
ENVIRONMENT=production
APP_NAME=CryptoVault
APP_VERSION=2.0.0
DEBUG=false
APP_URL=https://www.cryptovault.financial

HOST=0.0.0.0
PORT=8000

MONGO_URL=mongodb+srv://team_db_user:mWPe3V6ZhoNNEWUk@cryptovaultcluster.vobw2w8.mongodb.net/?appName=CryptoVaultCluster
DB_NAME=cryptovault
MONGO_MAX_POOL_SIZE=10
MONGO_TIMEOUT_MS=5000

USE_REDIS=true
UPSTASH_REDIS_REST_URL=https://emerging-sponge-14455.upstash.io
UPSTASH_REDIS_REST_TOKEN=ATh3AAIncDE5OTMzNjFiM2M4NzA0NmEzOWQwOWE2MjgwODczMDNlM3AxMTQ0NTU
REDIS_PREFIX=cryptovault:

JWT_SECRET=jmZgXmsOEx10hwWOIE6EvhCft56jew6PVSiSweq-JQI
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CSRF_SECRET=9f5cb48d-aa6b-4923-a760-ce8065e4238d
USE_CROSS_SITE_COOKIES=true

CORS_ORIGINS=https://www.cryptovault.financial,http://localhost:3000,http://127.0.0.1:3000

EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=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
EMAIL_FROM=teams@cryptovault.financial
EMAIL_FROM_NAME=CryptoVault Financial
EMAIL_VERIFICATION_URL=https://cryptovault.financial/verify

COINCAP_API_KEY=68aa5a01aa84e5704a10f5d6f730dadd9381901161e06d07085fcca8587f41e3
COINCAP_RATE_LIMIT=50
USE_MOCK_PRICES=false

NOWPAYMENTS_API_KEY=ZKDVT1B-4WTMVAZ-KZ7E38G-GPNE8Q7
NOWPAYMENTS_IPN_SECRET=bEEgqlb1q+TF6ygQfNJ+fUJyWvARDJwp
NOWPAYMENTS_SANDBOX=false

FIREBASE_CREDENTIALS_PATH=/app/backend/firebase-credentials.json

SENTRY_DSN=https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/4510716879503360
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1

RATE_LIMIT_PER_MINUTE=60

LOG_LEVEL=INFO
```

---

## Step 2: Configure Build & Start Commands

### Build Command
```bash
pip install -r backend/requirements.txt
```

### Start Command
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.server:socket_app --bind 0.0.0.0:$PORT
```

### Root Directory
```
.
```
(Leave as root - Render will find requirements.txt)

---

## Step 3: Set Up Firebase Credentials (If Using)

Firebase credentials are sensitive and should be handled securely:

### Option A: Using Environment Variable (Recommended)
1. The `FIREBASE_CREDENTIALS_PATH` env var is set to `/app/backend/firebase-credentials.json`
2. You can also use `FIREBASE_CREDENTIAL` env var with the JSON content directly
3. In your `backend/server.py`, handle Firebase initialization:

```python
import json
import os
from firebase_admin import initialize_app, credentials

if os.getenv("FIREBASE_CREDENTIALS_PATH"):
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
    initialize_app(cred)
elif os.getenv("FIREBASE_CREDENTIAL"):
    cred = credentials.Certificate(json.loads(os.getenv("FIREBASE_CREDENTIAL")))
    initialize_app(cred)
```

### Option B: Upload as File
If you have a `firebase-credentials.json` file:
1. Add to your `.gitignore` (never commit secrets)
2. Render will preserve files in `/app` directory
3. Reference via `FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json`

---

## Step 4: Verify Deployment

### Health Check Endpoints
```bash
# Simple ping
curl https://cryptovault-api.onrender.com/ping
# Expected: { "status": "ok", "message": "pong" }

# Full health check
curl https://cryptovault-api.onrender.com/health
# Expected: { "status": "healthy", "database": "connected", ... }

# Configuration validation
curl https://cryptovault-api.onrender.com/api/config
# Expected: Configuration object with app settings
```

### Check Logs
1. Go to **Services** → **cryptovault-api** → **Logs**
2. Look for:
   ```
   ✅ Environment Validated
   ✅ Database indexes ensured
   ✅ Real-time price stream service started
   ✅ Server startup complete!
   ```

### Test From Frontend
1. Visit https://www.cryptovault.financial
2. Open browser DevTools → Network tab
3. Make any API request
4. Check:
   - Status should be 200 (not 500)
   - CORS headers present: `Access-Control-Allow-Origin: https://www.cryptovault.financial`
   - No console errors

---

## Step 5: Monitor Production

### Sentry Error Tracking
Your Sentry DSN is configured:
```
https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/4510716879503360
```

Visit https://sentry.io to:
- Monitor errors in real-time
- Set up alerts for critical issues
- View performance metrics

### Check Render Logs
Watch for:
- **Blue badge** = Deployment successful
- **Red badge** = Deployment failed
- Click **Logs** tab for detailed error messages

### Rate Limiting Status
Check headers in any API response:
```bash
curl -I https://cryptovault-api.onrender.com/api/ping | grep -i ratelimit
# X-RateLimit-Limit: 60
# X-RateLimit-Remaining: 59
# X-RateLimit-Reset: 1705...
```

---

## Troubleshooting

### Issue: 500 Error on /api/ping

**Solution 1: Check Environment Variables**
```bash
# In Render Logs, should see:
# ✅ Environment Validated
# ✅ Database: cryptovault
# ✅ Redis: Enabled (Upstash)
```

**Solution 2: Verify MongoDB Connection**
```bash
# Test in MongoDB Atlas dashboard:
# 1. Go to Clusters → Connect
# 2. Test with MongoDB Shell
# 3. Verify credentials in MONGO_URL
```

**Solution 3: Check Upstash Redis**
```bash
# Verify at https://console.upstash.io
# 1. Check database is active
# 2. Verify REST API URL matches UPSTASH_REDIS_REST_URL
# 3. Verify token matches UPSTASH_REDIS_REST_TOKEN
```

---

### Issue: CORS Errors in Browser Console

**Error**: `Access to XMLHttpRequest at 'https://cryptovault-api.onrender.com/api/crypto' from origin 'https://www.cryptovault.financial' has been blocked by CORS policy`

**Solution:**
```bash
# Verify CORS_ORIGINS includes your frontend:
CORS_ORIGINS=https://www.cryptovault.financial,http://localhost:3000,http://127.0.0.1:3000

# Restart service in Render dashboard:
Services → cryptovault-api → More → Restart Service
```

---

### Issue: Database Connection Timeout

**Solution 1: Check MongoDB Atlas IP Whitelist**
1. Go to https://cloud.mongodb.com
2. Security → Network Access
3. Add Render IP: `0.0.0.0/0` (allows all IPs)
   - ⚠️ This is convenient for development but less secure
   - For production, whitelist specific Render IPs

**Solution 2: Verify Connection String**
```bash
# Your MONGO_URL should have:
# ✓ Username and password encoded
# ✓ Cluster name: cryptovaultcluster
# ✓ Database name in path: cryptovault
# ✓ appName parameter for connection pooling

# Format:
mongodb+srv://team_db_user:mWPe3V6ZhoNNEWUk@cryptovaultcluster.vobw2w8.mongodb.net/?appName=CryptoVaultCluster
```

---

### Issue: Redis/Upstash Not Connecting

**Solution 1: Verify REST API URL & Token**
```bash
# Test Upstash connection:
curl -H "Authorization: Bearer ATh3AAIncDE5OTMzNjFiM2M4NzA0NmEzOWQwOWE2MjgwODczMDNlM3AxMTQ0NTU" \
  https://emerging-sponge-14455.upstash.io/ping

# Expected response: +PONG
```

**Solution 2: Enable Redis in Config**
```bash
# Make sure env vars are set:
USE_REDIS=true
UPSTASH_REDIS_REST_URL=https://emerging-sponge-14455.upstash.io
UPSTASH_REDIS_REST_TOKEN=ATh3AAIncDE5OTMzNjFiM2M4NzA0NmEzOWQwOWE2MjgwODczMDNlM3AxMTQ0NTU
```

---

### Issue: SendGrid Email Not Sending

**Solution:**
```bash
# Verify SendGrid API key:
SENDGRID_API_KEY=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

# Check in SendGrid dashboard:
# 1. API Keys → Verify key is active
# 2. Sender Authentication → Verify sender domain
# 3. Email From should be: teams@cryptovault.financial
```

---

## Performance Tuning

### MongoDB Optimization
- `MONGO_MAX_POOL_SIZE=10` - Increase to 20 for high traffic
- `MONGO_TIMEOUT_MS=5000` - Increase to 10000 for slower connections
- Create indexes in MongoDB Atlas Dashboard

### Gunicorn Workers
Current: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker`

For different server sizes:
- **Small** (512MB RAM): `-w 2`
- **Standard** (2GB RAM): `-w 4`
- **Large** (4GB+ RAM): `-w 8`

### Rate Limiting
Current: `RATE_LIMIT_PER_MINUTE=60`

Adjust based on actual usage:
- Low traffic: `30`
- Normal traffic: `60`
- High traffic: `120`

---

## Security Checklist

- [ ] JWT_SECRET is unique random string (✓ Set)
- [ ] CSRF_SECRET is unique random string (✓ Set)
- [ ] CORS_ORIGINS is specific domain, not wildcard
- [ ] SendGrid API key is protected (not logged/exposed)
- [ ] MongoDB password is secure
- [ ] Upstash token is secure
- [ ] Firebase credentials are not in git
- [ ] Sentry DSN is production DSN (not dev)
- [ ] Email verification URL is HTTPS
- [ ] Rate limiting is enabled

---

## Testing the Full Stack

### 1. Frontend to Backend Connection
```bash
# From browser console on https://www.cryptovault.financial
fetch('/api/ping')
  .then(r => r.json())
  .then(d => console.log('Backend response:', d))

# Should log: { status: "ok", message: "pong" }
```

### 2. WebSocket Connection
```bash
# From browser console
const socket = new WebSocket('wss://cryptovault-api.onrender.com/socket.io/');
socket.onopen = () => console.log('WebSocket connected');
socket.onerror = (e) => console.error('WebSocket error:', e);
```

### 3. API Request with CORS
```bash
# From browser console
fetch('/api/crypto/list', {
  method: 'GET',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  }
})
  .then(r => r.json())
  .then(d => console.log('Crypto data:', d))
```

---

## Deployment Checklist

Before marking deployment complete:

- [ ] All environment variables set in Render
- [ ] Build command: `pip install -r backend/requirements.txt`
- [ ] Start command: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.server:socket_app --bind 0.0.0.0:$PORT`
- [ ] Service shows "Live" status (blue badge)
- [ ] `/ping` returns 200 OK
- [ ] `/health` returns healthy status
- [ ] `/api/config` returns configuration
- [ ] Frontend can reach backend (no CORS errors)
- [ ] WebSocket connects successfully
- [ ] Sentry receives events (if configured)
- [ ] SendGrid can send emails
- [ ] Rate limiting headers present in responses

---

## Next Steps

1. **Monitor Logs**: Watch Render logs for first 24 hours
2. **Set Alerts**: Configure Sentry alerts for critical errors
3. **Performance**: Monitor response times and adjust workers if needed
4. **Scale**: If traffic increases, upgrade Render plan or add more workers
5. **Backup**: Enable MongoDB Atlas automated backups
6. **DNS**: Ensure www.cryptovault.financial points to Vercel

---

## Support

If you encounter issues:

1. **Check Render Logs**: Services → cryptovault-api → Logs
2. **Test Health**: `curl https://cryptovault-api.onrender.com/health`
3. **Check Config**: Review environment variables in Render dashboard
4. **Verify External Services**:
   - MongoDB Atlas connectivity
   - Upstash Redis accessibility
   - SendGrid API key validity
   - Sentry project active

---

**Last Updated**: 2025-01-21  
**Status**: Production Configuration Complete  
**Environment**: Render.com  
**Frontend**: https://www.cryptovault.financial  
**Backend**: https://cryptovault-api.onrender.com
