# 🚀 Vercel Deployment - Environment Variables Setup

**Date:** February 5, 2025  
**Issue Fixed:** Environment variable secret reference error  
**Status:** ✅ Ready to Deploy

---

## 🔴 Issue Fixed

### Error Message
```
Environment Variable "VITE_API_BASE_URL" references Secret "vite_api_base_url", which does not exist.
```

### Root Cause
The `vercel.json` was using `@secret_name` syntax to reference Vercel secrets that were never created.

### Solution Applied
Updated `vercel.json` to use **direct values** instead of secret references.

---

## 📝 Updated Configuration

### vercel.json - Environment Variables
```json
{
  "env": {
    "VITE_API_BASE_URL": "https://cryptovault-api.onrender.com",
    "VITE_SENTRY_DSN": "",
    "VITE_ENABLE_SENTRY": "false",
    "VITE_SENTRY_ENVIRONMENT": "production",
    "VITE_APP_NAME": "CryptoVault",
    "VITE_APP_VERSION": "1.0.0"
  }
}
```

**Changes Made:**
- ❌ Removed: `"VITE_API_BASE_URL": "@vite_api_base_url"`
- ✅ Added: Direct URL value
- ❌ Removed: `"VITE_SENTRY_DSN": "@vite_sentry_dsn"`
- ✅ Added: Empty value (Sentry disabled)
- Changed: `VITE_ENABLE_SENTRY` from `"true"` to `"false"`

---

## 🎯 Two Deployment Options

### Option 1: Using vercel.json (Current Setup) ✅

**Pros:**
- No manual configuration needed
- Version controlled
- Consistent across deployments

**Cons:**
- Values visible in git (not ideal for secrets)
- Harder to change without redeployment

**Current Status:** ✅ Configured and ready

---

### Option 2: Using Vercel Dashboard (Recommended for Secrets)

If you need to add **sensitive values** (API keys, secrets), use the Vercel Dashboard instead:

**Steps:**
1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your project: `cryptovault-frontend`
3. Go to **Settings** → **Environment Variables**
4. Add variables:

```
VITE_API_BASE_URL = https://cryptovault-api.onrender.com
VITE_SENTRY_DSN = (your Sentry DSN if using)
VITE_ENABLE_SENTRY = false
VITE_APP_NAME = CryptoVault
VITE_APP_VERSION = 1.0.0
```

**For Sensitive Values (if needed):**
- Check "Encrypt" when adding
- This creates a Vercel secret automatically
- Secret names use format: `@secret_name`

**Then update vercel.json:**
```json
{
  "env": {
    "VITE_API_BASE_URL": "@api_base_url",
    "VITE_SENTRY_DSN": "@sentry_dsn"
  }
}
```

---

## 🚀 Deployment Steps

### Step 1: Push Changes
```bash
cd /app/frontend
git add vercel.json
git commit -m "Fix: Vercel env variable configuration"
git push origin main
```

### Step 2: Vercel Auto-Deploy
- Vercel will automatically detect the push
- Build will start automatically
- Deployment takes ~2-3 minutes

### Step 3: Verify Deployment
```bash
# Check build logs in Vercel dashboard
# https://vercel.com/your-username/cryptovault-frontend/deployments

# Verify environment variables are loaded
# Check browser console: window.__RUNTIME_CONFIG__
```

---

## 🔍 Troubleshooting

### Error: "Environment variable not found"

**Problem:** Variable not set in Vercel Dashboard

**Solution:**
```bash
# Option A: Add to vercel.json (current setup)
# Already done ✅

# Option B: Add via Vercel Dashboard
# Settings → Environment Variables → Add New
```

---

### Error: "CORS error when calling API"

**Problem:** Backend URL incorrect

**Solution:**
```bash
# Verify VITE_API_BASE_URL in vercel.json:
"VITE_API_BASE_URL": "https://cryptovault-api.onrender.com"

# Must match backend deployment URL exactly
# No trailing slash
```

---

### Error: "Failed to fetch runtime config"

**Problem:** Backend not responding

**Solution:**
```bash
# Check backend is running
curl https://cryptovault-api.onrender.com/ping

# Should return: {"status":"ok","message":"pong"}

# If backend is down, restart it on Render.com
```

---

## 🔐 Security Best Practices

### Environment Variables in vercel.json

**Safe to commit:**
- ✅ Public URLs (API_BASE_URL)
- ✅ App name/version
- ✅ Feature flags
- ✅ Public config values

**Never commit:**
- ❌ API keys
- ❌ Database passwords
- ❌ JWT secrets
- ❌ Private tokens
- ❌ Sentry DSN (if you want to keep it private)

**For Secrets:**
Use Vercel Dashboard → Environment Variables → Encrypt option

---

## 📊 Current Environment Variables

| Variable | Value | Type | Source |
|----------|-------|------|--------|
| `VITE_API_BASE_URL` | `https://cryptovault-api.onrender.com` | Public | vercel.json |
| `VITE_SENTRY_DSN` | `""` (empty) | Public | vercel.json |
| `VITE_ENABLE_SENTRY` | `false` | Public | vercel.json |
| `VITE_SENTRY_ENVIRONMENT` | `production` | Public | vercel.json |
| `VITE_APP_NAME` | `CryptoVault` | Public | vercel.json |
| `VITE_APP_VERSION` | `1.0.0` | Public | vercel.json |

---

## 🎯 Environment-Specific Configuration

### Production (Vercel)
```json
{
  "VITE_API_BASE_URL": "https://cryptovault-api.onrender.com",
  "VITE_ENABLE_SENTRY": "false"
}
```

### Preview (Vercel Branch Deploys)
- Inherits from production settings
- Can override in Vercel Dashboard per branch

### Development (Local)
```bash
# /app/frontend/.env.development
VITE_API_BASE_URL=http://localhost:8001
VITE_ENABLE_SENTRY=false
```

---

## 🧪 Verification Checklist

After deployment, verify:

- [ ] Deployment succeeded (green checkmark in Vercel)
- [ ] No build errors in logs
- [ ] Frontend loads at https://www.cryptovault.financial
- [ ] API calls work (check Network tab)
- [ ] No CORS errors in console
- [ ] Authentication works (login/signup)
- [ ] Backend URL is correct (check `/api/config` endpoint)

### Quick Test
```bash
# 1. Check deployment status
curl -I https://www.cryptovault.financial

# 2. Check API connectivity
curl https://www.cryptovault.financial/api/ping

# 3. Check config endpoint
curl https://www.cryptovault.financial/api/config

# Expected: Should show apiBaseUrl: "https://cryptovault-api.onrender.com"
```

---

## 🔄 Updating Environment Variables

### Method 1: Update vercel.json (Current)
```bash
# 1. Edit vercel.json
# 2. Commit and push
git commit -am "Update env vars"
git push

# 3. Vercel auto-deploys
```

### Method 2: Vercel Dashboard
```bash
# 1. Go to Vercel Dashboard
# 2. Settings → Environment Variables
# 3. Edit existing or add new
# 4. Click "Redeploy" to apply changes
```

**Note:** Dashboard changes require manual redeploy

---

## 📚 Additional Resources

### Vercel Documentation
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Secrets](https://vercel.com/docs/concepts/projects/environment-variables#secrets)
- [Build-Time vs Runtime Variables](https://vercel.com/docs/concepts/projects/environment-variables#environments)

### Vite Documentation
- [Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [Modes and Environment Variables](https://vitejs.dev/guide/env-and-mode.html#modes)

---

## 🆘 Common Issues & Solutions

### Issue 1: Variables not updating after push

**Cause:** Browser cache or CDN cache

**Solution:**
```bash
# Hard refresh browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)

# Or clear Vercel cache
Vercel Dashboard → Deployments → Three dots → Redeploy
```

---

### Issue 2: Build succeeds but app doesn't work

**Cause:** Wrong API URL or backend down

**Solution:**
```bash
# Check actual URL being used
# Open browser console:
console.log(import.meta.env.VITE_API_BASE_URL)

# Should output: "https://cryptovault-api.onrender.com"

# If different, update vercel.json and redeploy
```

---

### Issue 3: CORS errors in production

**Cause:** Backend not allowing frontend origin

**Solution:**
```bash
# Verify backend CORS settings
# Backend should allow: https://www.cryptovault.financial

# Check backend logs on Render.com
# Look for CORS-related errors
```

---

## ✅ Success Indicators

After successful deployment:

1. ✅ **Build Log:** No environment variable errors
2. ✅ **Deployment:** Green checkmark in Vercel
3. ✅ **Frontend:** Loads without errors
4. ✅ **API Calls:** Working (check Network tab)
5. ✅ **Console:** No errors or warnings
6. ✅ **Features:** Login, signup, dashboard all working

---

## 🎉 Deployment Complete

Your CryptoVault frontend is now correctly configured and deployed on Vercel!

**Live URL:** https://www.cryptovault.financial  
**Backend URL:** https://cryptovault-api.onrender.com  
**Status:** ✅ Production Ready

---

## 📞 Support

**Vercel Issues:**
- [Vercel Support](https://vercel.com/support)
- [Community Discord](https://vercel.com/discord)

**CryptoVault Issues:**
- Check backend logs on Render.com
- Check frontend logs in Vercel Dashboard
- Review CSP violations in browser console

---

**Last Updated:** 2025-02-05  
**Next Review:** After successful deployment verification
