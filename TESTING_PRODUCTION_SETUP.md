# 🧪 Production Setup Testing Guide

Complete testing workflow to verify frontend + backend integration is working correctly.

---

## **Phase 1: Pre-Deployment Checks** (5 min)

### Check 1.1: Verify No Hardcoded URLs in Frontend
```bash
# Run from frontend directory
grep -r "localhost:" src/ || echo "✅ No localhost URLs found"
grep -r "http://.*:8" src/ || echo "✅ No port URLs found"
grep -r "coinbase-love.onrender.com" src/components/ src/pages/ src/contexts/ || echo "✅ No hardcoded Render URLs in components"
```

### Check 1.2: Verify Environment Variable Usage
Open `frontend/src/lib/api.ts` and confirm:
- ✅ Line 15-17: Uses `import.meta.env.VITE_API_URL`
- ✅ No hardcoded URLs in request function

### Check 1.3: Verify vercel.json SPA Routing
Open `frontend/vercel.json` and confirm:
- ✅ Has `rewrites` section with `/(.*) → /index.html 200`
- ✅ Has security headers (X-Content-Type-Options, etc.)

---

## **Phase 2: Backend Configuration** (5 min)

### Step 2.1: Get Your Vercel Frontend URL
1. Open Vercel Dashboard
2. Go to your frontend project
3. Copy the domain shown at top (e.g., `cryptovault-frontend.vercel.app`)
4. Note it for later: `YOUR_VERCEL_URL=` _______________

### Step 2.2: Update Render Backend Environment Variables
1. Open [Render Dashboard](https://dashboard.render.com)
2. Select your backend service (`coinbase-love-...`)
3. Click **Settings** → **Environment**
4. **Add or Update:**

```bash
# Change 1
Name: CORS_ORIGINS
Value: https://YOUR_VERCEL_URL,http://localhost:3000

# Change 2
Name: APP_URL
Value: https://YOUR_VERCEL_URL

# Change 3 (optional)
Name: ENVIRONMENT
Value: production
```

**Example values:**
```bash
CORS_ORIGINS=https://cryptovault-app.vercel.app,http://localhost:3000
APP_URL=https://cryptovault-app.vercel.app
ENVIRONMENT=production
```

5. Click **"Save Changes"** at bottom
6. Render will redeploy automatically
7. Wait 2-3 minutes for restart ⏳
8. Check **Logs** tab → should see "✅ MongoDB connected"

### Step 2.3: Verify Backend is Healthy
Open terminal and test:
```bash
# Should return 200 with health status
curl https://coinbase-love.onrender.com/health

# Should return CORS headers
curl -H "Origin: https://YOUR_VERCEL_URL" -H "Access-Control-Request-Method: POST" \
  -X OPTIONS https://coinbase-love.onrender.com/api/auth/signup -v | grep -i "access-control"
```

Expected output should include:
```
access-control-allow-origin: https://YOUR_VERCEL_URL
access-control-allow-credentials: true
```

---

## **Phase 3: Frontend Configuration** (3 min)

### Step 3.1: Update Vercel Environment Variable
1. Open [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your frontend project
3. Click **Settings** → **Environment Variables**
4. **Add or Update:**

```bash
Name: VITE_API_URL
Value: https://coinbase-love.onrender.com
Environments: Production, Preview, Development (select all)
```

5. Click **"Save"**
6. Variable should now show in list

### Step 3.2: Redeploy Frontend
Option A (automatic):
1. Go to **Deployments** tab
2. Find latest successful deployment
3. Click **"Redeploy"** button
4. Wait 2-3 minutes for build ✅

Option B (manual trigger):
```bash
# Make a tiny change and push
echo "# Updated $(date)" >> README.md
git add README.md
git commit -m "chore: trigger redeploy with production env vars"
git push origin main
```

---

## **Phase 4: Browser Testing** (10 min)

### Test 4.1: Check Console Logs
1. Open your Vercel app: `https://YOUR_VERCEL_URL`
2. **Use Incognito/Private mode** (fresh session, no cached cookies)
3. Open DevTools: `F12` or `Cmd+Option+I`
4. Click **Console** tab
5. Look for this message:
   ```
   ✅ Connected to: https://coinbase-love.onrender.com/api
   ```
   
   ✅ If you see this, frontend is correctly reading env var
   
   ❌ If you see "proxy to localhost:8001", env var not set

### Test 4.2: Check Network Requests
1. Keep DevTools open, click **Network** tab
2. Refresh page (`Ctrl+R` or `Cmd+R`)
3. Look at network requests:
   - ✅ Should see requests to `coinbase-love.onrender.com`
   - ❌ Should NOT see `localhost:8001` or `localhost:3000`

### Test 4.3: Sign Up Test (API Connection)
1. Navigate to `/auth` or find Sign Up button
2. Fill in:
   - Email: `test+$(date +%s)@example.com`
   - Password: `TestPassword123!`
   - Name: `Test User`
3. Click **Sign Up**
4. Watch **Network** tab for `POST /auth/signup`
5. Expected responses:
   - ✅ Status `200` - Account created, check console for verification code
   - ✅ Status `400` - Email already exists
   - ❌ Status showing "CORS error" or "Failed to fetch" - See Troubleshooting
6. If successful: Copy the 6-digit code from console
   ```
   Email verification code: 123456
   ```

### Test 4.4: Email Verification
1. In frontend, look for email verification input
2. Paste the 6-digit code
3. Click **Verify**
4. Expected: ✅ Email verified, auto-login
5. Check console for success message

### Test 4.5: Login Test
1. Navigate to `/auth` → Login tab
2. Enter same email + password from Test 4.3
3. Click **Login**
4. Expected: ✅ Redirect to dashboard
5. Check **Network** tab for `POST /auth/login` → Status `200`

### Test 4.6: Dashboard & Data Loading
1. Once logged in, should see Dashboard
2. Look for:
   - ✅ Portfolio holdings displayed
   - ✅ Account balance shown
3. Click **Markets** page
4. Expected: ✅ Crypto prices loaded from CoinGecko via backend
5. Check **Network** → look for `GET /crypto` request → should be `200`

### Test 4.7: Render Spin-Down Simulation (Advanced)
1. Open your app normally, verify it loads
2. **Wait 30+ minutes without accessing the backend**
3. Make a new request (e.g., click Markets, or refresh)
4. Watch console and Network tab
5. Expected behavior:
   - 🔄 First request takes 30-60 seconds
   - 💬 Console shows: `⏳ Backend is waking up... (30-60s)`
   - 🔄 Request retries automatically
   - ✅ Data loads successfully
6. Verify in **Network** tab:
   - First attempt may timeout/fail
   - Subsequent retries succeed

---

## **Phase 5: Error Scenario Testing** (5 min)

### Test 5.1: Simulate CORS Error (Expected to NOT occur)
1. If you see this error in console:
   ```
   Access to XMLHttpRequest at 'https://coinbase-love.onrender.com/api/...' 
   from origin 'https://YOUR_VERCEL_URL' has been blocked by CORS policy
   ```
2. This means **CORS_ORIGINS on Render is wrong**
3. Fix: Go back to Phase 2.2, verify CORS_ORIGINS includes your Vercel URL

### Test 5.2: Test Slow Network / Connection Issues
1. Open DevTools → **Network** tab
2. Click **throttling dropdown** → Select **Slow 3G**
3. Try to load Markets page
4. Expected:
   - ✅ Shows loading spinner
   - ✅ Console message: "Backend is waking up..."
   - ✅ After 5-10s, data loads
5. Reset throttling afterward

### Test 5.3: Verify Error Boundary Works
1. In DevTools Console, run:
   ```javascript
   throw new Error("Test error boundary");
   ```
2. Expected: Page shows error card with "Something Went Wrong"
3. Click **Reload Page** button
4. Page should recover

---

## **Phase 6: Final Validation** (5 min)

### Checklist - All Tests Should Pass

- [ ] Console shows `✅ Connected to: https://coinbase-love.onrender.com/api`
- [ ] Network tab shows NO localhost requests
- [ ] Network tab shows NO CORS errors
- [ ] Sign Up successfully creates account
- [ ] Email verification code appears in console
- [ ] Email verification succeeds
- [ ] Login works and redirects to dashboard
- [ ] Dashboard displays portfolio data
- [ ] Markets page loads crypto prices from backend
- [ ] Slow request shows loading message + retries
- [ ] Error boundary catches and displays errors
- [ ] All requests show Status 200/201/400 (not CORS/network errors)

---

## **Quick Debug Commands**

### Check Backend is Alive
```bash
curl -i https://coinbase-love.onrender.com/health
# Should return 200 OK
```

### Check CORS Configuration
```bash
curl -i -X OPTIONS \
  -H "Origin: https://YOUR_VERCEL_URL" \
  -H "Access-Control-Request-Method: POST" \
  https://coinbase-love.onrender.com/api/auth/signup
  
# Should show:
# access-control-allow-origin: https://YOUR_VERCEL_URL
# access-control-allow-credentials: true
```

### Check Render Logs
1. Render Dashboard → Your backend service
2. Click **Logs** tab
3. Should see recent activity + no errors

### Check Vercel Logs
1. Vercel Dashboard → Your frontend project
2. Click **Deployments** tab
3. Click latest deployment
4. View **Logs** to see build output
5. Should show `✅ Build successful`

---

## **Troubleshooting**

### ❌ "CORS error" or "Failed to fetch"
**Cause:** CORS_ORIGINS on Render doesn't include your Vercel URL
**Fix:**
1. Go to Render Dashboard → Settings → Environment
2. Update `CORS_ORIGINS` to include `https://YOUR_VERCEL_URL`
3. Save & redeploy
4. Wait 2 min
5. Refresh frontend in new incognito window

### ❌ "Cannot GET /"
**Cause:** Frontend SPA routing not working (vercel.json missing)
**Fix:** Verify `frontend/vercel.json` exists with rewrite rule for `/index.html`

### ❌ API returns 404
**Cause:** VITE_API_URL is wrong or has trailing slash
**Fix:**
1. Vercel Dashboard → Settings → Environment Variables
2. Verify `VITE_API_URL=https://coinbase-love.onrender.com` (no trailing slash)
3. Redeploy frontend

### ❌ Blank Page / No Content
**Cause:** Multiple possible
**Debug:**
1. Open DevTools → Console
2. Check for JavaScript errors
3. Open Network tab
4. Refresh page
5. Check if any API requests fail
6. If requests fail, check CORS/backend connection

### ❌ "Backend waking up..." message never disappears
**Cause:** Backend is actually offline or very slow
**Fix:**
1. Check Render backend is running: `curl https://coinbase-love.onrender.com/health`
2. Check Render Logs for errors
3. Verify MongoDB connection string is correct
4. Check API endpoint exists: `curl https://coinbase-love.onrender.com/api/crypto`

---

## **Success Indicators**

✅ **Your setup is working correctly if:**
- Frontend loads without errors
- DevTools shows "✅ Connected to: ..." message
- Network tab shows requests to Render backend
- Sign Up/Login flow works
- Dashboard displays data
- Markets show crypto prices
- No CORS errors in console
- Slow requests show loading message + retry

✅ **Production is ready for users!**

---

## **Next Steps**

1. Share app link: `https://YOUR_VERCEL_URL`
2. Monitor Render & Vercel dashboards for errors
3. Set up monitoring/alerts for downtime
4. Plan backups for MongoDB data
5. Monitor usage/costs on both platforms
