# 🏦 CryptoVault - Institutional-Grade Crypto Platform

> **Production Candidate** | Secure, scalable cryptocurrency trading and custody platform with advanced features

[![Status](https://img.shields.io/badge/status-production--candidate-yellow)](/)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](/)
[![License](https://img.shields.io/badge/license-MIT-green)](/)

## 🌟 Features

### Core Platform
- ✅ **User Authentication** - JWT + Refresh tokens, 2FA, account lockout
- ✅ **Wallet Management** - Multi-currency support, instant deposits
- ✅ **Trading Engine** - Market, limit, stop-loss, take-profit orders
- ✅ **P2P Transfers** - Free instant transfers between users
- ✅ **Real-time Updates** - WebSocket price feeds and notifications
- ✅ **Admin Dashboard** - User management, analytics, withdrawal approval

### Advanced Features
- 🚀 **Withdrawal System** - Automated processing with fee calculation
- 💹 **Advanced Order Types** - Stop-loss, take-profit, time-in-force
- 📊 **Business Analytics** - Revenue tracking, conversion funnels
- 🔔 **Real-time Notifications** - WebSocket-based alert system
- ⚡ **Multi-layer Caching** - L1/L2/L3 cache for optimal performance
- 🗄️ **Optimized Database** - Compound indexes for fast queries
- 📱 **Mobile Responsive** - Touch-optimized interface

### Security & Compliance
- 🔐 **Enterprise Security** - Rate limiting, audit logs, security headers
- 🛡️ **Account Protection** - Brute-force protection, device tracking
- 📝 **Comprehensive Logging** - Request correlation, structured logs
- 🎯 **Error Tracking** - Sentry integration for production monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- MongoDB (local or Atlas)

### 1. Clone & Install

```bash
# Clone repository
git clone <your-repo-url>
cd cryptovault

# Install backend
cd backend
pip install -r requirements.txt

# Install frontend
cd ../frontend
npm install
```

### 2. Configure

**Backend** (`backend/.env`):
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=cryptovault
PORT=8001
JWT_SECRET=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
```

**Frontend** (uses `.env.development`):
```bash
# Already configured - uses Vite proxy
VITE_API_BASE_URL=
```

### 3. Run

**Terminal 1 - Backend**:
```bash
cd backend
python run_server.py
# Running on http://localhost:8001
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
# Running on http://localhost:3000
```

### 4. Access

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8001/api/docs
- **Admin Panel**: http://localhost:3000/admin

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [📖 Quick Start Guide](QUICK_START_GUIDE.md) | Detailed setup instructions |
| [🚀 Production Enhancements](PRODUCTION_ENHANCEMENTS_COMPLETE.md) | Feature documentation |
| [🔧 Network Error Fix](NETWORK_ERROR_FIX.md) | Connection troubleshooting |
| [💚 Health Check Fix](HEALTH_CHECK_FIX_SUMMARY.md) | Health check details |
| [📦 Deployment Guide](DEPLOYMENT_GUIDE.md) | Production deployment |
| [✅ Production Readiness](docs/PRODUCTION_READINESS.md) | Source-of-truth go-live checklist and open gaps |

## 🚦 Release Status

This repository has a production-capable architecture, but **go-live must be gated by checklist completion** in `docs/PRODUCTION_READINESS.md` and `docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`.

The project should only be labeled "Production Ready" when those checklists are complete for the target environment.

## 🏗️ Architecture

### Tech Stack

**Backend**:
- FastAPI (Python)
- MongoDB (Database)
- Redis (Caching - optional)
- WebSocket (Real-time)
- JWT (Authentication)

**Frontend**:
- React 18 + TypeScript
- Vite (Build tool)
- TailwindCSS (Styling)
- TanStack Query (Data)
- Zustand (State)

**Infrastructure**:
- Sentry (Error tracking)
- Render/Vercel (Hosting)
- MongoDB Atlas (Database)
- Upstash Redis (Cache)

### Project Structure

```
cryptovault/
├── backend/              # FastAPI backend
│   ├── routers/         # API endpoints
│   ├── services/        # Business logic
│   ├── models.py        # Data models
│   ├── database.py      # DB connection
│   └── config.py        # Configuration
│
├── frontend/            # React frontend
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # UI components
│   │   ├── lib/         # API client
│   │   └── services/    # Health check
│   ├── .env.development # Dev config
│   └── vite.config.ts   # Vite config
│
└── docs/                # Documentation
```

## 🔌 API Endpoints

### Authentication
```
POST   /api/auth/signup              - Create account
POST   /api/auth/login               - Login
POST   /api/auth/logout              - Logout
POST   /api/auth/refresh             - Refresh token
GET    /api/auth/me                  - Get profile
POST   /api/auth/verify-email        - Verify email
POST   /api/auth/forgot-password     - Request reset
POST   /api/auth/reset-password      - Reset password
```

### Wallet & Transfers
```
GET    /api/wallet/balance           - Get balance
POST   /api/wallet/deposit/create    - Create deposit
POST   /api/wallet/withdraw          - Request withdrawal
GET    /api/wallet/withdrawals       - Withdrawal history
POST   /api/wallet/transfer          - P2P transfer
GET    /api/wallet/transfers         - Transfer history
```

### Trading
```
GET    /api/orders                   - Order history
POST   /api/orders                   - Create order
POST   /api/orders/advanced          - Advanced order types
DELETE /api/orders/:id               - Cancel order
```

### Admin
```
POST   /api/admin/setup-first-admin  - Create first admin
GET    /api/admin/stats              - Platform stats
GET    /api/admin/users              - User list
GET    /api/admin/withdrawals        - Pending withdrawals
POST   /api/admin/withdrawals/:id/approve  - Approve withdrawal
```

### System
```
GET    /ping                         - Simple health check
GET    /health                       - Full health check
```

See full API documentation at `http://localhost:8001/api/docs`

## 🧪 Testing

### Manual Testing

```bash
# Test backend health
curl http://localhost:8001/ping

# Test API endpoint
curl http://localhost:8001/api/crypto/prices

# View API docs
open http://localhost:8001/api/docs
```

### Frontend Testing

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 🚢 Deployment

### Backend (Render)

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `python run_server.py`
5. Add environment variables (see `.env.example`)

### Frontend (Vercel/Netlify)

1. Connect GitHub repository
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Add environment variables:
   ```
   VITE_API_BASE_URL=https://your-backend.com
   VITE_NODE_ENV=production
   ```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for details.

## 🔧 Configuration

### Environment Variables

**Backend** (`backend/.env`):
```bash
# Required
MONGO_URL=mongodb://...
DB_NAME=cryptovault
JWT_SECRET=secret-key
CORS_ORIGINS=http://localhost:3000

# Optional
RESEND_API_KEY=          # Email service
UPSTASH_REDIS_REST_URL=  # Redis cache
SENTRY_DSN=              # Error tracking
```

**Frontend** (`.env.development` / `.env.production`):
```bash
# Required for production
VITE_API_BASE_URL=https://api.yourdomain.com

# Optional
VITE_SENTRY_DSN=         # Error tracking
```

## 🐛 Troubleshooting

### Common Issues

**"NetworkError when attempting to fetch resource"**
- ✅ Make sure backend is running on http://localhost:8001
- ✅ Check `VITE_API_BASE_URL` is empty in development
- ✅ See [NETWORK_ERROR_FIX.md](NETWORK_ERROR_FIX.md)

**"Health check experiencing issues"**
- ✅ Normal during backend cold start (free hosting)
- ✅ Health check continues with exponential backoff
- ✅ See [HEALTH_CHECK_FIX_SUMMARY.md](HEALTH_CHECK_FIX_SUMMARY.md)

**"Database connection failed"**
- ✅ Make sure MongoDB is running: `mongosh`
- ✅ Check `MONGO_URL` in backend/.env
- ✅ Use MongoDB Atlas for production

**"Port already in use"**
```bash
# Kill process on port 8001 (backend)
lsof -i :8001 && kill -9 <PID>

# Kill process on port 3000 (frontend)
lsof -i :3000 && kill -9 <PID>
```

See [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) for more troubleshooting.

## 📊 Performance

### Metrics
- **API Response**: < 200ms (95th percentile)
- **Cache Hit Rate**: > 80% (L1), > 60% (L2)
- **Database Queries**: < 50ms (with indexes)
- **WebSocket Latency**: < 50ms

### Optimization
- ✅ Multi-layer caching (L1/L2/L3)
- ✅ Database compound indexes
- ✅ Code splitting & lazy loading
- ✅ Response compression
- ✅ Connection pooling

## 🔐 Security

### Features
- ✅ JWT with refresh tokens
- ✅ Rate limiting (per user/IP)
- ✅ Account lockout (5 failed attempts)
- ✅ 2FA support
- ✅ Security headers
- ✅ CSRF protection
- ✅ Audit logging
- ✅ Token blacklisting

### Best Practices
- All passwords hashed with bcrypt
- Secure cookies (HttpOnly, SameSite)
- Request ID correlation
- Structured logging
- Error tracking (Sentry)

## 📈 Monitoring

### Health Checks
- `/ping` - Simple health (no DB)
- `/health` - Full system health
- Frontend health check service (4min interval)

### Logging
- Structured JSON logs in production
- Request correlation IDs
- Audit logs for all actions
- Error tracking with Sentry

### Analytics
- User growth metrics
- Trading volume tracking
- Revenue analytics
- Conversion funnel analysis

See [PRODUCTION_ENHANCEMENTS_COMPLETE.md](PRODUCTION_ENHANCEMENTS_COMPLETE.md) for details.

## 🎯 Roadmap

### Phase 1: Launch ✅
- [x] Core authentication & authorization
- [x] Wallet management
- [x] Trading engine
- [x] Admin dashboard
- [x] Production deployment

### Phase 2: Enhancements ✅
- [x] Withdrawal system
- [x] P2P transfers
- [x] Advanced order types
- [x] Real-time notifications
- [x] Business analytics

### Phase 3: Future
- [ ] Mobile app (React Native)
- [ ] Advanced trading charts
- [ ] Margin trading
- [ ] Staking/Yield farming
- [ ] Multi-language support
- [ ] White-label solution

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/my-feature`
5. Submit pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🆘 Support

- **Documentation**: See `/docs` folder
- **API Docs**: http://localhost:8001/api/docs
- **Issues**: Create GitHub issue with logs
- **Email**: support@cryptovault.com

## ✨ Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [MongoDB](https://www.mongodb.com/) - Database
- [TailwindCSS](https://tailwindcss.com/) - Styling
- [Vite](https://vitejs.dev/) - Build tool

## 🎉 Acknowledgments

Special thanks to all contributors and the open-source community!

---

**Status**: 🟡 Production Candidate (checklist-gated) | **Version**: 1.0.0 | **Last Updated**: February 2026

Made with ❤️ by the CryptoVault team
