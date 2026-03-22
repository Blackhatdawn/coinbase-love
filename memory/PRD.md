# CryptoVault PRD - Crypto Exchange Platform

## Original Problem Statement
Deep review and investigate the entire web application. Identify what hasn't been done and what needs updating. Admin panel/dashboard access review. App is meant to be like Bybit, Coinbase, Binance.

## Architecture
- **Frontend**: Vite + React + TypeScript + TailwindCSS + Framer Motion + Chart.js + Socket.IO + Firebase SDK
- **Backend**: FastAPI + MongoDB Atlas + Socket.IO + Firebase Admin SDK
- **Database**: MongoDB Atlas (16+ collections)
- **Real-time**: WebSocket price streaming from Coinbase/CoinGecko/Kraken
- **Push Notifications**: Firebase Cloud Messaging (LIVE)
- **Email**: SMTP (GMX) with mock fallback in dev

## User Personas
1. **Retail Crypto Trader** - Buy/sell crypto, view portfolios, set price alerts
2. **Passive Investor** - Stake/earn features, flexible/locked staking
3. **Admin** - User management, transaction monitoring, system health
4. **Referral Ambassador** - Share codes, earn tiered bonuses

## Core Requirements
- User registration/login with secure sessions (httpOnly cookies)
- Live crypto price data from multiple sources
- Trading (market/limit orders)
- Wallet management (deposit/withdraw)
- Staking/Earn products
- Admin dashboard with OTP-secured access
- P2P transfers, price alerts, referral system
- Push notifications via Firebase
- Tiered referral reward system

## What's Been Implemented

### Session 1 (2026-03-15): Deep Audit & Bug Fixes
12 bugs identified and fixed:
1. Login → Dashboard redirect race condition
2. Admin password reset + OTP auto-fill in dev mode
3. Admin OTP datetime mismatch fix
4. Redis cache 400 errors (Upstash exhausted, disabled)
5. WebSocket URLs hardcoded to localhost
6. Auth cookies missing Secure flag
7. Staking/Earn enabled
8. Onboarding loader reduced
9. Vercel analytics removed
10. React Router v7 deprecation warnings
11. Welcome animation optimized
12. Email service graceful fallback

### Session 2 (2026-03-15): Referral Rewards + Firebase Push
1. **Referral Reward System (Fixed $10 Bonus)** - Both sides get $10 on signup
2. **Firebase Push Notifications** - FCM service with mock fallback

### Session 3 (2026-03-22): Firebase Live + SendGrid + VAPID Key
1. **Firebase Push Notifications - LIVE MODE**:
   - Service account credentials configured (crypto-vault-8026a)
   - Fixed env loading issue (fallback to file path when os.environ not set)
   - FCM token registration, test, status endpoints all working
   - mock_mode: false, firebase_setup_required: false
2. **SendGrid Email Service**:
   - Configured with API key (currently returning 401 - key needs renewal)
   - Added graceful fallback to mock mode in dev for both SendGrid AND SMTP failures
   - Signup flow works regardless of email service status
3. **VAPID Key**:
   - Web push VAPID key configured in frontend .env
   - Service worker ready for browser push permission prompts
4. **Gunicorn Clarification**:
   - FastAPI uses ASGI (not WSGI), correct command: `gunicorn -k uvicorn.workers.UvicornWorker server:app`
   - Already handled by start_server.py

## Testing Status
- Backend: 100% (20/20 tests passed)
- Frontend: 95% (all UI features working, minor session timeout during extended Playwright testing)
- Firebase: LIVE (mock_mode=false)
- Email: SendGrid with mock fallback (key needs renewal)

## Prioritized Backlog

### P0 (Critical - None remaining)
All critical bugs fixed.

### P1 (High Priority)
- [ ] Fix GMX SMTP credentials (user needs to verify password)
- [ ] VAPID key for web push (user needs to generate from Firebase Console → Cloud Messaging)
- [ ] Upstash Redis - upgrade plan or provision new instance

### P2 (Medium Priority)
- [ ] Advanced trading charts (TradingView integration)
- [ ] Blog/Careers pages - connect to CMS or API
- [ ] Sentry error tracking - configure for production
- [ ] Mobile responsive testing and optimization
- [ ] KYC/AML verification flow

### P3 (Low Priority)
- [ ] Telegram bot admin notifications webhook mode
- [ ] Email templates for all transactional emails
- [ ] Rate limiting with Redis
- [ ] Production deployment hardening
- [ ] Social login (Google OAuth)

## Credentials
- Admin: admin@cryptovault.financial / CryptoAdmin2026! (OTP auto-fills in dev)
- Firebase: crypto-vault-8026a (service account at /app/backend/firebase-credentials.json)
- SMTP: services.fortivault@gmx.us (credentials need updating)
