# Backend System & Integration Review - CryptoVault

**Date:** January 2026  
**Project:** CryptoVault (React Frontend + Node.js/Express Backend)  
**Status:** Multiple critical and high-priority issues identified

---

## Executive Summary

Your backend system is well-structured with a solid foundation, but contains **3 critical issues** and **3 high-priority security concerns** that must be addressed before production deployment:

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 3 | Must fix immediately |
| 🟠 High | 3 | Fix before production |
| 🟡 Medium | 5 | Improve for robustness |
| 🟢 Low | 2 | Nice to have |

---

## Part 1: System Architecture Overview

### Server Setup
**File:** `server/src/server.ts`

✅ **Good:**
- Security-first middleware order (helmet → CORS → cookieParser)
- Global rate limiting (100 req/15min per IP)
- Request logging with timing
- Centralized error handling
- Health check endpoint

```
Middleware Stack (correct order):
1. Helmet (security headers)
2. Custom security headers (CSP with nonce)
3. CORS (with credentials)
4. Cookie parser
5. Body size limits (10kb)
6. Rate limiters (global + per-route)
7. Route handlers
8. 404 handler
9. Error handler
```

### Database Configuration
**File:** `server/src/config/database.ts`

✅ **Good:**
- Connection pooling (max: 20, min: 5)
- Query logging for debugging
- Schema initialization on startup
- Proper indexes on frequently queried fields

⚠️ **Concern:**
- Default credentials in code (`host=localhost, user=postgres, password=postgres`)
- Should use environment variables for production

**Schema:**
- `users` - Account info
- `portfolios` - Per-user portfolio (UNIQUE constraint)
- `holdings` - Crypto positions (UNIQUE per portfolio/symbol)
- `orders` - Trading orders
- `transactions` - Transaction history
- `revoked_refresh_tokens` - Token revocation tracking
- `user_2fa` - 2FA configuration
- `audit_logs` - Security audit trail

---

## Part 2: Critical Issues 🔴

### Issue #1: Duplicate API Key in Frontend (BREAKS AUTH)
**Severity:** 🔴 CRITICAL  
**File:** `src/lib/api.ts` (lines 134 and 151)  
**Impact:** Frontend authentication completely broken

**Problem:**
The `api.auth` object is declared twice. The second declaration overwrites the first:

```typescript
// First declaration (lines 134-146)
auth: {
  signup: (email, password, name) => request('/auth/signup', ...),
  login: (email, password) => request('/auth/login', ...),
  logout: () => request('/auth/logout', ...),
  getProfile: () => request('/auth/me'),
  refresh: () => request('/auth/refresh', ...),
  verifyEmail: (token, email) => request('/auth/verify-email', ...),
},

// Second declaration (lines 151-162) - OVERWRITES FIRST
auth: {
  setup2FA: () => request('/auth/2fa/setup', ...),
  verify2FA: (code) => request('/auth/2fa/verify', ...),
  get2FAStatus: () => request('/auth/2fa/status'),
  disable2FA: (password) => request('/auth/2fa/disable', ...),
  getBackupCodes: () => request('/auth/2fa/backup-codes', ...),
},
```

**Consequence:**
When `src/contexts/AuthContext.tsx` calls `api.auth.getProfile()`, `api.auth.login()`, etc., they are `undefined`, causing runtime errors.

**Fix:**
Merge both objects into a single `auth` namespace:

```typescript
auth: {
  // Auth methods
  signup: (email, password, name) => request('/auth/signup', ...),
  login: (email, password) => request('/auth/login', ...),
  logout: () => request('/auth/logout', ...),
  getProfile: () => request('/auth/me'),
  refresh: () => request('/auth/refresh', ...),
  verifyEmail: (token, email) => request('/auth/verify-email', ...),
  
  // 2FA methods
  setup2FA: () => request('/auth/2fa/setup', ...),
  verify2FA: (code) => request('/auth/2fa/verify', ...),
  get2FAStatus: () => request('/auth/2fa/status'),
  disable2FA: (password) => request('/auth/2fa/disable', ...),
  getBackupCodes: () => request('/auth/2fa/backup-codes', ...),
},
```

---

### Issue #2: Token Type Not Enforced - Security Bypass
**Severity:** 🔴 CRITICAL  
**File:** `server/src/middleware/auth.ts` (lines 24-35)  
**Impact:** Refresh tokens can be used as access tokens

**Problem:**
The `verifyToken` function ignores the `isRefresh` parameter and doesn't validate token type:

```typescript
export const verifyToken = (token: string, isRefresh: boolean = false) => {
  try {
    const secret = process.env.JWT_SECRET;
    if (!secret) throw new Error('JWT_SECRET not configured');
    
    const decoded = jwt.verify(token, secret);
    return decoded as { id: string; email: string; type: string; jti?: string };
    // BUG: Never checks if decoded.type matches the expected type!
  } catch (error) {
    return null;
  }
};
```

And in `authMiddleware` (line 129):
```typescript
const decoded = verifyToken(token, false); // isRefresh=false parameter is ignored
if (!decoded) {
  return res.status(401).json({ error: 'Invalid or expired token' });
}
// BUG: Never validates decoded.type === 'access'
req.user = decoded;
next();
```

**Attack Scenario:**
1. Attacker steals a long-lived refresh token (7-day expiry)
2. Uses it as the `accessToken` cookie or in `Authorization` header
3. `authMiddleware` accepts it as a valid access token
4. Attacker gains full API access

**Fix:**
Add type checking in `verifyToken`:

```typescript
export const verifyToken = (token: string, isRefresh: boolean = false) => {
  try {
    const secret = process.env.JWT_SECRET;
    if (!secret) throw new Error('JWT_SECRET not configured');
    
    const decoded = jwt.verify(token, secret) as { 
      id: string; 
      email: string; 
      type: string; 
      jti?: string 
    };
    
    // CRITICAL: Enforce token type
    const expectedType = isRefresh ? 'refresh' : 'access';
    if (decoded.type !== expectedType) {
      console.warn(`Token type mismatch: expected ${expectedType}, got ${decoded.type}`);
      return null;
    }
    
    return decoded;
  } catch (error) {
    return null;
  }
};
```

---

### Issue #3: 2FA Backup Codes Stored in Plaintext
**Severity:** 🔴 CRITICAL  
**File:** `server/src/utils/2fa.ts` (lines 75-89)  
**Impact:** If database is compromised, all backup codes are exposed

**Problem:**
Backup codes are generated and stored as plaintext in the database:

```typescript
export const hashBackupCode = (code: string): string => {
  // In production, use bcryptjs.hash()
  // For now, return as-is (should be encrypted in database)
  return code; // Returns plaintext!
};

export const verifyBackupCode = (code: string, hashedCode: string): boolean => {
  // In production, use bcryptjs.compare()
  // For now, simple comparison
  return code === hashedCode; // Plaintext comparison!
};
```

In `server/src/routes/2fa.ts` (line 31):
```typescript
const backupCodes = generateBackupCodes(10);
await query(
  `INSERT INTO user_2fa (user_id, totp_secret, backup_codes)
   VALUES ($1, $2, $3)`,
  [req.user.id, secret, backupCodes] // Stored as plaintext!
);
```

**Consequence:**
- SQL injection attack → attacker reads all backup codes
- Database breach → all users' backup codes exposed
- Backup codes are 2FA bypass mechanism

**Fix:**
Hash backup codes before storage using bcrypt:

```typescript
import bcrypt from 'bcryptjs';

const BACKUP_CODE_SALT_ROUNDS = 10;

export const hashBackupCode = async (code: string): Promise<string> => {
  return bcrypt.hash(code, BACKUP_CODE_SALT_ROUNDS);
};

export const verifyBackupCode = async (code: string, hashedCode: string): Promise<boolean> => {
  return bcrypt.compare(code, hashedCode);
};

// In 2FA route:
const hashedBackupCodes = await Promise.all(
  backupCodes.map(code => hashBackupCode(code))
);
await query(
  `INSERT INTO user_2fa (user_id, totp_secret, backup_codes)
   VALUES ($1, $2, $3)`,
  [req.user.id, secret, hashedBackupCodes]
);
```

---

## Part 3: High-Priority Security Issues 🟠

### Issue #4: 2FA Disable Endpoint Skips Password Verification
**Severity:** 🟠 HIGH  
**File:** `server/src/routes/2fa.ts` (lines 194-240)  
**Impact:** Users can disable 2FA without proving identity

**Problem:**
```typescript
router.post('/disable', authMiddleware, asyncHandler(async (req, res) => {
  const { password } = req.body;
  
  if (!password) {
    return res.status(400).json({ error: 'Password required' });
  }
  
  // TODO: Implement password verification
  // const passwordValid = await comparePassword(...);
  // if (!passwordValid) return res.status(401).json(...);
  
  // Disables 2FA without verification!
  await query(`UPDATE user_2fa SET totp_enabled = false ...`);
}));
```

**Attack:**
If attacker gains access to authenticated session (but not password), they can disable 2FA.

**Fix:**
```typescript
import { comparePassword } from '@/utils/password';

router.post('/disable', authMiddleware, asyncHandler(async (req, res) => {
  const { password } = req.body;
  
  if (!password) {
    return res.status(400).json({ error: 'Password required to disable 2FA' });
  }
  
  const userResult = await query(
    'SELECT password_hash FROM users WHERE id = $1',
    [req.user.id]
  );
  
  if (userResult.rows.length === 0) {
    return res.status(404).json({ error: 'User not found' });
  }
  
  // Verify password
  const passwordValid = await comparePassword(
    password, 
    userResult.rows[0].password_hash
  );
  
  if (!passwordValid) {
    const { ipAddress, userAgent } = getClientInfo(req);
    await logAuditEvent(
      req.user.id,
      AuditAction.TWO_FA_DISABLE_FAILED,
      AuditResource.ACCOUNT,
      req.user.id,
      AuditStatus.FAILURE,
      ipAddress,
      userAgent
    );
    return res.status(401).json({ error: 'Invalid password' });
  }
  
  // Now safe to disable 2FA
  await query(`UPDATE user_2fa SET totp_enabled = false ...`);
}));
```

---

### Issue #5: No Refresh Token Rotation
**Severity:** 🟠 HIGH  
**File:** `server/src/routes/auth.ts` (refresh endpoint)  
**Impact:** Compromised refresh tokens remain valid indefinitely

**Problem:**
When issuing a new refresh token via `/auth/refresh`, the old token remains valid:

```
Timeline:
1. User logs in → gets refresh token with jti="ABC-123" (7-day expiry)
2. User calls /auth/refresh → gets new token with jti="DEF-456" (7-day expiry)
3. Both tokens are now valid (both have 7 days left)
4. If "ABC-123" is compromised, attacker can keep using it to refresh
5. No automatic revocation of old token
```

**Recommended Implementation:**
Store only the latest refresh token jti per user, or explicitly revoke the old one:

```typescript
// Option 1: Revoke old refresh on new refresh
const oldJti = decoded.jti;
if (oldJti) {
  await revokeRefreshToken(req.user.id, oldJti);
}
const newRefreshToken = generateRefreshToken(userId, email);
setAuthCookies(res, newAccessToken, newRefreshToken);

// Option 2: Store only latest jti per user
// Modify database: ALTER TABLE user_2fa ADD COLUMN active_refresh_jti UUID;
// On refresh: UPDATE ... SET active_refresh_jti = new_jti;
// In isTokenRevoked: Check if jti !== active_refresh_jti;
```

---

### Issue #6: Email Service Not Production-Ready
**Severity:** 🟠 HIGH  
**File:** `server/src/utils/email.ts`  
**Impact:** Verification emails are mock/development only

**Problem:**
```typescript
export const sendVerificationEmail = async (
  email: string,
  name: string,
  token: string
): Promise<boolean> => {
  // TODO: Implement actual email service (SendGrid, SES, etc.)
  console.log(`[DEV] Verification email would be sent to: ${email}`);
  return true; // Always succeeds, but no email actually sent
};
```

**Fix:**
Implement production email service (e.g., SendGrid):

```typescript
import sgMail from '@sendgrid/mail';

sgMail.setApiKey(process.env.SENDGRID_API_KEY!);

export const sendVerificationEmail = async (
  email: string,
  name: string,
  token: string
): Promise<boolean> => {
  try {
    const verificationLink = `${process.env.FRONTEND_URL}/auth/verify?token=${token}&email=${email}`;
    
    await sgMail.send({
      to: email,
      from: process.env.SENDER_EMAIL!,
      subject: 'Verify Your CryptoVault Account',
      html: generateVerificationEmailHTML(name, verificationLink),
    });
    
    return true;
  } catch (error) {
    console.error('Failed to send verification email:', error);
    return false;
  }
};
```

---

## Part 4: Medium-Priority Improvements 🟡

### Issue #7: Missing Tests for Token Flows
**Severity:** 🟡 MEDIUM  
**Impact:** Critical auth logic has no automated validation

Add tests for:
- Token type enforcement (access vs refresh)
- Refresh token revocation
- Concurrent refresh attempts
- Expired token handling

### Issue #8: CSP Nonce Generation
**Severity:** 🟡 MEDIUM  
**File:** `server/src/middleware/security.ts`  
**Status:** Currently implemented correctly

✅ Per-request nonce is generated and used in CSP header. Ensure:
- All inline scripts use the nonce
- No hardcoded `unsafe-inline`

### Issue #9: Audit Log Retention
**Severity:** 🟡 MEDIUM  
**File:** `server/src/routes/auditLogs.ts`  
**Concern:** Audit logs accumulate indefinitely

Recommendation: Implement automatic cleanup:
```typescript
// Monthly cleanup job
await query(
  `DELETE FROM audit_logs 
   WHERE created_at < NOW() - INTERVAL '90 days'`
);
```

### Issue #10: Rate Limiting on Sensitive Routes
**Severity:** 🟡 MEDIUM  
**Status:** Partially implemented

Current limits:
- Global: 100 req/15min per IP
- Auth: 5 req/15min per IP ✅
- 2FA strict: 20 req/15min per IP ✅

Suggestions:
- Add per-user rate limiting (not just per IP)
- Log rate limit violations for security monitoring

### Issue #11: Transaction Isolation
**Severity:** 🟡 MEDIUM  
**File:** `server/src/routes/orders.ts`  
**Status:** Correctly implemented with FOR UPDATE locks

✅ Order creation uses:
```typescript
BEGIN TRANSACTION;
SELECT * FROM portfolios WHERE user_id = $1 FOR UPDATE;
-- Update logic
COMMIT;
```

---

## Part 5: Frontend-Backend Integration

### API Client Structure
**File:** `src/lib/api.ts`

**Good:**
- Automatic token refresh on 401
- Concurrent refresh prevention (isRefreshing flag)
- Credentials included (`fetch(..., { credentials: 'include' }))`)
- Structured error handling

**Issues:**
- Duplicate `auth` key (covered above as Critical Issue #1)
- Refresh failure handling silently logs to console (should notify UI)

### Authentication Context
**File:** `src/contexts/AuthContext.tsx`

**Dependencies:**
- Calls `api.auth.getProfile()` on mount
- Calls `api.auth.login()` and `api.auth.signup()`
- Calls `api.auth.logout()`

**Blocked by:** Critical Issue #1 (duplicate api.auth key)

---

## Part 6: Production Deployment Checklist

### Environment Variables Required
```bash
# JWT & Security
JWT_SECRET=<generate 32+ char random>
NODE_ENV=production

# Database
DB_HOST=<postgres-host>
DB_PORT=5432
DB_NAME=cryptovault
DB_USER=<non-root-user>
DB_PASSWORD=<strong-password>

# Email Service
SENDGRID_API_KEY=<your-sendgrid-key>
SENDER_EMAIL=noreply@cryptovault.com
FRONTEND_URL=https://yourdomain.com

# CORS
CORS_ORIGIN=https://yourdomain.com

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100
```

### Pre-Deployment Validation
- [ ] Fix Critical Issue #1 (duplicate api.auth)
- [ ] Fix Critical Issue #2 (token type enforcement)
- [ ] Fix Critical Issue #3 (backup code hashing)
- [ ] Fix High Issue #4 (password verification in 2FA disable)
- [ ] Implement refresh token rotation (High Issue #5)
- [ ] Setup email service (High Issue #6)
- [ ] Remove verification token from signup response (security)
- [ ] Enable HTTPS (secure: true in cookies)
- [ ] Configure CORS_ORIGIN to production domain
- [ ] Test all auth flows (signup, login, refresh, logout, 2FA)
- [ ] Load test rate limiters
- [ ] Setup database backups
- [ ] Setup audit log monitoring

---

## Part 7: Summary of All Issues

| # | Issue | Severity | File | Fix Complexity | Must Do |
|---|-------|----------|------|-----------------|---------|
| 1 | Duplicate api.auth key | 🔴 CRITICAL | src/lib/api.ts | 5 min | YES |
| 2 | No token type enforcement | 🔴 CRITICAL | server/src/middleware/auth.ts | 10 min | YES |
| 3 | Plaintext backup codes | 🔴 CRITICAL | server/src/utils/2fa.ts | 30 min | YES |
| 4 | 2FA disable no password check | 🟠 HIGH | server/src/routes/2fa.ts | 10 min | YES |
| 5 | No refresh token rotation | 🟠 HIGH | server/src/routes/auth.ts | 20 min | YES |
| 6 | Mock email service | 🟠 HIGH | server/src/utils/email.ts | 60 min | YES |
| 7 | No auth tests | 🟡 MEDIUM | - | 120 min | NO |
| 8 | Audit log retention | 🟡 MEDIUM | server/src/routes/auditLogs.ts | 15 min | NO |
| 9 | Per-user rate limiting | 🟡 MEDIUM | server/src/middleware/security.ts | 30 min | NO |
| 10 | Verify token response | 🟡 MEDIUM | server/src/routes/auth.ts | 5 min | YES |
| 11 | CSP validation | 🟢 LOW | - | 0 min | DONE |

---

## Recommendations for Next Steps

**Phase 1: Critical Fixes (1-2 hours)**
1. Fix duplicate api.auth key
2. Implement token type enforcement
3. Hash backup codes with bcrypt
4. Add password verification to 2FA disable

**Phase 2: High-Priority (1-2 hours)**
5. Implement refresh token rotation
6. Setup email service integration
7. Remove verification token from signup response

**Phase 3: Testing & Validation (2-3 hours)**
- Integration tests for auth flows
- Penetration testing of token handling
- Load testing of rate limiters

**Phase 4: Monitoring & Operations (ongoing)**
- Setup audit log monitoring and alerts
- Database backup automation
- Token revocation monitoring dashboard

---

## Security Contact & Questions

For questions or concerns, refer to:
- `server/src/middleware/auth.ts` - Token generation and verification
- `server/src/routes/auth.ts` - Authentication endpoints
- `src/lib/api.ts` - Frontend API client

**Estimated Total Fix Time:** 2-3 hours for all critical and high-priority issues
