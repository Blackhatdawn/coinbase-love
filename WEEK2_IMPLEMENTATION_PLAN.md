# Week 2 High-Priority Hardening - Implementation Plan

## 🎯 Objective

Implement email verification enhancements, Two-Factor Authentication (TOTP), and comprehensive audit logging system.

**Duration:** 1 week (35 engineer hours)  
**Risk Level:** Medium (new features, no breaking changes)

---

## 📋 Features to Implement

### 1. Email Verification System (Enhanced) ⭐
**Status:** Partially complete, needs enhancement

**Enhancements Needed:**
- [ ] Resend verification email functionality
- [ ] Email verification success page
- [ ] Better error messages
- [ ] Token expiration UI feedback

**Files to Create/Modify:**
- `server/src/routes/auth.ts` - Add resend endpoint
- `src/pages/Auth.tsx` - Improve verification UX
- `server/src/utils/email.ts` - Email template improvements

**Time Estimate:** 8 hours

---

### 2. Two-Factor Authentication (TOTP) ⭐⭐⭐
**Status:** Not started

**Features:**
- [ ] Setup/enable TOTP in user account settings
- [ ] QR code generation (via speakeasy)
- [ ] Backup codes generation
- [ ] 6-digit TOTP code verification
- [ ] Disable 2FA functionality
- [ ] Recovery codes management

**User Flow:**
1. User navigates to Settings > Security
2. Clicks "Enable Two-Factor Authentication"
3. Gets QR code to scan with Authenticator app
4. Verifies with 6-digit code
5. Gets 10 backup codes for account recovery
6. 2FA enabled

**Files to Create:**
- `server/src/routes/2fa.ts` - 2FA endpoints
- `src/pages/Settings.tsx` - Settings page
- `src/components/TwoFactorSetup.tsx` - 2FA setup component
- Database migration: `2fa_secrets` table

**Dependencies:**
- `speakeasy` - TOTP generation
- `qrcode` - QR code generation

**Time Estimate:** 12 hours

---

### 3. Audit Logging System ⭐⭐
**Status:** Not started

**Features:**
- [ ] Track all sensitive operations
- [ ] Log authentication events
- [ ] Log data modifications (orders, portfolio)
- [ ] Log admin actions
- [ ] Searchable audit log viewer
- [ ] Audit log export (CSV)

**Audit Events to Track:**
- User login/logout
- Email verification
- Password change
- 2FA enable/disable
- Order creation/cancellation
- Portfolio modifications
- Transaction creation
- User profile updates

**Files to Create:**
- `server/src/utils/auditLog.ts` - Audit logging utility
- `server/src/routes/auditLog.ts` - Audit log endpoints
- `src/pages/AuditLog.tsx` - Audit log viewer page
- Database: `audit_logs` table

**Time Estimate:** 15 hours

---

## 🔧 Technical Implementation Details

### Part 1: Database Schema Changes

```sql
-- 2FA Secrets Table
CREATE TABLE IF NOT EXISTS user_2fa (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  totp_secret VARCHAR(32) NOT NULL,
  totp_enabled BOOLEAN DEFAULT FALSE,
  backup_codes TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action VARCHAR(100) NOT NULL,  -- 'login', 'logout', 'order_create'
  resource VARCHAR(100),  -- 'user', 'order', 'portfolio'
  resource_id UUID,
  status VARCHAR(20) DEFAULT 'success',  -- 'success', 'failure'
  ip_address INET,
  user_agent TEXT,
  details JSONB DEFAULT '{}'::JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes
CREATE INDEX idx_user_2fa_user_id ON user_2fa(user_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

### Part 2: Backend Implementation

**2FA Service (`server/src/utils/2fa.ts`):**
```typescript
import speakeasy from 'speakeasy';
import QRCode from 'qrcode';

export const generateSecret = () => {
  return speakeasy.generateSecret({
    name: 'CryptoVault',
    length: 32
  });
};

export const verifyToken = (secret: string, token: string): boolean => {
  return speakeasy.totp.verify({
    secret,
    encoding: 'base32',
    token,
    window: 2
  });
};

export const generateBackupCodes = (): string[] => {
  return Array.from({ length: 10 }).map(() => 
    Math.random().toString(36).substring(2, 10).toUpperCase()
  );
};

export const generateQRCode = async (
  secret: string,
  email: string
): Promise<string> => {
  const otpauthUrl = speakeasy.otpauthURL({
    secret,
    label: `CryptoVault (${email})`,
    issuer: 'CryptoVault',
    encoding: 'base32'
  });
  
  return QRCode.toDataURL(otpauthUrl);
};
```

**Audit Log Service (`server/src/utils/auditLog.ts`):**
```typescript
import { query } from '@/config/database';

export const logAuditEvent = async (
  userId: string | null,
  action: string,
  resource: string | null,
  resourceId: string | null,
  status: string,
  ipAddress: string,
  userAgent: string,
  details: Record<string, any> = {}
): Promise<void> => {
  try {
    await query(
      `INSERT INTO audit_logs 
       (user_id, action, resource, resource_id, status, ip_address, user_agent, details)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
      [userId, action, resource, resourceId, status, ipAddress, userAgent, JSON.stringify(details)]
    );
  } catch (error) {
    console.error('Failed to log audit event:', error);
  }
};
```

### Part 3: Frontend Implementation

**2FA Setup Component:**
- QR code display
- Manual entry option (for manual key entry)
- 6-digit code verification
- Backup codes display & download
- Copy-to-clipboard functionality

**Audit Log Viewer:**
- Searchable table of audit events
- Filter by action/date/resource
- Export to CSV
- Real-time updates (optional)

---

## 📅 Week-by-Week Breakdown

### Day 1: Database Schema & Backend Setup
- [ ] Create database migrations
- [ ] Implement 2FA service (speakeasy + QRCode)
- [ ] Implement audit logging utility
- [ ] Create middleware for automatic audit logging

### Day 2-3: 2FA Endpoints
- [ ] POST /api/auth/2fa/setup - Get QR code
- [ ] POST /api/auth/2fa/verify - Verify and enable
- [ ] GET /api/auth/2fa/status - Check if enabled
- [ ] POST /api/auth/2fa/disable - Disable 2FA
- [ ] GET /api/auth/2fa/backup-codes - Get new codes

### Day 3-4: Email & Audit Enhancements
- [ ] POST /api/auth/resend-verification - Resend email
- [ ] POST /api/audit-logs - Get logs (with pagination)
- [ ] GET /api/audit-logs/{id} - Get log detail
- [ ] POST /api/audit-logs/export - Export CSV

### Day 4-5: Frontend Implementation
- [ ] Create 2FA setup component
- [ ] Create 2FA disable component
- [ ] Create audit log viewer page
- [ ] Integrate with settings page

### Day 5: Testing & Deployment
- [ ] Unit tests for 2FA service
- [ ] Integration tests
- [ ] Staging deployment
- [ ] Production canary rollout

---

## 🔐 Security Considerations

### 2FA Security
- TOTP codes valid for 30 seconds (with 1-window buffer)
- Each code can only be used once
- Backup codes single-use (auto-delete after use)
- 2FA required for sensitive operations (optional enforcement)

### Audit Logging
- Cannot be disabled by users
- Immutable logs (no deletion)
- IP addresses logged (for forensics)
- Sensitive data sanitized from details

### Database Protection
- Encrypt TOTP secrets at rest (optional)
- Rate limit 2FA attempts (5 attempts / 5 min)
- Backup codes hashed before storage

---

## 📊 Expected Outcomes

After Week 2 deployment:

✅ Users can enable optional 2FA  
✅ Email verification working smoothly  
✅ All sensitive operations logged  
✅ Audit logs searchable and exportable  
✅ Account recovery via backup codes  
✅ Security audit trail complete  

**Expected Security Improvement:**
- Before: 9/10
- After: 9.2/10 (incremental improvements)
- Account takeover risk: -50%
- Audit trail: 100% coverage

---

## 📋 Implementation Checklist

### Backend
- [ ] Install dependencies: speakeasy, qrcode
- [ ] Create database migrations
- [ ] Implement 2FA service
- [ ] Implement audit logging
- [ ] Create 2FA endpoints
- [ ] Create audit log endpoints
- [ ] Add email verification enhancements
- [ ] Add rate limiting to 2FA endpoints
- [ ] Add backup code management

### Frontend
- [ ] Create 2FA setup component
- [ ] Create audit log viewer
- [ ] Integrate into settings page
- [ ] Add 2FA status display
- [ ] Add backup codes download
- [ ] Add 2FA disable functionality

### Testing
- [ ] Unit tests for 2FA (verify token, generate codes)
- [ ] Unit tests for audit logging
- [ ] Integration tests for endpoints
- [ ] Manual QA testing
- [ ] Security testing (backup code limits, etc)

### Deployment
- [ ] Code review & approval
- [ ] Staging deployment
- [ ] Smoke tests
- [ ] Production canary (10% → 50% → 100%)
- [ ] 24-hour monitoring

---

## 💾 Database Migrations

Run in order:

```sql
-- Migration 1: Create 2FA table
CREATE TABLE IF NOT EXISTS user_2fa (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  totp_secret VARCHAR(32),
  totp_enabled BOOLEAN DEFAULT FALSE,
  backup_codes TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_user_2fa_user_id ON user_2fa(user_id);

-- Migration 2: Create audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  action VARCHAR(100) NOT NULL,
  resource VARCHAR(100),
  resource_id UUID,
  status VARCHAR(20) DEFAULT 'success',
  ip_address INET,
  user_agent TEXT,
  details JSONB DEFAULT '{}'::JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

---

## 🎯 Success Criteria

Week 2 is complete when:

- ✅ 2FA system working (setup, verify, disable)
- ✅ Users can generate & store backup codes
- ✅ Audit logs capturing all sensitive operations
- ✅ Email verification UX improved
- ✅ Rate limiting on 2FA endpoints (5 req/5 min)
- ✅ No performance regression
- ✅ Error rate remains < 0.5%
- ✅ User feedback positive

---

## 📞 Key Files Created/Modified

### Files to Create
- `server/src/utils/2fa.ts` - TOTP service
- `server/src/routes/2fa.ts` - 2FA endpoints
- `server/src/routes/auditLog.ts` - Audit log endpoints
- `server/src/utils/auditLog.ts` - Audit logging utility
- `server/src/middleware/auditLogging.ts` - Auto-logging middleware
- `src/pages/Settings.tsx` - Settings page
- `src/components/TwoFactorSetup.tsx` - 2FA setup
- `src/components/AuditLogViewer.tsx` - Audit log viewer

### Files to Modify
- `server/src/server.ts` - Add 2FA routes + audit middleware
- `server/src/config/database.ts` - Add migrations
- `server/src/routes/auth.ts` - Add resend verification
- `server/package.json` - Add speakeasy + qrcode
- `src/pages/Auth.tsx` - Improve verification UX

---

## 🚀 Timeline

- **Day 1:** Database + backend setup (8 hours)
- **Day 2-3:** 2FA endpoints (12 hours)
- **Day 4:** Email + audit endpoints (8 hours)
- **Day 5:** Frontend components (8 hours)
- **Day 6:** Testing + fixes (5 hours)
- **Day 7:** Staging & production deployment (5 hours)

**Total:** 46 hours (35 planned + buffer for issues)

---

**Status:** Ready to Start Implementation  
**Next Step:** Install dependencies and create database migrations
