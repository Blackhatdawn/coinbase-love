# CryptoVault - Product Requirements Document

## Overview
CryptoVault is a secure cryptocurrency trading platform with institutional-grade custody solutions. Built with React (Vite) frontend and FastAPI backend.

## Architecture
- **Frontend**: Vite + React + TypeScript (Tailwind CSS, Shadcn/UI)
- **Backend**: FastAPI + Python
- **Database**: MongoDB Atlas (primary), Redis/Upstash (caching, OTPs, sessions)
- **Integrations**: CoinGecko (live prices), SendGrid (emails), NOWPayments (deposits - ready), Firebase FCM (push - ready)

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

### Phase 1 - January 2026
- ✅ Complete authentication flow (signup, OTP verification, login)
- ✅ Email service with SendGrid integration
- ✅ Redis caching for OTPs and API responses
- ✅ CoinGecko integration for live prices
- ✅ Portfolio dashboard with holdings display
- ✅ Markets page with live prices and green/red indicators
- ✅ Trading page with price charts (lightweight-charts v5)
- ✅ Mobile-first responsive design across all pages
- ✅ Custom logo.svg used consistently across all pages
- ✅ Price ticker with auto-refresh (15s intervals)
- ✅ Touch-friendly buttons (min 44x44px)
- ✅ Gold/orange theme consistently applied

### Phase 2 - January 2026 (Latest Update)
- ✅ **Enhanced LivePriceTicker** - Flash animations on price changes, horizontal swipe on mobile
- ✅ **Social Proof Section** - 4 testimonials + trust statistics (Secured $10B+, 99.99% Uptime, 2M+ Users, 150+ Countries)
- ✅ **Onboarding Loader** - Full-screen branded loading animation
- ✅ **Password Reset Flow** - Request page + confirmation with token
- ✅ **Order Confirmation Modal** - Shows trade details after execution
- ✅ **Wallet Deposit Page** - Crypto payment form (NOWPayments ready)
- ✅ **Price Alerts Page** - Create/manage price notifications
- ✅ **Admin Dashboard** - User management, trade monitoring, volume charts
- ✅ **SEO Optimization** - Meta tags, Open Graph support
- ✅ **Security Headers** - CSP, X-Frame-Options, etc. in vercel.json
- ✅ **Lazy Loading** - React.lazy for performance optimization

## API Endpoints Added
- `POST /api/auth/password-reset/request` - Request password reset
- `POST /api/auth/password-reset/confirm` - Confirm with token
- `GET /api/alerts` - Get user price alerts
- `POST /api/alerts` - Create price alert
- `PATCH /api/alerts/{id}` - Update alert
- `DELETE /api/alerts/{id}` - Delete alert
- `POST /api/wallet/deposit/create` - Create deposit invoice
- `GET /api/admin/stats` - Admin statistics
- `GET /api/admin/users` - User management
- `GET /api/admin/trades` - Trade monitoring

## Prioritized Backlog

### P0 (Critical - Next Sprint)
- [ ] NOWPayments webhook integration for deposit confirmation
- [ ] Firebase FCM push notification implementation
- [ ] Real-time WebSocket for price updates
- [ ] Email templates for password reset

### P1 (High Priority)
- [ ] Two-factor authentication (2FA)
- [ ] Advanced charting with technical indicators
- [ ] Order execution with exchange integration
- [ ] KYC verification flow

### P2 (Medium Priority)
- [ ] Multi-language support (i18n)
- [ ] Social trading features
- [ ] API key management
- [ ] Tax reporting exports

### P3 (Future Considerations)
- [ ] Staking and yield features
- [ ] NFT marketplace integration
- [ ] Mobile app (React Native)
- [ ] Advanced order types (limit, stop-loss)

## Testing Checklist
| Feature | Desktop | Mobile | Backend |
|---------|---------|--------|---------|
| Live Price Ticker | ✅ | ✅ | ✅ |
| Flash Animations | ✅ | ✅ | N/A |
| Social Proof | ✅ | ✅ | N/A |
| Password Reset | ✅ | ✅ | ✅ |
| Wallet Deposit | ✅ | ✅ | ✅ |
| Price Alerts | ✅ | ✅ | ✅ |
| Admin Dashboard | ✅ | ✅ | ✅ |
| Auth Flow | ✅ | ✅ | ✅ |

## Deployment Notes

### Vercel (Frontend)
1. Connect GitHub repository
2. Set environment variables from `.env.example`
3. Update `VITE_API_BASE` to Render backend URL
4. Enable Vercel Analytics

### Render (Backend)
1. Connect GitHub repository
2. Set environment variables from `backend/.env.example`
3. Configure health check endpoint: `/api/health`
4. Set CORS_ORIGINS to production domains

## Environment Variables Required
See `.env.example` files in both `/frontend` and `/backend` directories.
