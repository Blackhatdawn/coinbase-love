# 🚀 DEPLOYMENT GUIDE - CryptoVault Enterprise

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment (Render)](#cloud-deployment-render)
6. [CI/CD Setup](#cicd-setup)
7. [Post-Deployment](#post-deployment)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Node.js v20+ | Python 3.11+ | Docker 24.x+ | MongoDB 7+ | Redis 7+

### Required Accounts
MongoDB Atlas | Upstash Redis | SendGrid | Sentry | Render | GitHub

## Quick Start

### Local Development
```bash
# Backend
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn server:app --reload --port 8001

# Frontend (new terminal)
cd frontend && yarn install
cp .env.example .env
yarn dev
```

### Production Deployment
```bash
# Build Docker images
docker build -t cryptovault-backend -f Dockerfile.backend .
docker build -t cryptovault-frontend -f Dockerfile.frontend .

# Deploy with compose
docker-compose up -d

# Or deploy to Render (via CI/CD)
git push origin production
```

## Environment Configuration

### Backend (.env.production)
```bash
ENVIRONMENT=production
MONGO_URL=mongodb+srv://...
JWT_SECRET=$(openssl rand -base64 64)
CORS_ORIGINS=https://www.cryptovault.financial
SENTRY_DSN=https://...
```

### Frontend (.env.production)
```bash
VITE_API_BASE_URL=https://www.cryptovault.financial
VITE_SENTRY_DSN=https://...
```

## Post-Deployment Verification

```bash
# Health checks
curl https://www.cryptovault.financial/api/health

# Security headers
curl -I https://www.cryptovault.financial | grep X-Frame-Options

# SSL certificate
openssl s_client -connect www.cryptovault.financial:443 < /dev/null 2>&1 | grep 'Verify return code'
```

## Troubleshooting

**Backend won't start**: Check Render logs and environment variables  
**Frontend blank**: Verify VITE_API_BASE_URL and CORS settings  
**Slow performance**: Enable Redis caching and check database indexes

Full documentation: See [/app/ENTERPRISE_TRANSFORMATION.md](/app/ENTERPRISE_TRANSFORMATION.md)

---
**Version**: 2.0.0 | **Last Updated**: 2026-01-18
