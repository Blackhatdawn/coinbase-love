# Security Fix #2: Content Security Policy (CSP) Hardening

## Issue
Current CSP policy is too permissive, allowing inline scripts and eval:
```
"default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
```

This defeats CSP's purpose and increases XSS attack surface.

## Solution
Implement strict CSP with minimal required exceptions.

### Update server/src/middleware/security.ts

**Old Code:**
```typescript
export const securityHeaders = (req: Request, res: Response, next: NextFunction) => {
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
  );
  
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-Powered-By', 'CryptoVault');
  
  next();
};
```

**New Code:**
```typescript
export const securityHeaders = (req: Request, res: Response, next: NextFunction) => {
  const isProduction = process.env.NODE_ENV === 'production';
  
  // Strict CSP with nonce for inline styles
  const cspDirectives = {
    'default-src': "'self'",
    'script-src': "'self' https://cdn.jsdelivr.net https://cdn.tailwindcss.com",
    'style-src': "'self' https://fonts.googleapis.com https://cdn.tailwindcss.com",
    'font-src': "'self' https://fonts.gstatic.com",
    'img-src': "'self' https: data:",
    'media-src': "'self'",
    'connect-src': "'self' https://api.coingecko.com wss:", // For future WebSocket
    'frame-ancestors': "'none'",
    'base-uri': "'self'",
    'form-action': "'self'",
    'manifest-src': "'self'",
    'object-src': "'none'",
    'prefetch-src': "'self'",
    'worker-src': "'self'",
    'upgrade-insecure-requests': isProduction ? '' : undefined,
  };
  
  const cspString = Object.entries(cspDirectives)
    .filter(([, value]) => value !== undefined && value !== '')
    .map(([key, value]) => `${key} ${value}`)
    .join('; ');
  
  res.setHeader('Content-Security-Policy', cspString);
  
  // Additional security headers
  res.setHeader('Content-Security-Policy-Report-Only', cspString);
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
  res.setHeader('X-Powered-By', 'CryptoVault/2.0');
  
  next();
};
```

### For Production with Tailwind CSS

If using Tailwind with inline styles (which it does), two options:

**Option A: Use Nonce (Recommended)**

```typescript
import { randomBytes } from 'crypto';

export const securityHeaders = (req: Request, res: Response, next: NextFunction) => {
  // Generate unique nonce for each request
  const nonce = randomBytes(16).toString('base64');
  res.locals.nonce = nonce;
  
  const cspDirectives = {
    'default-src': "'self'",
    'script-src': `'self' 'nonce-${nonce}' https://cdn.jsdelivr.net`,
    'style-src': `'self' 'nonce-${nonce}' https://fonts.googleapis.com`,
    'img-src': "'self' https: data:",
    'connect-src': "'self' https://api.coingecko.com",
    'frame-ancestors': "'none'",
  };
  
  const cspString = Object.entries(cspDirectives)
    .map(([key, value]) => `${key} ${value}`)
    .join('; ');
  
  res.setHeader('Content-Security-Policy', cspString);
  next();
};

// In Vite config (frontend), inject nonce into HTML
// This requires server-side rendering or template
```

**Option B: Allow Tailwind (Acceptable for now)**

```typescript
export const securityHeaders = (req: Request, res: Response, next: NextFunction) => {
  const cspDirectives = {
    'default-src': "'self'",
    'script-src': "'self' https://cdn.jsdelivr.net",
    'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com", // Tailwind needs this
    'font-src': "'self' https://fonts.gstatic.com",
    'img-src': "'self' https: data:",
    'connect-src': "'self' https://api.coingecko.com",
    'frame-ancestors': "'none'",
  };
  
  const cspString = Object.entries(cspDirectives)
    .map(([key, value]) => `${key} ${value}`)
    .join('; ');
  
  res.setHeader('Content-Security-Policy', cspString);
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  
  next();
};
```

## Environment Variables

Add to .env:
```env
# CSP Configuration
CSP_REPORT_URI=https://example.report-uri.com/r/d/csp/reportOnly
CSP_ENFORCE_UPGRADE_INSECURE=true
```

## Testing CSP Policy

### 1. Test in Firefox Developer Tools

1. Open DevTools > Storage > Cookies
2. Check if auth_token cookie exists and is HttpOnly
3. Try to access in console: `document.cookie` should be empty

### 2. Verify CSP Headers

```bash
# Check response headers
curl -I http://localhost:5000/api/health

# Should include:
# Content-Security-Policy: default-src 'self'; ...
```

### 3. Test CSP Violations

Create a test endpoint:
```typescript
app.get('/test-csp-violation', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
      <head><title>CSP Test</title></head>
      <body>
        <h1>CSP Violation Test</h1>
        <script>
          // This will be blocked by CSP
          console.log('This should be blocked');
        </script>
        <script src="https://trusted-cdn.com/script.js"></script>
      </body>
    </html>
  `);
});
```

Then check browser console for CSP violation messages.

## Reporting CSP Violations

To monitor CSP violations in production:

```typescript
// server/src/routes/csp-reports.ts
import { Router, Request, Response } from 'express';

const router = Router();

router.post('/csp-report', (req: Request, res: Response) => {
  const { 'csp-report': report } = req.body;
  
  // Log violation
  console.error('CSP Violation:', {
    'document-uri': report['document-uri'],
    'violated-directive': report['violated-directive'],
    'effective-directive': report['effective-directive'],
    'original-policy': report['original-policy'],
    'blocked-uri': report['blocked-uri'],
    'source-file': report['source-file'],
    'line-number': report['line-number'],
    'status-code': report['status-code'],
  });
  
  // Send to external service (Sentry, ReportURI, etc.)
  // await externalReporter.report(report);
  
  res.status(204).send();
});

export default router;

// In server.ts:
// app.use('/api/csp-report', cspReportRoutes);
```

## CSP Directive Explained

| Directive | Value | Purpose |
|-----------|-------|---------|
| `default-src` | `'self'` | Default for all content types |
| `script-src` | `'self'` | Only allow scripts from same origin |
| `style-src` | `'self' 'unsafe-inline'` | Styles from self and inline (Tailwind needs this) |
| `img-src` | `'self' https: data:` | Images from self, HTTPS, and data URIs |
| `font-src` | `'self' https://fonts.gstatic.com` | Fonts from self and Google Fonts |
| `connect-src` | `'self' https://api.coingecko.com` | API calls to self and CoinGecko |
| `frame-ancestors` | `'none'` | Prevent embedding in iframes |
| `base-uri` | `'self'` | Only allow base tag to self |
| `object-src` | `'none'` | Disable object/embed/applet tags |

## Gradual Rollout

1. **Week 1:** Deploy with `Content-Security-Policy-Report-Only` header (non-blocking)
2. **Monitor violations** for 5 days
3. **Adjust policy** based on reported violations
4. **Week 2:** Deploy with enforcing CSP header
5. **Monitor for issues** throughout week
6. **Remove report-only** header once stable

## Monitoring Tools

- **Report-URI.com** - Free CSP violation monitoring
- **Sentry** - Error tracking with CSP support
- **Splunk** - Enterprise logging and CSP analysis

## Validation

After deployment, verify:
- [ ] No CSP violations in DevTools console
- [ ] All external resources load (fonts, CDN scripts)
- [ ] Inline Tailwind styles work
- [ ] App functionality unchanged
- [ ] API calls work normally
- [ ] No JavaScript eval() anywhere
- [ ] No inline script tags (except with nonce)
