## 🎯 CryptoVault Backend - Production Deployment Checklist

### Phase 1: Pre-Deployment Validation ✅

#### 1.1 Environment Setup
- [ ] Clone repository and navigate to `backend/` directory
- [ ] Copy `.env.example` to `.env`: `cp .env.example .env`
- [ ] Update all required variables in `.env`
- [ ] Verify no `.env` is committed to version control

#### 1.2 Critical Environment Variables
- [ ] `PORT` is set (8000 or platform-assigned)
- [ ] `ENVIRONMENT=production`
- [ ] `FULL_PRODUCTION_CONFIGURATION=true`
- [ ] `MONGO_URL` points to production MongoDB Atlas
- [ ] `JWT_SECRET` is NOT the default value
- [ ] `CSRF_SECRET` is NOT the default value
- [ ] `APP_URL` matches frontend domain
- [ ] `CORS_ORIGINS` includes frontend domain(s)
- [ ] `PUBLIC_API_URL` is correct (for frontend config)
- [ ] `PUBLIC_WS_URL` is correct (for WebSocket)

#### 1.3 Service Configuration
- [ ] Email service configured (SMTP, SendGrid, or Resend)
- [ ] Database connectivity verified
- [ ] Redis/Upstash configuration (if using caching)
- [ ] External APIs configured (CoinCap, NOWPayments, etc.)

#### 1.4 Pre-flight Checks
```bash
# Run deployment validation script
cd backend
bash deploy_preflight_check.sh
```
Expected output: ✅ All critical checks passed!

---

### Phase 2: Installation & Build ✅

#### 2.1 Python Environment
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Verify critical packages
python -c "import fastapi, motor, redis; print('✅ Dependencies OK')"
```

#### 2.2 Build Verification
```bash
# Syntax check
python -m py_compile backend/server.py
python -m py_compile backend/config.py
python -m py_compile backend/startup.py
```

#### 2.3 Container Build (if using Docker)
```bash
# Build image
docker build -t cryptovault-backend -f backend/Dockerfile .

# Verify build
docker images | grep cryptovault-backend
```

---

### Phase 3: Database Preparation ✅

#### 3.1 MongoDB Atlas
- [ ] Database cluster created and running
- [ ] Database user created (with strong password)
- [ ] Connection string in MONGO_URL format
- [ ] IP whitelist updated (allow deployment server IP)
- [ ] SSL enabled (required for production)

#### 3.2 Database Initialization (First Time Only)
```bash
# Connect to database (once server starts)
# Run:
# POST /api/init/database
# This creates collections and indexes
```

#### 3.3 Index Creation
- [ ] Database indexes created on startup (automatic)
- [ ] Verify in MongoDB Atlas under "Indexes"

---

### Phase 4: Security Verification ✅

#### 4.1 Secrets Management
- [ ] All secrets in environment variables (NOT in code)
- [ ] Secrets stored in platform's secret management
  - Render.com: Environment section
  - Railway: Variables section
  - AWS: Secrets Manager
  - Vercel: Environment Variables
- [ ] No `.env` file in production deployment
- [ ] Secrets rotated regularly

#### 4.2 Security Settings
- [ ] `COOKIE_SECURE=true` (for HTTPS)
- [ ] `COOKIE_SAMESITE=lax` (CSRF protection)
- [ ] HSTS enabled (via header)
- [ ] CSP headers configured
- [ ] Rate limiting enabled

#### 4.3 TLS/HTTPS
- [ ] HTTPS is enforced (not HTTP)
- [ ] SSL certificate is valid
- [ ] Certificate expires date checked
- [ ] Mixed content warnings checked (if on HTTPS)

---

### Phase 5: Startup & Health Checks ✅

#### 5.1 Server Startup

**Option A: Direct Python**
```bash
python start_server.py
# Expected: Shows startup checks and "✅ SERVER STARTUP COMPLETE"
```

**Option B: Gunicorn (Production)**
```bash
gunicorn -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  server:app
```

**Option C: Shell Script**
```bash
bash start_production.sh
```

#### 5.2 Startup Output Verification

Expected startup logs contain:
```
🚀 CRYPTOVAULT API SERVER - ENTERPRISE STARTUP
✅ Configuration Validation: PASS
✅ MongoDB Connection: PASS
✅ Database indexes created
✅ Price stream service started
✅ Server startup complete!
```

#### 5.3 Health Endpoint Checks
```bash
# Liveness probe (must return 200)
curl -i https://api.yourdomain.com/health/live
# Expected: 200 OK

# Readiness probe (must return 200)
curl -i https://api.yourdomain.com/health/ready
# Expected: 200 OK with dependency status

# Simple ping
curl https://api.yourdomain.com/ping
# Expected: { "status": "ok", "version": "1.0.0" }
```

---

### Phase 6: API Testing ✅

#### 6.1 CORS & Headers
```bash
# Test CORS headers
curl -i -H "Origin: https://www.yourdomain.com" \
  https://api.yourdomain.com/health

# Verify headers present:
# - Strict-Transport-Security: max-age=31536000
# - X-Content-Type-Options: nosniff
# - X-Frame-Options: DENY
# - Access-Control-Allow-Origin: https://www.yourdomain.com
```

#### 6.2 CSRF Protection
```bash
# Get CSRF token
curl -i -b cookies.txt -c cookies.txt \
  https://api.yourdomain.com/api/csrf

# Expected: Returns csrf_token in response and sets cookie
```

#### 6.3 Authentication
```bash
# Test login endpoint
curl -X POST https://api.yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: <token_from_above>" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# Expected: 200 with user data and tokens
# OR 401 if credentials wrong (which is correct)
```

#### 6.4 WebSocket Connection
```bash
# Using wscat (npm install -g wscat)
wscat -c wss://api.yourdomain.com/socket.io/

# Expected: Connected message
# Send: {"auth": {"token": "your_jwt_token"}}
# Expected: Authentication acknowledgment
```

---

### Phase 7: Integration Testing ✅

#### 7.1 Frontend-Backend Integration
```bash
# Test from frontend domain
curl -E certificate.pem \
  -H "Authorization: Bearer <token>" \
  https://api.yourdomain.com/api/users

# Expected: 200 with user data (or 401 if no token)
```

#### 7.2 Email Service
```bash
# Test email sending (if available)
# Varies by email service configuration
# Check logs for email delivery status
```

#### 7.3 External Data Services
```bash
# Test price data endpoint
curl https://api.yourdomain.com/api/prices

# Expected: 200 with cryptocurrency prices
```

---

### Phase 8: Monitoring & Logging Setup ✅

#### 8.1 Log Aggregation
- [ ] Logs configured in JSON format (production)
- [ ] Log aggregation tool connected
  - Vercel Log Insights
  - Railway Logs
  - CloudWatch
  - Datadog
  - ELK Stack

#### 8.2 Error Tracking
- [ ] Sentry DSN configured in `SENTRY_DSN`
- [ ] Test error is sent: `GET /test-error` (if available)
- [ ] Error dashboard accessible

#### 8.3 Performance Monitoring
- [ ] Response times tracked
- [ ] Database query times monitored
- [ ] Error rates tracked
- [ ] Alerts configured for anomalies

---

### Phase 9: Load Testing (Optional) ✅

#### 9.1 Rate Limiting Test
```bash
# Make 65 requests in 1 minute (limit is 60)
for i in {1..65}; do
  curl https://api.yourdomain.com/health
  sleep 1
done

# Expected: Last 5 requests return 429 (Too Many Requests)
```

#### 9.2 Concurrent Connections Test
```bash
# Test concurrent WebSocket connections
# Use Apache Bench or similar load testing tool
ab -n 100 -c 10 https://api.yourdomain.com/health

# Expected: Server handles 100 requests with 10 concurrent
```

---

### Phase 10: Post-Deployment Verification ✅

#### 10.1 24-Hour Health Check
- [ ] No critical errors in logs in last 24 hours
- [ ] Error rate < 1% of requests
- [ ] Average response time < 500ms
- [ ] Database connections stable
- [ ] All external services operational

#### 10.2 Security Verification
- [ ] No sensitive data in logs
- [ ] HTTPS enforced (no HTTP)
- [ ] Security headers present
- [ ] Rate limiting working
- [ ] CSRF tokens rotating
- [ ] No unauthorized access attempts

#### 10.3 Frontend Integration
- [ ] Frontend can authenticate
- [ ] Frontend receives user data
- [ ] WebSocket real-time updates working
- [ ] File uploads working (if applicable)
- [ ] All API endpoints accessible

---

### Rollback Plan (If Issues) ⚠️

#### Immediate Actions
```bash
# 1. Stop the server
# 2. Check logs for error details
tail -f logs.json | jq 'select(.level == "ERROR")'

# 3. Common fixes:
# - Restart with updated environment variables
# - Restart database connection: DELETE all env vars, re-apply
# - Clear cache: Restart Redis or wait for TTL expiry
# - Restart process: Kill and restart server
```

#### Rollback Procedure
```bash
# 1. Note the commit/version that failed
git log --oneline | head -1

# 2. Revert to last known good version
git checkout <previous_commit>

# 3. Rebuild and redeploy
pip install -r requirements.txt
python start_server.py
```

---

## 📊 Deployment Monitoring Dashboard

| Metric | Threshold | Check |
|--------|-----------|-------|
| API Response Time | < 500ms | ✅ Performance monitoring |
| Error Rate | < 1% | ✅ Log aggregation |
| Uptime | > 99.5% | ✅ Uptime monitor |
| Database Latency | < 100ms | ✅ DB monitoring |
| CPU Usage | < 70% | ✅ Container metrics |
| Memory Usage | < 75% | ✅ Container metrics |

---

## 🆘 Emergency Contacts & Documentation

**Key Resources**:
1. [PRODUCTION_HARDENING.md](./PRODUCTION_HARDENING.md) - Complete hardening details
2. [FRONTEND_BACKEND_INTEGRATION.md](./FRONTEND_BACKEND_INTEGRATION.md) - API integration
3. [BACKEND_DEPLOYMENT_COMPLETE.md](./BACKEND_DEPLOYMENT_COMPLETE.md) - Deployment overview
4. Sentry Dashboard - Error tracking
5. Log Aggregation Service - Log viewing
6. MongoDB Atlas Console - Database management

**Escalation Path**:
- Level 1: Check logs and health endpoints
- Level 2: Review environment variables and configuration
- Level 3: Check external service status
- Level 4: Database connectivity and performance
- Level 5: Rollback to last known good version

---

## ✅ Deployment Sign-Off

```
Date: _________________
Deployed By: _________________
Environment: PRODUCTION
Version: 2.0.0

Pre-flight Checks:    ☐ PASS  ☐ FAIL
Health Checks:        ☐ PASS  ☐ FAIL
Integration Tests:    ☐ PASS  ☐ FAIL
Security Checks:      ☐ PASS  ☐ FAIL
Performance Tests:    ☐ PASS  ☐ FAIL

Status: ☐ APPROVED ☐ HOLD ☐ ROLLBACK

Notes: _________________________________________________
_______________________________________________________
```

---

**Deployment Time**: ~15-30 minutes
**Rollback Time**: ~5-10 minutes  
**Monitoring Period**: 24 hours recommended

🎉 **Ready to deploy! Follow this checklist for a smooth production rollout.**
