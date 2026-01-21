# Production Deployment Checklist - CryptoVault

**Last Updated:** January 21, 2026  
**Status:** Ready for Production Release  
**Deployment Target:** Vercel (Frontend) + Render (Backend)

---

## Pre-Deployment Phase (1-2 Days Before)

### Security & Compliance
- [ ] Run security audit: `npm audit` (fix all HIGH and CRITICAL)
- [ ] Review all environment secrets - ensure no secrets in code
- [ ] Verify CORS configuration for production domains
- [ ] Enable HTTPS everywhere (automatic on Vercel/Render)
- [ ] Check Content Security Policy headers in vercel.json
- [ ] Verify CSRF token generation and validation
- [ ] Review authentication token expiration and refresh logic
- [ ] Enable rate limiting on API endpoints (backend)
- [ ] Verify firewall rules and DDoS protection via Cloudflare (if using)

### Performance & Optimization
- [ ] Run Lighthouse audit on production-like build
  ```bash
  npm run build
  npm run preview
  # Open in Chrome DevTools > Lighthouse
  ```
- [ ] Check bundle size (target: <150KB main bundle)
  ```bash
  npm run build
  # Check dist/ folder sizes
  ```
- [ ] Verify compression is enabled (Gzip/Brotli)
- [ ] Test Service Worker offline functionality
- [ ] Verify caching headers for static assets
- [ ] Check Core Web Vitals (LCP, FID, CLS)
- [ ] Performance test with network throttling (3G)

### Testing & QA
- [ ] Run full test suite: `npm run test` (if exists)
- [ ] Run ESLint: `npm run lint`
- [ ] Manual smoke tests on staging:
  - [ ] Login/Logout flow
  - [ ] API calls under normal conditions
  - [ ] API calls under simulated slow network
  - [ ] API calls with network outage (Service Worker fallback)
  - [ ] WebSocket connections and real-time data
  - [ ] Offline mode functionality
  - [ ] Mobile responsiveness (iOS Safari, Chrome, Android)
  - [ ] Form submissions and validations
  - [ ] Payment/transaction flows
- [ ] Test error scenarios:
  - [ ] Server downtime
  - [ ] Network timeout
  - [ ] Invalid responses
  - [ ] Rate limiting
  - [ ] Authentication failures
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Cross-browser testing:
  - [ ] Chrome (latest)
  - [ ] Firefox (latest)
  - [ ] Safari (latest)
  - [ ] Edge (latest)

### Database & Backend
- [ ] Database backups configured and tested
- [ ] Run database migrations on staging
- [ ] Verify database connection pooling
- [ ] Check backend logging configuration
- [ ] Verify backend monitoring and alerting
- [ ] Test backend auto-scaling policies
- [ ] Verify environment variables are set in production
- [ ] Test JWT token rotation and expiration
- [ ] Verify Redis/cache configuration (if using)

### Infrastructure & Deployment
- [ ] Vercel project configured with production environment
  - [ ] Custom domain configured
  - [ ] SSL certificate verified
  - [ ] Environment variables added
  - [ ] Build and preview deployments verified
- [ ] Render backend configured
  - [ ] Custom domain or API endpoint configured
  - [ ] Auto-scaling rules configured
  - [ ] Environment variables added
  - [ ] Persistent volumes configured (if using databases)
  - [ ] Health check endpoint configured
- [ ] Database backups scheduled (daily)
- [ ] Log aggregation configured (Sentry, DataDog, etc.)
- [ ] Monitoring and alerting rules set up
- [ ] Incident response plan documented
- [ ] Rollback procedure documented and tested

### Documentation
- [ ] README updated with production URLs
- [ ] Environment variables documented in `.env.example`
- [ ] Deployment guide created for team
- [ ] Runbook created for common issues
- [ ] Incident response procedure documented
- [ ] API documentation current (Swagger/OpenAPI)
- [ ] System architecture diagram updated

---

## Deployment Phase (Day of Deployment)

### Pre-Deployment Steps (30 mins before)
- [ ] Notify stakeholders of deployment window
- [ ] Create incident channel/war room
- [ ] Have rollback plan ready
- [ ] Verify all team members are available for support
- [ ] Take final database backup
- [ ] Verify monitoring dashboards are accessible

### Backend Deployment (Render)
```bash
# 1. Review environment variables in Render dashboard
# 2. Check deploy logs for any pre-deployment errors
# 3. Visit https://api.yourdomain.com/health to verify health endpoint

# If using Git deployment:
git push origin main  # This triggers automatic deployment on Render
# Monitor deployment in Render dashboard > Logs

# Manual verification:
curl -I https://api.yourdomain.com/health
# Expected: HTTP/1.1 200 OK
```

**Checklist:**
- [ ] Backend deployment triggered
- [ ] Build logs show no errors
- [ ] Health endpoint returns 200
- [ ] Database migrations completed successfully
- [ ] All environment variables loaded correctly
- [ ] WebSocket endpoint accessible (for Socket.IO)
- [ ] API endpoints responding normally

### Frontend Deployment (Vercel)
```bash
# 1. Ensure all tests pass locally
npm run build
npm run lint

# 2. Create git tag for this release
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# 3. Push to main branch (triggers Vercel deployment)
git push origin main

# Vercel will automatically build and deploy
# Monitor at vercel.com > Your Project > Deployments
```

**Checklist:**
- [ ] All code committed and pushed
- [ ] Build completes without errors
- [ ] Tests pass (if configured)
- [ ] Preview deployment successful
- [ ] Preview URLs accessible
- [ ] Service Worker loads correctly
- [ ] Service Worker cache working
- [ ] API calls routing to correct backend

### Post-Deployment Verification (2 hours)

#### Immediate Checks (0-10 mins)
- [ ] Access production URL in browser
- [ ] Check for any console errors (DevTools)
- [ ] Verify Service Worker registration (DevTools > Application)
- [ ] Check Network tab for API calls
- [ ] Monitor Sentry for errors in real-time

#### Smoke Tests (10-30 mins)
- [ ] Login flow works
- [ ] Dashboard loads and displays data
- [ ] API calls succeed (<500ms response time)
- [ ] WebSocket connection established
- [ ] Real-time data updates working
- [ ] Navigation works without errors
- [ ] Forms submit successfully
- [ ] File uploads (if applicable) work
- [ ] Logout flow works

#### Performance Checks (30-45 mins)
- [ ] Run Lighthouse audit on production
- [ ] Check Core Web Vitals in Sentry
- [ ] Monitor error rates in Sentry (should be <0.1%)
- [ ] Check response times in Sentry (p95 should be <500ms)
- [ ] Monitor backend resource usage (CPU, memory, requests/s)
- [ ] Check database performance (query times)
- [ ] Verify CDN is caching static assets

#### Load Testing (45-60 mins)
```bash
# Use Apache Bench or similar
ab -n 1000 -c 10 https://yourdomain.com/
# Monitor backend during load test
```

#### Error Scenario Tests (60-90 mins)
- [ ] Simulate network outage (Service Worker fallback works)
- [ ] Simulate slow network (graceful degradation)
- [ ] Simulate server error (error handling works)
- [ ] Verify error messages are user-friendly
- [ ] Check retry logic works for failures

#### Monitoring & Alerting (90-120 mins)
- [ ] All monitoring dashboards showing data
- [ ] Alerting rules configured and working
- [ ] Sentry receiving error events
- [ ] Analytics tracking page views
- [ ] Performance metrics being collected
- [ ] No false positive alerts firing

---

## Post-Deployment Phase (Days 1-7)

### Daily Checks
- [ ] Check error rate in Sentry (should stay <0.1%)
- [ ] Review performance metrics (response times, load times)
- [ ] Check for any failed API requests
- [ ] Monitor uptime (should be >99.9%)
- [ ] Review user feedback and support tickets

### First Week Checks
- [ ] Monitor for any unusual patterns in error logs
- [ ] Review performance reports (Core Web Vitals)
- [ ] Check for any resource leaks (memory, connections)
- [ ] Verify backup and recovery procedures work
- [ ] Get team feedback on deployment process
- [ ] Document any issues encountered and resolutions

### Production Monitoring Dashboard

Set up monitoring for these metrics:

| Metric | Target | Tools |
|--------|--------|-------|
| Error Rate | <0.1% | Sentry |
| Uptime | >99.9% | StatusPage.io |
| API Response Time (p50) | <100ms | Sentry |
| API Response Time (p95) | <500ms | Sentry |
| First Contentful Paint | <2s | Lighthouse |
| Largest Contentful Paint | <2.5s | Lighthouse |
| Cumulative Layout Shift | <0.1 | Lighthouse |
| Service Worker Cache Hit Rate | >70% | Custom |
| User Session Duration | Monitor | Google Analytics |
| Conversion Rate | Monitor | Analytics |

---

## Rollback Procedure (If Issues Arise)

### Immediate Response
1. **Alert the team** - Post in incident channel
2. **Assess severity** - Error rate? Functionality broken? User impact?
3. **Decide: Hotfix or Rollback**
   - Hotfix: If minor issue, deploy fix to main and push new version
   - Rollback: If critical issue affecting many users, rollback immediately

### Rollback Steps

#### Vercel Rollback (Frontend)
```bash
# 1. Go to Vercel dashboard > Deployments
# 2. Find the last working deployment
# 3. Click the three dots menu > Promote to Production

# Or via CLI:
vercel rollback --token $VERCEL_TOKEN
```

#### Render Rollback (Backend)
```bash
# 1. Go to Render dashboard > Services > Backend
# 2. Find the last working deployment
# 3. Click "Deploy" next to that version

# Or via Git:
git revert HEAD  # Revert last commit
git push origin main  # Push revert
```

#### Manual Hotfix
```bash
# 1. Create hotfix branch
git checkout -b hotfix/issue-description

# 2. Fix the issue
# 3. Commit and push
git commit -am "Fix: issue description"
git push origin hotfix/issue-description

# 4. Create Pull Request
# 5. Merge to main after review
# 6. Deploy (same as normal deployment)
```

---

## Important Production URLs

| Service | URL | Status Page |
|---------|-----|-------------|
| Frontend | https://cryptovault.com | - |
| API | https://api.cryptovault.com | - |
| Health Check | https://api.cryptovault.com/health | - |
| Monitoring | https://sentry.io/organizations/your-org | - |
| Analytics | https://analytics.google.com | - |
| Logs | https://your-logs-service.com | - |

---

## Emergency Contacts

| Role | Name | Phone | Email |
|------|------|-------|-------|
| DevOps Lead | TBD | - | - |
| Backend Lead | TBD | - | - |
| Frontend Lead | TBD | - | - |
| Product Manager | TBD | - | - |
| CEO | TBD | - | - |

---

## Post-Incident Retrospective

After any major incident:
1. [ ] Conduct 48-hour retrospective meeting
2. [ ] Document root cause and timeline
3. [ ] Create action items for prevention
4. [ ] Update runbook with lessons learned
5. [ ] Share findings with team
6. [ ] Update monitoring/alerting as needed

---

**Last Deployed:** [Add date and version]  
**Deployed By:** [Add name]  
**Notes:** [Add any important notes about this deployment]
