# CryptoVault: 7-Week Phased Rollout Plan

## Executive Overview

This document outlines a zero-downtime, risk-mitigated rollout of critical security, code quality, and infrastructure updates to CryptoVault. The plan prioritizes safety through incremental deployment, comprehensive testing, and rollback procedures.

**Total Timeline:** 7 weeks (49 days)  
**Team Size:** 3-4 engineers  
**Risk Level:** Medium (mitigated through blue-green deployments)  
**Budget:** ~$400/month additional infrastructure + 250 engineer hours

---

## Week 1: Critical Security Fixes (Highest Priority)

### Objective
Fix XSS vulnerabilities, implement refresh tokens, and harden CSP.

### Phase 1.1: Preparation (Days 1-2)

#### Day 1: Project Setup & Risk Assessment

**Morning (4 hours):**
```bash
# Create feature branches
git checkout -b security/auth-migration-v2
git checkout -b security/csp-hardening-v2
git checkout -b security/input-validation-v2

# Set up staging environment
# Using Render: https://dashboard.render.com
# Create new services:
# - Frontend staging (https://cryptovault-staging.onrender.com)
# - Backend staging (https://api-staging.cryptovault.onrender.com)
# - PostgreSQL (use production copy)

# Database backup
pg_dump -h prod-postgres.c.render.com -U postgres \
  cryptovault > backup_$(date +%Y%m%d).sql

# Tag current version
git tag -a v1.0.0 -m "Pre-security-audit baseline"
git push origin v1.0.0
```

**Afternoon (4 hours):**
- Code review preparation documents
- Documentation of rollback procedures
- Alert/monitoring setup for staging

#### Day 2: Implement & Test Locally

**Development (8 hours):**
- Implement JWT → HttpOnly cookie migration
- Add refresh token system
- Harden CSP policy
- Create migration scripts

**Testing (local):**
```bash
npm install  # Frontend
cd server && npm install  # Backend

npm run dev  # Start frontend (http://localhost:8080)
# In another terminal:
cd server && npm run dev  # Start backend (http://localhost:5000)

# Test sign up/login with cookies
# Test protected endpoints
# Test CSP headers
# Test refresh token flow
```

### Phase 1.2: Deployment to Staging (Day 3)

#### Deployment Steps

**8:00 AM - Code Review & Merge**
```bash
# Create pull request on GitHub
git push origin security/auth-migration-v2

# Peer review requirements:
# - 2+ approvals from senior engineers
# - All tests passing
# - No security issues flagged

# Merge with --no-ff for history
git merge --no-ff security/auth-migration-v2
```

**9:00 AM - Deploy to Staging**

```bash
# Render deployment (automatic via GitHub)
# OR manual deployment:

# Build frontend
npm run build
# Backend
cd server && npm run build

# Deploy to staging
# Using Render environment variables:
# JWT_SECRET=test-secret-staging
# JWT_REFRESH_SECRET=test-refresh-staging
# NODE_ENV=staging
# DATABASE_URL=postgresql://staging-db...
```

**10:00 AM - Smoke Tests on Staging**

```bash
# Test authentication flow
curl -X POST https://api-staging.cryptovault.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123456"}' \
  -v  # See cookies

# Test protected endpoint
curl -b "auth_token=<token>" \
  https://api-staging.cryptovault.onrender.com/api/auth/me

# Test refresh token
curl -b "refresh_token=<token>" -X POST \
  https://api-staging.cryptovault.onrender.com/api/auth/refresh

# Check CSP headers
curl -I https://api-staging.cryptovault.onrender.com/api/health \
  | grep Content-Security-Policy

# Run Cypress E2E tests
npm run test:e2e:staging
```

**12:00 PM - Load Test**

```bash
# Using autocannon or k6
npm install -D autocannon

autocannon -d 60 -c 100 \
  https://api-staging.cryptovault.onrender.com/api/crypto

# Expected results:
# - P95 latency < 500ms
# - Error rate < 1%
# - CPU/Memory within normal ranges
```

**1:00 PM - Security Audit**

```bash
# Run OWASP ZAP scan (automated)
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://api-staging.cryptovault.onrender.com

# Manual testing:
# - Try XSS in auth forms
# - Verify localStorage is empty (no tokens)
# - Verify cookie flags (HttpOnly, Secure, SameSite)
# - Test CSRF protection
```

### Phase 1.3: Canary Deployment to Production (Day 4)

#### Blue-Green Setup

```
BLUE (Current v1.0.0):
  - cryptovault.onrender.com → v1.0.0 on port 5000
  - Traffic: 100%
  
GREEN (New v2.0.0):
  - cryptovault-green.onrender.com → v2.0.0 on port 5001
  - Traffic: 0% (ready to receive traffic)
```

#### 8:00 AM - Deploy Green

```bash
# Create new service instance in Render:
# Name: cryptovault-green
# Region: Same as current
# Environment: Use v2.0.0 image

# Deploy v2.0.0
git deploy production --version v2.0.0 --instance green

# Verify green environment
curl https://cryptovault-green.onrender.com/api/health
# Should return: {"status":"ok"}
```

#### 9:00 AM - Canary Traffic Shift (10%)

```bash
# Using load balancer configuration or Render routing:
# Shift 10% of traffic to GREEN
# Traffic distribution:
#   BLUE:  90%
#   GREEN: 10%

# Monitor error rate
# Monitor latency
# Monitor specific 401 errors (token issues)
```

#### 10:00 AM - 2:00 PM - Monitoring Window

**Metrics to watch:**
```
1. Error Rate
   - Target: < 1% on GREEN
   - If > 2%: Immediate rollback

2. HTTP 401 Rate
   - Expected: ~0.1% (token expiry)
   - If > 5%: Investigate token issue

3. Response Latency (p95)
   - Target: < 500ms
   - If > 1000ms: Investigate

4. Database Connection Pool
   - Target: < 80% utilization
   - If > 95%: Increase pool size

5. CoinGecko API Calls
   - Monitor for rate limit errors
   - Should be ~30 req/min

6. Authentication Attempts
   - Monitor for brute force
   - Rate limiter should kick in

Monitoring Tools:
- Render Dashboard: https://dashboard.render.com
- Sentry: https://sentry.io (error tracking)
- CloudFlare Analytics: (if using)
```

**Actions if issues detected:**

```bash
# If error rate > 2%:
git revert production --instance green
# Traffic automatically shifts back to BLUE

# If specific issues:
# Check logs
curl https://cryptovault-green.onrender.com/logs

# Database queries slow?
# Check PostgreSQL slow query log

# Authentication failing?
# Verify JWT_SECRET and JWT_REFRESH_SECRET match
```

#### 2:00 PM - 50% Canary Shift

If green stable for 4 hours:
```bash
# Increase traffic to GREEN
#   BLUE:  50%
#   GREEN: 50%

# Continue monitoring for 2 more hours
```

#### 4:00 PM - Full Cutover

If still stable:
```bash
# Shift 100% traffic to GREEN
#   BLUE:  0%
#   GREEN: 100%

# Keep BLUE available for instant rollback
```

### Phase 1.4: Production Verification (Day 5)

#### Morning: Post-Deployment Validation

```bash
# Test complete user journey
1. Sign up as new user
   POST /api/auth/signup
   
2. Verify cookies set
   GET /api/auth/me (with cookies)
   
3. Check no localStorage tokens
   Browser DevTools > Application > Local Storage
   
4. Test logout
   POST /api/auth/logout
   
5. Verify cookies cleared
   GET /api/auth/me (should fail with 401)
   
6. Test token refresh
   POST /api/auth/refresh
```

#### Afternoon: Production Health Metrics

```
✅ Checklist:
- [ ] Error rate < 0.5% (good level)
- [ ] HTTP 401 rate < 2% (expected)
- [ ] API latency p95 < 500ms
- [ ] Database health OK
- [ ] External API (CoinGecko) responding
- [ ] No spike in 500 errors
- [ ] Users reporting successful logins
- [ ] Session persistence working
- [ ] CORS working (no blocked requests)
- [ ] CSP headers present
```

#### End of Day: Decommission BLUE

```bash
# Only after 24 hours of stable GREEN performance
# Keep BLUE for 24 more hours as failsafe
# Then decommission

git tag -a v2.0.0-deployed -m "v2.0.0 deployed to production"
git push origin v2.0.0-deployed
```

### Phase 1.5: Incident Response Training (Day 5)

**3-hour session:**
1. How to identify token-related issues
2. How to query refresh_tokens table
3. How to revoke tokens if needed
4. How to rollback (procedure walkthrough)
5. Communication protocol for incidents

---

## Week 2: High-Priority Hardening

### Objective
Email verification, 2FA/TOTP, audit logging, database encryption.

### Phase 2.1: Email Verification System

**Implementation:**
```typescript
// Add to schema:
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
ALTER TABLE users ADD COLUMN verification_token_expires_at TIMESTAMP;

// Create email service
npm install nodemailer
npm install -D @types/nodemailer

// Routes:
POST /api/auth/signup  // Send verification email
POST /api/auth/verify-email  // Verify token
POST /api/auth/resend-verification  // Resend email
```

**Testing:**
- Use MailHog (local email testing) in development
- Use SendGrid (or similar) in production
- Test verification link expiration
- Test resend functionality

**Rollout:** Canary → 50% → 100% (same as Phase 1)

### Phase 2.2: Two-Factor Authentication (TOTP)

**Implementation:**
```bash
npm install speakeasy qrcode

# Add to schema:
ALTER TABLE users ADD COLUMN totp_secret VARCHAR(255);
ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN backup_codes TEXT[];

# Routes:
GET /api/auth/2fa/setup  // Get QR code
POST /api/auth/2fa/enable  // Enable 2FA
POST /api/auth/2fa/verify  // Verify TOTP code
POST /api/auth/2fa/disable  // Disable 2FA
```

**Testing:**
- Use Google Authenticator / Authy for testing
- Test backup codes
- Test time-based code validation
- Test code replay protection

### Phase 2.3: Audit Logging System

**Implementation:**
```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  action VARCHAR(100),  -- 'login', 'logout', 'order_create'
  resource VARCHAR(100),  -- 'user', 'order', 'portfolio'
  resource_id UUID,
  status VARCHAR(20),  -- 'success', 'failure'
  ip_address INET,
  user_agent TEXT,
  details JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

**Logging in routes:**
```typescript
// Middleware to capture audit info
app.use((req, res, next) => {
  res.on('finish', async () => {
    // Log to audit_logs table
    if (SENSITIVE_ACTIONS.includes(req.method + req.path)) {
      await query(
        'INSERT INTO audit_logs (user_id, action, status, ip_address, user_agent) VALUES ...',
        [req.user?.id, req.path, res.statusCode, req.ip, req.get('user-agent')]
      );
    }
  });
  next();
});
```

### Phase 2.4: Database Connection Pool Hardening

**Update server/src/config/database.ts:**
```typescript
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'cryptovault',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
  
  // Pool sizing based on expected load
  max: parseInt(process.env.DB_POOL_MAX || '30'),  // Increased from default
  min: parseInt(process.env.DB_POOL_MIN || '10'),
  
  // Timeouts
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
  statement_timeout: '30s',  // Query timeout
  
  // SSL for production
  ssl: process.env.NODE_ENV === 'production' 
    ? { rejectUnauthorized: false }
    : false,
});
```

### Week 2 Metrics

- Email verification: 95%+ of new users verify within 24 hours
- 2FA adoption: Target 10% of users (voluntary) in Week 2
- Audit logs: All sensitive operations logged
- Database: Connection pool utilization < 80%

---

## Week 3: Code Quality & Type Safety

### Objective
Enable TypeScript strict mode, add unit tests, implement linting.

### Phase 3.1: TypeScript Strict Mode

**Gradual enablement:**

**Day 1: Enable noImplicitAny**
```json
{
  "compilerOptions": {
    "noImplicitAny": true
  }
}
```
Fix errors, commit: `chore: enable noImplicitAny`

**Day 2: Enable strictNullChecks**
```json
{
  "compilerOptions": {
    "strictNullChecks": true
  }
}
```
Fix errors, commit: `chore: enable strictNullChecks`

**Day 3: Enable all strict flags**
```json
{
  "strict": true
}
```
Fix remaining errors.

**Day 4: Add strict-mode ESLint rules**
```bash
npm install -D @typescript-eslint/eslint-plugin
```

Update `.eslintrc`:
```json
{
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/explicit-function-return-types": "warn"
  }
}
```

### Phase 3.2: Unit Tests

**Frontend testing:**
```bash
npm install -D vitest @testing-library/react @testing-library/user-event

# Create tests/
# - AuthContext.test.tsx
# - api.test.ts
# - ProtectedRoute.test.tsx
# - components/Header.test.tsx
```

**Backend testing:**
```bash
cd server
npm install -D vitest supertest

# Create tests/
# - routes/auth.test.ts
# - routes/orders.test.ts
# - middleware/auth.test.ts
# - utils/password.test.ts
```

**Target: 50% code coverage**
```bash
npm run test -- --coverage
```

### Phase 3.3: ESLint & Prettier Setup

```bash
npm install -D prettier eslint-plugin-security eslint-plugin-import

# .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5",
  "printWidth": 100
}

# Format all files
npm run format

# Add pre-commit hook
npm install -D husky
npx husky install
npx husky add .husky/pre-commit "npm run lint && npm run format"
```

---

## Week 4: Integration Testing & API Documentation

### Objective
E2E tests, API contract testing, Swagger documentation.

### Phase 4.1: End-to-End Testing with Cypress

```bash
npm install -D cypress

# Create cypress/e2e/
# - auth.cy.ts (signup, login, logout)
# - trading.cy.ts (place order, cancel order)
# - portfolio.cy.ts (view holdings, add holding)
# - market.cy.ts (view market data)

# Run tests
npm run test:e2e

# CI/CD integration
# GitHub Actions runs E2E tests on every PR
```

### Phase 4.2: Request Retry Logic

**Update src/lib/api.ts:**
```typescript
async function requestWithRetry(
  endpoint: string,
  options: RequestInit = {},
  maxRetries: number = 3
): Promise<any> {
  let lastError: any;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await request(endpoint, options);
    } catch (error) {
      lastError = error;
      
      // Don't retry client errors (4xx) or last attempt
      if (error.status >= 400 && error.status < 500) {
        throw error;
      }
      
      if (attempt === maxRetries) break;
      
      // Exponential backoff: 1s, 2s, 4s
      const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  
  throw lastError;
}
```

### Phase 4.3: Swagger/OpenAPI Documentation

```bash
npm install swagger-ui-express swagger-jsdoc

# server/src/swagger.ts
const swaggerSpec = swaggerJsdoc({
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'CryptoVault API',
      version: '2.0.0',
    },
    servers: [
      { url: '/api', description: 'API Server' },
    ],
  },
  apis: ['src/routes/*.ts'],
});

// In server.ts
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));
```

Add JSDoc comments to routes:
```typescript
/**
 * @swagger
 * /auth/login:
 *   post:
 *     summary: User login
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               email: { type: string }
 *               password: { type: string }
 *     responses:
 *       200:
 *         description: Successful login
 *       401:
 *         description: Invalid credentials
 */
```

Access at: `https://api.cryptovault.com/api/docs`

---

## Week 5: DevOps & Infrastructure

### Objective
Docker containerization, GitHub Actions CI/CD, database migrations.

### Phase 5.1: Create Dockerfiles

**Dockerfile.backend**
```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY server/package*.json ./
RUN npm ci --only=production

COPY server/src ./src
COPY server/tsconfig.json .

RUN npm run build

EXPOSE 5000

CMD ["node", "dist/server.js"]
```

**Dockerfile.frontend**
```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**docker-compose.yml**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: cryptovault
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "5000:5000"
    environment:
      DB_HOST: postgres
      DB_PORT: 5432
      DB_NAME: cryptovault
      DB_USER: postgres
      DB_PASSWORD: postgres_dev
      JWT_SECRET: dev-secret-key
      JWT_REFRESH_SECRET: dev-refresh-key
      NODE_ENV: development
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8080:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Local testing:**
```bash
docker-compose up -d
docker-compose ps
docker-compose logs -f backend
```

### Phase 5.2: GitHub Actions CI/CD Pipeline

**`.github/workflows/ci.yml`**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: cryptovault_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      
      # Frontend
      - run: npm ci
      - run: npm run lint
      - run: npm run test -- --coverage
      - run: npm run build
      
      # Backend
      - run: cd server && npm ci
      - run: cd server && npm run lint
      - run: cd server && npm run test
      - run: cd server && npm run build
      
      # E2E tests
      - run: npm run test:e2e:ci
      
      # Upload coverage
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Render (Staging)
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/v1/services/[staging-service-id]/deploys \
            -H "Authorization: Bearer $RENDER_API_KEY"

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    
    environment:
      name: production
      url: https://cryptovault.onrender.com
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Render (Production)
        env:
          RENDER_API_KEY: ${{ secrets.RENDER_API_KEY }}
        run: |
          curl -X POST https://api.render.com/v1/services/[prod-service-id]/deploys \
            -H "Authorization: Bearer $RENDER_API_KEY"
      
      - name: Run smoke tests
        run: npm run test:smoke
```

### Phase 5.3: Database Migrations with Knex.js

```bash
npm install -D knex
npx knex init

# Create migrations
npx knex migrate:make create_refresh_tokens_table

# Migration files: server/src/database/migrations/
# Seeds: server/src/database/seeds/

# Apply migrations
npx knex migrate:latest

# Rollback
npx knex migrate:rollback
```

---

## Week 6: Performance & Observability

### Objective
Redis caching, distributed tracing, performance monitoring.

### Phase 6.1: Redis Caching Layer

```bash
npm install redis ioredis

# Create cache layer
server/src/cache/index.ts

# Cache crypto prices (CoinGecko responses)
# Cache portfolio summaries
# Cache user profile data
```

**Implementation:**
```typescript
// server/src/cache/index.ts
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || {
  host: 'localhost',
  port: 6379,
});

export const cache = {
  get: async (key: string) => redis.get(key),
  set: async (key: string, value: any, ttl: number = 300) => {
    await redis.setex(key, ttl, JSON.stringify(value));
  },
  del: async (key: string) => redis.del(key),
  clear: async () => redis.flushdb(),
};

// In crypto route:
router.get('/', async (req, res) => {
  const cacheKey = 'crypto:all';
  
  // Try cache first
  const cached = await cache.get(cacheKey);
  if (cached) {
    return res.json({ ...JSON.parse(cached), cached: true });
  }
  
  // Fetch from CoinGecko
  const data = await getAllCryptoPrices();
  
  // Cache for 5 minutes
  await cache.set(cacheKey, { data, count: data.length }, 300);
  
  res.json({ data, count: data.length, cached: false });
});
```

**Result:** CoinGecko API calls reduced by 90%+

### Phase 6.2: Structured Logging with Winston

```bash
npm install winston pino-pretty

# server/src/logger.ts
import winston from 'winston';

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple(),
    }),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' }),
  ],
});

// Usage
logger.info('User logged in', { userId: user.id });
logger.error('Database error', { error: err.message });
```

### Phase 6.3: Error Tracking with Sentry

```bash
npm install @sentry/node @sentry/react
npm install -D @sentry/tracing

# Backend: server/src/server.ts
import * as Sentry from "@sentry/node";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
});

app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.errorHandler());

# Frontend: src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  tracesSampleRate: 1.0,
});
```

---

## Week 7: Documentation & Handoff

### Objective
Comprehensive documentation, training, knowledge transfer.

### Phase 7.1: Architecture Decision Records (ADRs)

Create `docs/adr/` folder with decisions:

**ADR-001: JWT to HttpOnly Cookies**
- Status: Accepted
- Context: XSS vulnerability from localStorage
- Decision: Move to HttpOnly, Secure, SameSite cookies
- Consequences: Improved security, requires CSRF token for some endpoints

**ADR-002: Refresh Token System**
- Status: Accepted
- Context: 7-day token expiry caused logout issues
- Decision: Implement 15-min access + 7-day refresh tokens
- Consequences: Better UX, requires refresh endpoint

### Phase 7.2: Runbooks & Incident Response

**docs/runbooks/authentication-issues.md**
```markdown
# Authentication Issues Runbook

## Symptom: Users reporting 401 errors on login

### Quick Check
1. Verify JWT_SECRET in env: `echo $JWT_SECRET | wc -c` (should be 32+ chars)
2. Check refresh_tokens table: `SELECT COUNT(*) FROM refresh_tokens;`
3. Monitor error rate in Sentry

### Root Causes & Solutions

**Cause: JWT_SECRET changed or missing**
```bash
# Check current secret
env | grep JWT_SECRET

# Rotate secret (requires all users to re-login)
# 1. Generate new secret: openssl rand -hex 32
# 2. Update environment variable
# 3. Monitor for 401 spike
# 4. After 24h, old secret no longer works
```

**Cause: refresh_tokens table full**
```bash
# Clean old tokens
DELETE FROM refresh_tokens WHERE expires_at < CURRENT_TIMESTAMP;
```

**Cause: Database connection issue**
```bash
# Check pool
SELECT COUNT(*) FROM pg_stat_activity;

# Increase pool if needed
UPDATE pg_settings SET value = '50' WHERE name = 'max_connections';
```
```

**docs/runbooks/database-recovery.md**
**docs/runbooks/rollback-procedure.md**
**docs/runbooks/performance-degradation.md**

### Phase 7.3: Training Sessions

**Session 1: Architecture Overview (2 hours)**
- System components
- Data flow
- Integration points

**Session 2: Security Posture (2 hours)**
- Token management
- Rate limiting
- Audit logging

**Session 3: Operations & Monitoring (2 hours)**
- Key metrics
- Alerting
- Incident response

**Session 4: Deployment Procedures (2 hours)**
- Blue-green deployment
- Rollback procedure
- Load testing

### Phase 7.4: Final Documentation Checklist

- [ ] README.md updated with v2.0 features
- [ ] DEPLOYMENT.md with step-by-step guide
- [ ] SECURITY.md with security model
- [ ] API.md with endpoint documentation
- [ ] TROUBLESHOOTING.md with common issues
- [ ] MONITORING.md with key metrics
- [ ] CHANGELOG.md with v2.0 changes

---

## Master Timeline

```
Week 1: Critical Security (JWT, CSP, Refresh Tokens)
├── Day 1-2: Local development + staging
├── Day 3-4: Canary deployment (10% → 50% → 100%)
└── Day 5: Production verification + decommissioning

Week 2: Hardening (Email, 2FA, Audit Logs)
├── Email verification system
├── TOTP 2FA setup
├── Audit logging
└── Database pool optimization

Week 3: Code Quality (TypeScript Strict, Tests, Linting)
├── Enable TypeScript strict mode
├── Unit test implementation (50% coverage)
└── ESLint + Prettier setup

Week 4: Integration (E2E Tests, Retry Logic, Swagger)
├── Cypress E2E tests
├── Request retry with backoff
└── API documentation

Week 5: DevOps (Docker, CI/CD, Migrations)
├── Dockerfile creation
├── GitHub Actions pipeline
└── Database migrations

Week 6: Performance (Redis, Logging, Monitoring)
├── Redis caching layer
├── Structured logging
└── Sentry error tracking

Week 7: Documentation & Handoff
├── ADRs (Architecture Decision Records)
├── Runbooks for operations
├── Training sessions
└── Knowledge transfer
```

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Auth migration breaks login | 5% | Critical | 5-day staging validation, blue-green |
| Database migration fails | 3% | Critical | Full backup, separate test DB |
| Performance regression | 20% | High | Load testing, monitoring |
| 3rd-party API failure | 15% | Medium | Cache fallback, circuit breaker |
| User session hijacking | 1% | Critical | HttpOnly cookies, CSRF tokens |
| Data loss | < 1% | Critical | Daily backups, point-in-time recovery |

## Success Metrics

**Security:**
- 0 stored JWT tokens in localStorage
- 100% refresh token coverage
- CSP no violations after 7 days
- 0 SQL injection attempts caught

**Performance:**
- API latency p95 < 500ms
- Cache hit rate > 80%
- CoinGecko API calls reduced 90%

**Reliability:**
- Uptime > 99.9%
- Error rate < 0.5%
- Deployment time < 30 minutes

**Code Quality:**
- 50%+ test coverage
- 0 ESLint errors
- TypeScript strict mode enabled

---

## Budget & Timeline Summary

| Phase | Duration | Cost | Engineer Hours |
|-------|----------|------|----------------|
| Phase 1: Security | 1 week | $0 | 40 |
| Phase 2: Hardening | 1 week | $200 | 35 |
| Phase 3: Code Quality | 1 week | $0 | 30 |
| Phase 4: Integration | 1 week | $100 | 45 |
| Phase 5: DevOps | 1 week | $50 | 50 |
| Phase 6: Performance | 1 week | $200 | 40 |
| Phase 7: Documentation | 1 week | $0 | 25 |
| **TOTAL** | **7 weeks** | **$550** | **265** |

---

## Post-Rollout: 30-Day Support

- Monitor error rates daily
- Weekly performance reviews
- Monthly security audits
- User feedback integration
- Optimization based on real-world usage

---

**Document Status:** Ready for Implementation  
**Last Updated:** 2024  
**Next Review:** Week 7 completion
