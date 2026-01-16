# CryptoVault API Misconfiguration Audit Report

**Date**: January 2026  
**Status**: ✅ **CRITICAL ISSUES IDENTIFIED AND FIXED**  
**Severity Levels**: 🔴 HIGH (2), 🟠 MEDIUM (4), 🟡 LOW (2)

---

## Executive Summary

A comprehensive audit of the frontend and backend API systems identified **8 misconfiguration issues**, of which **2 are HIGH severity** and will cause authentication failures in production. These issues have been identified and **remediated** as follows:

### High Priority Issues (FIXED ✅)
1. **CORS Wildcard + Credentials Mismatch** → Added production validation to prevent deployment with misconfiguration
2. **Cookie SameSite Policy** → Fixed to support cross-site authentication with proper conditional logic

### Medium Priority Issues (IDENTIFIED)
3. Inconsistent request validation
4. Legacy API client endpoints
5. Unimplemented export functionality
6. CSRF protection not wired

---

## 🔴 HIGH PRIORITY ISSUES (FIXED)

### Issue 1: CORS Wildcard with Credentials (Production Breaking)

**Location**: `backend/config.py` (lines 40-136), `backend/server.py` (lines 329-352)

**Problem**:
- Default configuration has `CORS_ORIGINS="*"` with `allow_credentials=True`
- Browsers **reject** credentialed cross-origin requests when CORS uses wildcard
- This silently breaks authentication when frontend and API are on different origins
- Example: `https://app.vercel.app` (frontend) → `https://api.render.com` (backend)

**Impact**: 
- ❌ **CRITICAL**: All API requests with cookies will fail in production
- Users cannot login, refresh tokens, or stay authenticated
- Frontend gets 401 errors, token refresh fails repeatedly

**The Fix** ✅ (APPLIED):
1. Added `use_cross_site_cookies` setting to `backend/config.py`
2. Added production validation that **raises an error** if `CORS_ORIGINS=="*"` in production
3. Error message guides deployment process:
   ```
   🛑 PRODUCTION ERROR: CORS_ORIGINS cannot be '*' when using credential-based authentication. 
   Browsers will reject credentialed requests with wildcard CORS. 
   Set CORS_ORIGINS to specific frontend origin(s) in production.
   Example: CORS_ORIGINS=https://app.my-domain.com,https://app-staging.my-domain.com
   ```

**Required Environment Variable** (SET FOR PRODUCTION):
```bash
# In your production environment, set:
CORS_ORIGINS=https://your-frontend-domain.com
# Or for multiple domains:
CORS_ORIGINS=https://app.vercel.app,https://app-staging.vercel.app
```

**Testing**:
```bash
# Before deploying, test CORS configuration:
curl -X OPTIONS https://api.render.com/ \
  -H "Origin: https://app.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
# Should return: Access-Control-Allow-Credentials: true
# And: Access-Control-Allow-Origin: https://app.vercel.app (NOT *)
```

---

### Issue 2: Cookie SameSite Policy (Cross-Site Authentication Failure)

**Location**: `backend/routers/auth.py` (multiple cookie setter calls - NOW FIXED)

**Problem**:
- Cookies set with `SameSite="lax"` on login, refresh, and verify-email endpoints
- `SameSite="lax"` **blocks cookies on cross-site POST requests** in browsers
- When frontend and API are different origins (typical production setup), cookies are not sent
- Result: Silent authentication failure even if CORS is correctly configured

**Example Failure Scenario**:
1. User logs in on `https://app.vercel.app`
2. Backend (on different origin) sets `access_token` cookie with `SameSite="lax"`
3. Browser sees cross-site request, blocks cookie from being sent to API
4. Frontend tries `/api/portfolio` → Server returns 401 (no cookie)
5. Token refresh tries → Fails (refresh_token cookie also not sent)
6. User is logged out

**The Fix** ✅ (APPLIED):
1. Created `set_auth_cookies()` helper function that conditionally sets `SameSite`:
   - If `USE_CROSS_SITE_COOKIES=true`: Uses `SameSite="none"` + `Secure=true` (HTTPS required)
   - If `USE_CROSS_SITE_COOKIES=false`: Uses `SameSite="lax"` (same-site default, more secure)
   
2. Updated all cookie setters in auth.py:
   - Login endpoint (`/api/auth/login`)
   - Token refresh endpoint (`/api/auth/refresh`)
   - Email verification endpoint (`/api/auth/verify-email`)

3. Added safety: `SameSite="none"` requires `Secure=true` and only works over HTTPS

**Required Environment Variable** (SET FOR CROSS-SITE DEPLOYMENT):
```bash
# Only needed if frontend and API are on DIFFERENT origins in production:
USE_CROSS_SITE_COOKIES=true

# Must also ensure:
CORS_ORIGINS=https://your-frontend-domain.com
# And API served over HTTPS
```

**Security Implications**:
- ✅ Default (`SameSite="lax"`): Better security for same-origin setups
- ⚠️ With `USE_CROSS_SITE_COOKIES=true`: Requires proper CORS restriction + HTTPS

---

## 🟠 MEDIUM PRIORITY ISSUES (IDENTIFIED)

### Issue 3: Inconsistent Request Validation

**Location**: `backend/routers/admin.py` (setup_first_admin), other endpoints

**Problem**:
- Some endpoints manually parse `request.json()` with minimal validation
- Others use Pydantic models with automatic validation and type safety
- Manual validation is error-prone and inconsistent
- Example: `setup_first_admin` checks email presence but not format

**Recommendation**:
- Prefer Pydantic models for all request bodies
- Example fix:
  ```python
  # Before (manual, unsafe)
  data = await request.json()
  if not data.get("email"):
      raise HTTPException(400, "Missing email")
  
  # After (Pydantic, safe)
  @dataclass
  class FirstAdminRequest:
      email: EmailStr
      password: str
  
  async def setup_first_admin(data: FirstAdminRequest, db=Depends(get_db)):
      # Validation happens automatically
  ```

---

### Issue 4: Legacy API Client Endpoints

**Location**: `frontend/src/lib/apiClient_old.ts` vs `backend/routers/wallet.py`

**Problem**:
- Old client uses `/wallet/balances` (plural)
- Backend provides `/wallet/balance` (singular)
- If old client is still imported, calls will 404

**Status**: Not used in current frontend code (good!)

**Recommendation**:
- Remove `frontend/src/lib/apiClient_old.ts` entirely to avoid confusion
- Verify no imports remain: `grep -r "apiClient_old" frontend/`

---

### Issue 5: Unimplemented Export Functionality

**Location**: `frontend/src/lib/apiClient.ts` (line 549), `backend/routers/admin.py`

**Problem**:
- Frontend calls `GET /api/admin/audit-logs?export=true`
- Backend doesn't recognize `export` parameter; ignores it
- Frontend expects CSV/streaming response but gets JSON

**Recommendation**:
- Either implement export on backend (return CSV format) or remove export feature from frontend

---

### Issue 6: CSRF Protection Not Wired

**Location**: `backend/server.py` (GET `/csrf`), `frontend/src/lib/apiClient.ts`

**Problem**:
- Backend provides `/csrf` endpoint that sets CSRF token cookie
- Frontend API client doesn't retrieve or send token on mutating requests
- CSRF protection exists but isn't used

**Recommendation**:
- For cookie-based auth with cross-origin mutations, implement CSRF:
  ```typescript
  // Frontend: retrieve and send token
  const csrfToken = await api.health.csrf(); // Get token
  headers['X-CSRF-Token'] = csrfToken;       // Send on POST/PUT/DELETE
  ```

---

## 🟡 LOW PRIORITY ISSUES (IDENTIFIED)

### Issue 7: Rate Limit Header Mismatch

**Location**: `backend/server.py`, `frontend/src/lib/apiClient.ts`

**Problem**:
- Backend sends `x-ratelimit-limit` and `x-ratelimit-policy` headers
- Frontend's error handler looks for `x-ratelimit-reset` or `retry-after`
- Client cannot provide accurate retry timing

**Recommendation**: Add `Retry-After` header to 429 responses

---

### Issue 8: VITE_API_BASE_URL Normalization

**Location**: `frontend/src/lib/apiClient.ts`, `frontend/vercel.json`

**Problem**:
- If `VITE_API_BASE_URL` is set with trailing `/api`, final URLs become `/api/api/...`
- No validation to catch this

**Recommendation**:
- Document expected format: `VITE_API_BASE_URL` should be base host WITHOUT `/api`
- Example: `https://api.render.com` (not `https://api.render.com/api`)

---

## 📋 ENDPOINT INVENTORY

### Backend Endpoints (by router)

```
/api/auth/*
  POST   /api/auth/signup
  POST   /api/auth/login
  POST   /api/auth/logout
  GET    /api/auth/me
  PUT    /api/auth/profile
  POST   /api/auth/refresh
  POST   /api/auth/verify-email
  POST   /api/auth/2fa/setup
  ... (14 total auth endpoints)

/api/admin/*
  POST   /api/admin/setup-first-admin
  GET    /api/admin/stats
  GET    /api/admin/users
  GET    /api/admin/audit-logs
  ... (9 total admin endpoints)

/api/portfolio/*
  GET    /api/portfolio
  GET    /api/portfolio/holding/{symbol}
  POST   /api/portfolio/holding
  DELETE /api/portfolio/holding/{symbol}

/api/wallet/*
  GET    /api/wallet/balance
  POST   /api/wallet/deposit/create
  POST   /api/wallet/withdraw
  ... (8 total wallet endpoints)

/api/orders/*
  GET    /api/orders
  POST   /api/orders
  GET    /api/orders/{order_id}

/api/prices/*
  GET    /api/prices
  GET    /api/prices/{symbol}
  GET    /api/prices/bulk/{symbols}

/api/transactions/*
  GET    /api/transactions
  GET    /api/transactions/{transaction_id}

/api/transfers/*
  POST   /api/transfers/p2p
  GET    /api/transfers/p2p/history

/api/alerts/*
  GET/POST/PATCH/DELETE /api/alerts/*

/api/users/*
  GET    /api/users/search?email=...
  GET    /api/users/{user_id}

/api/crypto/*
  GET    /api/crypto
  GET    /api/crypto/{coin_id}

WebSocket
  /ws/prices
  /ws/prices/{symbol}

Health/Docs
  GET    /health
  GET    /api/health
  GET    /api/docs
  GET    /api/openapi.json
```

---

## 🚀 PRODUCTION DEPLOYMENT CHECKLIST

### Required Steps (Before Deploy)

- [ ] **Set CORS_ORIGINS environment variable**
  ```bash
  CORS_ORIGINS=https://your-app-domain.com
  # For multiple domains:
  CORS_ORIGINS=https://app.vercel.app,https://staging.vercel.app
  ```

- [ ] **For cross-origin setup, enable cross-site cookies**
  ```bash
  USE_CROSS_SITE_COOKIES=true
  CORS_ORIGINS=https://your-frontend-domain.com
  # Verify backend is served over HTTPS
  ```

- [ ] **Verify API base URL configuration**
  ```bash
  # Frontend environment
  VITE_API_BASE_URL=https://your-api-domain.com  # No /api suffix
  # OR leave empty to use relative /api/* paths with Vercel rewrite
  ```

- [ ] **Test auth flow end-to-end**
  ```bash
  # 1. Test CORS preflight
  curl -X OPTIONS https://api.domain.com/api/auth/login \
    -H "Origin: https://app.domain.com" -v
  
  # 2. Test login (should set cookies)
  curl -X POST https://api.domain.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"test"}' \
    -c cookies.txt
  
  # 3. Test credentialed request (should use cookies)
  curl https://api.domain.com/api/portfolio \
    -b cookies.txt -v
  ```

- [ ] **Verify HTTPS** (Required for SameSite=None)
  ```bash
  # All API and frontend URLs must be HTTPS
  https://app.domain.com      ✅
  https://api.domain.com      ✅
  http://api.domain.com       ❌ Won't work with SameSite=None
  ```

- [ ] **Check environment variables are set**
  ```bash
  # Backend production env should have:
  ENVIRONMENT=production
  CORS_ORIGINS=<your-frontend-url>
  MONGO_URL=<mongo-connection>
  JWT_SECRET=<secure-32-char-minimum>
  
  # Frontend production env should have:
  VITE_API_BASE_URL=https://api.domain.com  (or empty for relative)
  VITE_SENTRY_DSN=<sentry-url>
  ```

### Verification Steps (After Deploy)

- [ ] **Test login flow**
  - Navigate to `/auth`
  - Enter credentials
  - Verify cookies are set in browser DevTools (Application → Cookies)
  - Verify `access_token` and `refresh_token` are present
  - Check `SameSite` attribute: should be `none` if cross-origin, `lax` if same-origin

- [ ] **Test API calls with credentials**
  - Open browser console
  - Call `api.portfolio.get()`
  - Verify request includes cookies (Network tab → Cookies sent with request)
  - Verify response includes user data (not 401)

- [ ] **Monitor error logs**
  - Check Sentry for 401/403 errors
  - Monitor backend logs for CORS rejections
  - Look for "token refresh failed" errors

---

## 📊 SUMMARY TABLE

| Issue | Severity | Status | File | Fix |
|-------|----------|--------|------|-----|
| CORS wildcard + credentials | 🔴 HIGH | ✅ FIXED | config.py, server.py | Set CORS_ORIGINS to specific origin |
| Cookie SameSite="lax" | 🔴 HIGH | ✅ FIXED | routers/auth.py | Use conditional SameSite, enable USE_CROSS_SITE_COOKIES |
| Inconsistent validation | 🟠 MEDIUM | - | routers/admin.py | Use Pydantic models consistently |
| Legacy client endpoints | 🟠 MEDIUM | - | lib/apiClient_old.ts | Remove legacy client |
| Unimplemented export | 🟠 MEDIUM | - | routers/admin.py | Implement or remove feature |
| CSRF not wired | 🟠 MEDIUM | - | lib/apiClient.ts | Add CSRF token retrieval/sending |
| Rate limit headers | 🟡 LOW | - | server.py | Add Retry-After header |
| VITE_API_BASE_URL format | 🟡 LOW | - | lib/apiClient.ts | Normalize and document |

---

## 🔍 Files Modified in This Audit

1. **backend/config.py**
   - Added `use_cross_site_cookies: bool = False` setting
   - Added production validation that raises error if CORS_ORIGINS == "*"

2. **backend/server.py**
   - Updated CORS warning messages for clarity
   - Added development guidance

3. **backend/routers/auth.py**
   - Created `set_auth_cookies()` helper function with conditional SameSite logic
   - Updated login endpoint to use helper
   - Updated refresh endpoint to use conditional SameSite
   - Updated verify-email endpoint to use helper

4. **frontend/vercel.json** (already fixed in previous session)
   - Removed unsupported properties (analytics, speedInsights, etc.)

---

## 📚 Additional Resources

- **CORS + Credentials**: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#credentials_mode
- **SameSite Cookies**: https://web.dev/same-site-cookies-explained/
- **Cross-Origin API Auth**: https://owasp.org/www-community/attacks/csrf
- **FastAPI CORS**: https://fastapi.tiangolo.com/tutorial/cors/

---

## Questions?

If you encounter authentication failures after deployment:
1. Check browser DevTools → Application → Cookies (verify access_token presence)
2. Check Network tab → Headers (verify Set-Cookie response header)
3. Check backend logs for CORS rejections
4. Verify CORS_ORIGINS environment variable is set correctly
5. Ensure both frontend and backend are on HTTPS (for SameSite=None)

