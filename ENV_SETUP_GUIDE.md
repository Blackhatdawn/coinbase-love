# Environment Variables Setup Guide

**Project:** CryptoVault (Frontend + Backend)  
**Status:** Complete Configuration Instructions  
**Last Updated:** January 21, 2026

---

## Overview

This guide ensures your project loads environment variables **directly from `.env` files** rather than relying on environment secrets in deployment dashboards.

### Why This Matters
- **Local Development:** Load secrets from .env file automatically
- **Consistency:** Same configuration approach across dev/staging/production
- **Security:** .env file is in .gitignore, never committed to repo
- **Ease of Setup:** New developers just copy `.env.example` to `.env`

---

## Project Structure

```
CryptoVault/
├── frontend/
│   ├── .env.development          # Frontend dev env (IGNORED by git)
│   ├── .env.production           # Frontend prod env (IGNORED by git)
│   ├── .env.example              # Template for frontend (IN git)
│   └── src/
│       └── lib/
│           └── runtimeConfig.ts  # Loads VITE_ variables
├── backend/
│   ├── .env                      # Backend env (IGNORED by git)
│   ├── .env.example              # Template for backend (IN git)
│   ├── config.py                 # Environment loader (NEW)
│   └── main.py                   # FastAPI app
├── .gitignore                    # Excludes .env files
└── ENV_SETUP_GUIDE.md            # This file
```

---

## Backend Setup (.env File Loading)

### Step 1: Create Backend .env File

```bash
# Navigate to project root
cd cryptovault-project

# Copy the example to create your .env
cp backend/.env.example backend/.env

# Edit with your actual values
nano backend/.env  # or vim, code, etc.
```

### Step 2: Configure backend/.env

Update these critical values:

```env
# Core settings
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cryptovault_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Security (generate with: openssl rand -hex 32)
JWT_SECRET=your-actual-secret-key-here
CSRF_SECRET=your-csrf-secret-here

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Sentry (optional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### Step 3: Use Settings in Backend Code

In your FastAPI application:

```python
# backend/main.py
from config import settings
from fastapi import FastAPI

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

@app.on_event("startup")
async def startup():
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️ Database: {settings.DATABASE_URL[:50]}...")
    print(f"📍 Server: {settings.PUBLIC_SERVER_URL}")

# Use settings in route handlers
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration using settings
from sqlalchemy import create_engine

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT
)
```

### Step 4: Test Environment Loading

```bash
# From project root
python -m backend.config

# Output should show:
# ✅ Loading environment from: /path/to/backend/.env
# [Configuration details displayed]
```

---

## Frontend Setup (Vite Environment Variables)

### Step 1: Create Frontend .env Files

```bash
# Development environment
cp frontend/.env.example frontend/.env.development

# Production environment
cp frontend/.env.example frontend/.env.production
```

### Step 2: Configure frontend/.env.development

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8001

# App Configuration
VITE_APP_NAME=CryptoVault
VITE_APP_VERSION=2.0.0-dev
VITE_NODE_ENV=development

# Sentry (optional for development)
VITE_SENTRY_DSN=
VITE_SENTRY_ENVIRONMENT=development
VITE_ENABLE_SENTRY=false

# Features
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_PWA=false

# Social Media (optional)
VITE_SOCIAL_TWITTER_URL=https://twitter.com/CryptoVaultFin
VITE_SOCIAL_LINKEDIN_URL=https://linkedin.com/company/cryptovault-financial
VITE_SOCIAL_DISCORD_URL=https://discord.gg/cryptovault
VITE_SOCIAL_TELEGRAM_URL=https://t.me/cryptovaultfinancial
```

### Step 3: Configure frontend/.env.production

```env
# API Configuration (use Vercel rewrites or API gateway)
VITE_API_BASE_URL=

# App Configuration
VITE_APP_NAME=CryptoVault
VITE_APP_VERSION=2.0.0
VITE_NODE_ENV=production

# Sentry
VITE_SENTRY_DSN=https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/4510716879503360
VITE_SENTRY_ENVIRONMENT=production
VITE_ENABLE_SENTRY=true

# Features
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_PWA=true

# Social Media
VITE_SOCIAL_TWITTER_URL=https://twitter.com/CryptoVaultFin
VITE_SOCIAL_LINKEDIN_URL=https://linkedin.com/company/cryptovault-financial
VITE_SOCIAL_DISCORD_URL=https://discord.gg/cryptovault
VITE_SOCIAL_TELEGRAM_URL=https://t.me/cryptovaultfinancial
```

### Step 4: Vite Automatically Loads .env Files

Vite automatically loads variables based on the environment:

```bash
# Development - loads .env and .env.development
npm run dev

# Production build - loads .env and .env.production
npm run build

# Preview - loads .env and .env.production
npm run preview
```

### Step 5: Access in Code

```typescript
// frontend/src/lib/runtimeConfig.ts
// These are automatically available via import.meta.env

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const appName = import.meta.env.VITE_APP_NAME;
const appVersion = import.meta.env.VITE_APP_VERSION;
const sentryDsn = import.meta.env.VITE_SENTRY_DSN;

// In React components:
console.log(import.meta.env.VITE_APP_NAME); // "CryptoVault"
console.log(import.meta.env.VITE_API_BASE_URL); // "" or "http://localhost:8001"
```

---

## .gitignore Configuration

### Root .gitignore

Make sure your `.gitignore` excludes .env files:

```
# Environment variables
.env
.env.local
.env.*.local
.env.production.local
.env.development.local

# Backend
backend/.env
backend/.env.local
backend/venv/
backend/__pycache__/

# Frontend
frontend/.env.local
frontend/.env.development.local
frontend/.env.production.local
frontend/node_modules/
frontend/dist/

# IDEs
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### Verify .gitignore

```bash
# Check that .env files won't be committed
git status --ignored

# Should NOT show .env files
# Should show .env.example files
```

---

## Local Development Workflow

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/cryptovault.git
cd cryptovault

# 2. Backend setup
cp backend/.env.example backend/.env
# Edit backend/.env with your values

# 3. Frontend setup
cp frontend/.env.example frontend/.env.development
# Keep defaults or customize

# 4. Install dependencies
cd backend
pip install -r requirements.txt

cd ../frontend
npm install

# 5. Start development servers
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Daily Development

```bash
# Backend loads from backend/.env automatically
python -m uvicorn main:app --reload
# ✅ Loading environment from: /path/to/backend/.env

# Frontend loads from frontend/.env.development automatically
npm run dev
# VITE v5.4.21 ready in 500ms
# [Loads .env.development with VITE_ variables]
```

---

## Production Deployment

### Vercel (Frontend)

**Option 1: Using Environment Dashboard (Recommended for Secrets)**

1. Go to Vercel Dashboard → Project Settings → Environment Variables
2. Add variables:
   ```
   VITE_API_BASE_URL = https://api.cryptovault.com
   VITE_SENTRY_DSN = https://...
   VITE_ENABLE_SENTRY = true
   ```
3. These override .env.production at build time

**Option 2: Using .env.production File**

1. Create `.env.production` in frontend directory
2. Add sensitive variables
3. Vercel automatically loads from .env files during build
4. ⚠️ Never commit this file (already in .gitignore)

### Render (Backend)

**Environment Variables in Render Dashboard**

1. Go to Render Dashboard → Services → Backend
2. Click "Environment" tab
3. Add variables:
   ```
   ENVIRONMENT=production
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   JWT_SECRET=...
   CORS_ORIGINS=https://cryptovault.com,https://www.cryptovault.com
   SENTRY_DSN=https://...
   ```

**Or using .env File (For Self-Hosted)**

```bash
# Create production .env on server
nano /app/backend/.env

# Populate with production values
ENVIRONMENT=production
DATABASE_URL=postgresql://prod-user:password@prod-host:5432/cryptovault
# ... etc

# Restart backend service
systemctl restart cryptovault-backend
```

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.11

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .

# Load .env from environment variables passed to container
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Run with environment variables
docker run \
  -e DATABASE_URL="postgresql://..." \
  -e REDIS_URL="redis://..." \
  -e JWT_SECRET="..." \
  -e ENVIRONMENT="production" \
  cryptovault-backend
```

---

## Troubleshooting

### Issue: "Missing required environment variables"

**Cause:** .env file not found or not loaded

**Solution:**
```bash
# Check if .env file exists
ls -la backend/.env
ls -la frontend/.env.development

# Test environment loading
python -m backend.config

# Verify file permissions
chmod 644 backend/.env
```

### Issue: Variables show as undefined in code

**Frontend:**
```bash
# Check that variable starts with VITE_
echo $VITE_API_BASE_URL  # Should show value

# Restart dev server after changing .env
npm run dev

# Clear cache if needed
rm -rf node_modules/.vite
npm run dev
```

**Backend:**
```python
# Test loading
from config import settings
print(settings.DATABASE_URL)  # Should show actual value
print(settings.ENVIRONMENT)   # Should show environment
```

### Issue: Production shows different values than development

**Check which .env file is loaded:**

Frontend:
```bash
# In package.json, check build script
"build": "vite build"  # Uses .env.production

# Or explicitly specify
"build": "vite build --mode production"  # Uses .env.production
```

Backend:
```bash
# Check ENVIRONMENT variable
echo $ENVIRONMENT  # Should be "production"

# Verify settings
python -m backend.config
```

---

## Security Best Practices

### ✅ DO

- ✅ Add `.env` to `.gitignore` (already done)
- ✅ Commit `.env.example` with placeholder values
- ✅ Use strong secrets (JWT_SECRET, CSRF_SECRET)
- ✅ Rotate secrets regularly
- ✅ Use different secrets for dev/staging/production
- ✅ Never log or expose secrets
- ✅ Use environment variables for all sensitive data

### ❌ DON'T

- ❌ Commit `.env` files to git
- ❌ Check secrets into version control
- ❌ Share `.env` files via email/chat
- ❌ Use same secrets across environments
- ❌ Hardcode secrets in source code
- ❌ Print secrets in logs
- ❌ Make `.env` world-readable (chmod 644)

---

## Verification Checklist

### Backend

- [ ] `backend/.env` file created from `.env.example`
- [ ] All required variables populated with actual values
- [ ] `python -m backend.config` runs without errors
- [ ] `ENVIRONMENT=development` for local dev
- [ ] `JWT_SECRET` is unique and strong
- [ ] `DATABASE_URL` points to correct database
- [ ] `REDIS_URL` is valid
- [ ] File is in `.gitignore`
- [ ] `backend/config.py` imports work in FastAPI app

### Frontend

- [ ] `frontend/.env.development` created
- [ ] `frontend/.env.production` created
- [ ] `VITE_API_BASE_URL` set correctly for environment
- [ ] `VITE_APP_NAME` is correct
- [ ] `VITE_SENTRY_DSN` set for production only
- [ ] `npm run dev` loads variables correctly
- [ ] `npm run build` loads production variables
- [ ] Files are in `.gitignore`
- [ ] `import.meta.env` variables accessible in code

### Deployment

- [ ] Environment variables set in Vercel dashboard (frontend)
- [ ] Environment variables set in Render dashboard (backend)
- [ ] Production `.env` file created on production server
- [ ] Variables test correctly in production
- [ ] Sensitive values are not exposed in logs

---

## Reference Commands

```bash
# Backend
cd backend
cp .env.example .env
nano .env  # Edit values
python -m config  # Test loading
python -m uvicorn main:app --reload

# Frontend
cd frontend
cp .env.example .env.development
cp .env.example .env.production
npm run dev  # Uses .env.development
npm run build  # Uses .env.production

# Git
git status  # Check that .env files are NOT listed
git ls-files | grep .env  # Should only show .env.example
```

---

## Next Steps

1. **Setup:** Follow the Backend and Frontend setup sections above
2. **Verify:** Run the verification checklist
3. **Test:** Run `npm run dev` and `python -m uvicorn main:app --reload`
4. **Deploy:** Use Vercel + Render with environment variables set in dashboards
5. **Monitor:** Check Sentry and logs for any configuration issues

---

**Questions?** See the Troubleshooting section or check official documentation:
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-modes.html)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
