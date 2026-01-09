import { Router, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { query } from '@/config/database';
import {
  authMiddleware,
  generateAccessToken,
  generateRefreshToken,
  verifyToken,
  AuthRequest,
  setAuthCookies,
  clearAuthCookies,
  isTokenRevoked,
  revokeRefreshToken,
} from '@/middleware/auth';
import { logAuditEvent, AuditAction, AuditResource, AuditStatus, getClientInfo } from '@/utils/auditLog';
import { hashPassword, comparePassword } from '@/utils/password';
import { signUpSchema, signInSchema } from '@/utils/validation';
import { generateVerificationToken, getVerificationTokenExpiry, sendVerificationEmail } from '@/utils/email';
import {
  authLimiter,
  validateEmail,
  validatePassword,
  validateName,
  handleValidationErrors,
  asyncHandler,
} from '@/middleware/security';

const router = Router();

// ============================================================================
// SIGN UP ROUTE - with rate limiting and validation
// ============================================================================
router.post(
  '/signup',
  authLimiter,
  [
    validateEmail(),
    validatePassword(),
    validateName(),
  ],
  handleValidationErrors,
  asyncHandler(async (req, res) => {
    const { email, password, name } = req.body;

    // Double-check with Zod schema (defense in depth)
    try {
      signUpSchema.parse({ email, password, name });
    } catch (zodError: any) {
      return res.status(400).json({ error: zodError.errors[0].message });
    }

    // Check if user already exists
    const existingUser = await query('SELECT id FROM users WHERE email = $1', [email.toLowerCase()]);
    if (existingUser.rows.length > 0) {
      return res.status(409).json({ error: 'An account with this email already exists' });
    }

    // Hash password
    const passwordHash = await hashPassword(password);

    // Generate verification token
    const verificationToken = generateVerificationToken();
    const verificationExpiry = getVerificationTokenExpiry();

    // Create user
    const result = await query(
      'INSERT INTO users (email, name, password_hash, email_verification_token, email_verification_expires) VALUES ($1, $2, $3, $4, $5) RETURNING id, email, name, created_at',
      [email.toLowerCase(), name, passwordHash, verificationToken, verificationExpiry]
    );

    const user = result.rows[0];

    // Create portfolio for user
    await query(
      'INSERT INTO portfolios (user_id, total_balance) VALUES ($1, $2)',
      [user.id, 10000] // Default starting balance
    );

    // Send verification email
    const emailSent = await sendVerificationEmail(user.email, user.name, verificationToken);

    if (!emailSent) {
      console.warn(`Failed to send verification email to ${user.email}`);
    }

    // For development: return verification token in response
    // In production, only send via email
    const responseData: any = {
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        createdAt: user.created_at,
        emailVerified: false,
      },
    };

    if (process.env.NODE_ENV === 'development') {
      responseData.verificationToken = verificationToken;
      responseData.message = 'Check console for verification email link. In development, you can use the verificationToken to verify your email.';
    } else {
      responseData.message = 'Verification email sent. Please check your inbox to verify your email address.';
    }

    res.status(201).json(responseData);
  })
);

// ============================================================================
// SIGN IN ROUTE - with rate limiting and validation
// ============================================================================
router.post(
  '/login',
  authLimiter,
  [
    validateEmail(),
    body('password').isLength({ min: 1 }).withMessage('Password required'),
  ],
  handleValidationErrors,
  asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    // Double-check with Zod schema
    try {
      signInSchema.parse({ email, password });
    } catch (zodError: any) {
      return res.status(400).json({ error: zodError.errors[0].message });
    }

    // Find user by email
    const result = await query(
      'SELECT id, email, name, password_hash, email_verified, created_at FROM users WHERE email = $1',
      [email.toLowerCase()]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    const user = result.rows[0];

    // Check if email is verified
    if (!user.email_verified) {
      return res.status(403).json({
        error: 'Email not verified',
        code: 'EMAIL_NOT_VERIFIED',
        message: 'Please verify your email address before signing in. Check your inbox for a verification link.'
      });
    }

    // Compare password
    const isPasswordValid = await comparePassword(password, user.password_hash);

    const { ipAddress, userAgent } = getClientInfo(req);

    if (!isPasswordValid) {
      // Log failed login attempt
      await logAuditEvent(
        user.id,
        AuditAction.LOGIN_FAILED,
        AuditResource.AUTH,
        user.id,
        AuditStatus.FAILURE,
        ipAddress,
        userAgent,
        { reason: 'invalid_password' }
      );

      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Generate access and refresh tokens
    const accessToken = generateAccessToken(user.id, user.email);
    const refreshToken = generateRefreshToken(user.id, user.email);

    // Set HttpOnly cookies
    setAuthCookies(res, accessToken, refreshToken);

    // Log successful login
    await logAuditEvent(
      user.id,
      AuditAction.LOGIN,
      AuditResource.AUTH,
      user.id,
      AuditStatus.SUCCESS,
      ipAddress,
      userAgent
    );

    res.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        createdAt: user.created_at,
        emailVerified: user.email_verified,
      },
    });
  })
);

// ============================================================================
// GET CURRENT USER - Protected route
// ============================================================================
router.get(
  '/me',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    const result = await query(
      'SELECT id, email, name, created_at FROM users WHERE id = $1',
      [req.user?.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    const user = result.rows[0];
    res.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        createdAt: user.created_at,
      },
    });
  })
);

// ============================================================================
// LOGOUT ROUTE - Clear authentication cookies and revoke refresh token
// ============================================================================
router.post(
  '/logout',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    const { ipAddress, userAgent } = getClientInfo(req);

    // Revoke the refresh token for explicit logout
    const refreshToken = req.cookies?.refreshToken;
    if (refreshToken && req.user?.id) {
      try {
        const decoded = verifyToken(refreshToken, true);
        if (decoded && decoded.jti) {
          await revokeRefreshToken(req.user.id, decoded.jti);
        }
      } catch (error) {
        console.warn('Could not revoke token on logout:', error);
        // Continue with logout even if revocation fails
      }
    }

    // Clear HttpOnly cookies
    clearAuthCookies(res);

    // Log logout event
    if (req.user?.id) {
      await logAuditEvent(
        req.user.id,
        AuditAction.LOGOUT,
        AuditResource.AUTH,
        req.user.id,
        AuditStatus.SUCCESS,
        ipAddress,
        userAgent
      );
    }

    res.json({ message: 'Logged out successfully' });
  })
);

// ============================================================================
// VERIFY EMAIL ROUTE - Verify email using token
// ============================================================================
router.post(
  '/verify-email',
  asyncHandler(async (req, res) => {
    const { token, email } = req.body;

    if (!token || !email) {
      return res.status(400).json({ error: 'Verification token and email are required' });
    }

    // Find user by email and verification token
    const result = await query(
      'SELECT id, email, name, email_verified, email_verification_token, email_verification_expires FROM users WHERE email = $1 AND email_verification_token = $2',
      [email.toLowerCase(), token]
    );

    if (result.rows.length === 0) {
      return res.status(400).json({ error: 'Invalid verification token' });
    }

    const user = result.rows[0];
    const { ipAddress, userAgent } = getClientInfo(req);

    // Check if token is expired
    if (user.email_verification_expires < new Date()) {
      await logAuditEvent(
        user.id,
        AuditAction.EMAIL_VERIFICATION_FAILED,
        AuditResource.USER,
        user.id,
        AuditStatus.FAILURE,
        ipAddress,
        userAgent,
        { reason: 'token_expired' }
      );

      return res.status(400).json({ error: 'Verification token has expired. Please request a new one.' });
    }

    // Check if already verified
    if (user.email_verified) {
      return res.status(200).json({ message: 'Email already verified' });
    }

    // Mark email as verified
    await query(
      'UPDATE users SET email_verified = true, email_verification_token = NULL, email_verification_expires = NULL WHERE id = $1',
      [user.id]
    );

    // Log successful email verification
    await logAuditEvent(
      user.id,
      AuditAction.EMAIL_VERIFIED,
      AuditResource.USER,
      user.id,
      AuditStatus.SUCCESS,
      ipAddress,
      userAgent
    );

    res.json({ message: 'Email verified successfully. You can now sign in.' });
  })
);

// ============================================================================
// REFRESH TOKEN ROUTE - Get new access token using refresh token
// ============================================================================
router.post(
  '/refresh',
  asyncHandler(async (req: AuthRequest, res: Response) => {
    // Get refresh token from cookie
    const refreshToken = req.cookies?.refreshToken;

    if (!refreshToken) {
      return res.status(401).json({ error: 'No refresh token provided' });
    }

    // Verify refresh token
    const decoded = verifyToken(refreshToken, true);

    if (!decoded) {
      clearAuthCookies(res);
      return res.status(401).json({ error: 'Invalid or expired refresh token' });
    }

    // Check if token has been revoked (explicitly logged out)
    if (decoded.jti) {
      const revoked = await isTokenRevoked(decoded.jti);
      if (revoked) {
        clearAuthCookies(res);
        return res.status(401).json({ error: 'Refresh token has been revoked. Please log in again.' });
      }
    }

    // Verify user still exists
    const userResult = await query(
      'SELECT id, email, name FROM users WHERE id = $1',
      [decoded.id]
    );

    if (userResult.rows.length === 0) {
      clearAuthCookies(res);
      return res.status(401).json({ error: 'User not found' });
    }

    const user = userResult.rows[0];

    // Generate new access and refresh tokens
    const newAccessToken = generateAccessToken(user.id, user.email);
    const newRefreshToken = generateRefreshToken(user.id, user.email);

    // Set new tokens in cookies
    setAuthCookies(res, newAccessToken, newRefreshToken);

    res.json({
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
      },
    });
  })
);

export default router;
