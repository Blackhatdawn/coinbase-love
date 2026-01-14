# CryptoVault - Product Requirements Document

## Overview
CryptoVault is a secure cryptocurrency trading platform with institutional-grade custody solutions. Built with React (Vite) frontend and FastAPI backend.

## Architecture
- **Frontend**: Vite + React + TypeScript (Tailwind CSS, Shadcn/UI)
- **Backend**: FastAPI + Python
- **Database**: MongoDB Atlas (primary), Redis/Upstash (caching, OTPs, sessions)
- **Integrations**: CoinGecko (live prices), SendGrid (email), JWT auth

## User Personas
1. **Retail Crypto Traders** - Individual users trading cryptocurrencies
2. **Institutional Investors** - Organizations requiring secure custody
3. **New Crypto Users** - First-time cryptocurrency buyers

## Core Requirements (Static)
- Secure JWT-based authentication with email OTP verification
- Live cryptocurrency prices from CoinGecko
- Portfolio management with real-time value updates
- Buy/Sell trading functionality
- Wallet management (deposit/withdraw)
- Order history tracking
- Mobile-first responsive design
- Gold/orange theme branding

## What's Been Implemented
### January 2026
- ✅ Complete authentication flow (signup, OTP verification, login)
- ✅ Email service with SendGrid integration
- ✅ Redis caching for OTPs and API responses
- ✅ CoinGecko integration for live prices
- ✅ Portfolio dashboard with holdings display
- ✅ Markets page with live prices and green/red indicators
- ✅ Trading page with price charts (lightweight-charts v5)
- ✅ Mobile-first responsive design across all pages
- ✅ Custom logo.svg used consistently across all pages
- ✅ Price ticker with auto-refresh (15-30s intervals)
- ✅ Touch-friendly buttons (min 44x44px)
- ✅ Gold/orange theme consistently applied

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] Email verification with actual OTP codes (currently SendGrid configured)
- [ ] Password reset flow
- [ ] Order execution and confirmation flow
- [ ] Deposit/withdraw functionality with payment integration

### P1 (High Priority)
- [ ] Two-factor authentication (2FA)
- [ ] Price alerts and notifications
- [ ] Advanced charting with technical indicators
- [ ] Multiple portfolio support

### P2 (Medium Priority)
- [ ] Social trading features
- [ ] API key management for programmatic access
- [ ] Tax reporting exports
- [ ] Multi-language support (i18n)

### P3 (Future Considerations)
- [ ] Staking and yield features
- [ ] NFT marketplace integration
- [ ] Mobile app (React Native)
- [ ] Advanced order types (limit, stop-loss)

## Technical Debt
- Fix CORS OPTIONS preflight handling
- Improve mobile menu close button z-index
- Add comprehensive error boundaries
- Implement request retry logic with exponential backoff

## Environment Variables Required
```
# Backend (.env)
MONGO_URL=<mongodb_connection_string>
DB_NAME=cryptovault_db
JWT_SECRET=<secure_secret>
JWT_ALGORITHM=HS256
SENDGRID_API_KEY=<sendgrid_key>
EMAIL_SERVICE=sendgrid
EMAIL_FROM=noreply@cryptovault.financial
UPSTASH_REDIS_REST_URL=<upstash_url>
UPSTASH_REDIS_REST_TOKEN=<upstash_token>
COINGECKO_API_KEY=<optional_for_pro>

# Frontend (.env)
REACT_APP_BACKEND_URL=<backend_api_url>
```

## Next Tasks
1. Test SendGrid email delivery in production
2. Implement OTP resend with rate limiting
3. Add loading states to all forms
4. Implement order history page
5. Add wallet deposit flow with payment gateway
