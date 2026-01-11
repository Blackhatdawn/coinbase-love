# 🚀 IMMEDIATE ACTIONS - Fix Frontend in 10 Minutes

Your frontend is failing because backend CORS and environment variables aren't properly configured.  
**This guide will fix it in 3 steps, ~10 minutes total.**

---

## **STEP 1: Configure Render Backend (3 minutes)**

### Where: Render Dashboard → Your Backend Service

1. Open [Render Dashboard](https://dashboard.render.com)
2. Click on your backend service (name like `coinbase-love`)
3. Click **Settings** (or **Environment** tab)
4. Click **Environment Variables**
5. **Find or Add these 3 variables:**

```bash
# Variable 1 - COPY YOUR VERCEL FRONTEND URL FROM HERE:
# https://your-app-name.vercel.app

CORS_ORIGINS
Value: https://your-app-name.vercel.app,http://localhost:3000

APP_URL
Value: https://your-app-name.vercel.app

ENVIRONMENT
Value: production
```

**Real Example:**
```bash
CORS_ORIGINS=https://cryptovault-app.vercel.app,http://localhost:3000
APP_URL=https://cryptovault-app.vercel.app
ENVIRONMENT=production
```

6. Click **Save** (or at bottom if needed)
7. **Render will auto-redeploy** ✅
8. **Wait 2-3 minutes** for restart (watch Logs tab)

---

## **STEP 2: Configure Vercel Frontend (2 minutes)**

### Where: Vercel Dashboard → Your Frontend Project → Settings

1. Open [Vercel Dashboard](https://vercel.com/dashboard)
2. Click your **frontend project name**
3. Click **Settings** tab (top menu)
4. Click **Environment Variables** (left sidebar)
5. **Add this variable:**

```bash
Name: VITE_API_URL
Value: https://coinbase-love.onrender.com
Environments: Select all (Production, Preview, Development)
```

6. Click **Add** / **Save**
7. Variable should appear in the list ✅

---

## **STEP 3: Redeploy Frontend (2 minutes)**

### Option A: Quick Redeploy (Recommended)

1. Stay in Vercel Dashboard
2. Click **Deployments** tab
3. Find your latest successful deployment
4. Click the **"..."** menu → **Redeploy**
5. Confirm
6. **Wait 2-3 minutes** for build ✅

### Option B: Trigger via Git

```bash
cd frontend
echo "# Deploying with production env vars" >> README.md
git add README.md
git commit -m "chore: redeploy with production settings"
git push origin main
```

---

## **STEP 4: Verify It Works (3 minutes)**

### In Browser

1. Open your **Vercel frontend URL** in **Incognito mode**
   - Example: `https://your-app.vercel.app`

2. Press `F12` to open **DevTools**

3. Click **Console** tab

4. **Look for this message:**
   ```
   ✅ Connected to: https://coinbase-love.onrender.com/api
   ```

   - ✅ If you see this → **SUCCESS!** Go to Step 5
   - ❌ If you don't see it → Backend env vars not saved yet, wait 2-3 min & refresh

5. Try to **Sign Up**
   - Email: `test@example.com`
   - Password: `Test123!@#`
   - Name: `Test User`

6. **If Sign Up works** → You're done! 🎉

---

## **Troubleshooting in 30 Seconds**

### ❌ Still blank screen?
1. Press `Ctrl+Shift+R` (hard refresh) to clear cache
2. Check **Console** tab for red errors
3. Check **Network** tab → see if requests go to `coinbase-love.onrender.com`

### ❌ See "CORS error"?
- **Render backend env vars NOT updated yet**
- Go back to STEP 1
- Check `CORS_ORIGINS` includes your Vercel URL
- Save & wait 2-3 min

### ❌ See "Failed to fetch"?
1. Check Render backend is running:
   ```bash
   curl https://coinbase-love.onrender.com/health
   ```
2. Should return `200 OK`
3. If not, restart Render service in dashboard

### ❌ Sign Up fails with error?
1. Check **Network** tab → Click `auth/signup` request
2. Look at **Response** tab
3. If you see `CORS error` → Render env vars not saved
4. If you see `400 Bad Request` → API is working, just validation error (try different email)

---

## **Success = All These Are True**

- ✅ Console shows `✅ Connected to: https://coinbase-love.onrender.com/api`
- ✅ Network tab shows requests to `coinbase-love.onrender.com` (not `localhost`)
- ✅ No red errors in Console
- ✅ No CORS errors in Console
- ✅ Sign Up request gets `200` or `400` (not CORS/network error)
- ✅ Can create account
- ✅ Can verify email (code in console in dev mode)
- ✅ Can login
- ✅ Dashboard loads

---

## **More Help?**

See full guides:
- 📋 **VERCEL_DEPLOYMENT_CHECKLIST.md** - Complete deployment guide with screenshots
- 🧪 **TESTING_PRODUCTION_SETUP.md** - Full testing procedure
- 📝 **PRODUCTION_FIXES_SUMMARY.md** - What was changed & why

---

**Your frontend should be LIVE in ~10 minutes!** ✅
