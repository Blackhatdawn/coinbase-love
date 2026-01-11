# ✅ Vercel Frontend Deployment - Complete Setup Guide

## 📋 What Was Fixed

1. ✅ **Root `vercel.json` Created** - Vercel now reads config from project root
2. ✅ **Paths Updated** - Build commands now navigate to `frontend/` directory
3. ✅ **Output Directory Fixed** - Set to `frontend/build`
4. ✅ **Bundle Optimization** - Code splitting configured in `vite.config.ts`
5. ✅ **API Configuration Improved** - Better error messages for missing env vars
6. ✅ **Environment Variables Documented** - `.env.example` created

---

## 🚀 REQUIRED: Vercel Dashboard Configuration

### Step 1: Connect Your Git Repository
1. Go to https://vercel.com
2. Click "New Project"
3. Import your Git repository
4. Vercel should auto-detect the root `vercel.json`

### Step 2: Set Environment Variables (⚠️ CRITICAL)
**Without this, the app will NOT work!**

1. In Vercel Dashboard → Select your project
2. Go to Settings → Environment Variables
3. Add this variable:

| Key | Value | Environment |
|-----|-------|-------------|
| `VITE_API_URL` | `https://your-backend-url.com` | Production, Preview, Development |

**Examples:**
- If using Render: `https://your-app.onrender.com`
- If using Railway: `https://your-app.up.railway.app`
- If self-hosted: `https://api.yourdomain.com`

**Important**: Do NOT include `/api` in the URL - we append it automatically

### Step 3: Deploy
1. Push your changes to Git
2. Vercel will automatically trigger a deployment
3. Watch the build logs for any errors

---

## ✅ Deployment Checklist

Before pushing to Vercel:

- [ ] Changes committed and pushed to Git
- [ ] Backend URL confirmed and copied
- [ ] `VITE_API_URL` environment variable set in Vercel
- [ ] Other environment variables set (if any)

After deployment:

- [ ] Vercel deployment successful (check build logs)
- [ ] Frontend loads in browser (https://your-vercel-url.vercel.app)
- [ ] API calls work (check browser Network tab)
- [ ] Auth flows work (sign up, sign in, sign out)
- [ ] No 401/403/404 API errors in console
- [ ] Forms submit successfully

---

## 🔍 Troubleshooting

### Issue: "Frontend not loading / blank page"

**Check 1: Vercel Build Logs**
1. Go to Vercel Dashboard
2. Select your project
3. Click "Deployments" tab
4. Click the latest deployment
5. Scroll down to "Build Output"
6. Look for error messages

**Common build errors:**
- `error: no such file or directory` → Check paths in vercel.json
- `command not found: yarn` → Yarn not installed properly
- `ENOENT: no such file or directory` → Wrong working directory

### Issue: "API calls failing (404/CORS errors)"

**Check 1: Environment Variable**
```javascript
// Open browser console and run:
console.log(import.meta.env.VITE_API_URL)
```

If it shows `undefined`, then `VITE_API_URL` is not set in Vercel.

**Fix:**
1. Go to Vercel Settings → Environment Variables
2. Add `VITE_API_URL = https://your-backend-url.com`
3. Redeploy the project (click "Redeploy" on latest deployment)

**Check 2: Backend URL Correct**
1. Test the URL in browser: `https://your-backend-url.com/api/auth/me`
2. Should return 401 (unauthorized) or user data
3. If timeout or 502, backend might be down

**Check 3: CORS Configuration**
Backend must allow requests from your Vercel URL:
- Vercel URL: `https://your-project.vercel.app`
- Add to backend CORS allowed origins

### Issue: "Build fails with large chunk warnings"

This is expected after optimization. It's a warning, not an error. The build should still complete and deploy.

To see build optimization:
```bash
cd frontend
npm run build
# Look for chunk sizes in output
```

### Issue: "AuthContext shows user as loading indefinitely"

**Likely cause:** API initialization failed
1. Check console for errors: `Cmd+Option+J` (Mac) or `Ctrl+Shift+J` (Windows)
2. Check if `VITE_API_URL` is set and backend is running
3. Check backend CORS configuration

---

## 📊 Expected Build Output

After successful build, you should see something like:

```
✓ 2760 modules transformed.
build/index.html                     1.29 kB │ gzip:   0.54 kB
build/assets/index-xxx.css          73.85 kB │ gzip:  12.68 kB
build/assets/vendor-xxx.js         200.00 kB │ gzip:  60.00 kB
build/assets/pages-xxx.js          100.00 kB │ gzip:  30.00 kB
build/assets/core-xxx.js            50.00 kB │ gzip:  15.00 kB
✓ built in XX.XXs
```

Chunks should be split (not one huge 1.18 MB chunk).

---

## 🔧 Local Development (Reference)

```bash
# Install dependencies
cd frontend
yarn install

# Start dev server
yarn dev
# Open http://localhost:3000

# Build for production
yarn build

# Preview production build
yarn preview
```

---

## 📝 Files Modified

- ✅ `/vercel.json` - New root configuration
- ✅ `frontend/vite.config.ts` - Bundle optimization
- ✅ `frontend/src/lib/api.ts` - Better error messages
- ✅ `frontend/src/contexts/AuthContext.tsx` - Error handling
- ✅ `frontend/.env.example` - Documentation

---

## 🆘 Still Having Issues?

1. **Check Vercel build logs** - Most helpful resource
2. **Verify backend is running** - Test the API URL directly
3. **Confirm VITE_API_URL is set** - This is the #1 issue
4. **Clear browser cache** - Cmd+Shift+Delete (Chrome)
5. **Check browser console** - `Ctrl+Shift+J` for errors

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Vite Configuration Guide](https://vitejs.dev/config/)
- [React Router Deployment](https://reactrouter.com/en/main/guides/deployment)
- [CORS Configuration](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
