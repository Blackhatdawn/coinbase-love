import rateLimit from 'express-rate-limit';
import { body, validationResult, Result, ValidationError } from 'express-validator';
import { Request, Response, NextFunction } from 'express';

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
 * Custom security headers (used with helmet)
 */
export const securityHeaders = (req: Request, res: Response, next: NextFunction) => {
  // Content Security Policy
  res.setHeader(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'"
  );
  
  // Prevent MIME sniffing
  res.setHeader('X-Content-Type-Options', 'nosniff');
  
  // Prevent clickjacking
  res.setHeader('X-Frame-Options', 'DENY');
  
  // Disable X-Powered-By header
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
