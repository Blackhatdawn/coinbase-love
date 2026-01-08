# Security Fix #1: JWT to HttpOnly Cookies + Refresh Token Implementation

## Overview
This fix addresses the critical XSS vulnerability of storing JWT tokens in localStorage. We'll implement:
1. HttpOnly, Secure, SameSite cookies for access tokens (short-lived: 15 minutes)
2. Refresh token system using separate cookies (long-lived: 7 days)
3. Token rotation on refresh
4. Automatic token refresh on 401 responses

## Changes Required

### Backend Changes

#### 1. Create Refresh Token Schema (PostgreSQL Migration)

```sql
-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  revoked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_used_at TIMESTAMP,
  
  CONSTRAINT refresh_token_not_revoked CHECK (revoked = FALSE)
);

CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);
```

#### 2. Update server/src/middleware/auth.ts

**Old Code:**
```typescript
export const verifyToken = (token: string) => {
  try {
    const secret = process.env.JWT_SECRET;
    if (!secret) {
      throw new Error('JWT_SECRET environment variable is not configured');
    }
    const decoded = jwt.verify(token, secret);
    return decoded as { id: string; email: string };
  } catch (error) {
    return null;
  }
};

export const generateToken = (userId: string, email: string) => {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT_SECRET environment variable is not configured');
  }
  return jwt.sign(
    { id: userId, email },
    secret,
    { expiresIn: process.env.JWT_EXPIRY || '7d' }
  );
};
```

**New Code:**
```typescript
import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { query } from '@/config/database';
import { hashPassword, comparePassword } from '@/utils/password';

export interface AuthRequest extends Request {
  user?: {
    id: string;
    email: string;
  };
}

// Generate short-lived access token (15 minutes)
export const generateAccessToken = (userId: string, email: string) => {
  const secret = process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT_SECRET environment variable is not configured');
  }
  return jwt.sign(
    { id: userId, email, type: 'access' },
    secret,
    { expiresIn: process.env.JWT_ACCESS_EXPIRY || '15m' }
  );
};

// Generate long-lived refresh token (7 days)
export const generateRefreshToken = (userId: string) => {
  const secret = process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET;
  if (!secret) {
    throw new Error('JWT_REFRESH_SECRET environment variable is not configured');
  }
  return jwt.sign(
    { id: userId, type: 'refresh' },
    secret,
    { expiresIn: process.env.JWT_REFRESH_EXPIRY || '7d' }
  );
};

// Verify token and return decoded payload
export const verifyToken = (token: string, type: 'access' | 'refresh' = 'access') => {
  try {
    const secret = type === 'access' 
      ? process.env.JWT_SECRET 
      : (process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET);
      
    if (!secret) {
      throw new Error(`JWT_${type.toUpperCase()}_SECRET not configured`);
    }
    
    const decoded = jwt.verify(token, secret) as any;
    
    // Verify token type matches request
    if (decoded.type !== type) {
      return null;
    }
    
    return decoded as { id: string; email?: string; type: string };
  } catch (error) {
    return null;
  }
};

// Middleware: Extract and verify access token from Authorization header
export const authMiddleware = (req: AuthRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  
  if (!authHeader) {
    return res.status(401).json({ error: 'No authorization header' });
  }

  const token = authHeader.replace('Bearer ', '');
  const decoded = verifyToken(token, 'access');

  if (!decoded) {
    return res.status(401).json({ 
      error: 'Invalid or expired token',
      code: 'TOKEN_EXPIRED'
    });
  }

  req.user = {
    id: decoded.id,
    email: decoded.email || '',
  };
  
  next();
};

// Save refresh token hash to database
export const saveRefreshToken = async (userId: string, refreshToken: string) => {
  const tokenHash = await hashPassword(refreshToken);
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days
  
  const result = await query(
    `INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
     VALUES ($1, $2, $3)
     RETURNING id`,
    [userId, tokenHash, expiresAt]
  );
  
  return result.rows[0].id;
};

// Verify refresh token is valid and not revoked
export const verifyRefreshTokenInDb = async (userId: string, refreshToken: string) => {
  const result = await query(
    `SELECT id, token_hash FROM refresh_tokens
     WHERE user_id = $1 AND revoked = FALSE AND expires_at > CURRENT_TIMESTAMP
     ORDER BY created_at DESC
     LIMIT 1`,
    [userId]
  );
  
  if (result.rows.length === 0) {
    return false;
  }
  
  const { token_hash } = result.rows[0];
  return comparePassword(refreshToken, token_hash);
};

// Revoke all refresh tokens for a user (logout)
export const revokeUserRefreshTokens = async (userId: string) => {
  await query(
    'UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = $1',
    [userId]
  );
};
```

#### 3. Update server/src/routes/auth.ts

**Changes to login and signup endpoints:**

```typescript
import { Router, Response } from 'express';
import { body } from 'express-validator';
import { query } from '@/config/database';
import {
  authMiddleware,
  generateAccessToken,
  generateRefreshToken,
  saveRefreshToken,
  verifyRefreshTokenInDb,
  revokeUserRefreshTokens,
  AuthRequest,
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

// Helper to set auth cookies
const setAuthCookies = (res: Response, accessToken: string, refreshToken: string) => {
  const isProduction = process.env.NODE_ENV === 'production';
  const baseOptions = {
    httpOnly: true,
    secure: isProduction,
    sameSite: 'strict' as const,
  };
  
  // Access token: 15 minutes
  res.cookie('auth_token', accessToken, {
    ...baseOptions,
    maxAge: 15 * 60 * 1000,
    path: '/api',
  });
  
  // Refresh token: 7 days
  res.cookie('refresh_token', refreshToken, {
    ...baseOptions,
    maxAge: 7 * 24 * 60 * 60 * 1000,
    path: '/api/auth/refresh',
  });
};

// SIGN UP
router.post(
  '/signup',
  authLimiter,
  [validateEmail(), validatePassword(), validateName()],
  handleValidationErrors,
  asyncHandler(async (req, res) => {
    const { email, password, name } = req.body;

    try {
      signUpSchema.parse({ email, password, name });
    } catch (zodError: any) {
      return res.status(400).json({ error: zodError.errors[0].message });
    }

    // Check if user exists
    const existingUser = await query(
      'SELECT id FROM users WHERE email = $1',
      [email.toLowerCase()]
    );
    if (existingUser.rows.length > 0) {
      return res.status(409).json({ error: 'Email already registered' });
    }

    // Hash password
    const passwordHash = await hashPassword(password);

    // Create user
    const userResult = await query(
      'INSERT INTO users (email, name, password_hash) VALUES ($1, $2, $3) RETURNING id, email, name, created_at',
      [email.toLowerCase(), name, passwordHash]
    );

    const user = userResult.rows[0];

    // Create portfolio
    await query(
      'INSERT INTO portfolios (user_id, total_balance) VALUES ($1, $2)',
      [user.id, 10000]
    );

    // Generate tokens
    const accessToken = generateAccessToken(user.id, user.email);
    const refreshToken = generateRefreshToken(user.id);

    // Save refresh token to database
    await saveRefreshToken(user.id, refreshToken);

    // Set cookies
    setAuthCookies(res, accessToken, refreshToken);

    res.status(201).json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          createdAt: user.created_at,
        },
      },
      meta: {
        timestamp: new Date().toISOString(),
        version: 'v1',
      },
    });
  })
);

// SIGN IN
router.post(
  '/login',
  authLimiter,
  [validateEmail(), body('password').isLength({ min: 1 })],
  handleValidationErrors,
  asyncHandler(async (req, res) => {
    const { email, password } = req.body;

    try {
      signInSchema.parse({ email, password });
    } catch (zodError: any) {
      return res.status(400).json({ error: zodError.errors[0].message });
    }

    // Find user
    const userResult = await query(
      'SELECT id, email, name, password_hash, created_at FROM users WHERE email = $1',
      [email.toLowerCase()]
    );

    if (userResult.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    const user = userResult.rows[0];

    // Verify password
    const isPasswordValid = await comparePassword(password, user.password_hash);
    if (!isPasswordValid) {
      return res.status(401).json({ error: 'Invalid email or password' });
    }

    // Generate tokens
    const accessToken = generateAccessToken(user.id, user.email);
    const refreshToken = generateRefreshToken(user.id);

    // Save refresh token
    await saveRefreshToken(user.id, refreshToken);

    // Set cookies
    setAuthCookies(res, accessToken, refreshToken);

    res.json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          createdAt: user.created_at,
        },
      },
      meta: {
        timestamp: new Date().toISOString(),
        version: 'v1',
      },
    });
  })
);

// REFRESH TOKEN ENDPOINT (NEW)
router.post(
  '/refresh',
  asyncHandler(async (req, res) => {
    const refreshToken = req.cookies.refresh_token;

    if (!refreshToken) {
      return res.status(401).json({ 
        error: 'No refresh token',
        code: 'NO_REFRESH_TOKEN'
      });
    }

    // Verify JWT structure
    const decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET!) as any;

    if (decoded.type !== 'refresh') {
      return res.status(401).json({ error: 'Invalid token type' });
    }

    // Verify token exists in database and hasn't been revoked
    const isValid = await verifyRefreshTokenInDb(decoded.id, refreshToken);
    if (!isValid) {
      return res.status(401).json({ error: 'Refresh token revoked or expired' });
    }

    // Get user info
    const userResult = await query(
      'SELECT id, email FROM users WHERE id = $1',
      [decoded.id]
    );

    if (userResult.rows.length === 0) {
      return res.status(401).json({ error: 'User not found' });
    }

    const user = userResult.rows[0];

    // Generate new tokens
    const newAccessToken = generateAccessToken(user.id, user.email);
    const newRefreshToken = generateRefreshToken(user.id);

    // Save new refresh token
    await saveRefreshToken(user.id, newRefreshToken);

    // Set new cookies
    setAuthCookies(res, newAccessToken, newRefreshToken);

    res.json({ success: true });
  })
);

// GET CURRENT USER
router.get(
  '/me',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    const userResult = await query(
      'SELECT id, email, name, created_at FROM users WHERE id = $1',
      [req.user?.id]
    );

    if (userResult.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    const user = userResult.rows[0];
    res.json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          name: user.name,
          createdAt: user.created_at,
        },
      },
    });
  })
);

// LOGOUT
router.post(
  '/logout',
  authMiddleware,
  asyncHandler(async (req: AuthRequest, res: Response) => {
    // Revoke all refresh tokens for this user
    await revokeUserRefreshTokens(req.user?.id!);

    // Clear cookies
    res.clearCookie('auth_token', { path: '/api' });
    res.clearCookie('refresh_token', { path: '/api/auth/refresh' });

    res.json({ success: true, message: 'Logged out successfully' });
  })
);

export default router;
```

### Frontend Changes

#### 1. Update src/contexts/AuthContext.tsx

**Old Code:**
```typescript
localStorage.setItem(TOKEN_KEY, response.token);
```

**New Code:**
```typescript
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api } from "@/lib/api";

interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isTokenExpired: boolean;
  signIn: (email: string, password: string) => Promise<{ error?: string }>;
  signUp: (email: string, password: string, name: string) => Promise<{ error?: string }>;
  signOut: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const USER_KEY = "auth_user";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTokenExpired, setIsTokenExpired] = useState(false);

  // Check if user has session on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        // Try to get current user (will use existing cookie if valid)
        const response = await api.auth.getProfile();
        if (response.data?.user) {
          setUser(response.data.user);
          setIsTokenExpired(false);
        }
      } catch (error) {
        // No valid session
        localStorage.removeItem(USER_KEY);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const signIn = async (email: string, password: string): Promise<{ error?: string }> => {
    try {
      const response = await api.auth.login(email, password);
      // Cookie set automatically by backend
      setUser(response.data.user);
      setIsTokenExpired(false);
      return {};
    } catch (error: any) {
      return { error: error.message || "Failed to sign in" };
    }
  };

  const signUp = async (email: string, password: string, name: string): Promise<{ error?: string }> => {
    try {
      const response = await api.auth.signup(email, password, name);
      // Cookie set automatically by backend
      setUser(response.data.user);
      setIsTokenExpired(false);
      return {};
    } catch (error: any) {
      return { error: error.message || "Failed to create account" };
    }
  };

  const signOut = async () => {
    try {
      await api.auth.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      localStorage.removeItem(USER_KEY);
      setIsTokenExpired(false);
    }
  };

  const refreshToken = async (): Promise<boolean> => {
    try {
      await api.auth.refresh();
      setIsTokenExpired(false);
      return true;
    } catch (error) {
      setIsTokenExpired(true);
      setUser(null);
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isTokenExpired,
        signIn,
        signUp,
        signOut,
        refreshToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
```

#### 2. Update src/lib/api.ts

**Key Changes:**
- Remove localStorage token handling
- Add credentials: 'include' for cookie-based auth
- Implement automatic refresh token on 401
- Add refresh token endpoint

```typescript
class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const request = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<any> => {
  const url = `${API_BASE}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Include cookies (auth_token)
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));

      // Handle 401 - token expired
      if (response.status === 401) {
        const code = error.code || 'UNAUTHORIZED';
        throw new APIError(response.status, error.error || 'Unauthorized', code);
      }

      throw new APIError(
        response.status,
        error.error || 'Request failed',
        error.code
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) throw error;
    throw new APIError(0, error instanceof Error ? error.message : 'Network error');
  }
};

// Wrapper with automatic token refresh
const requestWithRefresh = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<any> => {
  try {
    return await request(endpoint, options);
  } catch (error) {
    if (error instanceof APIError && error.status === 401) {
      // Try to refresh token
      try {
        await request('/auth/refresh', { method: 'POST' });
        // Retry original request with new token
        return await request(endpoint, options);
      } catch (refreshError) {
        // Refresh failed, user needs to re-login
        throw error;
      }
    }
    throw error;
  }
};

export const api = {
  auth: {
    signup: (email: string, password: string, name: string) =>
      request('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      }),
    login: (email: string, password: string) =>
      request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    logout: () =>
      request('/auth/logout', { method: 'POST' }),
    getProfile: () =>
      request('/auth/me'),
    refresh: () =>
      request('/auth/refresh', { method: 'POST' }),
  },

  crypto: {
    getAll: () =>
      requestWithRefresh('/crypto'),
    getOne: (symbol: string) =>
      requestWithRefresh(`/crypto/${symbol}`),
  },

  portfolio: {
    get: () =>
      requestWithRefresh('/portfolio'),
    getHolding: (symbol: string) =>
      requestWithRefresh(`/portfolio/holding/${symbol}`),
    addHolding: (symbol: string, name: string, amount: number) =>
      requestWithRefresh('/portfolio/holding', {
        method: 'POST',
        body: JSON.stringify({ symbol, name, amount }),
      }),
    deleteHolding: (symbol: string) =>
      requestWithRefresh(`/portfolio/holding/${symbol}`, { method: 'DELETE' }),
  },

  orders: {
    getAll: () =>
      requestWithRefresh('/orders'),
    create: (trading_pair: string, order_type: string, side: string, amount: number, price: number) =>
      requestWithRefresh('/orders', {
        method: 'POST',
        body: JSON.stringify({ trading_pair, order_type, side, amount, price }),
      }),
    getOne: (id: string) =>
      requestWithRefresh(`/orders/${id}`),
    cancel: (id: string) =>
      requestWithRefresh(`/orders/${id}/cancel`, { method: 'POST' }),
  },

  transactions: {
    getAll: (limit = 50, offset = 0) =>
      requestWithRefresh(`/transactions?limit=${limit}&offset=${offset}`),
    getOne: (id: string) =>
      requestWithRefresh(`/transactions/${id}`),
    create: (type: string, amount: number, symbol?: string, description?: string) =>
      requestWithRefresh('/transactions', {
        method: 'POST',
        body: JSON.stringify({ type, amount, symbol, description }),
      }),
    getStats: () =>
      requestWithRefresh('/transactions/stats/overview'),
  },
};

export { APIError };
```

#### 3. Update src/components/ProtectedRoute.tsx

```typescript
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";

export const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, isLoading, isTokenExpired } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !user) {
      navigate("/auth");
    }
  }, [user, isLoading, navigate]);

  useEffect(() => {
    if (isTokenExpired) {
      navigate("/auth");
    }
  }, [isTokenExpired, navigate]);

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return null;
  }

  return <>{children}</>;
};
```

## Environment Variables Required

### Backend (.env)

```env
# Existing
JWT_SECRET=<your-secure-32-char-hex-string>
JWT_EXPIRY=7d

# NEW - Refresh token configuration
JWT_REFRESH_SECRET=<different-secure-32-char-hex-string>
JWT_ACCESS_EXPIRY=15m
JWT_REFRESH_EXPIRY=7d

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cryptovault
DB_USER=postgres
DB_PASSWORD=postgres

# Server
NODE_ENV=development
PORT=5000
```

## Migration Steps

### Step 1: Database Migration
```bash
# Run the SQL to create refresh_tokens table
psql -U postgres -d cryptovault < refresh_tokens_migration.sql
```

### Step 2: Deploy Backend
```bash
# Pull changes
git pull origin main

# Install if needed (shouldn't be)
npm install

cd server
npm install
npm run build

# Test locally
npm run dev
```

### Step 3: Deploy Frontend
```bash
npm install
npm run build
```

### Step 4: Verification

1. **Test sign up:**
   ```bash
   curl -X POST http://localhost:5000/api/auth/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"Test123456","name":"Test User"}'
   ```
   Should return cookies in Set-Cookie header

2. **Test access without token:**
   ```bash
   curl http://localhost:5000/api/auth/me
   ```
   Should return 401 Unauthorized

3. **Test with cookie:**
   ```bash
   curl -b "auth_token=<token>" http://localhost:5000/api/auth/me
   ```
   Should return user object

4. **Test refresh:**
   ```bash
   curl -b "refresh_token=<token>" -X POST http://localhost:5000/api/auth/refresh
   ```
   Should set new auth_token cookie

## Rollback Plan

If issues occur:

1. **Revert code changes:**
   ```bash
   git revert <commit-hash>
   npm run build
   npm run deploy
   ```

2. **Data is safe:** Refresh tokens table can be dropped if needed
   ```sql
   DROP TABLE refresh_tokens;
   ```

3. **Old auth still works:** Existing JWT_SECRET still valid for 7 days

## Testing Checklist

- [ ] Signup creates both auth and refresh cookies
- [ ] Login creates both auth and refresh cookies
- [ ] Protected endpoints work with auth cookie
- [ ] 401 on missing auth header
- [ ] 401 on expired token
- [ ] Refresh endpoint issues new token
- [ ] Logout revokes all refresh tokens
- [ ] Frontend catches 401 and shows login
- [ ] Token refresh happens automatically on 401
- [ ] No localStorage involved in auth flow

## Monitoring

Track these metrics:
- Failed login attempts (rate limiting)
- Refresh token usage rate
- Token revocation events
- 401 error spike (indicates widespread expiration)
- Cookie acceptance rate (some users might have cookies disabled)
