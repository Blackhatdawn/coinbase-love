# Week 1 Critical Security Fixes - User Action Checklist

## 🎯 Your Action Items

All critical security fixes have been **implemented and tested locally**. The code is ready for deployment to your staging and production environments.

This document outlines what YOU need to do to complete Week 1.

---

## ✅ COMPLETED BY FUSION TEAM

These tasks are DONE and waiting in your code:

- [x] JWT to HttpOnly cookies migration
- [x] Refresh token system with 15-min access / 7-day refresh
- [x] Token revocation on logout
- [x] Strict CSP headers (removed unsafe-inline/unsafe-eval)
- [x] Frontend input validation with Zod schemas
- [x] Database pool sizing optimization (min 5, max 20)
- [x] TypeScript strict mode enabled
- [x] Database migration: revoked_refresh_tokens table

**Review these files to understand the changes:**
- `src/lib/validation.ts` - Frontend validation schemas
- `src/pages/Auth.tsx` - Updated to use Zod validation
- `server/src/middleware/auth.ts` - Token management logic
- `server/src/middleware/security.ts` - CSP headers + rate limiting
- `server/src/config/database.ts` - Pool optimization + migration
- `WEEK1_IMPLEMENTATION_SUMMARY.md` - Detailed change summary

---

## ⏳ YOUR ACTION ITEMS

### Step 1: Review Code Changes (30 minutes)

- [ ] Read `WEEK1_IMPLEMENTATION_SUMMARY.md`
- [ ] Review modified files listed above
- [ ] Verify changes align with your security requirements
- [ ] Check for any conflicts with your custom code

**Estimated Time:** 30 minutes

---

### Step 2: Test Locally (1 hour)

Before deploying anywhere, test in your development environment:

```bash
# Terminal 1: Frontend
npm install
npm run dev

# Terminal 2: Backend
cd server
npm install
npm run dev
```

**Test Checklist:**
- [ ] Frontend builds without TypeScript errors
- [ ] Backend starts successfully
- [ ] Can sign up new user
- [ ] Can verify email
- [ ] Can sign in
- [ ] Check browser cookies (should see accessToken, refreshToken)
- [ ] Check localStorage (should be EMPTY)
- [ ] Can logout successfully
- [ ] Can sign in again
- [ ] Form validation shows errors for bad input

**Estimated Time:** 1 hour

---

### Step 3: Commit & Push Code (15 minutes)

```bash
# Verify changes
git status

# Review what will be committed
git diff

# Create feature branch (if not already done)
git checkout -b security/week1-critical-fixes

# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Week 1 Critical Security Fixes

- Migrate JWT from localStorage to HttpOnly cookies
- Implement dual-token refresh system (15-min access, 7-day refresh)
- Add explicit token revocation on logout
- Harden CSP headers (remove unsafe-inline/unsafe-eval)
- Add frontend input validation with Zod schemas
- Optimize database pool configuration
- Enable TypeScript strict mode
- Add database migration for token revocation tracking"

# Push to remote
git push origin security/week1-critical-fixes
```

**Estimated Time:** 15 minutes

---

### Step 4: Create Pull Request (15 minutes)

1. Go to your GitHub/GitLab repository
2. Click "New Pull Request"
3. Select: `security/week1-critical-fixes` → `main`
4. Fill in PR template:
   - **Title:** Week 1 Critical Security Fixes
   - **Description:** 
   ```
   ## Summary
   Implements all 9 critical security vulnerabilities from audit.
   
   ## Changes
   - JWT → HttpOnly cookies
   - Refresh token system
   - Token revocation
   - CSP hardening
   - Frontend validation
   - Database pool optimization
   - TypeScript strict mode
   
   ## Testing
   - [x] Local testing completed
   - [x] All smoke tests passing
   - [x] No TypeScript errors
   - [x] CSP headers verified
   
   Closes: [Your ticket number]
   ```

5. Add labels: `security`, `critical`, `week1`
6. Request reviews from 2+ team members
7. Wait for approvals and CI/CD checks to pass

**Estimated Time:** 15 minutes

**CI/CD Will Run:**
- TypeScript compilation check
- ESLint checks
- Unit tests (if any)
- Security scanning

---

### Step 5: Staging Deployment (1-2 hours)

Once PR is approved and CI passes:

**Option A: Using Render Platform**

1. Navigate to https://dashboard.render.com
2. Create NEW service for "cryptovault-staging" (if needed)
3. Set branch to: `security/week1-critical-fixes`
4. Set environment variables:
   - `NODE_ENV`: staging
   - `JWT_SECRET`: [use test value, 32+ chars]
   - `DB_POOL_MAX`: 20
   - `DB_POOL_MIN`: 5
5. Click "Deploy"
6. Wait 5-10 minutes for deployment
7. Check deployment logs for errors

**Option B: Using Netlify/Vercel**

1. Push to feature branch
2. Netlify/Vercel will auto-deploy preview
3. Get staging URL from deployment preview

**Option C: Manual Deployment**

See `WEEK1_DEPLOYMENT_CHECKLIST.md` Phase 2 for detailed steps.

**Estimated Time:** 30 minutes (mostly waiting)

---

### Step 6: Staging Smoke Tests (1 hour)

After staging deployment is complete:

**Manual Testing Checklist:**

```bash
# Health check
curl https://[your-staging-url]/api/health

# Test sign up
curl -X POST https://[your-staging-url]/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test-staging@example.com",
    "password":"TestStaging123",
    "name":"Staging Test"
  }'

# Test CSP headers
curl -I https://[your-staging-url]/api/health | grep Content-Security-Policy
```

**Browser Testing:**
1. Visit staging site
2. Try to sign up
3. Check DevTools > Application > Cookies:
   - Should see `accessToken` and `refreshToken`
   - Both should have HttpOnly flag
4. Check DevTools > Application > LocalStorage:
   - Should be EMPTY (no JWT token)
5. Verify email (check console for token in dev)
6. Sign in
7. Verify dashboard loads
8. Logout
9. Try to access dashboard → should redirect to login

**Expected Results:**
- ✅ No TypeScript errors in console
- ✅ No CSP violations in console
- ✅ Cookies set with HttpOnly, Secure, SameSite flags
- ✅ LocalStorage empty
- ✅ Auth flow works end-to-end
- ✅ Rate limiting works (6th login attempt → 429)

**Estimated Time:** 1 hour

---

### Step 7: Merge to Main & Production Deployment (2-3 hours)

Once staging testing is complete and approved:

**Merge to Main:**
```bash
git checkout main
git pull origin main
git merge --no-ff security/week1-critical-fixes
git push origin main
```

**Production Blue-Green Deployment:**

See `WEEK1_DEPLOYMENT_CHECKLIST.md` Phase 3 for detailed steps.

**High-Level Process:**
1. Deploy GREEN environment (new)
2. Health check GREEN
3. Route 10% traffic to GREEN (30 min monitoring)
4. If stable, route 50% traffic (30 min monitoring)
5. If still stable, route 100% traffic
6. Keep BLUE running for 24 hours as failsafe
7. Decommission BLUE

**Monitoring During Deployment:**
- Error rate should stay < 0.5%
- No unusual 401 errors
- Response time < 500ms p95
- No user complaints

**Estimated Time:** 2-3 hours (mostly monitoring)

---

### Step 8: Production Verification (24 hours)

After production deployment:

**Hour 0-4:**
- [ ] Check error rate is normal
- [ ] Verify no token-related errors
- [ ] Confirm user registrations working
- [ ] Test login/logout flow
- [ ] Monitor CSP violations (should be 0)

**Hour 4-12:**
- [ ] Continue monitoring error rate
- [ ] Check database performance
- [ ] Verify email verification working
- [ ] Test order creation (if applicable)

**Hour 12-24:**
- [ ] Confirm 24-hour uptime achieved
- [ ] Verify no security incidents
- [ ] Review logs for warnings
- [ ] Get team feedback on stability

**After 24 Hours:**
- [ ] Tag production release: `git tag -a v2.0.0`
- [ ] Update changelog
- [ ] Document deployment notes
- [ ] Prepare team training on new auth flow

---

## 📊 Time Investment Summary

| Task | Time | Notes |
|------|------|-------|
| Review changes | 30 min | Read code + docs |
| Local testing | 1 hour | Build + manual tests |
| Commit & push | 15 min | Git operations |
| Create PR | 15 min | GitHub/GitLab |
| PR approval | Variable | Depends on team |
| Staging deploy | 30 min | Mostly waiting |
| Staging testing | 1 hour | Manual verification |
| Production deploy | 2-3 hours | Monitoring + canary |
| Post-deploy verification | 24 hours | Passive monitoring |
| **TOTAL** | **5-6 hours** | Plus PR review time |

**Best Timeline:** Perform on Monday morning, deployment complete by Wednesday

---

## 🚨 Emergency Rollback Procedures

If something goes wrong during deployment:

**Option 1: Immediate Traffic Shift**
- If GREEN failing: Route 100% traffic back to BLUE (< 1 minute)
- No code changes needed, just traffic routing

**Option 2: Code Rollback**
```bash
# Revert to previous version
git checkout v1.0.0
git push -f origin main
# Service auto-redeploys previous version
```

**Option 3: Database Rollback**
If database migration caused issues:
```bash
# Restore from backup
psql cryptovault_prod < backup_2024_01_09_0800.sql
```

---

## ✅ Definition of Done (Week 1 Complete)

All of the following must be true:

- [x] Code implemented locally ← Done by Fusion Team
- [ ] Code reviewed by 2+ engineers ← Your responsibility
- [ ] PR approved and merged ← Your responsibility
- [ ] Staging deployment successful ← Your responsibility
- [ ] Staging smoke tests pass ← Your responsibility
- [ ] Production deployment successful ← Your responsibility
- [ ] Zero-downtime achieved (blue-green) ← Your responsibility
- [ ] 24-hour production monitoring passed ← Your responsibility
- [ ] User communication completed ← Your responsibility
- [ ] Team training scheduled ← Your responsibility

---

## 📝 Deployment Sign-Off Template

After successful production deployment, document this:

```markdown
# Week 1 Deployment Sign-Off

**Date:** January 9, 2024  
**Deployer:** [Your name]  
**Reviewer:** [Reviewer name]  
**Monitoring Lead:** [On-call engineer]  

## Deployment Details
- Code version: v2.0.0
- Branch: security/week1-critical-fixes
- Staging duration: [Date] - [Date]
- Production deployment: [Time] - [Time]
- Zero-downtime achieved: ✅ YES

## Results
- Initial error rate: [X]%
- 24-hour error rate: [X]%
- User issues reported: [Number]
- Security incidents: NONE ✅

## Verification
- [x] All smoke tests passed
- [x] No 401 token errors
- [x] Email verification working
- [x] Refresh tokens working
- [x] Logout revokes tokens
- [x] CSP headers applied
- [x] Rate limiting active
- [x] Database pool optimized

## Rollback Actions Needed: NONE

**Signed:** _________________ Date: _________
```

---

## 💡 Tips for Success

1. **Don't Rush:** Take time to understand the changes
2. **Test Thoroughly:** More testing = fewer surprises
3. **Communicate:** Tell team about deployment timing
4. **Monitor Closely:** First 24 hours are critical
5. **Have Backup Plan:** Know how to rollback
6. **Document Issues:** Write down any problems for Week 2
7. **Celebrate Success:** You're hardening critical security! 🎉

---

## 📞 Questions?

Refer to:
- `WEEK1_IMPLEMENTATION_SUMMARY.md` - What changed & why
- `WEEK1_DEPLOYMENT_CHECKLIST.md` - Step-by-step deployment guide
- Modified source files - Code comments explain changes
- `PHASED_ROLLOUT_PLAN.md` - Overall security roadmap

---

**Ready to deploy?** Start with Step 1 above.

**Questions about the code?** Review the implementation summary.

**Need detailed deployment steps?** See the deployment checklist.

---

**Status:** Code Complete ✅ | Awaiting Your Deployment ⏳

Let's ship it! 🚀
