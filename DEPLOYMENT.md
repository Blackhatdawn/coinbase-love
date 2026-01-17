# CryptoVault - Production Deployment Guide

## Overview
CryptoVault is an enterprise-grade cryptocurrency trading platform with a Bybit-style professional dashboard interface.

## Tech Stack
- **Frontend**: React 18 + TypeScript, Vite, TailwindCSS, TanStack Query, Zustand, Framer Motion
- **Backend**: FastAPI (Python), MongoDB, JWT Auth, WebSocket
- **Database**: MongoDB Atlas (recommended for production)
- **Email**: SendGrid
- **Cache**: Redis (Upstash recommended)
- **Error Tracking**: Sentry

---

## Backend Deployment

### Required Environment Variables

```bash
# Database (Required)
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/?appName=CryptoVault
DB_NAME=cryptovault_production

# Security (Required)
JWT_SECRET=your-32-char-minimum-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (Required - Set to your frontend domain)
CORS_ORIGINS=https://your-frontend.com
APP_URL=https://your-frontend.com

# Email (Required for production)
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=CryptoVault

# Crypto Data (Required)
COINGECKO_API_KEY=your-key
USE_MOCK_PRICES=false

# Redis Cache (Recommended)
USE_REDIS=true
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=xxx

# Error Tracking (Recommended)
SENTRY_DSN=https://xxx@sentry.io/xxx

# Server
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
```

### Deployment Platforms
- **Railway**: `railway up`
- **Render**: Connect GitHub repo, set env vars
- **AWS ECS/Fargate**: Docker containerized
- **Google Cloud Run**: Docker containerized
- **DigitalOcean App Platform**: Connect repo

### Dockerfile (Backend)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

---

## Frontend Deployment

### Required Environment Variables
```bash
# Backend API URL (Required)
REACT_APP_BACKEND_URL=https://your-backend-api.com

# For Vite builds
VITE_API_BASE_URL=https://your-backend-api.com
```

### Build Command
```bash
yarn install
yarn build
```

### Deployment Platforms
- **Vercel**: `vercel --prod`
- **Netlify**: Connect repo, build command: `yarn build`, publish dir: `dist`
- **Cloudflare Pages**: Connect repo
- **AWS S3 + CloudFront**: Upload `dist/` folder
- **Firebase Hosting**: `firebase deploy`

---

## API Endpoints Overview

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/verify-email` - Verify email
- `POST /api/auth/reset-password` - Request password reset
- `POST /api/auth/change-password` - Change password

### Portfolio
- `GET /api/portfolio` - Get user portfolio
- `POST /api/portfolio/holdings` - Add holding
- `DELETE /api/portfolio/holdings/{id}` - Remove holding

### Wallet
- `POST /api/wallet/deposit` - Create deposit
- `POST /api/wallet/withdraw` - Request withdrawal
- `GET /api/wallet/balance` - Get balance

### Crypto
- `GET /api/crypto` - Get all cryptocurrencies
- `GET /api/crypto/{id}` - Get crypto details
- `GET /api/crypto/{id}/history` - Get price history

### Alerts
- `GET /api/alerts` - Get user alerts
- `POST /api/alerts` - Create alert
- `DELETE /api/alerts/{id}` - Delete alert

### Transactions
- `GET /api/transactions` - Get transactions

---

## Dashboard Pages

| Route | Page | Description |
|-------|------|-------------|
| `/dashboard` | Dashboard | Main overview with balance, assets, activity |
| `/trade` | Trade | Professional trading interface with charts |
| `/earn` | Earn | Staking products and rewards |
| `/wallet/deposit` | Deposit | Fund account with crypto |
| `/wallet/withdraw` | Withdraw | Withdraw funds |
| `/wallet/transfer` | P2P Transfer | Internal transfers |
| `/transactions` | Transactions | Transaction history |
| `/alerts` | Price Alerts | Price alert management |
| `/referrals` | Referrals | Referral program |
| `/security` | Security | Security settings |
| `/settings` | Settings | Account settings |

---

## Security Checklist

- [ ] Set strong JWT_SECRET (32+ characters)
- [ ] Configure CORS_ORIGINS to specific frontend domain (no wildcards in production)
- [ ] Enable HTTPS for both frontend and backend
- [ ] Configure rate limiting
- [ ] Enable Sentry for error tracking
- [ ] Set up MongoDB Atlas with IP whitelist
- [ ] Configure SendGrid for email verification
- [ ] Enable 2FA option for users
- [ ] Regular security audits

---

## Monitoring & Logging

### Backend Logs
- All API requests are logged with request ID
- Authentication events are logged
- Error tracking via Sentry

### Health Check
- `GET /health` - Backend health status
- `GET /api/health` - API health with database status

---

## Support

For deployment issues or questions, refer to:
- Backend: `/app/backend/` source code
- Frontend: `/app/frontend/` source code
- API Docs: `http://backend-url/docs` (Swagger UI)
