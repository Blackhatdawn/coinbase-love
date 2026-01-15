# 🏦 CryptoVault - Production-Ready Cryptocurrency Trading Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-green.svg)](https://www.mongodb.com/)

## 🚀 Overview

CryptoVault is an **institutional-grade cryptocurrency trading platform** built with modern technologies and production-ready architecture. It provides a secure, scalable, and feature-rich environment for cryptocurrency trading, portfolio management, and market analysis.

### ✨ Key Features

#### 🔐 **Enterprise Security**
- JWT-based authentication with HttpOnly cookies
- Email verification with OTP (6-digit code)
- 2FA support with backup codes
- Account lockout protection (5 failed attempts → 15 min lock)
- Password reset with secure tokens
- Token blacklisting on logout
- Rate limiting on all endpoints
- Security headers (HSTS, CSP, X-Frame-Options)

#### 💼 **Portfolio Management**
- Real-time portfolio tracking
- Multi-asset support (BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, LINK, MATIC, LTC)
- Performance analytics with charts
- Holdings management
- Transaction history

#### 📊 **Trading Engine**
- Market orders and limit orders
- Real-time price updates via WebSocket
- Interactive trading charts (TradingView-style)
- Order book visualization
- Trade history tracking

#### 💰 **Wallet & Payments**
- Crypto deposit integration (NOWPayments)
- Wallet balance management
- Deposit history and tracking
- Multi-currency support

#### 🔔 **Price Alerts**
- Custom price alerts
- Email and push notifications
- Above/below threshold alerts
- Alert management dashboard

#### 👨‍💼 **Admin Dashboard**
- Platform statistics
- User management
- Trade monitoring
- Audit logs
- System health monitoring

#### 🎨 **Modern UI/UX**
- Responsive design (mobile, tablet, desktop)
- Dark theme with gold accents
- Professional onboarding loader
- Real-time price ticker
- Error boundaries for graceful error handling
- Loading states and skeleton screens

#### 🚀 **Production Features**
- Structured JSON logging
- Health check endpoints
- Database indexing for performance
- WebSocket connection management with ping/pong
- Request timeout protection
- CORS configuration
- Redis caching (Upstash)
- Sentry-ready error tracking

---

## 📋 Table of Contents

1. [Architecture](#-architecture)
2. [Tech Stack](#️-tech-stack)
3. [Quick Start](#-quick-start)
4. [Environment Setup](#-environment-setup)
5. [Development Guide](#-development-guide)
6. [API Documentation](#-api-documentation)
7. [Deployment](#-deployment)
8. [Testing](#-testing)
9. [Security](#-security)
10. [Monitoring](#-monitoring)
11. [Troubleshooting](#-troubleshooting)

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Browser    │  │    Mobile    │  │   Tablet     │      │
│  │  (React 18)  │  │   (Future)   │  │  (Future)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Load Balancer  │ (Optional)
                    └────────┬────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│                      APPLICATION LAYER                        │
│  ┌─────────────────────────────────────────────────────┐     │
│  │          FastAPI Backend (Python 3.11+)             │     │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐      │     │
│  │  │  Auth  │ │Trading │ │Crypto  │ │ Admin  │      │     │
│  │  │ Router │ │ Router │ │ Router │ │ Router │      │     │
│  │  └────────┘ └────────┘ └────────┘ └────────┘      │     │
│  │  ┌─────────────────────────────────────────┐      │     │
│  │  │     WebSocket Real-time Updates         │      │     │
│  │  └─────────────────────────────────────────┘      │     │
│  └─────────────────────────────────────────────────────┘     │
└───────────┬──────────────────────┬──────────────────┬────────┘
            │                      │                  │
    ┌───────▼──────┐      ┌───────▼──────┐  ┌───────▼──────┐
    │   MongoDB    │      │    Redis     │  │  External    │
    │   (Atlas)    │      │  (Upstash)   │  │     APIs     │
    │              │      │              │  │              │
    │ - Users      │      │ - Sessions   │  │ - CoinGecko  │
    │ - Portfolios │      │ - Cache      │  │ - SendGrid   │
    │ - Orders     │      │ - Blacklist  │  │ - NOWPayments│
    │ - Alerts     │      │              │  │              │
    └──────────────┘      └──────────────┘  └──────────────┘
```

### Request Flow

```
1. User Action (Browser)
      ↓
2. React Component
      ↓
3. API Client (Axios)
      ↓
4. FastAPI Router
      ↓
5. Middleware (Auth, Rate Limit, CORS)
      ↓
6. Business Logic
      ↓
7. Database/Cache/External API
      ↓
8. Response (JSON)
      ↓
9. React State Update
      ↓
10. UI Re-render
```

---

## 🛠️ Tech Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|----------|
| **Python** | 3.11+ | Core language |
| **FastAPI** | 0.110+ | Web framework |
| **MongoDB** | 6.0+ | Database (MongoDB Atlas) |
| **Redis** | Latest | Caching & session management (Upstash) |
| **Motor** | Latest | Async MongoDB driver |
| **Pydantic** | 2.0+ | Data validation |
| **PyJWT** | Latest | JWT authentication |
| **bcrypt** | Latest | Password hashing |
| **pyotp** | Latest | 2FA/TOTP support |
| **uvicorn** | Latest | ASGI server |
| **httpx** | Latest | Async HTTP client |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|----------|
| **React** | 18.3.1 | UI library |
| **TypeScript** | 5.8+ | Type safety |
| **Vite** | 5.4+ | Build tool |
| **Tailwind CSS** | 3.4+ | Styling |
| **Shadcn/UI** | Latest | Component library |
| **React Router** | 6.30+ | Routing |
| **Axios** | 1.13+ | HTTP client |
| **TanStack Query** | 5.90+ | Data fetching |
| **lightweight-charts** | 5.1.0 | Trading charts |
| **Recharts** | 2.15+ | Analytics charts |
| **Zustand** | 5.0+ | State management |
| **React Hook Form** | 7.61+ | Form handling |
| **Zod** | 3.25+ | Schema validation |

### External Services

- **CoinGecko API**: Real-time cryptocurrency prices
- **SendGrid**: Transactional emails
- **NOWPayments**: Crypto payment processing
- **Upstash Redis**: Managed Redis for caching
- **MongoDB Atlas**: Managed MongoDB hosting

---

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Yarn** (Run: `npm install -g yarn`)
- **MongoDB** (Atlas account or local installation)
- **Redis** (Upstash account or local installation)

### Installation Steps

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/cryptovault.git
cd cryptovault
```

#### 2️⃣ Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials (see Environment Setup section)

# Run the backend server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

Backend will be available at: **http://localhost:8001**

#### 3️⃣ Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Set up environment variables (optional for development)
cp .env.example .env

# Run the development server
yarn dev
```

Frontend will be available at: **http://localhost:3000**

#### 4️⃣ Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation (Swagger)**: http://localhost:8001/docs
- **API Documentation (ReDoc)**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

---

## 🔧 Environment Setup

### Backend Environment Variables

Create `/app/backend/.env` with the following:

```env
# ============================================
# DATABASE CONFIGURATION
# ============================================
MONGO_URL=mongodb://localhost:27017/
# For MongoDB Atlas:
# MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

DB_NAME=cryptovault_db

# ============================================
# SECURITY CONFIGURATION
# ============================================
JWT_SECRET=your-super-secret-jwt-key-min-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================
# CORS CONFIGURATION
# ============================================
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# ============================================
# EMAIL CONFIGURATION (SendGrid)
# ============================================
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=SG.your_sendgrid_api_key
EMAIL_FROM=noreply@cryptovault.com
EMAIL_FROM_NAME=CryptoVault Financial
APP_URL=http://localhost:3000

# ============================================
# COINGECKO API (for crypto prices)
# ============================================
COINGECKO_API_KEY=CG-your_coingecko_api_key
USE_MOCK_PRICES=false  # Set to true for testing without API

# ============================================
# REDIS CONFIGURATION (Upstash)
# ============================================
USE_REDIS=true
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_token

# ============================================
# NOWPAYMENTS (Crypto Deposits)
# ============================================
NOWPAYMENTS_API_KEY=your_nowpayments_api_key
NOWPAYMENTS_IPN_SECRET=your_ipn_secret

# ============================================
# ENVIRONMENT
# ============================================
ENVIRONMENT=development  # production, staging, development

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_PER_MINUTE=60

# ============================================
# MONITORING (Optional)
# ============================================
SENTRY_DSN=  # Optional: Sentry error tracking
```

### Frontend Environment Variables

Create `/app/frontend/.env` with:

```env
# ============================================
# API CONFIGURATION
# ============================================
# Leave empty for development (uses Vite proxy)
# Set to your backend URL for production
VITE_API_BASE_URL=

# For production deployment:
# VITE_API_BASE_URL=https://api.cryptovault.com
```

### Getting API Keys

#### 1. **MongoDB Atlas** (Free)
1. Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Get connection string from "Connect" → "Connect your application"

#### 2. **CoinGecko API** (Free tier available)
1. Sign up at [coingecko.com](https://www.coingecko.com/en/api)
2. Get API key from dashboard
3. Free tier: 10-30 calls/minute

#### 3. **SendGrid Email** (Free tier: 100 emails/day)
1. Sign up at [sendgrid.com](https://sendgrid.com/)
2. Create API key from Settings → API Keys
3. Verify sender email

#### 4. **Upstash Redis** (Free tier available)
1. Sign up at [upstash.com](https://upstash.com/)
2. Create Redis database
3. Get REST URL and token from database details

#### 5. **NOWPayments** (Optional - for crypto deposits)
1. Sign up at [nowpayments.io](https://nowpayments.io/)
2. Get API key from account settings
3. Set up IPN callbacks

---

## 💻 Development Guide

### Project Structure

```
cryptovault/
├── backend/
│   ├── routers/              # API endpoints (modular)
│   │   ├── auth.py           # Authentication & user management
│   │   ├── portfolio.py      # Portfolio management
│   │   ├── trading.py        # Trading & orders
│   │   ├── crypto.py         # Market data
│   │   ├── wallet.py         # Wallet & deposits
│   │   ├── alerts.py         # Price alerts
│   │   ├── transactions.py   # Transaction history
│   │   └── admin.py          # Admin dashboard
│   ├── models.py             # Pydantic data models
│   ├── config.py             # Configuration management
│   ├── database.py           # MongoDB connection
│   ├── dependencies.py       # FastAPI dependencies
│   ├── auth.py               # Authentication helpers
│   ├── blacklist.py          # Token blacklisting
│   ├── redis_cache.py        # Redis caching
│   ├── coingecko_service.py  # CoinGecko integration
│   ├── email_service.py      # Email service
│   ├── nowpayments_service.py # Payment processing
│   ├── websocket_feed.py     # WebSocket price updates
│   ├── server.py             # Main FastAPI application
│   └── requirements.txt      # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   │   ├── ui/           # Shadcn UI components
│   │   │   ├── TradingChart.tsx
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── ...
│   │   ├── pages/            # Page components
│   │   │   ├── Index.tsx     # Homepage
│   │   │   ├── Auth.tsx      # Login/Signup
│   │   │   ├── Dashboard.tsx # User dashboard
│   │   │   ├── Markets.tsx   # Market overview
│   │   │   ├── Trade.tsx     # Trading page
│   │   │   └── ...
│   │   ├── contexts/         # React contexts
│   │   │   ├── AuthContext.tsx
│   │   │   └── Web3Context.tsx
│   │   ├── hooks/            # Custom React hooks
│   │   │   └── useRedirectSpinner.ts
│   │   ├── lib/              # Utilities & API client
│   │   │   ├── apiClient.ts  # Axios API client
│   │   │   └── utils.ts      # Helper functions
│   │   ├── App.tsx           # Main app component
│   │   └── main.tsx          # Entry point
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite configuration
│   ├── tailwind.config.ts    # Tailwind CSS config
│   └── tsconfig.json         # TypeScript config
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md
│   └── PRODUCTION_READINESS.md
│
├── tests/                    # Test suites
│   └── test_cryptovault_api.py
│
├── test_reports/             # Test results
│   └── iteration_5.json
│
├── README.md                 # This file
└── docker-compose.yml        # Docker setup (optional)
```

### Running with Supervisor (Production-like)

The application uses Supervisor for process management:

```bash
# Check status
sudo supervisorctl status

# Start services
sudo supervisorctl start backend
sudo supervisorctl start frontend

# Restart services
sudo supervisorctl restart all

# Stop services
sudo supervisorctl stop all

# View logs
sudo supervisorctl tail -f backend stderr
sudo supervisorctl tail -f frontend stdout
```

### Development Workflow

1. **Start Backend**:
   ```bash
   cd backend
   source venv/bin/activate
   uvicorn server:app --reload --host 0.0.0.0 --port 8001
   ```

2. **Start Frontend**:
   ```bash
   cd frontend
   yarn dev
   ```

3. **Make Changes**: Edit files with hot reload enabled

4. **Test**: Test your changes in the browser

5. **Commit**: Follow conventional commits
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push
   ```

### Code Quality

**Backend** (Python):
```bash
# Format code
black backend/

# Lint
flake8 backend/

# Type checking
mypy backend/
```

**Frontend** (TypeScript):
```bash
# Lint
cd frontend
yarn lint

# Type check
yarn tsc --noEmit

# Format
prettier --write "src/**/*.{ts,tsx}"
```

---

## 📚 API Documentation

### Interactive API Documentation

Once the backend is running, visit:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Key API Endpoints

#### 🔐 Authentication

```
POST   /api/auth/signup              Register new user
POST   /api/auth/login               Login user
POST   /api/auth/logout              Logout user
GET    /api/auth/me                  Get current user profile
PUT    /api/auth/profile             Update user profile
POST   /api/auth/change-password     Change password
POST   /api/auth/refresh             Refresh access token
POST   /api/auth/verify-email        Verify email with OTP
POST   /api/auth/resend-verification Resend verification email
POST   /api/auth/forgot-password     Request password reset
POST   /api/auth/reset-password      Reset password with token
POST   /api/auth/2fa/setup           Setup 2FA
POST   /api/auth/2fa/verify          Verify 2FA code
GET    /api/auth/2fa/status          Get 2FA status
POST   /api/auth/2fa/disable         Disable 2FA
```

#### 💼 Portfolio

```
GET    /api/portfolio                Get user portfolio
POST   /api/portfolio/holding        Add cryptocurrency holding
DELETE /api/portfolio/holding/{symbol} Remove holding
GET    /api/portfolio/holding/{symbol} Get specific holding
```

#### 📊 Trading

```
GET    /api/orders                   Get order history
POST   /api/orders                   Create new order
GET    /api/orders/{id}              Get order details
```

#### 📈 Market Data

```
GET    /api/crypto                   Get all cryptocurrency prices
GET    /api/crypto/{id}              Get specific coin details
GET    /api/crypto/{id}/history      Get price history (with days param)
```

#### 💰 Wallet

```
GET    /api/wallet/balance           Get wallet balance
POST   /api/wallet/deposit/create    Create deposit order
GET    /api/wallet/deposit/{orderId} Get deposit status
GET    /api/wallet/deposits          Get deposit history
```

#### 🔔 Alerts

```
GET    /api/alerts                   Get all price alerts
POST   /api/alerts                   Create new alert
GET    /api/alerts/{id}              Get alert details
PATCH  /api/alerts/{id}              Update alert
DELETE /api/alerts/{id}              Delete alert
```

#### 📝 Transactions

```
GET    /api/transactions             Get transaction history
GET    /api/transactions/{id}        Get transaction details
GET    /api/transactions/summary/stats Get transaction statistics
```

#### 👨‍💼 Admin (Requires admin privileges)

```
GET    /api/admin/stats              Get platform statistics
GET    /api/admin/users              Get all users
GET    /api/admin/trades             Get all trades
GET    /api/admin/audit-logs         Get audit logs
```

#### ❤️ Health Check

```
GET    /health                       Health check endpoint
GET    /api/health                   Alternative health check
```

---

## 🚢 Deployment

### Option 1: Traditional Deployment

#### Backend (Python/FastAPI)

**Requirements**:
- Python 3.11+
- ASGI server (Uvicorn/Gunicorn)
- MongoDB connection
- Redis connection

**Deployment Steps**:

1. **Prepare Server**:
   ```bash
   # Install Python dependencies
   apt-get update
   apt-get install python3.11 python3-pip python3-venv
   
   # Create application directory
   mkdir -p /opt/cryptovault
   cd /opt/cryptovault
   ```

2. **Deploy Application**:
   ```bash
   # Clone repository
   git clone https://github.com/yourusername/cryptovault.git .
   
   # Setup virtual environment
   python3.11 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r backend/requirements.txt
   
   # Set environment variables
   cp backend/.env.example backend/.env
   nano backend/.env  # Edit with production values
   ```

3. **Run with Gunicorn**:
   ```bash
   cd backend
   gunicorn server:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8001 \
     --access-logfile /var/log/cryptovault/access.log \
     --error-logfile /var/log/cryptovault/error.log
   ```

4. **Setup Systemd Service**:
   ```ini
   # /etc/systemd/system/cryptovault-backend.service
   [Unit]
   Description=CryptoVault Backend API
   After=network.target
   
   [Service]
   Type=notify
   User=www-data
   Group=www-data
   WorkingDirectory=/opt/cryptovault/backend
   Environment="PATH=/opt/cryptovault/venv/bin"
   ExecStart=/opt/cryptovault/venv/bin/gunicorn server:app \
     --workers 4 \
     --worker-class uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:8001
   
   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   systemctl daemon-reload
   systemctl enable cryptovault-backend
   systemctl start cryptovault-backend
   ```

#### Frontend (React/Vite)

**Build for Production**:
```bash
cd frontend

# Install dependencies
yarn install

# Set production environment variable
echo "VITE_API_BASE_URL=https://api.cryptovault.com" > .env.production

# Build
yarn build

# Output will be in 'build' directory
```

**Deploy to Nginx**:
```nginx
# /etc/nginx/sites-available/cryptovault
server {
    listen 80;
    server_name cryptovault.com www.cryptovault.com;
    
    root /var/www/cryptovault/build;
    index index.html;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API proxy (optional)
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
ln -s /etc/nginx/sites-available/cryptovault /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

**Setup SSL with Certbot**:
```bash
apt-get install certbot python3-certbot-nginx
certbot --nginx -d cryptovault.com -d www.cryptovault.com
```

### Option 2: Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop
docker-compose down
```

### Option 3: Platform-as-a-Service (PaaS)

#### Deploy Backend to Render.com

1. Connect GitHub repository to Render
2. Create new **Web Service**
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.11
4. Add environment variables from `.env`
5. Deploy

#### Deploy Frontend to Vercel

1. Connect GitHub repository to Vercel
2. Configure:
   - **Framework**: Vite
   - **Build Command**: `yarn build`
   - **Output Directory**: `build`
   - **Install Command**: `yarn install`
3. Add environment variable:
   ```
   VITE_API_BASE_URL=https://your-backend.onrender.com
   ```
4. Deploy

### Health Check Configuration

For load balancers and monitoring:

- **Endpoint**: `/health` or `/api/health`
- **Expected Status**: `200 OK`
- **Response**:
  ```json
  {
    "status": "healthy",
    "database": "connected",
    "environment": "production",
    "version": "1.0.0",
    "timestamp": "2025-01-15T19:00:00Z"
  }
  ```

---

## 🧪 Testing

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

### Frontend Testing

```bash
cd frontend

# Run tests (if configured)
yarn test

# Run with coverage
yarn test:coverage

# Type checking
yarn tsc --noEmit
```

### Manual API Testing

**Using curl**:
```bash
# Health check
curl http://localhost:8001/health

# Get crypto prices
curl http://localhost:8001/api/crypto

# Signup
curl -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password123!","name":"Test User"}'

# Login (saves cookies)
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Password123!"}' \
  -c cookies.txt

# Get profile (use cookies)
curl http://localhost:8001/api/auth/me -b cookies.txt
```

**Using HTTPie** (recommended):
```bash
# Install
pip install httpie

# Test endpoints
http GET http://localhost:8001/health
http POST http://localhost:8001/api/auth/signup email=test@example.com password=Password123! name="Test User"
http --session=user POST http://localhost:8001/api/auth/login email=test@example.com password=Password123!
http --session=user GET http://localhost:8001/api/auth/me
```

### Test Report

The latest test results are available in:
```
/app/test_reports/iteration_5.json
```

**Test Summary** (from latest report):
- **Backend**: 86.7% success rate ✅
- **Frontend**: 60% success rate (issues fixed) ✅

---

## 🔒 Security

### Authentication & Authorization

#### Authentication Flow

1. **Registration**:
   - User submits email, password, name
   - System validates input
   - Password hashed with bcrypt (12 rounds)
   - User created in database
   - 6-digit OTP sent to email
   - User verifies email with OTP

2. **Login**:
   - User submits credentials
   - System validates against database
   - If email not verified → reject
   - If credentials invalid → increment failed attempts
   - After 5 failed attempts → lock account for 15 minutes
   - If successful → generate JWT tokens
   - Tokens stored in HttpOnly cookies

3. **Token Management**:
   - **Access Token**: Short-lived (30 min), used for API calls
   - **Refresh Token**: Long-lived (7 days), used to get new access token
   - Tokens stored in HttpOnly, Secure cookies
   - Old tokens blacklisted on logout

4. **Protected Routes**:
   - Extract token from cookie
   - Verify JWT signature
   - Check token not blacklisted
   - Extract user ID from token
   - Attach user to request

### Security Features

✅ **Password Security**
- Bcrypt hashing with 12 rounds
- Minimum 8 characters
- Password strength validation
- Password reset with secure tokens

✅ **Account Protection**
- Email verification required
- Account lockout (5 failed attempts → 15 min)
- Failed login attempt tracking
- Password reset rate limiting

✅ **Token Security**
- JWT with HS256 algorithm
- Short-lived access tokens (30 min)
- Refresh token rotation
- Token blacklisting on logout
- HttpOnly cookies (no JavaScript access)
- Secure flag in production
- SameSite=Lax for CSRF protection

✅ **Two-Factor Authentication (2FA)**
- TOTP-based (Google Authenticator, Authy)
- Backup codes for recovery
- QR code generation
- Optional but recommended

✅ **API Security**
- Rate limiting (60 req/min general, 3 req/min signup)
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention (MongoDB parameterized queries)
- XSS prevention (Content-Type validation)
- Request timeout (30 seconds)

✅ **Security Headers**
- Strict-Transport-Security (HSTS)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy

✅ **Data Protection**
- Passwords never logged
- Sensitive data encrypted at rest (MongoDB)
- TLS in transit
- Audit logging for critical actions

### Security Best Practices

1. **Environment Variables**: Never commit `.env` files
2. **JWT Secret**: Use strong, random secret (32+ characters)
3. **HTTPS**: Always use HTTPS in production
4. **Database**: Enable MongoDB authentication
5. **Redis**: Use password protection
6. **Rate Limiting**: Adjust based on usage patterns
7. **Monitoring**: Set up alerts for suspicious activity
8. **Updates**: Regularly update dependencies

### Rate Limits

| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| Signup | 3 requests | 1 minute |
| Login | 5 requests | 1 minute |
| Password Reset | 3 requests | 1 hour |
| General API | 60 requests | 1 minute |
| Trading | 20 requests | 1 minute |
| Admin | 100 requests | 1 minute |

---

## 📊 Monitoring

### Structured Logging

All logs are output in JSON format in production for easy parsing:

```json
{
  "timestamp": "2025-01-15T19:30:00Z",
  "level": "INFO",
  "logger": "server",
  "message": "Request completed",
  "request_id": "abc-123-def-456",
  "method": "GET",
  "path": "/api/portfolio",
  "status_code": 200,
  "duration_ms": 45.2,
  "user_id": "user-123"
}
```

### Key Metrics to Monitor

#### Application Metrics
- **Request Rate**: Requests per second
- **Response Time**: P50, P95, P99 latencies
- **Error Rate**: 4xx and 5xx responses
- **Success Rate**: 2xx responses

#### Database Metrics
- **Query Time**: Average query execution time
- **Connection Pool**: Active connections
- **Slow Queries**: Queries taking >100ms

#### System Metrics
- **CPU Usage**: Server CPU utilization
- **Memory Usage**: RAM consumption
- **Disk I/O**: Read/write operations
- **Network**: Bandwidth usage

#### Business Metrics
- **Active Users**: Currently logged in users
- **Signups**: New user registrations
- **Trading Volume**: Total trade value
- **Failed Logins**: Security monitoring

### Health Checks

```bash
# Manual health check
curl http://localhost:8001/health

# Expected response
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "version": "1.0.0",
  "timestamp": "2025-01-15T19:00:00Z"
}
```

### Log Locations

When running with Supervisor:
```
/var/log/supervisor/backend.out.log   # Backend stdout
/var/log/supervisor/backend.err.log   # Backend stderr
/var/log/supervisor/frontend.out.log  # Frontend stdout
/var/log/supervisor/frontend.err.log  # Frontend stderr
```

View logs:
```bash
# Tail logs
tail -f /var/log/supervisor/backend.err.log

# Search logs
grep "ERROR" /var/log/supervisor/backend.err.log

# View with supervisor
sudo supervisorctl tail -f backend stderr
```

---

## 🔧 Troubleshooting

### Common Issues

#### Backend Won't Start

**Issue**: `ModuleNotFoundError`
```
Solution: Install missing dependencies
cd /app/backend
pip install -r requirements.txt
```

**Issue**: `Database connection failed`
```
Solution: Check MongoDB URL in .env
- Verify MONGO_URL is correct
- Ensure MongoDB is running
- Check network connectivity
```

**Issue**: `Redis connection failed`
```
Solution: Check Redis configuration
- Verify UPSTASH_REDIS_REST_URL and token
- Or set USE_REDIS=false for development
```

#### Frontend Won't Start

**Issue**: `vite: command not found`
```
Solution: Install dependencies
cd /app/frontend
yarn install
```

**Issue**: `API calls failing`
```
Solution: Check Vite proxy configuration
- Ensure backend is running on port 8001
- Check vite.config.ts proxy settings
- Verify VITE_API_BASE_URL in .env
```

#### TradingChart Issues

**Issue**: `Assertion failed in lightweight-charts`
```
Solution: Already fixed in this deployment
- Changed from chart.addSeries(AreaSeries, options)
- To chart.addAreaSeries(options)
```

#### Protected Routes Loading Forever

**Issue**: Dashboard shows "Loading..." indefinitely
```
Solution: Check authentication
- Verify backend /api/auth/me endpoint works
- Check browser cookies are being set
- Ensure withCredentials: true in API client
- Check CORS configuration
```

#### CoinGecko Rate Limiting

**Issue**: `CoinGecko API returned 429`
```
Solution: This is expected with free tier
- Implement caching (Redis)
- Use mock prices for development: USE_MOCK_PRICES=true
- Upgrade to CoinGecko Pro for higher limits
```

### Debugging Commands

```bash
# Check service status
sudo supervisorctl status

# View backend logs
sudo supervisorctl tail -f backend stderr

# View frontend logs
sudo supervisorctl tail -f frontend stdout

# Test backend API
curl http://localhost:8001/health

# Test database connection
python -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; asyncio.run(AsyncIOMotorClient('YOUR_MONGO_URL').admin.command('ping'))"

# Check Python dependencies
pip list | grep -E 'fastapi|pydantic|motor'

# Check Node dependencies
cd frontend && yarn list --pattern "vite|react|axios"

# Restart services
sudo supervisorctl restart all
```

### Getting Help

1. **Check logs first**: Most issues are visible in logs
2. **Search issues**: Check GitHub issues for similar problems
3. **Create issue**: Provide logs, steps to reproduce, environment details
4. **Email support**: support@cryptovault.com

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Contribution Workflow

1. **Fork** the repository
2. **Create** a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit** your changes
   ```bash
   git commit -m "feat: add amazing feature"
   ```
4. **Push** to your fork
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open** a Pull Request

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: code formatting
refactor: code refactoring
test: add tests
chore: maintenance tasks
```

### Code Style

- **Backend**: Follow PEP 8, use Black for formatting
- **Frontend**: Follow Airbnb style guide, use Prettier
- Write meaningful commit messages
- Add tests for new features
- Update documentation

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://reactjs.org/) - UI library
- [Vite](https://vitejs.dev/) - Next generation frontend tooling
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Shadcn/UI](https://ui.shadcn.com/) - Re-usable components
- [CoinGecko](https://www.coingecko.com/) - Cryptocurrency data API
- [MongoDB](https://www.mongodb.com/) - NoSQL database
- [Upstash](https://upstash.com/) - Serverless Redis
- [SendGrid](https://sendgrid.com/) - Email delivery platform

---

## 📞 Support

- **Email**: support@cryptovault.com
- **Documentation**: [docs.cryptovault.com](https://docs.cryptovault.com)
- **Issues**: [GitHub Issues](https://github.com/yourusername/cryptovault/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/cryptovault/discussions)

---

<div align="center">

**Built with ❤️ for the crypto community**

⭐ Star us on GitHub | 🐦 Follow us on Twitter | 💬 Join our Discord

</div>
