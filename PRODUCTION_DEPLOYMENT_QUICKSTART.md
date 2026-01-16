# Production Deployment Quickstart

## ⚠️ CRITICAL: Set These Before Deploy

### Backend Environment Variables

```bash
# === CRITICAL - SET FOR YOUR DOMAIN ===
CORS_ORIGINS=https://your-frontend-domain.com
# For multiple frontends:
# CORS_ORIGINS=https://app.vercel.app,https://staging.vercel.app

# === For cross-site authentication (frontend and API on different origins) ===
USE_CROSS_SITE_COOKIES=true

# === REQUIRED ===
ENVIRONMENT=production
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/cryptovault
DB_NAME=cryptovault
JWT_SECRET=your-super-secret-key-minimum-32-characters-long

# === OPTIONAL BUT RECOMMENDED ===
SENTRY_DSN=https://your-sentry-key@sentry.io/project-id
COINGECKO_API_KEY=your-coingecko-key

# === REDIS/CACHE ===
USE_REDIS=true
UPSTASH_REDIS_REST_URL=https://your-redis-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-redis-token

# === EMAIL ===
EMAIL_SERVICE=sendgrid  # or your email provider
EMAIL_FROM=noreply@cryptovault.com
EMAIL_FROM_NAME=CryptoVault
APP_URL=https://your-frontend-domain.com
```

### Frontend Environment Variables

```bash
# === CRITICAL ===
VITE_API_BASE_URL=https://your-api-domain.com
# OR leave empty to use Vercel rewrite to /api/*

# === OPTIONAL ===
VITE_SENTRY_DSN=https://your-sentry-key@sentry.io/project-id
VITE_APP_NAME=CryptoVault
VITE_APP_VERSION=1.0.0
VITE_NODE_ENV=production
```

---

## 🔐 What These Changes Fix

### ✅ Issue #1: CORS Wildcard Blocking Authentication
- **Before**: `CORS_ORIGINS="*"` + `allow_credentials=true` = 🔴 CORS rejection errors
- **After**: Set to specific domain = ✅ Authentication works

### ✅ Issue #2: Cross-Site Cookies Not Being Sent
- **Before**: Cookies set with `SameSite="lax"` = 🔴 Blocked on cross-site requests
- **After**: With `USE_CROSS_SITE_COOKIES=true` = ✅ Cookies sent properly

---

## ✅ Quick Verification Checklist

After deploying with the correct environment variables:

- [ ] **API responds to CORS preflight**
  ```bash
  curl -X OPTIONS https://api.your-domain.com/api/auth/login \
    -H "Origin: https://app.your-domain.com" \
    -H "Access-Control-Request-Method: POST" -i
  # Should see: Access-Control-Allow-Origin: https://app.your-domain.com
  ```

- [ ] **Login sets cookies**
  ```bash
  curl -X POST https://api.your-domain.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"password"}' -i
  # Should see: Set-Cookie: access_token=...
  ```

- [ ] **Browser console test**
  - Open app in browser
  - Login successfully
  - Check DevTools → Application → Cookies
  - Should see `access_token` and `refresh_token` with:
    - `SameSite`: `None` (if cross-site) or `Lax` (if same-site)
    - `Secure`: ✅ Checked (HTTPS only)
    - `HttpOnly`: ✅ Checked (can't be accessed by JS)

---

## 🚨 If Authentication Still Fails

1. **Check CORS_ORIGINS is set correctly**
   ```bash
   echo $CORS_ORIGINS
   # Should output your frontend domain, not "*"
   ```

2. **Verify HTTPS on both frontend and API**
   - `https://` (not `http://`)
   - SameSite=None requires HTTPS

3. **Check cookie is being sent**
   - Open browser DevTools → Network tab
   - Make any API request
   - Click on request → Headers → Scroll to Cookies section
   - Should show `access_token=...`

4. **Monitor backend logs**
   - Look for CORS errors: `CRITICAL: CORS_ORIGINS is '*'`
   - Look for auth errors: `401 Unauthorized`

5. **Check Sentry for errors** (if configured)
   - Go to your Sentry dashboard
   - Search for 401 or CORS errors

---

## 📞 Support

- **Full audit report**: See `API_MISCONFIGURATION_AUDIT_AND_FIXES.md`
- **Backend API docs**: `https://api.your-domain.com/api/docs`
- **Health check**: `https://api.your-domain.com/api/health`

