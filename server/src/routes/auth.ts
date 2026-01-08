import { Router, Response } from 'express';
import { body, validationResult } from 'express-validator';
import { query } from '@/config/database';
import {
  authMiddleware,
  generateAccessToken,
  generateRefreshToken,
  AuthRequest,
  setAuthCookies,
  clearAuthCookies,
} from '@/middleware/auth';
import { hashPassword, comparePassword } from '@/utils/password';
import { signUpSchema, signInSchema } from '@/utils/validation';
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

    // Create user
    const result = await query(
      'INSERT INTO users (email, name, password_hash) VALUES ($1, $2, $3) RETURNING id, email, name, created_at',
      [email.toLowerCase(), name, passwordHash]
    );

    const user = result.rows[0];

    // Create portfolio for user
    await query(
      'INSERT INTO portfolios (user_id, total_balance) VALUES ($1, $2)',
      [user.id, 10000] // Default starting balance
    );

    // Generate access and refresh tokens
    const accessToken = generateAccessToken(user.id, user.email);
    const refreshToken = generateRefreshToken(user.id, user.email);

    // Set HttpOnly cookies
    setAuthCookies(res, accessToken, refreshToken);

    res.status(201).json({
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
      'SELECT id, email, name, password_hash, created_at FROM users WHERE email = $1',
      [email.toLowerCase()]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    const user = result.rows[0];

    // Compare password
    const isPasswordValid = await comparePassword(password, user.password_hash);
    if (!isPasswordValid) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Generate access and refresh tokens
    const accessToken = generateAccessToken(user.id, user.email);
    const refreshToken = generateRefreshToken(user.id, user.email);

    // Set HttpOnly cookies
    setAuthCookies(res, accessToken, refreshToken);

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
// LOGOUT ROUTE - Clear authentication cookies
// ============================================================================
router.post(
  '/logout',
  authMiddleware,
  (req: AuthRequest, res: Response) => {
    // Clear HttpOnly cookies
    clearAuthCookies(res);

    res.json({ message: 'Logged out successfully' });
  }
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
    const decoded = require('@/middleware/auth').verifyToken(refreshToken, true);

    if (!decoded) {
      clearAuthCookies(res);
      return res.status(401).json({ error: 'Invalid or expired refresh token' });
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
