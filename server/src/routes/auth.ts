import { Router, Response } from 'express';
import { query } from '@/config/database';
import { authMiddleware, generateToken, AuthRequest } from '@/middleware/auth';
import { hashPassword, comparePassword } from '@/utils/password';
import { signUpSchema, signInSchema } from '@/utils/validation';

// Simple in-memory rate limiter for login attempts
const loginAttempts = new Map<string, { count: number; resetTime: number }>();

const checkLoginRateLimit = (email: string): boolean => {
  const now = Date.now();
  const attempt = loginAttempts.get(email);

  if (!attempt) {
    loginAttempts.set(email, { count: 1, resetTime: now + 15 * 60 * 1000 }); // 15 min window
    return true;
  }

  if (now > attempt.resetTime) {
    // Reset after window expires
    loginAttempts.set(email, { count: 1, resetTime: now + 15 * 60 * 1000 });
    return true;
  }

  // Max 5 attempts per 15 minutes
  if (attempt.count >= 5) {
    return false;
  }

  attempt.count += 1;
  return true;
};

const router = Router();

// Sign Up
router.post('/signup', async (req, res) => {
  try {
    const { email, password, name } = signUpSchema.parse(req.body);

    // Check if user already exists
    const existingUser = await query('SELECT id FROM users WHERE email = $1', [email.toLowerCase()]);
    if (existingUser.rows.length > 0) {
      return res.status(400).json({ error: 'An account with this email already exists' });
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

    // Generate token
    const token = generateToken(user.id, user.email);

    res.status(201).json({
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        createdAt: user.created_at,
      },
    });
  } catch (error: any) {
    if (error.name === 'ZodError') {
      return res.status(400).json({ error: error.errors[0].message });
    }
    console.error('Signup error:', error);
    res.status(500).json({ error: 'Failed to create account' });
  }
});

// Sign In
router.post('/login', async (req, res) => {
  try {
    const { email, password } = signInSchema.parse(req.body);

    // Check rate limit
    if (!checkLoginRateLimit(email.toLowerCase())) {
      return res.status(429).json({ error: 'Too many login attempts. Please try again in 15 minutes.' });
    }

    // Find user
    const result = await query(
      'SELECT id, email, name, password_hash, created_at FROM users WHERE email = $1',
      [email.toLowerCase()]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'No account found with this email' });
    }

    const user = result.rows[0];

    // Compare password
    const isPasswordValid = await comparePassword(password, user.password_hash);
    if (!isPasswordValid) {
      return res.status(401).json({ error: 'Incorrect password' });
    }

    // Generate token
    const token = generateToken(user.id, user.email);

    res.json({
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
        createdAt: user.created_at,
      },
    });
  } catch (error: any) {
    if (error.name === 'ZodError') {
      return res.status(400).json({ error: error.errors[0].message });
    }
    console.error('Login error:', error);
    res.status(500).json({ error: 'Failed to sign in' });
  }
});

// Get Current User
router.get('/me', authMiddleware, async (req: AuthRequest, res: Response) => {
  try {
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
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Failed to fetch user' });
  }
});

// Logout (client-side token removal, but here for completeness)
router.post('/logout', authMiddleware, (req: AuthRequest, res: Response) => {
  res.json({ message: 'Logged out successfully' });
});

export default router;
