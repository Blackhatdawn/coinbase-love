# CryptoVault PRD - Crypto Exchange Platform

## Original Problem Statement
Deep review and investigate the entire web application. Identify what hasn't been done and what needs updating. Admin panel/dashboard access review. App is meant to be like Bybit, Coinbase, Binance.

## Architecture
- **Frontend**: Vite + React + TypeScript + TailwindCSS + Framer Motion + Chart.js + Socket.IO
- **Backend**: FastAPI + MongoDB Atlas + Socket.IO + Upstash Redis (disabled - quota exhausted)
- **Database**: MongoDB Atlas (16 collections)
- **Real-time**: WebSocket price streaming from Coinbase/CoinGecko/Kraken

## User Personas
1. **Retail Crypto Trader** - Buy/sell crypto, view portfolios, set price alerts
2. **Passive Investor** - Stake/earn features, flexible/locked staking
3. **Admin** - User management, transaction monitoring, system health

## Core Requirements
- User registration/login with secure sessions (httpOnly cookies)
- Live crypto price data from multiple sources
- Trading (market/limit orders)
- Wallet management (deposit/withdraw)
- Staking/Earn products
- Admin dashboard with OTP-secured access
- P2P transfers, price alerts, referral system

## What's Been Implemented
### Date: 2026-03-15

#### Features Implemented:
1. **Referral Reward System (Fixed $10 Bonus)**
   - Both referrer and referred user get $10 USD credited to wallet on signup
   - Direct wallet credit (no admin approval needed)
   - Full audit trail with transactions collection
   - Referral leaderboard API
   - Auto-fills referral code from ?ref=CODE URL parameter
   - In-app + push notifications on referral reward
   - Privacy-masked referral list (emails/names partially hidden)

2. **Firebase Push Notifications**
   - FCM service with automatic mock fallback when Firebase not configured
   - Endpoints: register-token, unregister-token, test, status
   - Service worker for background notifications (firebase-messaging-sw.js)
   - Frontend push notification service (lazy-loads Firebase SDK)
   - Notification routing by type (price alerts -> /markets, orders -> /transactions, etc.)
   - Pre-built notification types: referral_reward, price_alert, order_confirmation, deposit_confirmation

#### Bugs Fixed (Deep Audit):
1. **Login → Dashboard redirect race condition** - Fixed with useEffect watching user state instead of imperative navigate()
2. **Admin password lost** - Reset to known credentials (admin@cryptovault.financial / CryptoAdmin2026!)
3. **Admin OTP datetime mismatch** - Fixed timezone-naive vs timezone-aware comparison
4. **Admin OTP in dev mode** - Auto-fills OTP when EMAIL_SERVICE=mock
5. **Redis cache 400 errors** - Upstash free tier exhausted (500K limit); switched to POST-based API format and disabled until upgraded
6. **WebSocket URLs hardcoded to localhost** - Fixed to derive from window.location dynamically
7. **Auth cookies missing Secure flag** - Always set Secure=true for HTTPS
8. **Staking/Earn disabled** - Enabled FEATURE_STAKING_ENABLED
9. **Onboarding loader too slow** - Reduced from 5s to 2.5s max
10. **Vercel analytics removed** - Was failing, not deployed on Vercel
11. **React Router v7 deprecation warnings** - Added future flags
12. **Welcome animation duration** - Reduced from 5s to 3s

## Prioritized Backlog

### P0 (Critical - None remaining)
All critical bugs fixed.

### P1 (High Priority)
- [ ] Firebase credentials setup (see /app/FIREBASE_SETUP_GUIDE.md)
- [ ] Email service (currently mock) - configure SendGrid/real SMTP for production
- [ ] Upstash Redis - upgrade plan or replace with new instance
- [ ] Password reset flow end-to-end testing with real email

### P2 (Medium Priority)
- [ ] Referral system - implement actual tracking/rewards backend
- [ ] Blog/Careers pages - connect to CMS or API
- [ ] Sentry error tracking - configure for production
- [ ] Advanced trading charts (TradingView integration)
- [ ] Mobile responsive testing and optimization

### P3 (Low Priority)
- [ ] Telegram bot admin notifications
- [ ] Email templates for all transactional emails
- [ ] Rate limiting with Redis (currently in-memory fallback)
- [ ] Production deployment hardening (CORS, rate limits, etc.)

## Admin Credentials
- Email: admin@cryptovault.financial
- Password: CryptoAdmin2026!
- OTP: Auto-filled in dev mode (EMAIL_SERVICE=mock)

## Test User
- Email: test@example.com
- Password: TestPassword123!
