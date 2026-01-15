# CryptoVault - Production-Ready Cryptocurrency Trading Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

## 🚀 Overview

CryptoVault is an institutional-grade cryptocurrency trading platform featuring:

- **Secure Authentication**: JWT-based with email OTP verification
- **Real-time Data**: Live cryptocurrency prices via CoinGecko API
- **Portfolio Management**: Track holdings with real-time valuations
- **Trading Engine**: Buy/sell functionality with order history
- **Admin Dashboard**: Platform monitoring and user management
- **Production-Ready**: Structured logging, error tracking, rate limiting

## 📋 Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Development](#development)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Security](#security)
- [Contributing](#contributing)

## 🏗️ Architecture

```
CryptoVault/
├── backend/           # FastAPI application
│   ├── routers/       # Modular API endpoints
│   ├── services/      # Business logic
│   └── models/        # Pydantic models
├── frontend/          # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── lib/
├── docs/              # Documentation
└── tests/             # Test suites
```

### System Architecture

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Browser   │─────▶│   Vercel    │─────▶│   Backend   │
│  (React)    │      │  (Frontend) │      │   (Render)  │
└─────────────┘      └─────────────┘      └──────┬──────┘
                                                  │
                     ┌────────────────────────────┼────────────┐
                     │                            │            │
              ┌──────▼──────┐            ┌───────▼──────┐ ┌──▼────┐
              │   MongoDB   │            │    Redis     │ │SendGrid│
              │   (Atlas)   │            │  (Upstash)   │ └────────┘
              └─────────────┘            └──────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI 0.110+
- **Database**: MongoDB Atlas
- **Cache**: Redis (Upstash)
- **Authentication**: JWT + bcrypt
- **Email**: SendGrid
- **API Integration**: CoinGecko

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS + Shadcn/UI
- **State Management**: React Context + Zustand
- **Charts**: lightweight-charts, Chart.js
- **HTTP Client**: Axios

### DevOps
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Render
- **CI/CD**: GitHub Actions
- **Monitoring**: Structured logging, Sentry-ready

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Redis (local or Upstash)

### Backend Setup

```bash
# Clone repository
git clone https://github.com/yourusername/cryptovault.git
cd cryptovault/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Run development server
uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Copy environment file
cp .env.example .env
# Edit .env if needed (Vite proxy is configured)

# Run development server
yarn dev
```

### Using Docker

```bash
# Build and run
docker-compose up --build

# Access:
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
# API Docs: http://localhost:8001/docs
```

## 🔐 Environment Variables

### Backend (.env)

```env
# Database
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=cryptovault_db

# Security
JWT_SECRET=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Email (SendGrid)
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=SG.xxx
EMAIL_FROM=noreply@cryptovault.com
APP_URL=http://localhost:3000

# CoinGecko
COINGECKO_API_KEY=CG-xxx
USE_MOCK_PRICES=false

# Redis (Upstash)
USE_REDIS=true
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=xxx

# Environment
ENVIRONMENT=development  # or production
```

### Frontend (.env)

```env
# API Configuration
VITE_API_BASE_URL=  # Leave empty for proxy in dev, set for production
```

## 💻 Development

### Project Structure

```
backend/
├── routers/           # API endpoints (modular)
│   ├── auth.py        # Authentication endpoints
│   ├── portfolio.py   # Portfolio management
│   ├── trading.py     # Trading & orders
│   ├── crypto.py      # Market data
│   └── admin.py       # Admin dashboard
├── services/          # Business logic
│   ├── email_service.py
│   ├── coingecko_service.py
│   └── redis_cache.py
├── models.py          # Pydantic models
├── config.py          # Configuration
├── dependencies.py    # FastAPI dependencies
├── auth.py            # Authentication helpers
└── server.py          # Main application

frontend/
├── src/
│   ├── components/    # React components
│   ├── pages/         # Page components
│   ├── contexts/      # React contexts
│   ├── hooks/         # Custom hooks
│   ├── lib/           # Utilities
│   │   ├── apiClient.ts  # API client
│   │   └── utils.ts      # Helper functions
│   └── App.tsx        # Main app component
└── public/            # Static assets
```

### Code Style

**Backend**:
```bash
# Format code
black backend/

# Lint
flake8 backend/

# Type checking
mypy backend/
```

**Frontend**:
```bash
# Lint
yarn lint

# Format
yarn prettier --write "src/**/*.{ts,tsx}"
```

### Database Indexes

The following indexes are automatically created on startup:

```javascript
// users
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ last_login: 1 })

// portfolios
db.portfolios.createIndex({ user_id: 1 }, { unique: true })

// orders
db.orders.createIndex({ user_id: 1 })
db.orders.createIndex({ created_at: 1 })

// audit_logs
db.audit_logs.createIndex({ user_id: 1 })
db.audit_logs.createIndex({ action: 1 })
db.audit_logs.createIndex({ timestamp: 1 })

// TTL indexes
db.login_attempts.createIndex({ timestamp: 1 }, { expireAfterSeconds: 2592000 })
db.blacklisted_tokens.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })
```

## 🚢 Deployment

### Vercel (Frontend)

1. Connect GitHub repository to Vercel
2. Set environment variables:
   ```
   VITE_API_BASE_URL=https://api.cryptovault.com
   ```
3. Deploy automatically on push to `main`

### Render (Backend)

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`
6. Enable auto-deploy from `main` branch

### Health Check Endpoint

Configure health checks:
- **Path**: `/health`
- **Expected Status**: 200
- **Response**: `{"status": "healthy"}`

## 📚 API Documentation

API documentation is automatically generated:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Key Endpoints

#### Authentication
```
POST /api/auth/signup        - Register new user
POST /api/auth/login         - Login user
POST /api/auth/logout        - Logout user
GET  /api/auth/me            - Get current user
POST /api/auth/refresh       - Refresh access token
```

#### Portfolio
```
GET    /api/portfolio           - Get portfolio
POST   /api/portfolio/holding   - Add holding
DELETE /api/portfolio/holding/{symbol} - Remove holding
```

#### Trading
```
GET  /api/orders           - Get order history
POST /api/orders           - Create order
GET  /api/orders/{id}      - Get order details
```

#### Market Data
```
GET /api/crypto                - Get all prices
GET /api/crypto/{id}           - Get coin details
GET /api/crypto/{id}/history   - Get price history
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Frontend Tests

```bash
# Run all tests
yarn test

# Run with coverage
yarn test:coverage

# Run in watch mode
yarn test:watch
```

## 🔒 Security

### Authentication Flow

1. User registers with email/password
2. System sends 6-digit OTP via email
3. User verifies email with OTP
4. System issues JWT access token (30 min) and refresh token (7 days)
5. Access token stored in httpOnly cookie
6. All protected endpoints require valid access token

### Security Features

- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ Email verification
- ✅ Account lockout after 5 failed login attempts
- ✅ Token blacklisting on logout
- ✅ Rate limiting on all endpoints
- ✅ CORS protection
- ✅ Security headers (HSTS, CSP, etc.)
- ✅ Request timeout protection
- ✅ Input validation with Pydantic

### Rate Limits

- Signup: 3 requests/minute
- Login: 5 requests/minute
- General API: 60 requests/minute
- Trading: 20 requests/minute

## 📊 Monitoring

### Structured Logging

All logs are output in JSON format in production:

```json
{
  "timestamp": "2025-01-15T14:30:00Z",
  "level": "INFO",
  "logger": "backend.server",
  "message": "Request completed",
  "request_id": "abc-123",
  "method": "GET",
  "path": "/api/portfolio",
  "status_code": 200,
  "duration_ms": 45.2
}
```

### Metrics to Monitor

- API response time (p95, p99)
- Error rate (5xx responses)
- Database connection pool status
- Redis cache hit/miss ratio
- Active user sessions
- Trade volume

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Pull Request Guidelines

- Follow existing code style
- Add tests for new features
- Update documentation
- Ensure all tests pass
- Keep commits atomic and well-described

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [CoinGecko](https://www.coingecko.com/)
- [SendGrid](https://sendgrid.com/)
- [MongoDB](https://www.mongodb.com/)
- [Vercel](https://vercel.com/)
- [Render](https://render.com/)

## 📞 Support

For support, email support@cryptovault.com or open an issue on GitHub.

---

**Built with ❤️ for the crypto community**
