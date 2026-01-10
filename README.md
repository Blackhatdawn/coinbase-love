# CryptoVault - Cryptocurrency Trading Platform

A full-stack cryptocurrency trading platform built with React, FastAPI, and MongoDB.

## 🚀 Current Status

✅ **Frontend**: Running on port 3000 (Vite + React + TypeScript)  
✅ **Backend**: Running on port 8001 (FastAPI + Python)  
✅ **Database**: MongoDB running locally  
✅ **All API endpoints implemented and functional**

---

## 📁 Project Structure

```
/app
├── backend/              # FastAPI backend
│   ├── server.py        # Main API server with all endpoints
│   ├── models.py        # Pydantic data models
│   ├── auth.py          # Authentication & JWT utilities
│   ├── dependencies.py  # FastAPI dependencies
│   └── requirements.txt # Python dependencies
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── pages/       # Page components
│   │   ├── contexts/    # React contexts (Auth)
│   │   ├── lib/         # Utilities (API client)
│   │   └── hooks/       # Custom hooks
│   ├── package.json
│   └── vite.config.ts
└── tests/              # Test directory
```

---

## 🔧 Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 5
- **UI Library**: Radix UI + Tailwind CSS
- **Routing**: React Router v6
- **State Management**: React Query + Context API
- **Form Handling**: React Hook Form + Zod

### Backend
- **Framework**: FastAPI 0.110
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT tokens with httpOnly cookies
- **Password Hashing**: Passlib with bcrypt
- **Validation**: Pydantic v2

---

## 🎯 Implemented Features

### Authentication & Security
- ✅ User signup with email & password
- ✅ User login with JWT tokens
- ✅ HttpOnly cookie-based auth
- ✅ Token refresh mechanism
- ✅ Two-Factor Authentication (2FA) setup/verify/disable
- ✅ Backup codes for 2FA recovery
- ✅ Audit logging for security events

### Cryptocurrency Data
- ✅ List all cryptocurrencies (10 major coins)
- ✅ Get individual cryptocurrency details
- ✅ Real-time price variations
- ✅ Market cap, volume, and 24h changes

### Portfolio Management
- ✅ View user portfolio
- ✅ Add holdings
- ✅ Update holdings
- ✅ Delete holdings
- ✅ Calculate total balance
- ✅ Asset allocation percentages

### Trading & Orders
- ✅ Create market/limit orders
- ✅ View order history
- ✅ Cancel pending orders
- ✅ Order status tracking (pending/filled/cancelled)
- ✅ Automatic order filling for demo

### Transaction History
- ✅ View all transactions (paginated)
- ✅ Create manual transactions
- ✅ Transaction types (deposit, withdrawal, trade, fee)
- ✅ Transaction statistics & overview
- ✅ Filter by type

### Audit Logs
- ✅ Comprehensive event logging
- ✅ Filter logs by action type
- ✅ Audit log summary with action counts
- ✅ Export audit logs
- ✅ IP address tracking

---

## 🔌 API Endpoints

### Authentication (`/api/auth/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | Login user |
| POST | `/auth/logout` | Logout user |
| GET | `/auth/me` | Get current user |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/verify-email` | Verify email (placeholder) |
| POST | `/auth/2fa/setup` | Setup 2FA |
| POST | `/auth/2fa/verify` | Verify & enable 2FA |
| GET | `/auth/2fa/status` | Get 2FA status |
| POST | `/auth/2fa/disable` | Disable 2FA |
| POST | `/auth/2fa/backup-codes` | Get backup codes |

### Cryptocurrency (`/api/crypto/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/crypto` | Get all cryptocurrencies |
| GET | `/crypto/{symbol}` | Get specific crypto |

### Portfolio (`/api/portfolio/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/portfolio` | Get user portfolio |
| GET | `/portfolio/holding/{symbol}` | Get specific holding |
| POST | `/portfolio/holding` | Add/update holding |
| DELETE | `/portfolio/holding/{symbol}` | Delete holding |

### Orders (`/api/orders/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/orders` | Get all orders |
| POST | `/orders` | Create new order |
| GET | `/orders/{id}` | Get specific order |
| POST | `/orders/{id}/cancel` | Cancel order |

### Transactions (`/api/transactions/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transactions` | Get transaction history |
| GET | `/transactions/{id}` | Get specific transaction |
| POST | `/transactions` | Create transaction |
| GET | `/transactions/stats/overview` | Get statistics |

### Audit Logs (`/api/audit-logs/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/audit-logs` | Get audit logs |
| GET | `/audit-logs/summary` | Get summary |
| GET | `/audit-logs/export` | Export logs |
| GET | `/audit-logs/{id}` | Get specific log |

---

## 🌐 Environment Variables

### Backend (`/app/backend/.env`)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
```

### Frontend (`/app/frontend/.env`)
```env
REACT_APP_BACKEND_URL=https://cleanup-maestro.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- MongoDB running locally
- Yarn package manager

### Installation

1. **Install Backend Dependencies**
```bash
cd /app/backend
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**
```bash
cd /app/frontend
yarn install
```

3. **Start Services**
```bash
# Restart all services
sudo supervisorctl restart all

# Check status
sudo supervisorctl status
```

4. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- API Docs: http://localhost:8001/docs

---

## 🧪 Testing

### Test Backend API
```bash
# Health check
curl http://localhost:8001/api/

# Get cryptocurrencies
curl http://localhost:8001/api/crypto

# Signup (example)
curl -X POST http://localhost:8001/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'
```

### Test Frontend
Navigate to http://localhost:3000 and:
1. Sign up for an account
2. View markets
3. Add holdings to portfolio
4. Place a trade order
5. View transaction history

---

## 📊 Mock Data

The backend uses mock cryptocurrency data for the following coins:
- Bitcoin (BTC)
- Ethereum (ETH)
- Tether (USDT)
- Binance Coin (BNB)
- Solana (SOL)
- Ripple (XRP)
- USD Coin (USDC)
- Cardano (ADA)
- Dogecoin (DOGE)
- TRON (TRX)

Prices include small random variations to simulate market movement.

---

## 🔐 Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT tokens with expiration
- ✅ HttpOnly cookies for token storage
- ✅ Token refresh mechanism
- ✅ Two-Factor Authentication support
- ✅ Audit logging for all sensitive actions
- ✅ CORS configuration
- ✅ Input validation with Pydantic

---

## 📝 Recent Changes & Fixes

### Mandatory Configuration Fixes
✅ Updated `vite.config.ts`:
  - Changed port from 8080 to 3000
  - Added `build.outDir: 'build'`
  - Changed host to `0.0.0.0`
  - Added `allowedHosts: true`
  - Fixed proxy target to port 8001

✅ Updated `package.json`:
  - Added `"start": "vite"` script

✅ Updated `.emergent/emergent.yml`:
  - Added `"source": "lovable"`

### Code Cleanup
✅ Removed 27 duplicate documentation files from frontend directory
✅ Removed unused Express server directory (`/app/frontend/server/`)
✅ Cleaned up outdated SETUP.md

### Backend Implementation
✅ Complete rewrite of backend with all required endpoints:
  - Full authentication system with JWT
  - Complete CRUD operations for all entities
  - MongoDB integration for all collections
  - Audit logging system
  - 2FA support

✅ Updated `requirements.txt`:
  - Removed unnecessary dependencies
  - Added required auth libraries (passlib, python-jose)

---

## 🎨 UI/UX Features

- Modern, clean interface with dark mode support
- Responsive design for mobile and desktop
- Real-time price updates
- Interactive charts (via Recharts)
- Toast notifications (via Sonner)
- Loading states and spinners
- Form validation with helpful error messages
- Protected routes with authentication

---

## 🔄 Development Workflow

### Making Changes

**Backend Changes:**
```bash
# Edit files in /app/backend/
# Restart backend
sudo supervisorctl restart backend

# Check logs
tail -f /var/log/supervisor/backend.err.log
```

**Frontend Changes:**
```bash
# Edit files in /app/frontend/src/
# Vite has hot reload - changes appear automatically
# If needed, restart:
sudo supervisorctl restart frontend

# Check logs
tail -f /var/log/supervisor/frontend.out.log
```

### Adding New Features

1. **Add Backend Endpoint:**
   - Define model in `models.py`
   - Add endpoint in `server.py`
   - Test with curl

2. **Add Frontend Feature:**
   - Create API function in `src/lib/api.ts`
   - Create/update component
   - Add route in `App.tsx` if needed

---

## 🐛 Known Issues & Limitations

1. **Email Verification**: Placeholder implementation (not functional)
2. **2FA Code Verification**: Accepts any 6-digit code (for demo)
3. **Cryptocurrency Data**: Uses mock data, not real API
4. **Order Execution**: Orders are auto-filled (for demo)
5. **TypeScript Linting**: ESLint configuration needs TypeScript parser setup

---

## 🚢 Deployment Considerations

For production deployment:

1. **Environment Variables:**
   - Set `REACT_APP_BACKEND_URL` to production backend URL
   - Use strong `SECRET_KEY` for JWT
   - Configure proper `CORS_ORIGINS`

2. **Security:**
   - Enable HTTPS
   - Set secure flags on cookies
   - Use environment-based secrets
   - Enable rate limiting

3. **Database:**
   - Use MongoDB Atlas or production MongoDB instance
   - Enable authentication
   - Set up backups

4. **Build Frontend:**
```bash
cd /app/frontend
yarn build
# Serve the /app/frontend/build directory
```

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## 🤝 Contributing

This is a demo/MVP project. For enhancements:

1. Add real cryptocurrency API integration (e.g., CoinGecko, CoinMarketCap)
2. Implement actual email verification
3. Add real-time WebSocket for price updates
4. Implement advanced trading features (stop-loss, take-profit)
5. Add charts and analytics
6. Implement KYC/compliance features

---

## 📄 License

This project is for demonstration purposes.

---

**Last Updated**: January 10, 2026  
**Version**: 1.0.0  
**Status**: ✅ Fully Functional MVP
