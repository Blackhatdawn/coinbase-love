# CryptoVault - Production Deployment Checklist

## Your Production URLs
- **Frontend:** https://www.cryptovault.financial
- **Backend:** https://cryptovault-api.onrender.com

---

## Pre-Deployment (Before Going Live)

### Backend Configuration (Render.com)

- [ ] Backend service created and connected to GitHub
- [ ] Build command configured:
  ```
  pip install -r backend/requirements.txt
  ```
- [ ] Start command configured:
  ```
  gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.server:socket_app --bind 0.0.0.0:$PORT
  ```

### Backend Environment Variables (Set in Render Dashboard)

**Critical (Required):**
- [ ] `ENVIRONMENT=production`
- [ ] `JWT_SECRET=` (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `CSRF_SECRET=` (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- [ ] `DATABASE_URL=` (MongoDB Atlas connection string)
- [ ] `REDIS_URL=` (Redis instance URL)
- [ ] `CORS_ORIGINS=https://www.cryptovault.financial,https://cryptovault.financial`

**Recommended:**
- [ ] `SENTRY_DSN=` (error tracking)
- [ ] `SMTP_HOST=smtp.sendgrid.net`
- [ ] `SMTP_USERNAME=apikey`
- [ ] `SMTP_PASSWORD=` (SendGrid API key)
- [ ] `EMAIL_FROM=noreply@cryptovault.financial`

**Optional (Feature Flags):**
- [ ] `FEATURE_2FA_ENABLED=true`
- [ ] `FEATURE_TRADING_ENABLED=true`
- [ ] `RATE_LIMIT_REQUESTS_PER_MINUTE=60`

### Frontend Configuration (Vercel)

- [ ] Frontend repository connected to Vercel
- [ ] Build command: `cd frontend && yarn install && yarn build`
- [ ] Output directory: `frontend/dist`
- [ ] Build framework: Vite
- [ ] Environment variable `VITE_API_BASE_URL=` (leave empty - uses relative paths)
- [ ] `vercel.json` updated with backend URL (already done: `https://cryptovault-api.onrender.com`)
- [ ] Custom domain configured: `www.cryptovault.financial`
- [ ] SSL certificate auto-enabled

### Network Configuration

- [ ] Backend CORS accepts frontend domain
- [ ] Frontend rewrites proxy to backend domain
- [ ] DNS records point to correct services:
  - `www.cryptovault.financial` → Vercel
  - `api.cryptovault.financial` → Render (if using custom domain)

### Security Verification

- [ ] No hardcoded secrets in code (grep check completed)
- [ ] Environment variables are set, not in `.env` files
- [ ] JWT_SECRET and CSRF_SECRET are unique random strings
- [ ] Database credentials are secure
- [ ] Redis instance is private/authenticated
- [ ] CORS origins are specific (not wildcard `*`)
- [ ] Security headers enabled in `vercel.json`

### Database & Cache

- [ ] MongoDB Atlas cluster exists and is accessible
- [ ] Redis instance exists and is accessible
- [ ] Database backups configured
- [ ] Redis persistence configured
- [ ] Connection strings verified in env vars

### Email Service

- [ ] SendGrid account created (or alternative SMTP)
- [ ] API key generated and stored securely
- [ ] Sender email domain verified in SendGrid
- [ ] Email templates tested

### Error Tracking (Optional but Recommended)

- [ ] Sentry project created at https://sentry.io
- [ ] DSN copied to `SENTRY_DSN` env var
- [ ] Environment set to `production`
- [ ] Sentry alerts configured for critical errors

---

## Deployment Day

### Backend Deployment

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Production deployment configuration"
   git push origin main
   ```

2. **Render Auto-Deploy:**
   - Render automatically deploys when main branch is pushed
   - Monitor deployment progress in Render dashboard
   - Wait for "Deploy Live" status

3. **Verify Backend:**
   ```bash
   # Should return pong
   curl https://cryptovault-api.onrender.com/ping
   
   # Should return health status
   curl https://cryptovault-api.onrender.com/health
   ```

4. **Check Startup Logs:**
   - Render Dashboard → Logs
   - Look for: `✅ Environment Validated`
   - Ensure no `❌ STARTUP FAILED` messages

### Frontend Deployment

1. **Vercel Auto-Deploy:**
   - Vercel automatically deploys when GitHub is pushed
   - Monitor deployment in Vercel dashboard
   - Wait for "Production Deployment" badge

2. **Verify Frontend:**
   ```bash
   # Visit production URL
   https://www.cryptovault.financial
   
   # Check browser console for errors
   # Should see no CORS errors
   # Should see API requests to /api/* endpoints
   ```

3. **Test Critical Flows:**
   - [ ] Login/signup works
   - [ ] API requests succeed (no 500 errors)
   - [ ] WebSocket connects (Socket.IO)
   - [ ] Health check passes
   - [ ] No console errors

---

## Post-Deployment (First 24 Hours)

### Monitoring

- [ ] Check Render logs for errors
- [ ] Check Vercel logs for errors
- [ ] Monitor Sentry for exceptions (if configured)
- [ ] Verify database connectivity (no timeout errors)
- [ ] Check Redis cache hits/misses
- [ ] Monitor rate limiting (adjust if needed)

### Functional Testing

- [ ] User registration works
- [ ] Login works
- [ ] Portfolio page loads and refreshes data
- [ ] Trading functionality works (if enabled)
- [ ] WebSocket price updates come through
- [ ] Email notifications send
- [ ] 2FA works (if enabled)

### Performance Checks

- [ ] Frontend Lighthouse score >80
- [ ] API response times <200ms
- [ ] Database queries are fast
- [ ] No 500 errors in logs
- [ ] No "too many connections" errors

### Security Checks

- [ ] HTTPS enforced (redirects http to https)
- [ ] Security headers present (check with curl):
  ```bash
  curl -I https://www.cryptovault.financial
  # Should show: Strict-Transport-Security, X-Frame-Options, etc.
  ```
- [ ] CORS headers correct for API requests
- [ ] CSRF tokens generated and validated
- [ ] No sensitive data in logs
- [ ] No API keys exposed in responses

### Rollback Plan

If critical issues arise:

1. **Revert Frontend:**
   - Go to Vercel → Deployments
   - Click "Rollback" on previous successful deployment

2. **Revert Backend:**
   - Go to Render → Service → Deployments
   - Select previous working deployment
   - Click "Deploy"

3. **Check Logs:**
   - Review error logs to identify issue
   - Fix in development
   - Redeploy

---

## Ongoing Maintenance

### Weekly

- [ ] Review error logs in Sentry
- [ ] Check database storage usage
- [ ] Verify all critical endpoints respond
- [ ] Monitor rate limit usage (adjust if needed)

### Monthly

- [ ] Review and rotate JWT/CSRF secrets if needed
- [ ] Update dependencies: `pip list --outdated`
- [ ] Check for security patches
- [ ] Review cloud service costs

### Quarterly

- [ ] Database optimization and indexing
- [ ] Cache strategy review
- [ ] Load testing under expected traffic
- [ ] Disaster recovery drill

---

## Useful Commands

### Backend Health Check
```bash
# Quick ping
curl https://cryptovault-api.onrender.com/ping

# Full health status
curl https://cryptovault-api.onrender.com/health

# API documentation
https://cryptovault-api.onrender.com/api/docs

# WebSocket health
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  https://cryptovault-api.onrender.com/socket.io/
```

### Frontend Debugging
```bash
# Check CSP headers
curl -I https://www.cryptovault.financial | grep -i "content-security"

# Check service worker
curl https://www.cryptovault.financial/sw.js

# Test API proxy
curl -v https://www.cryptovault.financial/api/ping
```

### Environment Variables (Render)
```bash
# SSH into Render service (if needed)
# Run from Render dashboard → Service → Shell

# View config
env | grep CRYPTOVAULT_

# Restart service
# Use Render dashboard → Service → Restart
```

---

## Emergency Contacts

- **Vercel Support:** https://vercel.com/support
- **Render Support:** https://render.com/support
- **MongoDB Support:** https://www.mongodb.com/support
- **Sentry Support:** https://sentry.io/support

---

## Success Criteria

✅ Deployment is successful when:

1. **Frontend loads** without console errors
2. **Backend responds** to health checks (200 OK)
3. **API requests** go through without CORS errors
4. **WebSocket connects** for real-time updates
5. **Users can login/signup** successfully
6. **Database queries** return data correctly
7. **No 500 errors** in backend logs
8. **Security headers** are present
9. **SSL/TLS certificate** is valid
10. **Performance** meets targets (<200ms API response)

---

## Configuration Summary

| Component | URL | Status |
|-----------|-----|--------|
| Frontend | https://www.cryptovault.financial | Vercel |
| Backend API | https://cryptovault-api.onrender.com | Render |
| Documentation | https://cryptovault-api.onrender.com/api/docs | Auto-generated |
| Database | MongoDB Atlas | Configured |
| Cache | Redis | Configured |
| Error Tracking | Sentry | Optional |
| Email | SendGrid | Configured |

---

**Last Updated:** 2025-01-21  
**Deployment Status:** Ready for production  
**Configuration Version:** Enterprise Grade v1.0
