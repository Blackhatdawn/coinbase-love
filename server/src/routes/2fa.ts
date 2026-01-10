import { Router, Response } from 'express';
import { authMiddleware, AuthRequest } from '@/middleware/auth';
import { query } from '@/config/database';
import {
  generateTOTPSecret,
  verifyTOTPToken,
  generateBackupCodes,
  normalizeBackupCode,
  hashBackupCode,
  verifyBackupCode,
} from '@/utils/2fa';
import { asyncHandler, strictLimiter } from '@/middleware/security';
import { logAuditEvent, AuditAction, AuditResource, AuditStatus, getClientInfo } from '@/utils/auditLog';

const router = Router();

// ============================================================================
// SETUP 2FA - Get QR code and secret for setup
// ============================================================================
router.post(
  '/setup',
  authMiddleware,
  strictLimiter,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    // Check if 2FA already enabled
    const existingResult = await query(
      'SELECT id FROM user_2fa WHERE user_id = $1 AND totp_enabled = true',
      [req.user.id]
    );

    if (existingResult.rows.length > 0) {
      return res.status(400).json({ error: '2FA is already enabled for this account' });
    }

    // Generate secret and QR code
    const { secret, qrCode, manualEntryKey } = await generateTOTPSecret(req.user.email);

    // Generate backup codes
    const backupCodes = generateBackupCodes(10);

    // Store secret temporarily (not enabled yet)
    await query(
      `INSERT INTO user_2fa (user_id, totp_secret, backup_codes)
       VALUES ($1, $2, $3)
       ON CONFLICT (user_id) DO UPDATE SET
       totp_secret = $2,
       backup_codes = $3,
       updated_at = CURRENT_TIMESTAMP`,
      [req.user.id, secret, backupCodes]
    );

    // Log audit event
    const { ipAddress, userAgent } = getClientInfo(req);
    await logAuditEvent(
      req.user.id,
      AuditAction.TWO_FA_ENABLED,
      AuditResource.ACCOUNT,
      req.user.id,
      AuditStatus.PENDING,
      ipAddress,
      userAgent,
      { step: 'setup_initiated' }
    );

    res.json({
      qrCode,
      secret: manualEntryKey,
      backupCodes,
      message: 'Scan the QR code with your authenticator app. You will need to verify with a 6-digit code.',
    });
  })
);

// ============================================================================
// VERIFY & ENABLE 2FA - Verify TOTP code and enable 2FA
// ============================================================================
router.post(
  '/verify',
  authMiddleware,
  strictLimiter,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { code } = req.body;

    if (!code) {
      return res.status(400).json({ error: 'Verification code required' });
    }

    // Get the pending 2FA secret
    const result = await query(
      'SELECT totp_secret, backup_codes FROM user_2fa WHERE user_id = $1',
      [req.user.id]
    );

    if (result.rows.length === 0) {
      return res.status(400).json({ error: 'No 2FA setup in progress. Start setup again.' });
    }

    const { totp_secret, backup_codes } = result.rows[0];

    if (!totp_secret) {
      return res.status(400).json({ error: 'No 2FA secret found. Start setup again.' });
    }

    // Verify the TOTP code
    const isValid = verifyTOTPToken(totp_secret, code);

    const { ipAddress, userAgent } = getClientInfo(req);

    if (!isValid) {
      await logAuditEvent(
        req.user.id,
        AuditAction.TWO_FA_VERIFICATION_FAILED,
        AuditResource.ACCOUNT,
        req.user.id,
        AuditStatus.FAILURE,
        ipAddress,
        userAgent
      );

      return res
        .status(401)
        .json({ error: 'Invalid verification code. Please try again.' });
    }

    // SECURITY FIX: Hash backup codes before storing
    const hashedBackupCodes = await Promise.all(
      backup_codes.map((code: string) => hashBackupCode(code))
    );

    // Enable 2FA with hashed backup codes
    await query(
      `UPDATE user_2fa
       SET totp_enabled = true, backup_codes = $2, updated_at = CURRENT_TIMESTAMP
       WHERE user_id = $1`,
      [req.user.id, hashedBackupCodes]
    );

    await logAuditEvent(
      req.user.id,
      AuditAction.TWO_FA_ENABLED,
      AuditResource.ACCOUNT,
      req.user.id,
      AuditStatus.SUCCESS,
      ipAddress,
      userAgent,
      { backup_codes_generated: backup_codes?.length || 0 }
    );

    res.json({
      message: '2FA successfully enabled!',
      backupCodes,
      warning:
        'Save your backup codes in a safe place. You can use them to recover your account if you lose your authenticator.',
    });
  })
);

// ============================================================================
// GET 2FA STATUS - Check if 2FA is enabled for user
// ============================================================================
router.get(
  '/status',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const result = await query(
      'SELECT totp_enabled FROM user_2fa WHERE user_id = $1',
      [req.user.id]
    );

    const enabled = result.rows.length > 0 && result.rows[0].totp_enabled;

    res.json({ enabled });
  })
);

// ============================================================================
// VERIFY TOTP CODE - For login flow (not here, in auth routes)
// This is a helper that auth routes would call
// ============================================================================
export const verifyUserTOTPCode = async (
  userId: string,
  code: string
): Promise<boolean> => {
  const result = await query(
    'SELECT totp_secret FROM user_2fa WHERE user_id = $1 AND totp_enabled = true',
    [userId]
  );

  if (result.rows.length === 0) {
    return false;
  }

  const { totp_secret } = result.rows[0];
  return verifyTOTPToken(totp_secret, code);
};

// ============================================================================
// DISABLE 2FA - Disable two-factor authentication
// ============================================================================
router.post(
  '/disable',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { password } = req.body;

    if (!password) {
      return res.status(400).json({ error: 'Password required to disable 2FA' });
    }

    // Verify password before allowing disable
    const userResult = await query(
      'SELECT password_hash FROM users WHERE id = $1',
      [req.user.id]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    // TODO: Implement password verification
    // const passwordValid = await comparePassword(password, userResult.rows[0].password_hash);
    // if (!passwordValid) {
    //   return res.status(401).json({ error: 'Invalid password' });
    // }

    // Disable 2FA
    await query(
      `UPDATE user_2fa
       SET totp_enabled = false, totp_secret = NULL, backup_codes = ARRAY[]::TEXT[]
       WHERE user_id = $1`,
      [req.user.id]
    );

    const { ipAddress, userAgent } = getClientInfo(req);
    await logAuditEvent(
      req.user.id,
      AuditAction.TWO_FA_DISABLED,
      AuditResource.ACCOUNT,
      req.user.id,
      AuditStatus.SUCCESS,
      ipAddress,
      userAgent
    );

    res.json({ message: '2FA has been disabled.' });
  })
);

// ============================================================================
// GET BACKUP CODES - Retrieve or regenerate backup codes
// ============================================================================
router.post(
  '/backup-codes',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    if (!req.user?.id) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    // Generate new backup codes
    const newBackupCodes = generateBackupCodes(10);

    // Update backup codes
    await query(
      `UPDATE user_2fa
       SET backup_codes = $2, updated_at = CURRENT_TIMESTAMP
       WHERE user_id = $1`,
      [req.user.id, newBackupCodes]
    );

    const { ipAddress, userAgent } = getClientInfo(req);
    await logAuditEvent(
      req.user.id,
      AuditAction.BACKUP_CODES_GENERATED,
      AuditResource.ACCOUNT,
      req.user.id,
      AuditStatus.SUCCESS,
      ipAddress,
      userAgent,
      { codes_generated: newBackupCodes.length }
    );

    res.json({
      backupCodes: newBackupCodes,
      message: 'New backup codes generated. Save them in a safe place.',
    });
  })
);

// ============================================================================
// USE BACKUP CODE - For 2FA fallback (used in login flow)
// ============================================================================
export const verifyBackupCodeAndRemove = async (
  userId: string,
  code: string
): Promise<boolean> => {
  const result = await query(
    'SELECT backup_codes FROM user_2fa WHERE user_id = $1',
    [userId]
  );

  if (result.rows.length === 0) {
    return false;
  }

  const { backup_codes } = result.rows[0];
  const normalizedCode = normalizeBackupCode(code);

  // Check if code exists in array
  const codeIndex = backup_codes?.findIndex(
    (c: string) => normalizeBackupCode(c) === normalizedCode
  );

  if (codeIndex === undefined || codeIndex < 0) {
    return false;
  }

  // Remove used backup code
  const updatedCodes = backup_codes.filter((_: string, idx: number) => idx !== codeIndex);

  await query(
    'UPDATE user_2fa SET backup_codes = $2 WHERE user_id = $1',
    [userId, updatedCodes]
  );

  return true;
};

export default router;
