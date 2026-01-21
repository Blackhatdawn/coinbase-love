# Updating Vercel Configuration for Different Backends

The `vercel.json` file contains hardcoded backend URLs. When deploying to different environments, you need to update the backend URL to match your deployment target.

## Production Deployment Steps

1. **Development/Preview Deployments**: Backend URL in `vercel.json` defaults to `https://cryptovault-api.onrender.com`

2. **Custom Backend**: To use a different backend URL:
   - Find all occurrences of `https://cryptovault-api.onrender.com` in `vercel.json`
   - Replace with your actual backend URL (e.g., `https://api.yourdomain.com`)
   - Commit and push to trigger a new deployment

3. **Via Vercel Environment Variables**:
   - Set `VITE_BACKEND_URL` in Vercel project settings
   - The frontend's `runtimeConfig.ts` will use this value if set

## Key Locations to Update

```json
{
  "rewrites": [
    { "destination": "https://cryptovault-api.onrender.com/api/docs" },
    { "destination": "https://cryptovault-api.onrender.com/api/docs/:path*" },
    { "destination": "https://cryptovault-api.onrender.com/api/redoc" },
    { "destination": "https://cryptovault-api.onrender.com/api/openapi.json" },
    { "destination": "https://cryptovault-api.onrender.com/api/:path*" },
    { "destination": "https://cryptovault-api.onrender.com/health" },
    { "destination": "https://cryptovault-api.onrender.com/ping" },
    { "destination": "https://cryptovault-api.onrender.com/csrf" },
    { "destination": "https://cryptovault-api.onrender.com/socket.io/:path*" },
    { "destination": "https://cryptovault-api.onrender.com/ws/:path*" }
  ]
}
```

## Alternative: Using Vercel Build Hooks

Create a `scripts/update-vercel-config.js` file to dynamically generate `vercel.json`:

```javascript
const fs = require('fs');
const baseConfig = require('../vercel.base.json');

const backendUrl = process.env.VITE_BACKEND_URL || 'https://cryptovault-api.onrender.com';

const config = {
  ...baseConfig,
  rewrites: baseConfig.rewrites.map(rewrite => ({
    ...rewrite,
    destination: rewrite.destination.replace('https://cryptovault-api.onrender.com', backendUrl)
  }))
};

fs.writeFileSync('./vercel.json', JSON.stringify(config, null, 2));
```

Then add to `package.json` scripts:
```json
{
  "scripts": {
    "prebuild": "node scripts/update-vercel-config.js && yarn build"
  }
}
```

## Best Practice: Runtime Configuration

The frontend loads most configuration at runtime from `/api/config`. This is the recommended approach for production flexibility.

Set these in your backend's `.env`:
```
PUBLIC_API_BASE_URL=https://yourdomain.com
PUBLIC_WS_BASE_URL=wss://yourdomain.com
PUBLIC_SENTRY_DSN=your-sentry-dsn
PUBLIC_BRANDING_SITE_NAME=CryptoVault
PUBLIC_BRANDING_SUPPORT_EMAIL=support@yourdomain.com
```

The frontend will fetch and use these values automatically.
