# CORS Issue & Fix Guide

## The Problem

Your frontend was unable to update with data from the backend due to a **CORS (Cross-Origin Resource Sharing)** misconfiguration.

### Root Cause
- Frontend is running on `localhost:3000` (or your Vercel domain)
- Backend is running on `https://cryptovault-api.onrender.com` (Render)
- Backend CORS was set to `*` (wildcard) with credentials enabled
- **Browsers reject this combination** - you cannot use wildcard CORS with credentialed requests

### Technical Details
The API client sends requests with `withCredentials: true`, which means it includes cookies/authentication headers. Browsers have a security restriction that prevents this when the backend uses wildcard CORS (`*`).

## The Solution

### Step 1: Update Render Environment Variables

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Find your service**: Look for `cryptovault-api` service
3. **Click on the service** to open settings
4. **Go to Environment** tab
5. **Add/Update the following environment variable**:
   ```
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://cryptovault.vercel.app
   ```
   
   ⚠️ **Important**: 
   - Replace `https://cryptovault.vercel.app` with your actual Vercel frontend domain
   - Separate multiple origins with commas (no spaces)
   - Use `http://localhost:3000` for local development
   - Use `https://` for production domains

6. **Click Save Changes** - This will redeploy your service (takes ~1-2 minutes)

### Step 2: Find Your Frontend Domain

If you don't know your frontend domain:

1. Go to **Vercel Dashboard**: https://vercel.com/dashboard
2. Find your project (likely named `cryptovault-frontend` or similar)
3. Copy the **Production URL** (usually something like `https://cryptovault-xxx.vercel.app`)
4. Use this URL in the `CORS_ORIGINS` variable above

### Step 3: Verify the Fix

Once Render redeploys:

1. **Open your frontend** in a browser
2. **Open Developer Tools** (F12 or Cmd+Opt+I)
3. **Go to Console** tab
4. **Go to Network** tab
5. **Reload the page** (F5 or Cmd+R)
6. **Look for API requests** to `/api/crypto` or other endpoints
7. **Check if they succeed** (status 200) instead of showing CORS errors

### Expected Behavior After Fix

✅ API requests should succeed
✅ Frontend should display crypto data
✅ No CORS errors in console
✅ Network tab shows successful API responses

---

## For Local Development

If you want to run the backend locally for development:

1. **Copy the `.env` file** from `backend/.env` (already created)
2. **Update MongoDB credentials** if needed
3. **Run the backend**: `python run_server.py` or `uvicorn backend.server:app --reload --host 0.0.0.0 --port 8000`
4. **Update `VITE_API_BASE_URL`** to empty string (to use Vite proxy) or `http://localhost:8000`
5. Frontend will use the Vite proxy to route `/api` requests to your local backend

---

## Troubleshooting

### Still seeing CORS errors after changes?

1. **Make sure Render finished redeploying**
   - Check Render dashboard - service should show "live" status
   - Wait 2-3 minutes after saving

2. **Hard refresh your browser**
   - Press Ctrl+Shift+R (or Cmd+Shift+R on Mac)
   - Or clear browser cache for the domain

3. **Check your CORS_ORIGINS value**
   - Make sure frontend domain is correct
   - No trailing slashes
   - Separate multiple origins with commas

4. **Check Network tab in DevTools**
   - Look for the actual CORS error message
   - It will tell you what origin is missing

### Backend responding with 401 Unauthorized?

This is different from CORS - it means authentication failed, not a cross-origin issue. Check:
- Token is valid
- Cookies are being sent (should see in Network tab)
- Authentication endpoint is working

---

## Files Modified

- ✅ `backend/.env` - Created with CORS configuration
- ✅ `backend/config.py` - Updated validation logic
- ✅ `backend/server.py` - Improved CORS middleware setup

## Next Steps

1. Update `CORS_ORIGINS` on Render (**Required**)
2. Wait for Render to redeploy
3. Test the frontend
4. If still not working, check browser console for specific errors
