# Quick API Reference & Connection Guide

## 🚀 Quick Facts

| Component | Details |
|-----------|---------|
| **Frontend Framework** | React 18 + Vite |
| **Frontend URL** | https://yourdomain.com (Vercel) |
| **Backend Framework** | FastAPI (Python) |
| **Backend URL** | https://cryptovault-api.onrender.com |
| **Database** | MongoDB (Render/Mongo Atlas) |
| **Cache** | Redis |
| **Price Data** | CoinCap (primary) → Binance (fallback) → CoinGecko (REST fallback) |
| **Real-time** | WebSocket (/ws/prices) |
| **Auth Type** | JWT via HttpOnly Cookies |
| **Rate Limit** | 60 req/min per user |

---

## 🔌 How Frontend Talks to Backend

### REST API

**Every HTTP request includes:**
- Cookies with `access_token` and `refresh_token`
- Header: `Content-Type: application/json`

**Example:**
```javascript
// From: frontend/src/lib/apiClient.ts
const response = await apiClient.get('/api/crypto')
// Becomes HTTP request:
// GET https://cryptovault-api.onrender.com/api/crypto
// Headers: Cookie: 'access_token=...', Content-Type: 'application/json'
// (withCredentials: true)
```

### WebSocket

**Connection:**
```javascript
// From: frontend/src/hooks/usePriceWebSocket.ts
const ws = new WebSocket('wss://cryptovault-api.onrender.com/ws/prices')
```

**Messages received every 1-10 seconds:**
```json
{
  "type": "price_update",
  "prices": {
    "bitcoin": "45000.50",
    "ethereum": "2500.25"
  },
  "timestamp": "2024-01-16T10:30:00Z",
  "source": "coincap"
}
```

---

## 🔐 Authentication Flow (Simplified)

### Login
```
1. User submits email + password (Auth.tsx)
   ↓
2. POST /api/auth/login
   ↓
3. Backend validates in MongoDB, creates JWT tokens
   ↓
4. Backend sets HttpOnly cookies in response
   ↓
5. Frontend stores user info in React Context
   ✅ User logged in!
```

### Keep Logged In
```
1. Frontend makes request to any /api endpoint
   ↓
2. Browser automatically includes access_token cookie
   ↓
3. Backend verifies JWT signature
   ✅ Request allowed
```

### Logout
```
1. User clicks logout (Header component)
   ↓
2. POST /api/auth/logout
   ↓
3. Backend adds token to blacklist, deletes cookies
   ↓
4. Frontend clears user Context state
   ✅ User logged out
```

### Token Expires (Automatic Refresh)
```
1. access_token expires after 15 minutes
   ↓
2. Next API request returns 401
   ↓
3. Frontend axios interceptor automatically:
   - Calls POST /api/auth/refresh
   - Backend creates new access_token from refresh_token cookie
   - Retries original request
   ↓
4. User doesn't notice anything!
   ✅ Session extended
```

---

## 📚 Most Used Endpoints

### Get Market Data
```javascript
// Frontend: frontend/src/pages/Markets.tsx line 44
const data = await api.crypto.getAll()
// Endpoint: GET /api/crypto
// Returns: { cryptocurrencies: [...] }
```

### Get Price History
```javascript
// Frontend: frontend/src/components/TradingChart.tsx
const history = await api.crypto.getHistory('bitcoin', 7)
// Endpoint: GET /api/crypto/bitcoin/history?days=7
// Returns: { prices: [[timestamp, price], ...] }
```

### Get User Profile
```javascript
// Frontend: frontend/src/contexts/AuthContext.tsx line 30
const user = await api.auth.getProfile()
// Endpoint: GET /api/auth/me
// Returns: { id, email, name, verified, ... }
```

### Create Price Alert
```javascript
// Frontend: frontend/src/components/PriceAlertModal.tsx
await api.alerts.create({
  symbol: 'BTC',
  targetPrice: 50000,
  condition: 'ABOVE'
})
// Endpoint: POST /api/alerts
// Returns: { id, ... }
```

### Get Transactions
```javascript
// Frontend: frontend/src/pages/TransactionHistory.tsx
const txns = await api.transactions.getAll(skip=0, limit=50)
// Endpoint: GET /api/transactions?skip=0&limit=50
// Returns: { transactions: [...], total: N }
```

---

## 🛠️ Common Tasks

### Making an API Call

**Step 1: Use the API client**
```javascript
import { api } from '@/lib/apiClient'

// Automatically handles:
// ✅ Base URL (VITE_API_BASE_URL)
// ✅ Cookies (withCredentials)
// ✅ Error transformation
// ✅ Token refresh
```

**Step 2: Call the endpoint**
```javascript
try {
  const data = await api.crypto.getAll()
  // Handle success
  setData(data)
} catch (error) {
  // Error is already transformed to APIClientError
  // Properties: error.message, error.code, error.statusCode
  console.error(error.message)
}
```

### Subscribing to Price Updates

**Step 1: Use the hook**
```javascript
import { usePriceWebSocket } from '@/hooks/usePriceWebSocket'

const { prices, status } = usePriceWebSocket()
```

**Step 2: Use in component**
```jsx
const marketPrice = prices['bitcoin'] || 0
const isConnected = status.isConnected

return (
  <div>
    {isConnected ? (
      <span>Price: ${marketPrice}</span>
    ) : (
      <span>Price stream disconnected</span>
    )}
  </div>
)
```

### Adding a New API Endpoint

**Step 1: Backend - Create router endpoint**
```python
# backend/routers/myfeature.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/status")
async def get_status():
    return {"status": "ok"}
```

**Step 2: Backend - Mount router**
```python
# backend/server.py
from routers import myfeature
app.include_router(myfeature.router, prefix="/api")
```

**Step 3: Frontend - Add to API client**
```javascript
// frontend/src/lib/apiClient.ts
export const api = {
  // ... existing
  myfeature: {
    getStatus: () => apiClient.get('/api/myfeature/status'),
  }
}
```

**Step 4: Frontend - Use in component**
```javascript
const data = await api.myfeature.getStatus()
```

---

## 🚨 Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Network error` | Backend unreachable | Check backend URL, CORS |
| `Invalid JWT` | Token expired/invalid | Auto-refresh or re-login |
| `401 Unauthorized` | No token or invalid token | Login again |
| `429 Too Many Requests` | Rate limit exceeded | Wait 1-60 minutes |
| `500 Internal Server Error` | Backend bug | Check server logs |
| `WebSocket failed` | Connection timeout | Retry automatically (max 10x) |

### Frontend Error Types

**From apiClient.ts - transformError():**
```javascript
// BACKEND_ERROR: Server returned error
error.code === 'BACKEND_ERROR'

// NETWORK_ERROR: No internet or backend down
error.code === 'NETWORK_ERROR'

// RATE_LIMIT_ERROR: Too many requests
error.code === 'RATE_LIMIT_ERROR'

// VALIDATION_ERROR: Bad input
error.code === 'VALIDATION_ERROR'

// TIMEOUT_ERROR: Request took >30s
error.code === 'TIMEOUT_ERROR'
```

### Getting Error Details

```javascript
try {
  await api.crypto.getAll()
} catch (error) {
  console.log(error.message)          // "User not found"
  console.log(error.code)             // "BACKEND_ERROR"
  console.log(error.statusCode)       // 404
  console.log(error.requestId)        // "abc-123-xyz"
  console.log(error.details)          // { ... backend data ... }
}
```

---

## 📊 Data Flow Diagrams

### Markets Page Loading
```
Component mounts
  ↓
fetchMarketData() runs
  ↓
api.crypto.getAll()
  ↓
HTTP GET /api/crypto
  ↓
Backend: Check cache → CoinGecko API → Cache result
  ↓
Response: { cryptocurrencies: [...] }
  ↓
setMarketData(data)
  ↓
Component renders list
  ↓
[PARALLEL] WebSocket sends price updates every 1-10s
  ↓
Merge WebSocket prices with REST data
  ↓
Display live-updating markets
```

### Login Process
```
User enters email + password
  ↓
Form submit
  ↓
api.auth.login({ email, password })
  ↓
POST /api/auth/login (with credentials)
  ↓
Backend validates email/password in MongoDB
  ↓
Backend creates JWT tokens, sets HttpOnly cookies
  ↓
Response: { user: { id, email, name, ... } }
  ↓
Frontend sets AuthContext.user
  ↓
Redirect to /dashboard
  ↓
Future requests automatically include cookies
```

### Price Update Flow (WebSocket)
```
Backend starts (startup event)
  ↓
PriceStreamService.start() connects to CoinCap WS
  ↓
Receives price stream: { bitcoin: 45000, ethereum: 2500, ... }
  ↓
Updates in-memory cache + Redis
  ↓
Frontend connects to /ws/prices
  ↓
Backend PriceStreamManager.broadcast_loop():
  - Every 1 second
  - Send all prices to all connected clients
  ↓
Frontend WebSocket.onmessage receives prices
  ↓
usePriceWebSocket hook updates state
  ↓
Components using usePriceWebSocket() re-render with new prices
```

---

## 🔗 Important Files

### Must Know Files
- `frontend/src/lib/apiClient.ts` - All API calls go through here
- `frontend/src/contexts/AuthContext.tsx` - Login/logout state
- `frontend/src/hooks/usePriceWebSocket.ts` - Real-time prices
- `backend/server.py` - Main app, middleware, startup/shutdown
- `backend/routers/auth.py` - Authentication endpoints
- `backend/routers/websocket.py` - WebSocket broadcasting

### Feature Files
| Feature | Frontend | Backend |
|---------|----------|---------|
| Markets | `pages/Markets.tsx` | `routers/crypto.py` |
| Trading | `pages/Trade.tsx` | `routers/trading.py` |
| Wallet | `pages/Wallet.tsx` | `routers/wallet.py` |
| Alerts | `components/PriceAlerts.tsx` | `routers/alerts.py` |
| Portfolio | `pages/Dashboard.tsx` | `routers/portfolio.py` |

---

## 🧪 Testing the Connection

### Test REST API
```bash
# In browser console or postman
curl -X GET https://cryptovault-api.onrender.com/health
# Should return: { "status": "ok" }
```

### Test WebSocket
```javascript
// In browser console
const ws = new WebSocket('wss://cryptovault-api.onrender.com/ws/prices')
ws.onopen = () => console.log('Connected!')
ws.onmessage = (event) => console.log(JSON.parse(event.data))
```

### Test Frontend → Backend
1. Open your frontend app
2. Open DevTools (F12)
3. Go to Network tab
4. Navigate to Markets page
5. Should see GET request to `/api/crypto`
6. Response should have `cryptocurrencies` array

---

## 📝 Configuration Files

### Frontend
- `.env.development` - Local dev settings
- `.env.production` - Vercel production settings
- `vite.config.ts` - Dev server proxy config
- `vercel.json` - Vercel deployment config

### Backend
- `.env` - Environment variables (not in repo)
- `backend/config.py` - Settings class
- `docker-compose.yml` - Local DB/Redis setup

---

## 🎯 Common Debugging

### Frontend Can't Reach Backend
```javascript
// Check in browser console:
import.meta.env.VITE_API_BASE_URL
// Should show: https://cryptovault-api.onrender.com

// Check Network tab for /api requests
// Should NOT show "CORS error"
// Should show real response or 401/500 (not preflight error)
```

### WebSocket Won't Connect
```javascript
// Open DevSocket in browser console:
const ws = new WebSocket('wss://...')
ws.onerror = (e) => console.log(e)
ws.onclose = (e) => console.log(e.code, e.reason)
// Common codes: 1000 (normal), 1001 (going away), 1006 (abnormal)
```

### Rate Limited
```
Response headers:
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1234567890
```

### Token Refresh Issue
```javascript
// Frontend attempts refresh when 401 received:
// POST /api/auth/refresh

// If this also returns 401:
// → refresh_token expired or invalid
// → User must login again

// Check cookies in DevTools:
// Should see: access_token, refresh_token (both HttpOnly)
```

---

## 🚀 Deployment Checklist

### Before Vercel Deploy
- [ ] Set VITE_API_BASE_URL in Vercel dashboard
- [ ] Set VITE_ENABLE_SENTRY if using Sentry
- [ ] Test locally with correct .env.production
- [ ] Run `yarn build` and verify no errors

### Before Render Deploy
- [ ] Set MONGO_URL in Render environment
- [ ] Set JWT_SECRET in Render environment
- [ ] Ensure CORS origins include frontend domain
- [ ] Test health check: `/health`

---

## 📚 Additional Resources

- **Frontend**: `FRONTEND_BACKEND_ARCHITECTURE.md` (detailed section 1-10)
- **API**: `PRICE_STREAM_FIX_SUMMARY.md` (price stream architecture)
- **Deployment**: `frontend/VERCEL_DEPLOYMENT_GUIDE.md` (Vercel setup)
- **Backend**: `backend/DEPLOYMENT_GUIDE.md` (Render setup)
