# CryptoVault - API Endpoints & Frontend-Backend Sync Guide

## 🔗 Architecture Overview

```
Frontend (React/Vite)              Vercel/Dev Server
    ↓ (Relative paths: /api/*)
    ├── Development: Vite Proxy → Backend (localhost:8001)
    └── Production: Vercel Rewrites → Backend (https://cryptovault-api.onrender.com)
    
Backend (FastAPI)                  Render/Local
    ↓ (All routes under /api/)
    ├── /api/config           → Configuration
    ├── /api/auth/**          → Authentication
    ├── /api/crypto/**        → Cryptocurrency data
    ├── /api/portfolio/**     → User portfolio
    ├── /api/wallet/**        → Wallet management
    ├── /api/trading/**       → Trading operations
    ├── /api/transactions/**  → Transaction history
    ├── /api/transfers/**     → P2P transfers
    ├── /api/alerts/**        → Price alerts
    ├── /api/users/**         → User management
    ├── /api/admin/**         → Admin operations
    ├── /api/notifications/** → Notifications
    ├── /health              → Health check
    ├── /ping                → Ping check
    └── /socket.io/          → WebSocket
```

---

## 📡 API Communication Flow

### Development (Vite Proxy)
```
Browser Request
    ↓
http://localhost:3000/api/crypto
    ↓
Vite Dev Server (port 3000)
    ↓ (Proxy configured in vite.config.ts)
http://localhost:8001/api/crypto
    ↓
FastAPI Backend (port 8001)
    ↓
Response returned to Browser
```

**Key File:** `frontend/vite.config.ts` (lines 93-145)

### Production (Vercel Rewrites)
```
Browser Request
    ↓
https://www.cryptovault.financial/api/crypto
    ↓
Vercel Edge Network
    ↓ (Rewrite rule in vercel.json)
https://cryptovault-api.onrender.com/api/crypto
    ↓
Render Backend
    ↓
Response returned to Browser
```

**Key File:** `vercel.json` (rewrites section)

---

## 🔌 Detailed API Endpoints

### Configuration
```
GET /api/config
Returns: {
  appUrl, apiBaseUrl, preferRelativeApi, wsBaseUrl, socketIoPath,
  environment, version, sentry config, branding
}
Usage: Called on frontend app initialization to get runtime configuration
```

### Authentication
```
POST /api/auth/login
POST /api/auth/signup
POST /api/auth/logout
POST /api/auth/refresh
GET /api/auth/profile
POST /api/auth/verify-email
POST /api/auth/password-reset
```

### Cryptocurrency Data
```
GET /api/crypto              → All cryptocurrencies
GET /api/crypto/{coin_id}    → Specific cryptocurrency
GET /api/crypto/{coin_id}/history?days=7 → Price history
GET /api/prices              → Current prices
GET /api/prices/{symbol}     → Specific price
```

### User Portfolio
```
GET /api/portfolio           → Get portfolio
POST /api/portfolio          → Create portfolio
PUT /api/portfolio/{id}      → Update portfolio
DELETE /api/portfolio/{id}   → Delete portfolio
```

### Wallet Management
```
GET /api/wallet/balance      → Get wallet balance
POST /api/wallet/deposit     → Deposit funds
POST /api/wallet/withdraw    → Withdraw funds
GET /api/wallet/transfers    → Transfer history
POST /api/wallet/transfer    → Send P2P transfer
```

### Trading
```
GET /api/trading/orders      → Get user orders
POST /api/trading/orders     → Create order
GET /api/trading/orders/{id} → Get order details
PUT /api/trading/orders/{id} → Update order
DELETE /api/trading/orders/{id} → Cancel order
```

### Transactions
```
GET /api/transactions                → All transactions
GET /api/transactions/{id}           → Transaction details
POST /api/transactions               → Create transaction
GET /api/transactions?page=1&limit=10 → Paginated transactions
```

### Transfers (P2P)
```
GET /api/transfers            → Transfer history
POST /api/transfers           → Create transfer
GET /api/transfers/{id}       → Transfer details
PUT /api/transfers/{id}       → Update transfer status
```

### Alerts & Notifications
```
GET /api/alerts               → Price alerts
POST /api/alerts              → Create alert
DELETE /api/alerts/{id}       → Delete alert
GET /api/notifications        → Notifications
POST /api/notifications/{id}/read → Mark as read
```

### User Management
```
GET /api/users/me             → Current user info
PUT /api/users/me             → Update profile
GET /api/users/{id}           → User details
```

### Admin Operations
```
GET /api/admin/stats          → Dashboard stats
GET /api/admin/users          → All users
GET /api/admin/transactions   → All transactions
POST /api/admin/users/{id}/suspend → Suspend user
```

### WebSocket (Real-time)
```
WS /socket.io/
Events:
  - price_update      → Real-time price changes
  - portfolio_update  → Portfolio changes
  - notification      → New notifications
```

### Health & Monitoring
```
GET /ping                     → Simple ping (returns ok)
GET /health                   → Full health status
GET /api/config               → Configuration (public)
GET /api/docs                 → Swagger UI
GET /api/redoc                → ReDoc
GET /api/openapi.json         → OpenAPI spec
```

---

## 🔐 Frontend API Client Configuration

### File: `frontend/src/lib/apiClient.ts`

**Base URL Resolution:**
```typescript
// Development: Uses relative paths (proxy)
// Production: Uses VITE_API_BASE_URL env var or relative paths

const BASE_URL = resolveApiBaseUrl();  // Empty string in dev/prod
// All requests: GET /api/crypto → Proxy/Rewrite handles routing
```

**Request Interceptor:**
- Adds authorization header
- Adds CSRF token for mutations
- Handles token refresh on 401

**Response Interceptor:**
- Transforms errors to APIClientError
- Handles CORS errors
- Retries on network failure

**Usage:**
```typescript
import { api } from '@/lib/apiClient';

// Get crypto prices
const prices = await api.crypto.getAll();

// Create order
const order = await api.orders.create({
  trading_pair: 'BTC/USD',
  quantity: 0.5,
  price: 45000
});

// Real-time updates
socket.on('price_update', (data) => {
  console.log('Price updated:', data);
});
```

---

## 🔧 Backend Configuration

### File: `backend/config.py`

**Environment-Driven:**
```python
# All settings from environment variables
MONGO_URL = os.getenv('MONGO_URL')
JWT_SECRET = os.getenv('JWT_SECRET')
CORS_ORIGINS = os.getenv('CORS_ORIGINS').split(',')
UPSTASH_REDIS_REST_URL = os.getenv('UPSTASH_REDIS_REST_URL')
```

**Available Settings:**
- Database: MONGO_URL, DB_NAME
- Cache: USE_REDIS, UPSTASH_REDIS_REST_URL
- Auth: JWT_SECRET, JWT_ALGORITHM
- CORS: CORS_ORIGINS
- External APIs: COINCAP_API_KEY, NOWPAYMENTS_API_KEY
- Email: SENDGRID_API_KEY, EMAIL_FROM
- Error Tracking: SENTRY_DSN

---

## 🚀 Frontend Integration Points

### 1. API Client Initialization (`frontend/src/App.tsx`)
```typescript
import { api } from '@/lib/apiClient';

// Called once on app startup
useEffect(() => {
  api.initializeCSRFToken();
  healthCheckService.start();
}, []);
```

### 2. Data Fetching (Example: `frontend/src/hooks/useCryptoData.ts`)
```typescript
import { api } from '@/lib/apiClient';

export function useCryptoData() {
  const [data, setData] = useState([]);
  
  useEffect(() => {
    api.crypto.getAll()
      .then(res => setData(res.cryptocurrencies))
      .catch(err => console.error(err));
  }, []);
  
  return data;
}
```

### 3. WebSocket Connection (`frontend/src/contexts/SocketContext.tsx`)
```typescript
import io from 'socket.io-client';

const socket = io(resolveWsBaseUrl(), {
  path: resolveSocketIoPath(),
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000
});

socket.on('price_update', handlePriceUpdate);
```

### 4. Runtime Configuration (`frontend/src/lib/runtimeConfig.ts`)
```typescript
// Called on app initialization
const config = await loadRuntimeConfig();
// Provides: apiBaseUrl, wsBaseUrl, environment, sentry config, etc.
```

---

## 🔄 Frontend-Backend Sync Checklist

### Development Environment

- [ ] **Backend Running**
  ```bash
  python run_server.py
  # Should start on http://localhost:8001
  ```

- [ ] **Frontend Running**
  ```bash
  cd frontend && yarn dev
  # Should start on http://localhost:3000
  ```

- [ ] **Health Checks**
  ```bash
  curl http://localhost:8001/ping
  # Response: { "status": "ok", "message": "pong" }
  
  curl http://localhost:3000/api/ping
  # Response: Should proxy to backend ping
  ```

- [ ] **CORS Verification**
  ```bash
  curl -I http://localhost:8001/api/crypto \
    -H "Origin: http://localhost:3000"
  # Should include: Access-Control-Allow-Origin: http://localhost:3000
  ```

- [ ] **Configuration Loading**
  - Browser Console: Check for "[API Client] Initialized" message
  - Should show: `(empty - using relative paths)` for BASE_URL

- [ ] **WebSocket Connection**
  - Browser DevTools → Network → Filter: WS
  - Should see WebSocket connection to `/socket.io/`

### Production Environment

- [ ] **Environment Variables Set** (on Render)
  - MONGO_URL
  - JWT_SECRET
  - CSRF_SECRET
  - CORS_ORIGINS
  - Other service keys

- [ ] **Vercel Rewrites Configured**
  - `vercel.json` rewrites point to backend URL
  - All `/api/*` routes rewrite to `https://cryptovault-api.onrender.com/api/*`

- [ ] **CORS Origins Match**
  ```
  Frontend: https://www.cryptovault.financial
  CORS_ORIGINS: https://www.cryptovault.financial,http://localhost:3000
  ```

- [ ] **Health Checks**
  ```bash
  curl https://cryptovault-api.onrender.com/ping
  curl https://cryptovault-api.onrender.com/health
  curl https://www.cryptovault.financial/api/ping
  ```

---

## 🧪 Testing API Endpoints

### Using cURL

**Get Crypto Prices:**
```bash
curl -X GET http://localhost:8001/api/crypto \
  -H "Content-Type: application/json"
```

**Get Configuration:**
```bash
curl -X GET http://localhost:8001/api/config \
  -H "Content-Type: application/json"
```

**Test with CORS Headers:**
```bash
curl -X GET http://localhost:8001/api/crypto \
  -H "Origin: http://localhost:3000" \
  -H "Content-Type: application/json" \
  -v
```

### Using Browser Console

```javascript
// Test relative path (should work in dev)
fetch('/api/ping')
  .then(r => r.json())
  .then(d => console.log('API Response:', d));

// Test with CORS headers
fetch('/api/crypto', {
  method: 'GET',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' }
})
  .then(r => r.json())
  .then(d => console.log('Crypto Data:', d));

// Test WebSocket
const socket = io('/socket.io/', {
  reconnection: true,
  reconnectionDelay: 1000
});
socket.on('connect', () => console.log('✓ WebSocket connected'));
socket.on('price_update', (data) => console.log('Price update:', data));
```

---

## 🔍 Debugging Common Issues

### Issue: CORS Error
```
Access to XMLHttpRequest at 'http://localhost:8001/api/crypto' 
from origin 'http://localhost:3000' has been blocked by CORS policy
```

**Solution:**
1. Check `CORS_ORIGINS` in backend/.env
2. Verify backend is running
3. Check Vite proxy is configured
4. Restart both frontend and backend

### Issue: 404 Not Found on /api/*
```
GET /api/crypto 404 Not Found
```

**Solution:**
1. Verify backend server is running on port 8001
2. Check router is registered in backend/server.py
3. Check API path is correct (should be `/api/crypto`, not `/crypto`)

### Issue: WebSocket Connection Failed
```
WebSocket connection to 'ws://localhost:3000/socket.io/' failed
```

**Solution:**
1. Check `resolveWsBaseUrl()` returns correct URL
2. Verify Socket.IO is mounted in backend
3. Check WebSocket proxy in vite.config.ts is configured
4. Restart both servers

### Issue: Empty Relative Path for API
```
[API Client] Initialized with BASE_URL: (empty - using relative paths)
```

**This is expected!** 
- In development: Vite proxy handles routing
- In production: Vercel rewrites handle routing
- Frontend uses relative paths `/api/*` which get proxied/rewritten

---

## 📊 Configuration Files Reference

| File | Purpose | Key Settings |
|------|---------|--------------|
| `backend/config.py` | Backend configuration | MONGO_URL, JWT_SECRET, CORS_ORIGINS, etc. |
| `backend/.env` | Backend environment variables | All configuration values |
| `backend/server.py` | FastAPI app setup | CORS middleware, routers, health checks |
| `frontend/vite.config.ts` | Frontend dev server config | Proxy settings for localhost:8001 |
| `frontend/src/lib/apiClient.ts` | API communication | Base URL, interceptors, error handling |
| `frontend/src/lib/runtimeConfig.ts` | Runtime config loading | Load config from /api/config |
| `vercel.json` | Production deployment | Rewrites, headers, environment variables |

---

## 🔄 Data Flow Diagram

```
User Action (e.g., "Load Prices")
    ↓
Frontend Component
    ↓
useCryptoData() Hook
    ↓
api.crypto.getAll()
    ↓
axios.get('/api/crypto')
    ↓
[DEV] Vite Proxy → localhost:8001/api/crypto
[PROD] Vercel Rewrite → cryptovault-api.onrender.com/api/crypto
    ↓
FastAPI Backend
    ↓
multi_source_service.get_prices()
    ↓
CoinCap API (primary) or CoinPaprika (fallback)
    ↓
Response: { cryptocurrencies: [...] }
    ↓
Frontend updates UI with crypto prices
```

---

## 🎯 Key Points

1. **Relative Paths:** Frontend always uses `/api/*` paths
2. **Dev Proxy:** Vite proxy routes `/api/*` to `localhost:8001`
3. **Prod Rewrites:** Vercel rewrites route `/api/*` to Render backend
4. **Config Endpoint:** `/api/config` provides runtime configuration
5. **CORS:** Backend validates `CORS_ORIGINS` environment variable
6. **WebSocket:** Socket.IO available at `/socket.io/` endpoint
7. **Health Checks:** Use `/ping` and `/health` for monitoring
8. **Error Handling:** API Client has built-in error transformation and retry logic

---

## ✅ Verification Steps

### Local Development
```bash
# 1. Start backend
python run_server.py
# Check logs: "✅ Environment Validated" and "Uvicorn running on..."

# 2. Start frontend (in new terminal)
cd frontend && yarn dev
# Check logs: "[Vite] Backend proxy configured for: http://localhost:8001"

# 3. Visit http://localhost:3000 in browser
# Check console: "[API Client] Initialized with BASE_URL: (empty - using relative paths)"

# 4. Test API
curl http://localhost:3000/api/ping
# Should return: { "status": "ok", "message": "pong" }
```

### Production
```bash
# 1. Check Render backend
curl https://cryptovault-api.onrender.com/health
# Should return: { "status": "healthy", ... }

# 2. Check Vercel frontend
curl https://www.cryptovault.financial/api/ping
# Should return: { "status": "ok", ... }

# 3. Check CORS
curl -I https://cryptovault-api.onrender.com/api/crypto \
  -H "Origin: https://www.cryptovault.financial"
# Should include: Access-Control-Allow-Origin: https://www.cryptovault.financial
```

---

**Status:** ✅ All API endpoints documented and synced  
**Configuration:** ✅ Environment-driven, production-ready  
**Testing:** ✅ Development and production verification steps provided
