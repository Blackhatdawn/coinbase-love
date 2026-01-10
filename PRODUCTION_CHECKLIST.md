# 🚀 Production Deployment Checklist

Use this checklist to ensure your CryptoVault deployment is production-ready.

---

## 📋 Pre-Deployment Checklist

### Code Preparation
- [ ] All features tested locally
- [ ] No console.log or debug statements
- [ ] All TODOs resolved or documented
- [ ] Code committed to Git repository
- [ ] Repository pushed to GitHub/GitLab

### Database Setup
- [ ] MongoDB Atlas account created
- [ ] M0 (free) or M10 cluster provisioned
- [ ] Database user created with strong password
- [ ] Network access configured (0.0.0.0/0 for Render)
- [ ] Connection string obtained and tested
- [ ] Database name decided (e.g., `cryptovault_production`)

### Environment Variables Prepared
- [ ] JWT secret generated (32+ characters)
- [ ] MongoDB connection string ready
- [ ] CORS origins documented
- [ ] All sensitive data NOT committed to Git

---

## 🖥️ Backend Deployment (Render)

### Initial Setup
- [ ] Render account created
- [ ] New Web Service created
- [ ] GitHub repository connected
- [ ] Root directory set to `backend`
- [ ] Python 3.11 runtime selected

### Build Configuration
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
- [ ] Health check path: `/health`

### Environment Variables Set
- [ ] `PYTHON_VERSION=3.11.0`
- [ ] `ENVIRONMENT=production`
- [ ] `MONGO_URL=<your-atlas-connection-string>`
- [ ] `DB_NAME=cryptovault_production`
- [ ] `JWT_SECRET=<generated-or-auto-generated>`
- [ ] `CORS_ORIGINS=<your-vercel-url>`
- [ ] `MONGO_MAX_POOL_SIZE=50`
- [ ] `MONGO_MIN_POOL_SIZE=10`
- [ ] `MONGO_TIMEOUT_MS=5000`
- [ ] `RATE_LIMIT_PER_MINUTE=60`

### Post-Deployment Verification
- [ ] Service deployed successfully
- [ ] Build logs show no errors
- [ ] Health check endpoint returns 200
- [ ] Test: `curl https://your-backend.onrender.com/health`
- [ ] Test: `curl https://your-backend.onrender.com/api/`
- [ ] Test: `curl https://your-backend.onrender.com/api/crypto`
- [ ] Backend URL saved for frontend configuration

---

## 🌐 Frontend Deployment (Vercel)

### Initial Setup
- [ ] Vercel account created
- [ ] New Project created
- [ ] GitHub repository connected
- [ ] Root directory set to `frontend`
- [ ] Framework preset: Vite

### Build Configuration
- [ ] Build command: `yarn build`
- [ ] Output directory: `build`
- [ ] Install command: `yarn install`
- [ ] Node.js version: 18.x or higher

### Environment Variables Set
- [ ] `VITE_API_URL=https://your-backend.onrender.com`

### Production Build Test
- [ ] Run `yarn build` locally - succeeds
- [ ] Run `yarn preview` locally - works
- [ ] No build errors
- [ ] No TypeScript errors

### Post-Deployment Verification
- [ ] Deployment succeeded
- [ ] Site accessible at Vercel URL
- [ ] No 404 errors on page refresh
- [ ] Browser console shows no errors
- [ ] Frontend URL saved for CORS configuration

---

## 🔄 Cross-Service Configuration

### Update Backend CORS
- [ ] Go to Render dashboard → Your service → Environment
- [ ] Update `CORS_ORIGINS` to your Vercel URL
- [ ] Format: `https://your-project.vercel.app`
- [ ] Multiple domains: comma-separated, no spaces
- [ ] Save changes (triggers auto-redeploy)
- [ ] Wait for backend to redeploy (~3 minutes)

### Verify CORS Configuration
- [ ] Open Vercel site in browser
- [ ] Open DevTools → Network tab
- [ ] Try to sign up/login
- [ ] No CORS errors in console
- [ ] API calls succeed (status 200)

---

## 🧪 End-to-End Testing

### Authentication Flow
- [ ] Sign up with test account works
- [ ] Email validation (if implemented)
- [ ] Login with credentials works
- [ ] JWT tokens set correctly (check cookies)
- [ ] Logout works
- [ ] Session persists on page refresh

### Core Functionality
- [ ] View markets (cryptocurrency data loads)
- [ ] Access dashboard (protected route works)
- [ ] Add portfolio holdings
- [ ] View portfolio value
- [ ] Create trade orders
- [ ] View transaction history
- [ ] 2FA setup (if implemented)

### Data Persistence
- [ ] Create user account
- [ ] Add portfolio holdings
- [ ] Refresh page - data persists
- [ ] Check MongoDB Atlas - collections created
- [ ] Logout and login - session restored

---

## 🔒 Security Verification

### SSL/HTTPS
- [ ] Frontend uses HTTPS (Vercel automatic)
- [ ] Backend uses HTTPS (Render automatic)
- [ ] Mixed content warnings checked
- [ ] All API calls use HTTPS

### CORS Configuration
- [ ] No wildcard (*) in production CORS
- [ ] Only specific domains whitelisted
- [ ] Testing with other domains fails (expected)

### Environment Variables
- [ ] No secrets in frontend code
- [ ] No secrets committed to Git
- [ ] .env files in .gitignore
- [ ] Sensitive values in platform dashboards only

### Password Security
- [ ] Bcrypt hashing enabled (check backend logs)
- [ ] Password requirements enforced (if implemented)
- [ ] No passwords logged

### JWT Security
- [ ] JWT secret is secure (32+ characters)
- [ ] HttpOnly cookies enabled
- [ ] SameSite attribute set
- [ ] Token expiration configured

---

## 📊 Monitoring Setup

### Health Checks
- [ ] Backend health endpoint: `/health`
- [ ] Returns proper status codes
- [ ] Set up uptime monitoring:
  - [ ] UptimeRobot account
  - [ ] Monitor configured for backend health
  - [ ] Alert email configured

### Error Tracking (Optional)
- [ ] Sentry account (or alternative)
- [ ] Frontend error tracking configured
- [ ] Backend error tracking configured
- [ ] Test by triggering an error

### Analytics (Optional)
- [ ] Vercel Analytics enabled
- [ ] Google Analytics (if desired)
- [ ] User behavior tracking (GDPR compliant)

---

## 🗄️ Database Management

### MongoDB Atlas
- [ ] Cluster status: Active
- [ ] Storage usage monitored
- [ ] Collections created correctly:
  - [ ] users
  - [ ] portfolios
  - [ ] orders
  - [ ] transactions
  - [ ] audit_logs
- [ ] Indexes created (if custom indexes needed)
- [ ] Backup configured (auto-backup enabled)

### Database Security
- [ ] User privileges: Read/Write only (not admin)
- [ ] Strong password used
- [ ] Connection string not exposed
- [ ] Network access configured correctly

---

## 📝 Documentation

### Internal Documentation
- [ ] README.md updated with production URLs
- [ ] Deployment guide reviewed
- [ ] Environment variables documented
- [ ] API endpoints documented (if team)
- [ ] Known issues documented

### External Documentation (if public)
- [ ] User guide created
- [ ] API documentation published
- [ ] Terms of service
- [ ] Privacy policy

---

## 🚀 Performance Optimization

### Frontend
- [ ] Build size checked (<500KB gzipped ideal)
- [ ] Images optimized
- [ ] Lazy loading implemented (if applicable)
- [ ] Service worker configured (if PWA)

### Backend
- [ ] Connection pooling configured
- [ ] Database indexes created
- [ ] Query performance tested
- [ ] Rate limiting active

### CDN
- [ ] Vercel CDN enabled (automatic)
- [ ] Static assets cached
- [ ] Gzip compression enabled (automatic)

---

## 🔄 Continuous Deployment

### Auto-Deployment Setup
- [ ] Render: Auto-deploy on push to main
- [ ] Vercel: Auto-deploy on push to main
- [ ] Preview deployments for PRs (Vercel)
- [ ] Branch protection rules (GitHub)

### Deployment Testing
- [ ] Make test commit
- [ ] Push to main branch
- [ ] Verify Render auto-deploys backend
- [ ] Verify Vercel auto-deploys frontend
- [ ] Test deployed changes work

---

## 🎯 Launch Checklist

### Final Verification
- [ ] All above checklists complete
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Security hardened
- [ ] Monitoring active

### Pre-Launch
- [ ] Backup MongoDB data
- [ ] Document rollback procedure
- [ ] Team notified of launch
- [ ] Support plan in place

### Launch
- [ ] Update DNS (if custom domain)
- [ ] Announce on social media (if applicable)
- [ ] Monitor for first hour
- [ ] Check logs for errors
- [ ] Verify user signups working

### Post-Launch
- [ ] Monitor uptime (24 hours)
- [ ] Check error rates
- [ ] Review performance metrics
- [ ] Gather user feedback
- [ ] Plan next iteration

---

## 🐛 Troubleshooting Verification

### Common Issues Tested
- [ ] Database connection failure → Health check returns 503
- [ ] CORS misconfiguration → Clear error message
- [ ] Invalid credentials → Proper 401 response
- [ ] Rate limiting → Returns 429 after limit
- [ ] Server error → Returns 500 with message

### Error Handling
- [ ] 404 pages work
- [ ] 500 errors logged
- [ ] User-friendly error messages
- [ ] No sensitive data in errors

---

## 📊 Success Metrics

### Technical Metrics
- [ ] Uptime > 99%
- [ ] Response time < 500ms (p95)
- [ ] Error rate < 1%
- [ ] Health checks passing

### User Metrics
- [ ] Users can sign up
- [ ] Users can complete core flows
- [ ] No critical support tickets
- [ ] Positive user feedback

---

## ✅ Final Sign-Off

### Stakeholder Approval
- [ ] Technical lead review
- [ ] Security review (if required)
- [ ] Product owner approval
- [ ] Legal compliance (if required)

### Documentation Complete
- [ ] Deployment guide
- [ ] Environment variables documented
- [ ] Monitoring dashboards configured
- [ ] Runbook for common issues

### Ready for Production
- [ ] All checklists complete
- [ ] Team confident in deployment
- [ ] Rollback plan documented
- [ ] **DEPLOY! 🚀**

---

## 🆘 Emergency Contacts

**In Case of Issues:**

### Platform Support
- Render Support: https://render.com/support
- Vercel Support: https://vercel.com/support
- MongoDB Atlas: https://support.mongodb.com/

### Rollback Procedure
1. Identify issue in logs
2. Revert Git commit
3. Redeploy previous version
4. Verify services healthy
5. Post-mortem analysis

---

**Deployment Date**: __________  
**Deployed By**: __________  
**Production URLs**:
- Frontend: __________
- Backend: __________
- Health Check: __________

**Status**: ✅ Production Ready

---

*This checklist should be completed for every production deployment.*
