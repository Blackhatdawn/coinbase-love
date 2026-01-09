/**
 * Two-Factor Authentication (TOTP) Service
 * Handles TOTP secret generation, QR code creation, and token verification
 */

import speakeasy from 'speakeasy';
import QRCode from 'qrcode';
import { randomBytes } from 'crypto';

/**
 * Configuration for TOTP
 */
const TOTP_CONFIG = {
  window: 2, // Allow +/- 1 time window (30s each way) for code validity
  length: 32, // Secret key length in bytes
  encoding: 'base32' as const,
};

/**
 * Generate a new TOTP secret and QR code
 * Used in the 2FA setup flow
 */
export const generateTOTPSecret = async (email: string) => {
  const secret = speakeasy.generateSecret({
    name: `CryptoVault (${email})`,
    issuer: 'CryptoVault',
    length: TOTP_CONFIG.length,
  });

  if (!secret.base32) {
    throw new Error('Failed to generate TOTP secret');
  }

  // Generate QR code as data URL
  const qrCodeUrl = await QRCode.toDataURL(secret.otpauth_url!);

  return {
    secret: secret.base32,
    qrCode: qrCodeUrl,
    manualEntryKey: secret.base32, // For manual entry if QR fails
  };
};

/**
 * Verify a TOTP token
 * Returns true if the token is valid (within the time window)
 */
export const verifyTOTPToken = (secret: string, token: string): boolean => {
  try {
    // Remove any whitespace from token
    const cleanToken = token.replace(/\s/g, '');

    // Token must be 6 digits
    if (!/^\d{6}$/.test(cleanToken)) {
      return false;
    }

    const verified = speakeasy.totp.verify({
      secret,
      encoding: TOTP_CONFIG.encoding,
      token: cleanToken,
      window: TOTP_CONFIG.window,
    });

    return verified;
  } catch (error) {
    console.error('Error verifying TOTP token:', error);
    return false;
  }
};

/**
 * Generate backup codes for account recovery
 * Each code is single-use and can be used if authenticator is lost
 */
export const generateBackupCodes = (count: number = 10): string[] => {
  const codes: string[] = [];

  for (let i = 0; i < count; i++) {
    // Generate 4-byte random string, convert to hex, uppercase
    const code = randomBytes(4).toString('hex').toUpperCase().slice(0, 8);
    codes.push(code);
  }

  return codes;
};

/**
 * Hash a backup code for safe storage
 * Use bcryptjs in actual implementation
 */
export const hashBackupCode = (code: string): string => {
  // In production, use bcryptjs.hash()
  // For now, return as-is (should be encrypted in database)
  return code;
};

/**
 * Verify a backup code
 */
export const verifyBackupCode = (code: string, hashedCode: string): boolean => {
  // In production, use bcryptjs.compare()
  // For now, simple comparison
  return code === hashedCode;
};

/**
 * Format backup codes for display/download
 * Groups into 2-4-2 format for readability
 */
export const formatBackupCodes = (codes: string[]): string => {
  return codes
    .map((code) => {
      // Format: XXXX-XXXX
      return `${code.slice(0, 4)}-${code.slice(4, 8)}`;
    })
    .join('\n');
};

/**
 * Get TOTP URI for manual entry
 * Used if QR code scanning fails
 */
export const getTOTPUri = (secret: string, email: string): string => {
  const uri = speakeasy.otpauthURL({
    secret,
    label: `CryptoVault (${email})`,
    issuer: 'CryptoVault',
    encoding: TOTP_CONFIG.encoding,
  });

  return uri;
};

/**
 * Validate backup code format
 */
export const isValidBackupCodeFormat = (code: string): boolean => {
  // Accept both formatted (XXXX-XXXX) and unformatted (XXXXXXXX)
  const unformatted = code.replace('-', '').toUpperCase();
  return /^[A-F0-9]{8}$/.test(unformatted);
};

/**
 * Normalize backup code for comparison
 */
export const normalizeBackupCode = (code: string): string => {
  return code.replace('-', '').replace(/\s/g, '').toUpperCase();
};
