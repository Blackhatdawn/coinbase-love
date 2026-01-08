import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

export interface AuthRequest extends Request {
  user?: {
    id: string;
    email: string;
  };
}

/**
 * Token expiry times
 * Access token: 15 minutes (short-lived)
 * Refresh token: 7 days (long-lived)
 */
const ACCESS_TOKEN_EXPIRY = '15m';
const REFRESH_TOKEN_EXPIRY = '7d';

export const verifyToken = (token: string, isRefresh: boolean = false) => {
  try {
    const secret = process.env.JWT_SECRET;
    if (!secret) {
      throw new Error('JWT_SECRET environment variable is not configured');
    }
    const decoded = jwt.verify(token, secret);
    return decoded as { id: string; email: string; type: string };
  } catch (error) {
    return null;
  }
};

/**
 * Generate access token (short-lived, for API requests)
 */
export const generateAccessToken = (userId: string, email: string) => {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT_SECRET environment variable is not configured');
  }
  return jwt.sign(
    { id: userId, email, type: 'access' },
    secret,
    { expiresIn: ACCESS_TOKEN_EXPIRY }
  );
};

/**
 * Generate refresh token (long-lived, used to get new access tokens)
 */
export const generateRefreshToken = (userId: string, email: string) => {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT_SECRET environment variable is not configured');
  }
  return jwt.sign(
    { id: userId, email, type: 'refresh' },
    secret,
    { expiresIn: REFRESH_TOKEN_EXPIRY }
  );
};

/**
 * Legacy function for backwards compatibility during migration
 * Use generateAccessToken for new code
 */
export const generateToken = (userId: string, email: string) => {
  return generateAccessToken(userId, email);
};

/**
 * Middleware to authenticate requests using HttpOnly cookies
 * Falls back to Authorization header for backwards compatibility during migration
 */
export const authMiddleware = (req: AuthRequest, res: Response, next: NextFunction) => {
  // Try to get token from HttpOnly cookie first (preferred)
  let token = req.cookies?.accessToken;

  // Fall back to Authorization header for backwards compatibility
  if (!token) {
    const authHeader = req.headers.authorization;
    if (authHeader) {
      token = authHeader.replace('Bearer ', '');
    }
  }

  if (!token) {
    return res.status(401).json({ error: 'No authorization token' });
  }

  const decoded = verifyToken(token, false);

  if (!decoded) {
    return res.status(401).json({ error: 'Invalid or expired token' });
  }

  req.user = decoded;
  next();
};

/**
 * Set secure HttpOnly cookies with credentials
 * Access token: HttpOnly, Secure, SameSite=Strict
 * Refresh token: HttpOnly, Secure, SameSite=Strict, Longer expiry
 */
export const setAuthCookies = (res: Response, accessToken: string, refreshToken: string) => {
  const isProduction = process.env.NODE_ENV === 'production';

  res.cookie('accessToken', accessToken, {
    httpOnly: true,           // Prevents JavaScript access (XSS protection)
    secure: isProduction,     // HTTPS only in production
    sameSite: 'strict',       // Prevents CSRF attacks
    maxAge: 15 * 60 * 1000,   // 15 minutes
    path: '/',
  });

  res.cookie('refreshToken', refreshToken, {
    httpOnly: true,
    secure: isProduction,
    sameSite: 'strict',
    maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    path: '/',
  });
};

/**
 * Clear auth cookies on logout
 */
export const clearAuthCookies = (res: Response) => {
  res.clearCookie('accessToken', { path: '/' });
  res.clearCookie('refreshToken', { path: '/' });
};
