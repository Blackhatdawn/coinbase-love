# 🚀 Vercel Frontend + Render Backend - Production Deployment Checklist

## **Current Status**
- ✅ Backend: LIVE on Render (https://coinbase-love.onrender.com)
- ✅ Frontend: Deployed on Vercel (needs env var fix + backend CORS update)
- ✅ Code: No hardcoded URLs (all use `import.meta.env.VITE_API_URL`)
- ✅ Routing: React Router v6 + vercel.json SPA routing configured

---

## **STEP 1: Configure Backend CORS on Render (5 minutes)**

### Action: Add environment variables to Render backend service

1. Go to **Render Dashboard** → Select your backend service (coinbase-love)
2. Click **"Environment"** (or **Settings** → **Environment Variables**)
3. **Add/Update these variables:**

```bash
# CORS Origins - Allow your Vercel frontend domain
# Format: https://your-app.vercel.app,http://localhost:3000
CORS_ORIGINS=https://your-vercel-app-name.vercel.app,http://localhost:3000

# App URL - For email verification links
# Must point to your Vercel frontend
APP_URL=https://your-vercel-app-name.vercel.app

# Optional: Set production environment
ENVIRONMENT=production
```

**Example (replace with YOUR Vercel URL):**
```bash
CORS_ORIGINS=https://cryptovault-frontend.vercel.app,http://localhost:3000
APP_URL=https://cryptovault-frontend.vercel.app
ENVIRONMENT=production
```

4. Click **"Deploy"** button to apply changes (Render will redeploy)
5. Wait 2-3 minutes for backend to restart ✅

---

## **STEP 2: Configure Frontend Environment Variables on Vercel (3 minutes)**

### Action: Set VITE_API_URL in Vercel dashboard

1. Go to **Vercel Dashboard** → Select your frontend project
2. Click **Settings** → **Environment Variables**
3. **Add new variable:**
   - **Name:** `VITE_API_URL`
   - **Value:** `https://coinbase-love.onrender.com`
   - **Environments:** Select `Production`, `Preview`, `Development`

4. Click **"Save"** ✅

---

## **STEP 3: Rebuild Frontend on Vercel (3 minutes)**

### Action: Trigger a new deployment

1. In Vercel Dashboard, click **"Deployments"** tab
2. Click **"Redeploy"** (top-right) on your latest successful deployment
3. **OR** push a commit to trigger auto-deployment:
   ```bash
   # Make a trivial change (e.g., update a comment) and push
   git add .
   git commit -m "chore: trigger redeploy with CORS fixes"
   git push origin main
   ```
4. Wait for build to complete (~2 min) ✅

---

## **STEP 4: Clear Cache & Test in Browser (5 minutes)**

### Test 1: Check Frontend Loads
1. Open your Vercel URL in **Incognito Mode** (Ctrl+Shift+N / Cmd+Shift+N)
2. Expected: App loads, **NO blank screen**
3. Open **DevTools** (F12 → Console tab)
4. Should see: `✅ Connected to: https://coinbase-love.onrender.com/api`

### Test 2: Check API Connectivity
1. Go to **Auth** page
2. Try to **Sign Up** with a test email
3. Watch **Network tab** (F12 → Network)
4. Expected: `POST /auth/signup` → Status `200` or `400` (not CORS error)
5. If you see **CORS error** (like `No 'Access-Control-Allow-Origin' header`):
   - ❌ Backend CORS not updated
   - Go back to STEP 1 and verify `CORS_ORIGINS` env var is set

### Test 3: Test Render Spin-Down Handling
1. After deploying, **wait 30+ minutes** without accessing the backend
2. Then access the app again
3. Expected: Page shows loading spinner + message "Backend is waking up..."
4. Backend should respond within 30-60 seconds
5. ✅ App loads data successfully

### Test 4: Verify No Hardcoded URLs
Open DevTools → Network tab → Look for these:
- ❌ `localhost:8001` requests (should NOT exist in production)
- ❌ `localhost:3000` requests (should NOT exist in production)
- ✅ All requests go to `https://coinbase-love.onrender.com`

---

## **STEP 5: Verify Production Behavior (10 minutes)**

### Test Portfolio/Dashboard
1. Sign Up → Verify Email (check console for verification code)
2. Login → Should land on Dashboard
3. Click **Markets** → Should see crypto prices (from CoinGecko via backend)
4. Try **Add to Portfolio** → Should create holdings

### Test Error Handling
1. Turn off WiFi/network
2. Try to make an API call (e.g., click Markets)
3. Expected: Spinner with "Backend is waking up..." message
4. Turn WiFi back on
5. Expected: Request retries and succeeds

---

## **Troubleshooting**

### ❌ Blank Screen on Vercel
**Solution:**
1. Open DevTools (F12)
2. Check **Console** tab for errors
3. Check **Network** tab to see if API calls are failing
4. Common causes:
   - VITE_API_URL not set in Vercel
   - Backend CORS not configured
   - Backend service not running

### ❌ CORS Error: "No 'Access-Control-Allow-Origin' header"
**Solution:**
1. Verify `CORS_ORIGINS` on Render backend includes your Vercel URL
2. Format must be: `https://your-app.vercel.app` (with https://)
3. Redeploy Render backend after changing env var

### ❌ API Calls Timeout/Fail Immediately
**Solution:**
1. Check if Render backend is running: `curl https://coinbase-love.onrender.com/health`
2. If offline: Start the service in Render dashboard
3. If response is slow: It's spinning down from idle
4. App should retry automatically (wait 30-60s)

### ❌ Email Links (password reset, verification) don't work
**Solution:**
1. Verify `APP_URL` on Render is set to your Vercel frontend URL
2. Example: `APP_URL=https://cryptovault-frontend.vercel.app`
3. Redeploy Render backend

---

## **Quick Checklist**

- [ ] Render backend has `CORS_ORIGINS` env var with your Vercel URL
- [ ] Render backend has `APP_URL` env var with your Vercel URL
- [ ] Render backend is redeployed after env var changes
- [ ] Vercel frontend has `VITE_API_URL=https://coinbase-love.onrender.com`
- [ ] Vercel frontend is redeployed
- [ ] No errors in browser DevTools Console
- [ ] Network requests go to `https://coinbase-love.onrender.com`
- [ ] Sign Up → Login → Dashboard flow works
- [ ] Markets page loads crypto prices
- [ ] Portfolio functionality works
- [ ] Spin-down message shows on slow first request

---

## **Environment Variables Summary**

### Render Backend (.env or Dashboard)
```bash
MONGO_URL=<your-mongodb-url>
DB_NAME=cryptovault_db
JWT_SECRET=<auto-generated-32-char-secret>
CORS_ORIGINS=https://your-vercel-app.vercel.app,http://localhost:3000
APP_URL=https://your-vercel-app.vercel.app
ENVIRONMENT=production
# ... other vars
```

### Vercel Frontend (Dashboard → Settings → Environment Variables)
```bash
VITE_API_URL=https://coinbase-love.onrender.com
```

### Local Development (.env.local)
```bash
VITE_API_URL=  # Leave empty to use Vite proxy (localhost:8001)
```

---

## **What Changed in Code**

1. ✅ `backend/config.py` - Added CORS comments, APP_URL comments
2. ✅ `frontend/.env.example` - Created template for developers
3. ✅ `frontend/src/lib/api.ts` - Enhanced Render spin-down messaging
4. ✅ No hardcoded URLs anywhere (all use env vars)

---

## **Success Criteria**

- ✅ Frontend loads without errors
- ✅ API calls reach backend (Network tab shows 200/201 responses)
- ✅ Sign Up/Login/Dashboard flow works
- ✅ Portfolio and Markets pages display data
- ✅ Render spin-down (first request after 15+ min idle) shows loading message and retries
- ✅ No CORS errors in console
- ✅ No hardcoded URLs in Network requests

---

**Need Help?**
- Check backend logs: `Render Dashboard → Logs`
- Check frontend logs: `Browser DevTools → Console`
- Check environment vars: `Render Settings → Environment Variables` and `Vercel Settings → Environment Variables`
