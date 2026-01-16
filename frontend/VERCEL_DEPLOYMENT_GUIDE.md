# Vercel Deployment Configuration Guide

## Overview
This guide explains how to properly configure CryptoVault for deployment on Vercel with all environment variables correctly set.

## ✅ Current Configuration Status

### Environment Files Created
- ✅ `frontend/.env.production` - Production environment variables
- ✅ `frontend/.env.development` - Development environment variables  
- ✅ `frontend/.env.example` - Template for reference
- ✅ `frontend/vercel.json` - Vercel configuration with API rewrites and security headers

### API Client Configuration
- ✅ `frontend/src/lib/apiClient.ts` - Uses `import.meta.env.VITE_API_BASE_URL`
- ✅ Sentry initialization in `frontend/src/lib/sentry.ts`
- ✅ Debug status component in `frontend/src/components/DebugApiStatus.tsx`

## Required Vercel Environment Variables

In your Vercel project dashboard, go to **Settings → Environment Variables** and add these:

### Variable: `VITE_API_BASE_URL`
- **Value**: `https://cryptovault-api.onrender.com`
- **Environments**: Production, Preview, Development
- **Description**: Base URL for all API calls

### Variable: `VITE_APP_NAME`
- **Value**: `CryptoVault`
- **Environments**: Production, Preview, Development
- **Description**: Application display name

### Variable: `VITE_APP_VERSION`
- **Value**: `1.0.0`
- **Environments**: Production, Preview, Development
- **Description**: Application version

### Variable: `VITE_NODE_ENV`
- **Value**: `production`
- **Environments**: Production only
- **Description**: Node environment mode

### Variable: `VITE_ENABLE_SENTRY`
- **Value**: `true`
- **Environments**: Production only
- **Description**: Enable Sentry error tracking in production

### Variable: `VITE_SENTRY_DSN`
- **Value**: `https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/4510716879503360`
- **Environments**: Production only
- **Description**: Sentry project DSN for error tracking

## Build Configuration

Your `vercel.json` is already configured with:

```json
{
  "version": 3,
  "framework": null,
  "buildCommand": "yarn build",
  "installCommand": "yarn install",
  "devCommand": "yarn dev",
  "outputDirectory": "dist"
}
```

## API Routing

The `vercel.json` file contains rewrites that proxy all `/api/*` requests to your backend:

```json
{
  "source": "/api/:path+",
  "destination": "https://cryptovault-api.onrender.com/:path+"
}
```

This means:
- Frontend makes requests to `https://yourdomain.com/api/auth/login`
- Vercel proxies them to `https://cryptovault-api.onrender.com/auth/login`
- Your `VITE_API_BASE_URL` is only used in development

## Security Headers

The following security headers are automatically applied:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=63072000`
- And more...

## Deployment Checklist

### Before Pushing to Vercel

- [ ] All environment variables are set in Vercel dashboard
- [ ] Environment files (`.env.production`, `.env.development`) are committed
- [ ] `.env.local` is in `.gitignore` (local overrides)
- [ ] Run `yarn build` locally to verify build succeeds
- [ ] Check for any console errors in local build

### After Pushing to Vercel

1. **Monitor Vercel Build**
   - Go to Vercel project dashboard
   - Click on the deployment
   - Check build logs for any errors

2. **Verify Environment Variables**
   - The logs should show: `[API Client] Initialized with BASE_URL: https://cryptovault-api.onrender.com`
   - If you see `(empty - using relative paths)`, env var was not set

3. **Test API Connectivity**
   - Open DevTools (F12)
   - Check Network tab for `/api/*` requests
   - Requests should go to `https://cryptovault-api.onrender.com`

4. **Check Sentry Integration**
   - If `VITE_ENABLE_SENTRY=true`, Sentry should initialize
   - Check console for: `Sentry initialized for production error tracking`

## Troubleshooting

### Issue: "VITE_API_BASE_URL is not configured"

**Solution**: 
1. Go to Vercel project Settings → Environment Variables
2. Add all required variables listed above
3. Make sure variables are available for "Production" environment
4. Click "Redeploy" to rebuild with new env vars

### Issue: API Calls Fail in Production

**Check these things**:
1. Open DevTools Network tab
2. Click on an API request
3. Verify URL is using `/api/...` (not full backend URL)
4. Check response for CORS errors
5. Verify backend is running and accessible

### Issue: Build Fails on Vercel

**Check build logs** for:
- Missing dependencies: Run `yarn install` locally and recommit `yarn.lock`
- TypeScript errors: Run `yarn build` locally to reproduce
- Missing env vars: Ensure all VITE_* variables are set
- Sentry DSN invalid: Verify exact format of `VITE_SENTRY_DSN`

### Issue: Sentry Not Initializing

**Verify**:
1. `VITE_ENABLE_SENTRY=true` in production
2. `VITE_SENTRY_DSN` is set correctly
3. Check browser console for errors
4. Ensure you're viewing production deployment (not preview)

## Local Development

To test environment variables locally:

```bash
# Development (uses localhost backend)
yarn dev

# Production build (uses remote backend)
yarn build
yarn preview
```

Environment files are loaded in this order:
1. `.env` - Base environment
2. `.env.development` or `.env.production` - Mode-specific
3. `.env.local` - Local overrides (not committed)

## Production Optimization

Your configuration includes:

- **Code splitting** by vendor, UI components, and pages
- **Source maps disabled** in production for security
- **Console/debugger statements removed** from production build
- **Gzip compression** via Vercel CDN
- **Static asset caching** with long-lived cache headers
- **HTML/CSS/JS caching** with stale-while-revalidate

## Monitoring

After deployment:

1. **Sentry**: Check error tracking dashboard
2. **Vercel Analytics**: Monitor performance metrics
3. **Health Check**: `/api/health` endpoint runs every 5 minutes
4. **Response Times**: Monitor API latency in Vercel dashboard

## Contact & Support

- **Vercel Support**: https://vercel.com/support
- **Sentry Documentation**: https://docs.sentry.io/
- **Vite Documentation**: https://vitejs.dev/
