import rateLimit from 'express-rate-limit';
import { body, validationResult, Result, ValidationError } from 'express-validator';
import { Request, Response, NextFunction } from 'express';
import { query as dbQuery } from '@/config/database';

/**
 * PRODUCTION SECURITY MIDDLEWARE
 * Implements rate limiting, input validation, and security headers
 */

// ============================================================================
// RATE LIMITING CONFIGURATIONS
// ============================================================================

/**
 * General API rate limiter
 * - 100 requests per 15 minutes per IP
 * - Used for all API routes
 */
export const generalLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100,
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true, // Return rate limit info in `RateLimit-*` headers
  skip: (req) => {
    // Skip rate limiting for health checks
    return req.path === '/health';
  },
});

/**
 * Authentication rate limiter
 * - 5 requests per 15 minutes per IP
 * - Prevents brute force attacks on login/signup
 */
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per 15 minutes
  message: 'Too many authentication attempts, please try again later.',
  skipSuccessfulRequests: false, // Count all requests, not just failures
  standardHeaders: true,
});

/**
 * Strict API rate limiter for sensitive endpoints
 * - 20 requests per 15 minutes per IP
 * - Used for portfolio, orders, and transactions endpoints
 */
export const strictLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 20,
  message: 'Too many requests, please try again later.',
  standardHeaders: true,
});

// ============================================================================
// INPUT VALIDATION & SANITIZATION
// ============================================================================

/**
 * Email validation and sanitization
 */
export const validateEmail = () => {
  return body('email')
    .trim()
    .toLowerCase()
    .isEmail()
    .withMessage('Please provide a valid email address')
    .normalizeEmail();
};

/**
 * Password validation (no sanitization to preserve intentional special chars)
 */
export const validatePassword = () => {
  return body('password')
    .isLength({ min: 8 })
    .withMessage('Password must be at least 8 characters long')
    .matches(/[A-Z]/)
    .withMessage('Password must contain at least one uppercase letter')
    .matches(/[a-z]/)
    .withMessage('Password must contain at least one lowercase letter')
    .matches(/[0-9]/)
    .withMessage('Password must contain at least one number');
};

/**
 * Name validation and sanitization
 */
export const validateName = () => {
  return body('name')
    .trim()
    .isLength({ min: 2, max: 100 })
    .withMessage('Name must be between 2 and 100 characters')
    .escape() // Escape HTML characters
    .withMessage('Name contains invalid characters');
};

/**
 * Trading pair validation
 */
export const validateTradingPair = () => {
  return body('trading_pair')
    .trim()
    .matches(/^[A-Z]{2,10}\/[A-Z]{2,10}$/)
    .withMessage('Invalid trading pair format (e.g., BTC/USD)');
};

/**
 * Generic amount validation (for orders, holdings, etc.)
 */
export const validateAmount = (field: string = 'amount') => {
  return body(field)
    .isFloat({ min: 0.00000001 })
    .withMessage(`${field} must be a positive number`)
    .toFloat();
};

/**
 * Generic price validation
 */
export const validatePrice = (field: string = 'price') => {
  return body(field)
    .isFloat({ min: 0.00000001 })
    .withMessage(`${field} must be a positive number`)
    .toFloat();
};

/**
 * Symbol validation (crypto symbols like BTC, ETH)
 */
export const validateSymbol = (field: string = 'symbol') => {
  return body(field)
    .trim()
    .matches(/^[A-Z]{2,10}$/)
    .withMessage(`${field} must be 2-10 uppercase letters`);
};

// ============================================================================
// VALIDATION ERROR HANDLER MIDDLEWARE
// ============================================================================

/**
 * Middleware to handle validation errors
 * Use this after running validation chains
 */
export const handleValidationErrors = (req: Request, res: Response, next: NextFunction) => {
  const errors: Result<ValidationError> = validationResult(req);
  
  if (!errors.isEmpty()) {
    return res.status(400).json({
      error: 'Validation failed',
      details: errors.array().map(err => ({
        field: err.type === 'field' ? err.path : 'unknown',
        message: err.msg,
      })),
    });
  }
  
  next();
};

// ============================================================================
// SECURITY HEADERS MIDDLEWARE
// ============================================================================

/**
 * Generate a random nonce for inline scripts
 */
const generateNonce = (): string => {
  return require('crypto').randomBytes(16).toString('hex');
};

/**
 * Custom security headers (used with helmet)
 * Implements strict Content Security Policy with nonce-based inline script protection
 */
export const securityHeaders = (req: Request, res: Response, next: NextFunction) => {
  // Generate a nonce for this request
  const nonce = generateNonce();

  // Store nonce on request object for use in templates
  (req as any).nonce = nonce;

  // Strict Content Security Policy (without unsafe-inline or unsafe-eval)
  // Using nonce for any necessary inline scripts
  const csp = [
    "default-src 'self'",                                    // Only allow same-origin by default
    `script-src 'self' 'nonce-${nonce}'`,                    // Allow self and inline scripts with nonce
    "style-src 'self' 'nonce-" + nonce + "'",               // Allow self and inline styles with nonce
    "img-src 'self' data: https:",                           // Allow self, data URIs, and HTTPS images
    "font-src 'self' data:",                                 // Allow self and data URIs for fonts
    "connect-src 'self' https:",                             // Allow API calls to self and HTTPS
    "frame-ancestors 'none'",                                // Prevent embedding in frames
    "base-uri 'self'",                                       // Restrict base URLs
    "form-action 'self'",                                    // Restrict form submissions
  ].join('; ');

  res.setHeader('Content-Security-Policy', csp);

  // Additional security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');       // Prevent MIME type sniffing
  res.setHeader('X-Frame-Options', 'DENY');                  // Prevent clickjacking
  res.setHeader('X-XSS-Protection', '1; mode=block');        // Enable XSS protection
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin'); // Control referrer info
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()'); // Restrict API access
  res.setHeader('X-Powered-By', 'CryptoVault');

  next();
};

// ============================================================================
// CORS CONFIGURATION UTILITY
// ============================================================================

/**
 * Get production-safe CORS configuration
 * Dynamically sets allowed origin based on environment
 */
export const getCorsOptions = () => {
  const nodeEnv = process.env.NODE_ENV || 'development';
  const corsOrigin = process.env.CORS_ORIGIN || 'http://localhost:8080';

  return {
    origin: (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
      // Allow requests with no origin (mobile apps, curl, postman, etc)
      if (!origin) {
        return callback(null, true);
      }

      // In development, allow any origin
      if (nodeEnv === 'development') {
        return callback(null, true);
      }

      // In production, only allow specified origins
      const allowedOrigins = [corsOrigin].filter(Boolean);

      if (allowedOrigins.includes(origin)) {
        return callback(null, true);
      }

      return callback(new Error('Not allowed by CORS'));
    },
    credentials: true, // Allow credentials (cookies) to be included in requests
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    exposedHeaders: ['Set-Cookie'], // Expose Set-Cookie header for credentials
    maxAge: 86400, // 24 hours
  };
};

// ============================================================================
// GLOBAL ERROR HANDLER FOR VALIDATION
// ============================================================================

/**
 * Async wrapper to handle validation errors in route handlers
 */
export const asyncHandler = (fn: (req: Request, res: Response, next: NextFunction) => Promise<any>) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};
