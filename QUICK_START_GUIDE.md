# 🚀 CryptoVault Quick Start Guide

## 📋 Prerequisites

- **Python**: 3.9+ (for backend)
- **Node.js**: 18+ (for frontend)
- **MongoDB**: Local or MongoDB Atlas account
- **Git**: For version control

## ⚡ Quick Start (5 Minutes)

### Step 1: Clone & Install

```bash
# Clone repository
git clone <repository-url>
cd cryptovault

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 2: Configure Environment

#### Backend Configuration

```bash
cd backend

# Create .env file
cat > .env << EOL
# MongoDB Configuration
MONGO_URL=mongodb://localhost:27017
DB_NAME=cryptovault

# Server Configuration  
PORT=8001
ENVIRONMENT=development

# Security
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (allow local development)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Optional: Email Service (leave empty for development)
RESEND_API_KEY=
ADMIN_EMAIL=admin@cryptovault.com

# Optional: Redis Cache (leave empty to use in-memory)
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
EOL

cd ..
```

#### Frontend Configuration

```bash
cd frontend

# Development uses .env.development (already created)
# Just verify it exists:
cat .env.development

# Should show:
# VITE_API_BASE_URL=
# (empty = uses Vite proxy)
```

### Step 3: Start Services

#### Terminal 1: Start Backend

```bash
cd backend
python run_server.py

# ✅ Should see:
# 🚀 Starting CryptoVault API Server
# ✅ MongoDB connected successfully
# ✅ Running on http://0.0.0.0:8001
# 📚 API docs: http://localhost:8001/api/docs
```

#### Terminal 2: Start Frontend

```bash
cd frontend
npm run dev

# ✅ Should see:
# VITE v5.x.x ready in XXX ms
# ➜ Local: http://localhost:3000
# ➜ Network: http://192.168.x.x:3000
```

### Step 4: Verify Setup

1. **Open Browser**: http://localhost:3000
2. **Check Console**: Should see health check success
3. **Create Account**: Sign up with email
4. **Verify Connection**: No network errors

## 🎯 What You Should See

### Successful Startup Logs

**Backend (Terminal 1)**:
```
======================================================================
🚀 Starting CryptoVault API Server
======================================================================
✅ Environment validation passed
🔌 Attempting MongoDB connection (attempt 1/5)...
✅ MongoDB connected successfully to database: cryptovault
✅ MongoDB health check passed
✅ Created TTL index on login_attempts
✅ Created TTL index on blacklisted_tokens
✅ Created indexes on users collection
...
💾 Redis Cache initialized (redis=False)
📡 WebSocket price feed initialized
🔥 Price streaming service initialized
======================================================================
✅ CryptoVault API Server Started Successfully
======================================================================
🌐 Server: http://0.0.0.0:8001
📚 API Docs: http://localhost:8001/api/docs
🔄 Redoc: http://localhost:8001/api/redoc
🌍 Environment: development
======================================================================
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

**Frontend (Terminal 2)**:
```
VITE v5.4.19 ready in 524 ms

➜  Local:   http://localhost:3000/
➜  Network: http://192.168.1.100:3000/
➜  press h + enter to show help
```

**Browser Console**:
```
[API Client] Initialized with BASE_URL: (empty - using relative paths)
[App] Warming up backend API...
[App] ✅ Backend API is active and responding
[HealthCheck] HealthCheckService initialized
[HealthCheck] HealthCheckService started
[HealthCheck] ✅ Health check passed (45ms) | Rate limit: 60/60
```

## 🔧 Configuration Details

### Backend Ports
- **API Server**: http://localhost:8001
- **API Docs**: http://localhost:8001/api/docs
- **WebSocket**: ws://localhost:8001/ws

### Frontend Ports
- **Dev Server**: http://localhost:3000
- **Preview**: http://localhost:4173 (after `npm run build`)

### Database
- **MongoDB**: mongodb://localhost:27017/cryptovault
- **Collections**: auto-created on first use

## 📁 Project Structure

```
cryptovault/
├── backend/                 # FastAPI Backend
│   ├── routers/            # API endpoints
│   │   ├── auth.py         # Authentication
│   │   ├── wallet.py       # Wallet & transfers
│   │   ├── trading.py      # Orders & trading
│   │   ├── admin.py        # Admin panel
│   │   └── notifications.py # Real-time notifications
│   ├── services/           # Business logic
│   ├── database.py         # MongoDB connection
│   ├── models.py           # Data models
│   ├── config.py           # Configuration
│   ├── run_server.py       # Server entry point
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React + TypeScript Frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   ├── components/     # Reusable components
│   │   ├── lib/            # API client, utilities
│   │   ├── services/       # Health check, etc.
│   │   └── contexts/       # Auth, Web3 contexts
│   ├── public/             # Static assets
│   ├── .env.development    # Dev environment
│   ├── .env.production     # Prod environment
│   ├── vite.config.ts      # Vite configuration
│   └── package.json        # Node dependencies
│
└── README.md               # Main documentation
```

## 🎓 Common Tasks

### Create First Admin User

```bash
# 1. Sign up regular account at http://localhost:3000/auth
# 2. Verify email (check terminal for verification code)
# 3. Make admin via API:

curl -X POST http://localhost:8001/api/admin/setup-first-admin \
  -H "Content-Type: application/json" \
  -d '{"email":"your-email@example.com"}'

# 4. Access admin panel at http://localhost:3000/admin
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8001/health

# Simple ping
curl http://localhost:8001/ping

# Get cryptocurrencies
curl http://localhost:8001/api/crypto/prices

# API documentation
open http://localhost:8001/api/docs
```

### Build for Production

```bash
# Backend (no build needed, just deploy Python app)
cd backend
# Set production environment variables

# Frontend
cd frontend
npm run build
# Creates ./dist folder

# Preview production build locally
npm run preview
```

## 🐛 Troubleshooting

### Backend Won't Start

**Issue**: `ConnectionError: Could not connect to MongoDB`

**Solution**:
```bash
# Option 1: Start local MongoDB
brew services start mongodb-community  # Mac
sudo systemctl start mongodb          # Linux
net start MongoDB                     # Windows

# Option 2: Use MongoDB Atlas
# Get connection string from https://cloud.mongodb.com
# Update MONGO_URL in backend/.env
```

**Issue**: `Port 8001 already in use`

**Solution**:
```bash
# Find process using port
lsof -i :8001              # Mac/Linux
netstat -ano | findstr :8001  # Windows

# Kill process
kill -9 <PID>              # Mac/Linux
taskkill /F /PID <PID>     # Windows

# Or change port in backend/.env
PORT=8002
```

### Frontend Won't Start

**Issue**: `EADDRINUSE: address already in use`

**Solution**:
```bash
# Kill process on port 3000
lsof -i :3000              # Mac/Linux
netstat -ano | findstr :3000  # Windows

# Or use different port
npm run dev -- --port 3001
```

**Issue**: `NetworkError when attempting to fetch resource`

**Solution**:
```bash
# 1. Make sure backend is running
curl http://localhost:8001/ping

# 2. Check VITE_API_BASE_URL is empty
cat frontend/.env.development

# 3. Restart frontend dev server
# Press Ctrl+C then npm run dev
```

### Database Issues

**Issue**: `Authentication failed` or `Connection refused`

**Solution**:
```bash
# Check MongoDB is running
mongosh  # Should connect

# Reset database (⚠️ deletes all data)
mongosh cryptovault --eval "db.dropDatabase()"

# Restart backend to recreate collections
```

### Health Check Failures

**Issue**: `Health check experiencing issues after 5 failures`

**Normal in these cases**:
- Backend is starting up (cold start)
- Backend temporarily unavailable
- Database initializing

**Not normal**:
- Backend not running
- Wrong URL configured
- Firewall blocking connection

**Solution**:
```bash
# 1. Verify backend is running
curl http://localhost:8001/ping

# 2. Check backend logs for errors
# Look in Terminal 1 for error messages

# 3. Restart backend
# Press Ctrl+C then python run_server.py
```

## 📚 Next Steps

### Learn the API

1. **API Documentation**: http://localhost:8001/api/docs
2. **Try endpoints**: Use the interactive docs
3. **Check schemas**: See request/response formats

### Explore Features

1. **User Authentication**: Sign up, log in, 2FA
2. **Wallet Management**: Deposit, withdraw, P2P transfer
3. **Trading**: Market orders, limit orders, advanced types
4. **Price Alerts**: Set up notifications
5. **Admin Panel**: User management, analytics

### Customize

1. **Branding**: Update logo, colors in `frontend/src/index.css`
2. **Features**: Enable/disable in `backend/config.py`
3. **Styling**: Modify Tailwind config in `frontend/tailwind.config.ts`

### Deploy

See deployment guides:
- `DEPLOYMENT_GUIDE.md` - Full deployment instructions
- `PRODUCTION_ENHANCEMENTS_COMPLETE.md` - Production checklist

## 🎯 Development Workflow

### Making Changes

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Make changes
# - Edit backend files in ./backend
# - Edit frontend files in ./frontend/src

# 3. Test changes
# - Backend: API docs + manual testing
# - Frontend: Browser + console logs

# 4. Commit
git add .
git commit -m "Add my feature"

# 5. Push
git push origin feature/my-feature
```

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Auto-reloads on file changes (Uvicorn --reload)
- **Frontend**: Instant HMR (Vite Hot Module Replacement)

Just save files and see changes immediately! 🔥

## ✅ Checklist

After quick start, verify:

- [ ] Backend running on http://localhost:8001
- [ ] Frontend running on http://localhost:3000
- [ ] MongoDB connected (check backend logs)
- [ ] Can access http://localhost:3000 in browser
- [ ] Can create account and log in
- [ ] Health check passing (check browser console)
- [ ] API docs accessible at http://localhost:8001/api/docs
- [ ] No errors in terminal or browser console

## 🆘 Getting Help

- **Documentation**: Check other .md files in project root
- **API Docs**: http://localhost:8001/api/docs
- **Logs**: Check terminal output for errors
- **Issues**: Create GitHub issue with error logs

## 🎉 You're Ready!

If you see:
- ✅ Backend logs showing successful startup
- ✅ Frontend loading at http://localhost:3000
- ✅ No errors in browser console
- ✅ Can create account and log in

**Congratulations!** 🎊 Your CryptoVault development environment is ready!

Start building! 🚀

---

**Need help?** Check:
- `DEPLOYMENT_GUIDE.md` - Production deployment
- `NETWORK_ERROR_FIX.md` - Connection issues  
- `HEALTH_CHECK_FIX_SUMMARY.md` - Health check details
- `PRODUCTION_ENHANCEMENTS_COMPLETE.md` - Feature documentation
