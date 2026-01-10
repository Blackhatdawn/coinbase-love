# Week 1 Deployment Checklist - Critical Security Fixes

## 🎯 Objective
Deploy critical security fixes to production with zero downtime using blue-green canary rollout strategy.

---

## ✅ Phase 1: Pre-Deployment Verification (Staging)

### Step 1: Environment Setup
- [ ] Create feature branch: `git checkout -b security/week1-critical-fixes`
- [ ] All changes committed and pushed
- [ ] Node.js version: v20+
- [ ] Database backup completed

### Step 2: Local Verification (Dev Environment)

**Frontend Tests:**
```bash
# Install dependencies (if needed)
npm install

# Build frontend
npm run build

# Check for TypeScript errors
npx tsc --noEmit
```

**Backend Tests:**
```bash
cd server

# Install dependencies (if needed)
npm install

# Build backend
npm run build

# Check for TypeScript errors
npx tsc --noEmit

# Verify database schema
npm run seed  # Or run migration script
```

### Step 3: Manual Testing (Local)

**Test Authentication Flow:**
1. Sign up with test account:
   - Email: `test-user-week1@example.com`
   - Password: `TestPassword123`
   - Name: `Test User`

2. Verify email (check console in dev environment for token)

3. Sign in with credentials

4. Check browser DevTools:
   - Application > Cookies: Should see `accessToken` and `refreshToken`
   - Application > LocalStorage: Should be EMPTY (no JWT tokens)
   - Network tab: Cookies should be sent with credentials: include

5. Test logout:
   - Navigate to dashboard
   - Click logout
   - Verify cookies cleared
   - Verify login required for protected routes

6. Test token refresh:
   - Wait 15 minutes OR manually trigger refresh endpoint
   - Verify new access token issued
   - User should remain logged in without re-authenticating

**Test CSP Headers:**
```bash
# In another terminal, with backend running on :5000
curl -I http://localhost:5000/api/health

# Should see header:
# Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-...'; ...
```

**Test Input Validation:**
1. Try signing up with invalid email: Should show error
2. Try password without uppercase: Should show error
3. Try name < 2 characters: Should show error
4. All errors should match Zod schemas

### Step 4: Code Review Checklist

- [ ] JWT tokens removed from localStorage ✅
- [ ] HttpOnly cookies set with Secure + SameSite flags ✅
- [ ] Refresh token system implemented (15min access + 7day refresh) ✅
- [ ] Token revocation table added to database ✅
- [ ] Logout revokes refresh tokens ✅
- [ ] CSP headers hardened (no unsafe-inline/unsafe-eval) ✅
- [ ] Input validation uses Zod schemas (frontend + backend) ✅
- [ ] Database pool sizing configured (min: 5, max: 20) ✅
- [ ] TypeScript strict mode enabled (noImplicitAny, strictNullChecks) ✅
- [ ] No secrets in code or config files ✅

---

## 📦 Phase 2: Staging Deployment

### Step 1: Push Code to Remote

```bash
# Push feature branch
git push origin security/week1-critical-fixes

# Create Pull Request on GitHub
# - Title: "Week 1 Critical Security Fixes"
# - Description: Include summary of changes
# - Add labels: security, critical, week1

# Code Review:
# - 2+ approvals required
# - All CI/CD checks passing
# - No security vulnerabilities detected
```

### Step 2: Merge to Staging Branch

```bash
# After approval
git checkout develop
git pull origin develop
git merge --no-ff security/week1-critical-fixes
git push origin develop
```

### Step 3: Deploy to Staging Environment

**Using Render (or similar platform):**
1. Navigate to Render dashboard
2. Select "cryptovault-staging" service
3. Trigger manual deploy OR automatic deploy will start on push to develop
4. Wait for deployment to complete (5-10 minutes)
5. Check deployment logs for errors

**Set Environment Variables (Staging):**
- `JWT_SECRET`: Use test secret (32+ characters)
- `JWT_REFRESH_SECRET`: Use test refresh secret (if using separate secrets)
- `DB_POOL_MAX`: 20
- `DB_POOL_MIN`: 5
- `NODE_ENV`: staging

### Step 4: Staging Verification

**Health Check:**
```bash
curl https://api-staging.cryptovault.onrender.com/api/health
# Should return: {"status":"ok","timestamp":"2024-01-09T..."}
```

**Smoke Tests:**

1. **Sign Up Flow:**
   ```bash
   curl -X POST https://api-staging.cryptovault.onrender.com/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email":"staging-test-1@example.com",
       "password":"StagingTest123",
       "name":"Staging User"
     }' \
     -v
   ```

   Expected:
   - Status: 201 Created
   - Response includes user data + verification message
   - NO JWT token in response

2. **Verify CSP Headers:**
   ```bash
   curl -I https://api-staging.cryptovault.onrender.com/api/health | grep Content-Security-Policy
   ```

   Should show CSP header WITHOUT `unsafe-inline` or `unsafe-eval`

3. **Test Authentication Cookies:**
   - Visit `https://cryptovault-staging.onrender.com` in browser
   - Open DevTools > Application tab
   - Sign up and verify
   - Check Cookies section - should have `accessToken` and `refreshToken`
   - Check LocalStorage - should be EMPTY

4. **Test Login & Logout:**
   - Complete email verification
   - Sign in
   - Verify dashboard loads
   - Click logout
   - Verify redirect to login
   - Try accessing protected route - should get 401

5. **Test Rate Limiting:**
   ```bash
   # Make 6 login attempts in quick succession
   for i in {1..6}; do
     curl -X POST https://api-staging.cryptovault.onrender.com/api/auth/login \
       -H "Content-Type: application/json" \
       -d '{"email":"test@example.com","password":"wrong"}' \
       -w "Attempt $i: %{http_code}\n"
   done
   ```

   Expected: First 5 return 401, 6th returns 429 (Too Many Requests)

6. **Database Pool Status:**
   - Backend logs should show pool initialization with min: 5, max: 20
   - Check for connection pool errors in logs

### Step 5: Performance Load Testing (Optional)

```bash
# Install autocannon if needed
npm install -D autocannon

# Run 30-second load test with 50 concurrent connections
npx autocannon -d 30 -c 50 \
  https://api-staging.cryptovault.onrender.com/api/health

# Expected results:
# - Mean latency < 200ms
# - P99 latency < 500ms
# - Error rate < 1%
```

---

## 🚀 Phase 3: Production Blue-Green Canary Rollout

### Step 1: Create Green Environment

**Option A: Render Platform**
1. In Render dashboard, click "Add Service"
2. Deploy existing code as "cryptovault-green" service
3. Set same environment variables as production (BLUE)
4. Deploy version `security/week1-critical-fixes`
5. Wait for health check to pass

**Option B: Manual Deployment**
```bash
# Tag the release
git tag -a v2.0.0-rc1 -m "Week 1 Security Fixes - RC1"
git push origin v2.0.0-rc1

# Deploy to green environment
# Depending on your platform:
# - Render: Create new service
# - Vercel: Create new deployment
# - AWS: Create new stack
```

### Step 2: Green Environment Verification

```bash
# Health check
curl https://cryptovault-green.onrender.com/api/health

# Quick smoke test
curl -X POST https://cryptovault-green.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"green-test@example.com",
    "password":"GreenTest123",
    "name":"Green Test"
  }'
```

### Step 3: Route Traffic - Canary 10%

**Using Render Load Balancer:**
1. Configure load balancer to send 10% traffic to GREEN
2. Monitor metrics:
   - Error rate (should be < 1%)
   - Response latency (should be < 500ms)
   - 401 errors (expected: 0.1-0.5%)
   - CSP violation reports (expected: 0)

**Monitoring Window: 30 minutes**

```bash
# Monitor error rate
watch -n 10 'curl -s https://cryptovault.onrender.com/api/health | jq'

# Check logs
tail -f /var/log/cryptovault/green.log
```

**If Issues Detected:**
```bash
# Immediate rollback
# Route 100% traffic back to BLUE
# Keep GREEN for investigation
```

### Step 4: Route Traffic - Canary 50%

If 10% traffic is stable:
1. Route 50% traffic to GREEN
2. Monitor for 30 minutes
3. Watch for:
   - User complaints in monitoring
   - Error spikes
   - Database connection issues
   - API latency degradation

### Step 5: Full Cutover to GREEN

If 50% traffic is stable:
1. Route 100% traffic to GREEN
2. Keep BLUE running as failover (1 hour minimum)
3. Monitor production metrics closely

**Metrics to Watch:**
```
Error Rate:        Target < 0.5%
Latency (p95):     Target < 500ms
CPU Usage:         Target < 70%
Memory Usage:      Target < 80%
DB Connections:    Target < 80% of pool
```

### Step 6: Decommission BLUE

After 24 hours of stable GREEN performance:
1. Tear down BLUE environment
2. Tag production version:
   ```bash
   git tag -a v2.0.0 -m "Week 1 Security Fixes - Production Release"
   git push origin v2.0.0
   ```
3. Document lessons learned

---

## 🔍 Phase 4: Production Verification (Day 1 Post-Deploy)

### Morning Checks (0-4 hours)

- [ ] Error rate normal (< 0.5%)
- [ ] No unusual 401 errors (token issues)
- [ ] User registrations working
- [ ] Email verifications succeeding
- [ ] Login/logout working
- [ ] Portfolio data loading
- [ ] Order creation working
- [ ] No CSP violation reports

### Mid-Day Checks (4-12 hours)

- [ ] Monitor alert-free operation
- [ ] Database performance stable
- [ ] API response times consistent
- [ ] User feedback positive
- [ ] No security incidents reported
- [ ] Refresh token system working (check logs)

### End-of-Day Checks (12-24 hours)

- [ ] 24-hour uptime achieved
- [ ] Error rate remains < 0.5%
- [ ] Database queries performing well
- [ ] No degradation in user experience
- [ ] All security checks passing
- [ ] Ready to move to Week 2 hardening

---

## 📊 Rollback Procedure (Emergency Only)

If critical issues detected:

### Option 1: Immediate Traffic Shift (< 1 minute downtime)
```bash
# If on BLUE failure:
# Route 100% traffic back to GREEN immediately
```

### Option 2: Code Rollback (5-10 minutes downtime)
```bash
# If on GREEN failure:
git checkout v1.0.0
git push -f origin main  # Force push previous version
# Service will redeploy automatically
```

### Option 3: Database Rollback (15-30 minutes downtime)
```bash
# If database schema issue
psql cryptovault_db < backup_$(date -d "1 hour ago" +%Y%m%d_%H).sql
```

---

## 🎯 Week 1 Success Criteria

- ✅ 0 JWT tokens in localStorage
- ✅ 100% of users receive HttpOnly cookies
- ✅ Refresh token system working (auto-refresh on 401)
- ✅ Logout revokes refresh tokens (users cannot extend sessions)
- ✅ CSP headers enforced (no inline scripts without nonce)
- ✅ Input validation on frontend (Zod schemas)
- ✅ Database pool optimized (min 5, max 20 connections)
- ✅ TypeScript strict mode enabled
- ✅ Error rate < 0.5%
- ✅ 0% increase in user-reported issues

---

## 📝 Sign-Off

- Reviewed by: _________________
- Approved by: _________________
- Deployed by: _________________
- Date: _________________________

---

## 📞 Emergency Contact

If issues arise during deployment:
1. Incident slack channel: #cryptovault-incidents
2. On-call engineer: Check rotation schedule
3. Database team: database-support@team.com
4. DevOps team: devops-support@team.com

---

**Document Status:** Ready for Week 1 Deployment  
**Last Updated:** January 9, 2024
