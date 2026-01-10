# 🚀 CryptoVault Production Deployment Guide

This guide covers everything needed to deploy CryptoVault to production on Render with comprehensive security hardening.

## Table of Contents

1. [Security Configuration](#security-configuration)
2. [Environment Variables Setup](#environment-variables-setup)
3. [Render Deployment Steps](#render-deployment-steps)
4. [Database Setup](#database-setup)
5. [Verification & Testing](#verification--testing)
6. [Post-Deployment Monitoring](#post-deployment-monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Security Configuration

### Week 1: Security Hardening Implementation ✅

The following security measures have been implemented:

#### 1. **Rate Limiting**
- ✅ General API limiter: 100 requests per 15 minutes per IP
- ✅ Auth limiter: 5 attempts per 15 minutes (prevents brute force)
- ✅ Strict limiter: 20 requests per 15 minutes for sensitive endpoints

**Files:** `server/src/middleware/security.ts`

#### 2. **Input Validation & Sanitization**
- ✅ Email validation and normalization
- ✅ Password requirements: min 8 chars, uppercase, lowercase, numbers
- ✅ Name sanitization (HTML escaping)
- ✅ Trading pair validation
- ✅ Amount/price validation with positive numbers only
- ✅ Symbol validation (2-10 uppercase letters)

**Files:** `server/src/middleware/security.ts`, `server/src/utils/validation.ts`

#### 3. **Security Headers**
- ✅ Helmet.js for OWASP security headers
- ✅ Content Security Policy (CSP)
- ✅ X-Frame-Options (prevent clickjacking)
- ✅ X-Content-Type-Options (prevent MIME sniffing)
- ✅ Custom security headers

**Files:** `server/src/server.ts`, `server/src/middleware/security.ts`

#### 4. **CORS Protection**
- ✅ Dynamic CORS origin configuration
- ✅ Different behavior for development vs. production
- ✅ Credentials handling
- ✅ Allowed HTTP methods and headers

**Code Location:** `server/src/middleware/security.ts` → `getCorsOptions()`

#### 5. **Payload Size Protection**
- ✅ JSON payload limit: 10KB (prevents large payload attacks)
- ✅ URL-encoded payload limit: 10KB

**Code Location:** `server/src/server.ts` → `express.json({ limit: '10kb' })`

---

## Environment Variables Setup

### Step 1: Generate Secure Secrets

Before deploying, generate strong random values for sensitive keys:

```bash
# Generate JWT_SECRET (32-character hex string)
openssl rand -hex 32
# Output: abc123def456... (copy this value)

# Generate a strong database password
openssl rand -base64 32
# Output: your-secure-password-here
```

### Step 2: Required Environment Variables

Copy these variables to your Render environment:

```env
# DATABASE
DATABASE_URL=postgresql://user:password@host:5432/cryptovault
DB_HOST=your-postgres-instance.c.render.com
DB_PORT=5432
DB_NAME=cryptovault
DB_USER=postgres
DB_PASSWORD=your-secure-password

# SECURITY
JWT_SECRET=your-generated-32-char-hex-string
JWT_EXPIRY=7d

# SERVER
NODE_ENV=production
PORT=5000

# CORS
CORS_ORIGIN=https://your-frontend-domain.onrender.com
```

### Step 3: Optional Advanced Configuration

```env
# MONITORING
LOG_LEVEL=info
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id

# CACHING (when Redis is available)
# REDIS_URL=redis://...
CACHE_TTL=300
```

---

## Render Deployment Steps

### Prerequisites

1. GitHub account with CryptoVault repository
2. Render account (https://render.com)
3. Generated JWT_SECRET (see above)

### Step 1: Create Render Account & Connect GitHub

1. Go to https://render.com
2. Click "Sign up with GitHub"
3. Authorize Render to access your repositories
4. Choose the CryptoVault repository

### Step 2: Create PostgreSQL Database

1. In Render dashboard, click "New +"
2. Select "PostgreSQL"
3. Database name: `cryptovault`
4. Region: Select closest to your users
5. Click "Create Database"
6. Wait for database to initialize (~5 minutes)
7. Copy the connection string (you'll use this for DATABASE_URL)

### Step 3: Deploy Backend Service

1. In Render dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Name: `cryptovault-backend`
5. Environment: `Node`
6. Build Command: `cd server && npm install && npm run build`
7. Start Command: `cd server && npm start`
8. Region: Same as database
9. Plan: Choose appropriate tier (starter or higher)
10. Click "Create Web Service"

### Step 4: Configure Environment Variables

1. Go to your web service settings
2. Click "Environment"
3. Add all variables from [Step 2](#step-2-required-environment-variables):

```
DATABASE_URL=postgresql://user:password@postgres-host/cryptovault
JWT_SECRET=your-generated-secret-here
CORS_ORIGIN=https://your-frontend-onrender.com
NODE_ENV=production
PORT=5000
JWT_EXPIRY=7d
```

4. Link PostgreSQL instance if available in Render UI
5. Save variables
6. Service will auto-redeploy

### Step 5: Deploy Frontend Service

1. Click "New +"
2. Select "Static Site"
3. Connect GitHub repository
4. Name: `cryptovault-frontend`
5. Build Command: `npm install && npm run build`
6. Publish Directory: `dist`
7. Add environment variable:
   ```
   VITE_API_URL=https://cryptovault-backend.onrender.com
   ```
8. Click "Create Static Site"

### Step 6: Configure Frontend API Proxy

Update `src/lib/api.ts` to use production backend URL:

```typescript
const apiBaseURL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
```

### Step 7: Update CORS_ORIGIN

After frontend deployment completes:
1. Note the frontend URL (e.g., https://cryptovault-frontend.onrender.com)
2. Go back to backend service environment variables
3. Update `CORS_ORIGIN` to match frontend URL
4. Save - backend will redeploy

---

## Database Setup

### Automatic Schema Initialization

The database schema is automatically created when the backend starts:

- Users table (with email unique constraint)
- Portfolios table (linked to users)
- Holdings table (user cryptocurrency holdings)
- Orders table (trading orders)
- Transactions table (transaction history)

All tables include:
- Auto-generated UUIDs as primary keys
- Automatic timestamps (created_at, updated_at)
- Foreign key constraints for referential integrity
- Proper indexes on frequently queried columns

### Manual Database Access (if needed)

To connect directly to your production database:

```bash
# Using psql (requires PostgreSQL client installed)
psql postgresql://user:password@host:port/database

# List tables
\dt

# Count users
SELECT COUNT(*) FROM users;

# View connections
\l

# Exit
\q
```

---

## Verification & Testing

### Step 1: Health Check

```bash
# Frontend should load
curl https://cryptovault-frontend.onrender.com

# Backend health endpoint
curl https://cryptovault-backend.onrender.com/health

# Expected response
{"status":"ok","timestamp":"2024-01-08T..."}
```

### Step 2: API Endpoint Testing

Test the API with curl or Postman:

```bash
# Sign up
curl -X POST https://cryptovault-backend.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"SecurePass123",
    "name":"Test User"
  }'

# Save the returned token
TOKEN="your-token-here"

# Get current user
curl https://cryptovault-backend.onrender.com/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Get crypto prices
curl https://cryptovault-backend.onrender.com/api/crypto
```

### Step 3: Security Validation

- ✅ Test rate limiting: Make 6 signup requests in quick succession (6th should fail)
- ✅ Test invalid input: Send invalid email format (should reject)
- ✅ Test CORS: Frontend should load backend data
- ✅ Test HTTPS: All requests must use HTTPS
- ✅ Check security headers: Use curl -I to verify headers

```bash
# Check security headers
curl -I https://cryptovault-backend.onrender.com/health

# Expected headers:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: ...
```

### Step 4: User Flow Testing

1. Open https://cryptovault-frontend.onrender.com
2. Click "Get Started" → Sign up
3. Use email: test@example.com, password: TestPass123
4. Should redirect to home page
5. Go to Markets → See live crypto prices
6. Go to Dashboard → See portfolio
7. Go to Trade → Try placing an order
8. Go to Transactions → See transaction history

---

## Post-Deployment Monitoring

### Enable Error Tracking with Sentry (Optional but Recommended)

1. Create Sentry account: https://sentry.io
2. Create new project for Node.js
3. Get DSN: `https://key@sentry.io/project-id`
4. Add to backend environment variables: `SENTRY_DSN=...`
5. Backend will now report all errors to Sentry

### Monitor Logs

In Render dashboard:
1. Go to backend service
2. Click "Logs"
3. View real-time server logs
4. Look for any errors or warnings

### Monitor Performance

Track these metrics:
- Response times (should be < 200ms for most endpoints)
- Error rates (should be < 1%)
- Database query times
- Rate limit hits (should be minimal)

### Set Up Alerts

Render can notify you of:
- Service crashes
- Build failures
- High error rates
- Memory/CPU issues

---

## Security Checklist

Before going live, verify:

- [ ] JWT_SECRET is 32+ characters and randomly generated
- [ ] Database password is strong and not shared
- [ ] CORS_ORIGIN matches your frontend domain exactly
- [ ] NODE_ENV is set to "production"
- [ ] Database is backed up (Render automatic)
- [ ] HTTPS enforced (Render automatic)
- [ ] Rate limiting is working (test by making 6 rapid requests)
- [ ] Input validation rejects bad data
- [ ] Security headers are present (curl -I)
- [ ] Sentry is configured for error tracking
- [ ] Health check endpoint is accessible

---

## Troubleshooting

### Database Connection Error

**Error:** `ECONNREFUSED` or `Connection refused`

**Solution:**
1. Verify DATABASE_URL is correct
2. Check database instance is running in Render
3. Verify DB_HOST, DB_USER, DB_PASSWORD environment variables
4. Wait 5 minutes after creating database (takes time to initialize)

### CORS Errors in Frontend

**Error:** `Access to XMLHttpRequest blocked by CORS policy`

**Solution:**
1. Verify CORS_ORIGIN matches frontend URL exactly (including protocol and domain)
2. Restart backend service after changing CORS_ORIGIN
3. Clear browser cache and cookies
4. Check browser console for exact error message

### Rate Limiting Too Strict

**Error:** `Too many requests` on legitimate usage

**Solution:**
1. Adjust rate limit in `server/src/middleware/security.ts`
2. Increase `max` values in `authLimiter` or `generalLimiter`
3. Redeploy backend

### JWT Token Errors

**Error:** `Invalid or expired token`

**Solution:**
1. Verify JWT_SECRET is same in environment variables
2. Check token hasn't expired (default 7 days)
3. Ensure Authorization header format: `Bearer <token>`

### Build Failures

**Error:** Build fails in Render dashboard

**Solution:**
1. Check build logs in Render
2. Common issues:
   - Missing npm dependencies (run `npm install`)
   - TypeScript compilation errors
   - Environment variables not set
3. Run locally: `cd server && npm install && npm run build`

### Service Crashes Immediately

**Error:** Service keeps restarting

**Solution:**
1. Check logs: Render dashboard → Logs
2. Look for error messages
3. Common causes:
   - Missing environment variables
   - Database connection failed
   - Port already in use
4. Fix and redeploy

---

## Rollback Procedure

If something goes wrong in production:

1. In Render dashboard, go to backend service
2. Click "Deployments"
3. Select previous working deployment
4. Click "Redeploy"
5. Verify health check passes
6. Test critical user flows

---

## Support & Resources

- **Render Docs:** https://render.com/docs
- **Express.js Docs:** https://expressjs.com
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Helmet.js Docs:** https://helmetjs.github.io/
- **Rate Limit Docs:** https://github.com/nfriedly/express-rate-limit

---

## Next Steps

After successful deployment to production:

1. ✅ Monitor logs and errors for first 24 hours
2. ✅ Test all critical user paths in production
3. ✅ Set up automated backups (Render handles this)
4. ✅ Configure monitoring/alerting (Sentry, Render alerts)
5. ✅ Document any custom configurations
6. 🚀 Proceed to Week 2: Performance & Caching
7. 🚀 Proceed to Week 3: WebSocket Implementation

---

**Estimated deployment time:** 30-45 minutes

**Status:** ✅ Ready for production deployment!
