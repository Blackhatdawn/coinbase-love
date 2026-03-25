# CryptoVault Pro - Product Requirements Document

## Original Problem Statement
Update the CryptoVault project with production-grade improvements across 8 major areas:
1. Price Stream Service with Redis caching and CoinMarketCap fallback
2. Health Check Endpoints (liveness/readiness probes)
3. Production Server Setup
4. Security & Compliance (KYC/AML, multi-approver withdrawals, geo-blocking, audit logging, S3)
5. Email Configuration for cryptovaultpro.finance domain
6. Domain Change (cryptovault.finance → cryptovaultpro.finance)
7. Database & Infrastructure (compound indexes, Redis)
8. Documentation Updates

## Architecture
- **Backend**: FastAPI (Python) + MongoDB + Redis (Upstash) + WebSocket
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS
- **Infrastructure**: Render.com (backend), Vercel (frontend), MongoDB Atlas, Upstash Redis

## User Personas
- **Traders**: Buy/sell crypto, view real-time prices, manage portfolio
- **Admin**: Approve withdrawals, manage users, view analytics
- **Compliance Officer**: Review KYC docs, AML screening, audit logs

## Core Requirements
- Real-time price streaming from multiple exchanges
- Secure authentication with JWT + 2FA
- Multi-currency wallet management
- P2P transfers between users
- KYC/AML compliance hooks
- Production-grade health monitoring

## What's Been Implemented (March 2026)

### Phase 1: Price Stream + Health + Redis
- [x] Rewrote `services/price_stream.py` with:
  - Redis caching for market data (45s TTL)
  - CoinMarketCap fallback provider (CoinGecko → CMC → cached data)
  - Exponential backoff with random jitter (0-1s) on all exchanges
  - Max retry limit (50) with 5-minute cooldown on Binance WS
  - Scheduled market data refresh (every 45s) instead of aggressive polling
  - Clear HTTP 451 (geo-blocked) logging for Binance
- [x] Created `routers/health.py` with:
  - `GET /health/live` - Fast liveness probe (no deps)
  - `GET /health/ready` - Full readiness check (MongoDB, Redis, price stream)
  - Parallel dependency checks with `asyncio.gather()` and timeouts
  - Proper HTTP 200/503 status codes

### Phase 2: Security & Compliance
- [x] Created `services/audit_service.py` - Comprehensive audit logging for all financial actions
- [x] Created `services/s3_service.py` - S3 document upload for KYC docs (with local fallback)
- [x] Created `middleware/geo_blocking.py` - IP/country blocking with GeoIP support
- [x] Created `routers/kyc_aml.py` - KYC document upload, status, AML screening hooks
- [x] Added multi-approver withdrawal workflow in `routers/wallet.py`:
  - $5,000+ withdrawals require 2 admin approvals
  - `POST /wallet/withdraw/{id}/approve` and `/reject` endpoints
  - Full audit trail for approvals/rejections
- [x] Added hot/cold wallet architecture documentation

### Phase 3: Email + Domain
- [x] Updated email config to cryptovaultpro.finance domain
- [x] SMTP settings: mail.spacemail.com, port 465 (SSL)
- [x] Sender: securedvault@cryptovaultpro.finance
- [x] Updated all frontend references (index.html, sitemap.xml, robots.txt, meta tags)
- [x] Updated backend references (config.py, email_templates.py, admin_auth.py)

### Phase 4: Infrastructure + Documentation
- [x] Created `production_start.sh` (Gunicorn + Uvicorn workers, graceful shutdown)
- [x] Added compound indexes for high-volume trading (order book, multi-approval)
- [x] Added new config fields (coinmarketcap_api_key, s3_*, blocked_countries, geoip_db_path)
- [x] Updated `.env.example` with all new environment variables
- [x] Updated `README.md` with new endpoints, Redis requirement, production commands
- [x] Updated `PRODUCTION_READINESS.md` checklist

## New Environment Variables
```
COINMARKETCAP_API_KEY=        # Optional: CoinMarketCap fallback
S3_ENDPOINT_URL=              # S3-compatible storage endpoint
S3_ACCESS_KEY_ID=             # S3 access key
S3_SECRET_ACCESS_KEY=         # S3 secret key
S3_REGION=us-east-1           # S3 region
S3_BUCKET_KYC=                # KYC documents bucket
S3_BUCKET_AUDIT=              # Audit logs bucket
BLOCKED_COUNTRIES=            # Comma-separated country codes to block
GEOIP_DB_PATH=                # Path to GeoLite2-Country.mmdb
MAXMIND_LICENSE_KEY=          # MaxMind license for auto-download
```

## Prioritized Backlog

### P0 (Critical for production)
- [ ] Configure Redis (Upstash) in production
- [ ] Set up real S3 credentials for KYC document storage
- [ ] Full end-to-end email delivery testing

### P1 (Important)
- [ ] Add MaxMind GeoIP database for IP-based country blocking
- [ ] Implement cold wallet integration with hardware signing
- [ ] Complete AML screening integration (Chainalysis/Elliptic)
- [ ] Database sharding plan for high-volume trading

### P2 (Nice to have)
- [ ] Load testing with realistic traffic patterns
- [ ] Penetration testing
- [ ] Webhook mode for Telegram in multi-worker deployments
- [ ] IP whitelisting for MongoDB Atlas

## Next Tasks
1. User to configure Upstash Redis URL in production .env
2. User to set up S3 credentials for KYC storage
3. User to obtain CoinMarketCap API key (free tier)
4. User to download GeoLite2-Country.mmdb from MaxMind
5. End-to-end testing with real email delivery
