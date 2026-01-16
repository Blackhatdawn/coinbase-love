# Frontend-Backend Architecture Analysis

## Quick Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React + Vite)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐       ┌──────────────────────┐        │
│  │  Pages & Components  │       │  State Management    │        │
│  │  - Markets.tsx       │───→   │  - AuthContext       │        │
│  │  - Dashboard.tsx     │   │   │  - Web3Context       │        │
│  │  - Trade.tsx         │   │   │  - useAuth()         │        │
│  │  - etc...            │   │   │  - usePriceWebSocket │        │
│  └──────────────────────┘   │   └──────────────────────┘        │
│           │                 │                                    │
│           └─────────────────┘                                    │
│                 │                                                │
│  ┌──────────────▼──────────────────────────────────────┐        │
│  │   API Client Layer (apiClient.ts)                   │        │
│  │   - Axios instance with credentials                │        │
│  │   - Request/Response interceptors                  │        │
│  │   - Token refresh logic                            │        │
│  │   - Error transformation                           │        │
│  └──────────────┬──────────────────────────────────────┘        │
│                 │ REST API calls (JSON)                         │
│                 │ WebSocket connections                         │
│                 ▼                                                │
└─────────────────────────────────────────────────────────────────┘
         │                                      │
         │ HTTPS/WSS                           │
         │                                      │
         ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│               BACKEND (FastAPI + Python)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────┐        │
│  │ Server (server.py) - Main App                       │        │
│  │ - CORS middleware (allow_credentials=True)          │        │
│  │ - Rate limiting via slowapi                         │        │
│  │ - Security headers middleware                       │        │
│  │ - Request ID tracking middleware                    │        │
│  │ - Sentry error tracking                             │        │
│  └─────────────────────────────────────────────────────┘        │
│           │                                                      │
│  ┌────────┴──────────────────────────────────────────────┐     │
│  │  Router Mounting (server.py lines 372-383)           │     │
│  │                                                        │     │
│  │  ├─ auth.router → /api/auth                           │     │
│  │  ├─ portfolio.router → /api/portfolio                 │     │
│  │  ├─ trading.router → /api/trading                     │     │
│  │  ├─ crypto.router → /api/crypto                       │     │
│  │  ├─ prices.router → /api/prices                       │     │
│  │  ├─ wallet.router → /api/wallet                       │     │
│  │  ├─ alerts.router → /api/alerts                       │     │
│  │  ├─ transactions.router → /api/transactions           │     │
│  │  ├─ admin.router → /api/admin                         │     │
│  │  └─ websocket.router → /ws/prices & /ws/prices/{id}   │     │
│  └────────┬──────────────────────────────────────────────┘     │
│           │                                                      │
│  ┌────────▼──────────────────────────────────────────────┐     │
│  │  Services & Background Tasks                         │     │
│  │                                                        │     │
│  │  ├─ PriceStreamService (WebSocket to CoinCap/Binance)│     │
│  │  │  └─ Connects to: wss://ws.coincap.io/prices       │     │
│  │  │  └─ Fallback: wss://stream.binance.com/...        │     │
│  │  │  └─ Updates: In-memory cache + Redis              │     │
│  │  │                                                    │     │
│  │  ├─ CoinGecko Service (REST API)                      │     │
│  │  │  └─ Fetches: prices, market data, history         │     │
│  │  │  └─ Caching: Redis (TTL: 5-30 seconds)            │     │
│  │  │                                                    │     │
│  │  └─ WebSocket Broadcasting                            │     │
│  │     └─ Broadcasts prices to all connected clients    │     │
│  └────────┬──────────────────────────────────────────────┘     │
│           │                                                      │
│  ┌────────▼──────────────────────────────────────────────┐     │
│  │  Data Layer                                            │     │
│  │  - MongoDB (user data, portfolios, orders, alerts)    │     │
│  │  - Redis (price cache, session cache)                │     │
│  │  - External APIs (CoinCap, Binance, CoinGecko)       │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Connection Points & Protocols

### A. REST API (HTTP/HTTPS)
- **Base URL**: `https://cryptovault-api.onrender.com` (production) or `http://localhost:8000` (development)
- **Protocol**: HTTPS with credentials (cookies)
- **Client Library**: Axios (`frontend/src/lib/apiClient.ts`)
- **Cookie Support**: `withCredentials: true` - sends HttpOnly cookies with every request
- **Automatic Features**:
  - Token refresh on 401 response
  - Request ID tracking
  - Error transformation
  - Request timeout (30 seconds)

### B. WebSocket (Real-time)
- **URL**: `wss://cryptovault-api.onrender.com/ws/prices` (production) or `ws://localhost:8000/ws/prices` (development)
- **Client Library**: Native WebSocket API (`frontend/src/hooks/usePriceWebSocket.ts`)
- **Features**:
  - Automatic reconnection (max 10 attempts)
  - Keep-alive pings every 30 seconds
  - Price update broadcasts (every 1-10 seconds)
  - Connection status monitoring

---

## 2. Authentication & Session Flow

### Complete Login Flow

```
User submits credentials (Auth.tsx)
        ↓
frontend/src/contexts/AuthContext.signIn()
        ↓
api.auth.login({ email, password })  [POST /api/auth/login]
        ↓
FRONTEND AXIOS:
  • withCredentials: true
  • Headers: { 'Content-Type': 'application/json' }
        ↓
HTTP Request sent with cookies (if any)
        ↓
BACKEND PROCESSING (backend/routers/auth.py lines 141-248):
  1. Validate email/password against MongoDB
  2. Check if user exists, password matches
  3. Create JWT tokens:
     - access_token (15 min expiry)
     - refresh_token (7 days expiry)
  4. Set HttpOnly cookies in response:
     - Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=Lax
     - Set-Cookie: refresh_token=<JWT>; HttpOnly; Secure; SameSite=Lax
  5. Return response with user data JSON
        ↓
BROWSER:
  • Cookies stored automatically (HttpOnly = JS cannot access)
  • Frontend state updated with user info (AuthContext)
        ↓
Login successful, redirect to /dashboard
```

### Session Recovery & Keep-Alive

```
User returns to app (or page refresh)
        ↓
frontend/src/contexts/AuthContext.checkSession()
        ↓
api.auth.getProfile()  [GET /api/auth/me]
        ↓
Browser automatically includes cookies in request
        ↓
BACKEND verifies access_token from cookie
        ↓
✅ If valid: Return user profile
❌ If expired: Return 401
        ↓
If 401, axios response interceptor triggers:
  • Call api.auth.refresh() [POST /api/auth/refresh]
  • Server verifies refresh_token from cookie
  • Server creates new access_token, sets it in cookie
  • Retry original request
  ↓
Session restored, user info updated
```

### Logout Flow

```
User clicks logout
        ↓
frontend/src/contexts/AuthContext.signOut()
        ↓
api.auth.logout()  [POST /api/auth/logout]
        ↓
BACKEND (backend/routers/auth.py lines 251-278):
  1. Extract access_token from cookie
  2. Add to blacklist (MongoDB collection: blacklisted_tokens)
  3. Delete cookies from response:
     - Set-Cookie: access_token=; Max-Age=0
     - Set-Cookie: refresh_token=; Max-Age=0
  4. Return success
        ↓
FRONTEND:
  • Cookies cleared by browser
  • Redux/Context state cleared
  • Redirect to /auth
```

---

## 3. API Endpoint Inventory

### Authentication (`/api/auth`)
```
POST   /api/auth/signup
POST   /api/auth/login
POST   /api/auth/logout
POST   /api/auth/refresh
GET    /api/auth/me
PUT    /api/auth/profile
POST   /api/auth/change-password
POST   /api/auth/verify-email
POST   /api/auth/resend-verification
POST   /api/auth/forgot-password
POST   /api/auth/reset-password
GET    /api/auth/validate-reset-token/:token
POST   /api/auth/2fa/setup
POST   /api/auth/2fa/verify
GET    /api/auth/2fa/status
POST   /api/auth/2fa/disable
POST   /api/auth/2fa/backup-codes
```

### Cryptocurrency Data (`/api/crypto`)
```
GET    /api/crypto
GET    /api/crypto/:coin_id
GET    /api/crypto/:coin_id/history?days=7
```

### Portfolio Management (`/api/portfolio`)
```
GET    /api/portfolio
POST   /api/portfolio/holding
DELETE /api/portfolio/holding/:symbol
GET    /api/portfolio/holding/:symbol
```

### Trading & Orders
```
GET    /api/orders
POST   /api/orders
GET    /api/orders/:order_id
GET    /api/trading
```

### Pricing & Market Data (`/api/prices`)
```
GET    /api/prices
GET    /api/prices/:symbol
GET    /api/prices/status/health
GET    /api/prices/bulk?symbols=BTC,ETH
GET    /api/prices/metrics?symbols=BTC,ETH
```

### Wallet & Transactions
```
GET    /api/wallet/balance
POST   /api/wallet/deposit/create
GET    /api/wallet/deposit/:order_id
GET    /api/wallet/deposits?skip=0&limit=20
POST   /api/wallet/withdraw
GET    /api/wallet/withdrawals?skip=0&limit=20
GET    /api/transactions?skip=0&limit=50&type=DEPOSIT
GET    /api/transactions/:id
GET    /api/transactions/summary/stats
```

### Alerts & Notifications
```
GET    /api/alerts
GET    /api/alerts/:id
POST   /api/alerts
PATCH  /api/alerts/:id
DELETE /api/alerts/:id
```

### Admin Panel
```
GET    /api/admin/stats
GET    /api/admin/users?skip=0&limit=50
GET    /api/admin/trades?skip=0&limit=100
GET    /api/admin/audit-logs?skip=0&limit=100
POST   /api/admin/setup-first-admin
GET    /api/admin/withdrawals?skip=0&limit=50
POST   /api/admin/withdrawals/:id/approve
POST   /api/admin/withdrawals/:id/complete
POST   /api/admin/withdrawals/:id/reject
```

### Health & Monitoring
```
GET    /health
GET    /api/health
```

### WebSocket Endpoints
```
WS     /ws/prices
WS     /ws/prices/:symbol
```

---

## 4. Data Flow Examples

### Example 1: Markets Page - Fetching Cryptocurrencies

**Timeline:**

```
Time T0: User navigates to /markets
         ↓ (0ms)
         React mounts Markets.tsx component
         useEffect triggers fetchMarketData()

Time T0+10ms:
         api.crypto.getAll()  [line 44 in Markets.tsx]
         ↓
         frontend/src/lib/apiClient.ts
         • axios GET request to /api/crypto
         • Headers: { Cookie: 'access_token=...', 'Content-Type': 'application/json' }
         • Body: none
         ↓
         HTTPS request to: https://cryptovault-api.onrender.com/api/crypto

Time T0+50ms: Backend receives request
         backend/server.py:
         • RequestIDMiddleware: generates unique request ID
         • RateLimitHeadersMiddleware: checks rate limit
         • SecurityHeadersMiddleware: adds security headers
         • Router matches: /api/crypto → crypto.router
         ↓
         backend/routers/crypto.py (lines 12-20):
         • Extract user from access_token cookie
         • Call coingecko_service.get_prices()
         ↓
         backend/coingecko_service.py (lines 34-103):
         • Check Redis cache for "prices:all"
         • If cached (not expired): return from cache
         • If not cached:
           - Make HTTP GET to https://api.coingecko.com/api/v3/simple/price
           - Parse response
           - Store in Redis with 5-minute TTL
           - Return data

Time T0+200ms: Response sent back
         HTTP 200 OK with JSON:
         {
           "cryptocurrencies": [
             { "id": "bitcoin", "symbol": "BTC", "price": 45000.50, ... },
             { "id": "ethereum", "symbol": "ETH", "price": 2500.25, ... },
             ...
           ]
         }

Time T0+220ms: Frontend processes response
         • axios interceptor parses JSON
         • setMarketData(response.cryptocurrencies)
         • Component re-renders with market list

Time T0+250ms: Parallel WebSocket Updates
         • usePriceWebSocket hook has already connected
         • WebSocket messages start arriving:
           { "type": "price_update", "prices": { "bitcoin": "45050.75", ... } }
         • setPrices(message.prices)
         • Markets page merges WS prices with REST data
         • Display shows real-time prices

FINAL STATE:
✅ Markets page shows list of cryptocurrencies
✅ Prices from REST API (cached, ~5s fresh)
✅ Real-time price updates from WebSocket (1-10 sec fresh)
```

### Example 2: WebSocket Price Stream Connection

**Timeline:**

```
Time T0: User opens app
         ↓
         frontend/src/hooks/usePriceWebSocket.ts useEffect() fires (line 286)
         ↓
         Determine WebSocket URL:
         • If import.meta.env.PROD: 'wss://cryptovault-api.onrender.com/ws/prices'
         • Else: 'ws://localhost:8000/ws/prices'
         ↓
         new WebSocket(url)

Time T0+10ms: Browser initiates WebSocket handshake
         HTTP GET with headers:
         • Connection: Upgrade
         • Upgrade: websocket
         • Sec-WebSocket-Key: <random>
         • Sec-WebSocket-Version: 13
         ↓
         Sent to backend: wss://cryptovault-api.onrender.com/ws/prices

Time T0+50ms: Backend receives WebSocket upgrade request
         backend/routers/websocket.py (lines 142-172):
         • @router.websocket("/ws/prices") handler receives request
         • await price_stream_manager.connect(websocket)
         ↓
         PriceStreamManager.connect():
         • await websocket.accept() — accepts connection
         • self.active_connections.add(websocket)
         • Start broadcast loop (if not running):
           asyncio.create_task(self.start_broadcast_loop())
         • Send initial connection message:
           {"type": "connection", "status": "connected", ...}

Time T0+60ms: Frontend WebSocket opens
         ws.onopen event fires
         ↓
         updateStatus({ isConnected: true })
         ↓
         Start ping interval (send ping every 30s to keep alive)

Time T0+100ms: Backend broadcast loop starts
         backend/routers/websocket.py (lines 97-118):
         • while True loop
         • Every 1 second:
           - Check if price_stream_service.prices is populated
           - Create message: {"type": "price_update", "prices": {...}, ...}
           - Send to all active_connections

Time T0+150ms: Backend price stream is running
         backend/services/price_stream.py:
         • async connection to wss://ws.coincap.io/prices?assets=ALL
         • Receives streams of prices from CoinCap
         • Processes message:
             { "bitcoin": "45000.50", "ethereum": "2500.25", ... }
         • Updates: self.prices = {...}
         • Updates Redis cache for each coin

Time T0+200ms: First price update sent to frontend
         Backend broadcast loop sends:
         { "type": "price_update", "prices": { "bitcoin": "45000.50", ... } }
         ↓
         Browser WebSocket receives data event
         ↓
         frontend ws.onmessage:
         • Parse JSON: const data = JSON.parse(event.data)
         • Dispatch price_update to hook state
         • setPrices(data.prices)
         • Call onPriceUpdate callback if provided

Time T0+210ms: Frontend renders with live prices
         Markets.tsx or Dashboard.tsx uses prices from usePriceWebSocket
         ↓
         Merges with REST data:
         const wsPrice = prices[symbol.toLowerCase()]
         displayPrice = wsPrice ? wsPrice : restPrice
         ↓
         UI shows live-updating prices

CONTINUOUS:
Every 1-10 seconds: Backend broadcasts new prices
Every 30 seconds: Frontend sends ping, backend responds pong
Backend: Maintains WebSocket to CoinCap (auto-reconnects on failure)
Backend: Falls back to Binance if CoinCap unreachable >30s

ON DISCONNECT:
If frontend closes: price_stream_manager.disconnect()
If backend crashes: frontend tries reconnect (max 10 attempts)
```

---

## 5. Error Handling Flow

### API Error Transformation

```
Backend error scenario: Database timeout on GET /api/crypto

Time T: Backend processing request
        ↓
        CoinGecko API call takes >30s
        ↓
        Backend raises: HTTPException(status_code=500, detail="Timeout")

Time T+30s: Response sent to frontend
        HTTP 500 Internal Server Error
        Headers: { 'x-request-id': 'abc-123', ... }
        Body: { "detail": "Timeout" }

Time T+30.5s: axios response interceptor catches error
        frontend/src/lib/apiClient.ts (line 104)
        ↓
        Calls transformError(axiosError) (lines 189-290)
        ↓
        Transform logic:
        1. Check if error.response?.data?.error exists (backend structured format)
           → If not, continue
        2. Check if error.response?.data?.detail exists (FastAPI format)
           → YES: Create APIClientError with code='BACKEND_ERROR'
        3. Extract error message
        4. Create APIClientError instance:
           new APIClientError(
             message: "Timeout",
             code: "BACKEND_ERROR",
             statusCode: 500,
             requestId: "abc-123",
             details: { "detail": "Timeout" }
           )
        ↓
        Return Promise.reject(error)

Time T+30.6s: Component catches error
        Try/catch in Markets.tsx (lines 45-69):
        catch (error) {
          setNetworkError(error.message)
          toast.error("Failed to load markets")
        }
        ↓
        User sees error message in UI and toast notification

ADDITIONAL CASES:

Rate Limit (429):
  Backend: slowapi Limiter blocks request (60 req/min per user)
  → Returns HTTP 429 with headers: { 'X-RateLimit-Reset': '1234567890' }
  → Frontend transformError extracts reset time from header
  → Shows user: "Rate limit exceeded. Try again after 12:34 PM"

Network Error (offline):
  Browser: Cannot reach backend
  → axios error: { code: 'ECONNABORTED' }
  → transformError detects: !error.response
  → Returns: APIClientError with code='NETWORK_ERROR'
  → Frontend shows: "Network error. Please check your internet connection"

Validation Error (400):
  Backend: Pydantic validation fails (invalid email format)
  → Returns HTTP 400 with body: [
      { "loc": ["email"], "msg": "Invalid email format", "type": "value_error" }
    ]
  → Frontend transformError detects: Array format
  → Combines messages: "Invalid email format"
  → Shows form validation error
```

---

## 6. Configuration & Environment Variables

### Frontend Configuration

**File**: `frontend/.env.production` and `frontend/.env.development`

```env
# Production
VITE_API_BASE_URL=https://cryptovault-api.onrender.com
VITE_APP_NAME=CryptoVault
VITE_APP_VERSION=1.0.0
VITE_NODE_ENV=production
VITE_ENABLE_SENTRY=true
VITE_SENTRY_DSN=https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/...

# Development
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=CryptoVault
VITE_APP_VERSION=1.0.0
VITE_NODE_ENV=development
VITE_ENABLE_SENTRY=false
VITE_SENTRY_DSN=
```

**How Frontend Uses These:**

1. **VITE_API_BASE_URL**:
   - `frontend/src/lib/apiClient.ts` line 9: `const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''`
   - If empty in development, uses Vite proxy (localhost:3000 → localhost:8000)
   - If set, all requests go to this URL

2. **WebSocket URL**:
   - `frontend/src/hooks/usePriceWebSocket.ts` line 39:
   - `const DEFAULT_URL = import.meta.env.PROD ? 'wss://...' : 'ws://localhost:8000/...'`

3. **Sentry Error Tracking**:
   - `frontend/src/lib/sentry.ts` line 11: checks `VITE_ENABLE_SENTRY === 'true'`
   - Only initializes in production if enabled

### Backend Configuration

**File**: `backend/.env` (not in repo, set via environment variables in production)

```env
# Database
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/cryptovault
MONGODB_DB_NAME=cryptovault

# JWT & Security
JWT_SECRET=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=noreply@cryptovault.com

# Sentry (error tracking)
SENTRY_DSN=https://...

# Environment
ENVIRONMENT=production
```

**Backend Usage** (`backend/config.py`):

```python
class Settings(BaseSettings):
    mongo_url: str = Field(..., env="MONGO_URL")
    db_name: str = Field(default="cryptovault", env="MONGODB_DB_NAME")
    jwt_secret: str = Field(..., env="JWT_SECRET")
    environment: str = Field(default="development", env="ENVIRONMENT")
    ...

settings = Settings()  # Auto-loads from .env and environment variables
```

**Impact on Cookies**:
```python
# backend/routers/auth.py line 230
secure = settings.environment == 'production'
# In production: Set-Cookie: ... ; Secure ; HttpOnly
# In development: Set-Cookie: ... ; HttpOnly (no Secure flag)
```

---

## 7. Request/Response Cycle - Complete Example

### Full Markets Request Cycle

```
STEP 1: User Action
────────────────────
Frontend: Click "Markets" in navigation
Path: /markets

STEP 2: Component Mounting
────────────────────────────
File: frontend/src/pages/Markets.tsx
useEffect hook at line 40 fires:
  1. setLoading(true)
  2. Call fetchMarketData()

STEP 3: API Call
────────────────
File: frontend/src/lib/apiClient.ts
Method: api.crypto.getAll() (line 426)
  ├─ Calls: apiClient.get('/api/crypto')
  ├─ Axios GET request
  ├─ URL: import.meta.env.VITE_API_BASE_URL + '/api/crypto'
  ├─ Headers:
  │  ├─ Cookie: 'access_token=eyJhbGc...; refresh_token=eyJhbGc...'
  │  ├─ Content-Type: 'application/json'
  │  └─ X-Requested-With: 'XMLHttpRequest'
  └─ withCredentials: true (cookie included)

STEP 4: Network
───────────────
Browser → HTTPS → Load Balancer → Backend Server

STEP 5: Backend Processing
────────────────────────────
File: backend/server.py (startup listeners)
1. RequestIDMiddleware: generates request_id = 'abc-123-xyz'
2. RateLimitHeadersMiddleware: checks rate limit
   └─ Key derived from access_token in cookie
   └─ Limit: 60 requests/minute
   └─ Decision: ALLOW
3. SecurityHeadersMiddleware: adds security headers to response
4. Sentry integration: logs request start

File: backend/server.py (router mounting)
→ Matches route /api/crypto
→ Dispatches to crypto.router

File: backend/routers/crypto.py
Function: get_all_cryptocurrencies (line 12)
  1. Check request.cookies['access_token']
  2. Decode JWT to verify signature and expiry
  3. Extract user_id from token claims
  4. Call coingecko_service.get_prices()

File: backend/coingecko_service.py
Function: get_prices() (lines 34-103)
  1. Check Redis cache key: "prices:all"
  2. If cached (< 5 minutes old):
     ├─ Return from cache (fast path, ~5ms)
  3. Else:
     ├─ Make HTTP request to CoinGecko API
     │  Method: GET https://api.coingecko.com/api/v3/simple/price
     │  Params: ids=bitcoin,ethereum,...&vs_currencies=usd
     │  Headers: accept: application/json
     ├─ Wait for response (~100-500ms depending on network)
     ├─ Parse JSON response
     ├─ Transform to internal format (lines 89-103):
     │  {
     │    "bitcoin": { "id": "bitcoin", "symbol": "BTC", "price": 45000.50, ... },
     │    ...
     │  }
     ├─ Cache in Redis with TTL=300 seconds
     └─ Return data

Back to crypto.py:
  4. Create HTTP response:
     {
       "cryptocurrencies": [
         { "id": "bitcoin", "symbol": "BTC", "price": 45000.50, ... },
         ...
       ]
     }
  5. Attach response headers:
     ├─ Content-Type: application/json
     ├─ X-Request-ID: abc-123-xyz
     ├─ X-RateLimit-Limit: 60
     ├─ X-RateLimit-Remaining: 59
     └─ (other security headers from middleware)

STEP 6: Response Sent Back
────────────────────────────
HTTP 200 OK
Content-Type: application/json
X-Request-ID: abc-123-xyz
X-RateLimit-Remaining: 59
Set-Cookie: (none, access_token already sent)

Body: {
  "cryptocurrencies": [
    { "id": "bitcoin", "symbol": "BTC", "price": 45000.50, ... },
    ...
  ]
}

STEP 7: Frontend Receives Response
──────────────────────────────────
File: frontend/src/lib/apiClient.ts
Response interceptor (line 104):
  1. Response status 200, no error
  2. Return response.data directly
  3. Promise resolves

STEP 8: Component Updates
──────────────────────────
File: frontend/src/pages/Markets.tsx
catch block not triggered (no error)
  1. setLoading(false)
  2. setMarketData(response.cryptocurrencies)
  3. Component re-renders

STEP 9: Parallel WebSocket Update
──────────────────────────────────
File: frontend/src/hooks/usePriceWebSocket.ts
Meanwhile, WebSocket has been connected since app load:
  • onmessage event fires every 1-10 seconds with price updates
  • setPrices(data.prices) updates local state
  
Markets.tsx renders with both:
  1. REST data (from api.crypto.getAll() - base info)
  2. WebSocket data (real-time prices from usePriceWebSocket)

STEP 10: Final Render
──────────────────────
User sees Markets page with:
  ✅ List of cryptocurrencies (from REST)
  ✅ Current prices (from WebSocket, updates 1-10 sec)
  ✅ Market cap, volume, change percentage
  ✅ Search & filter functionality
  ✅ No error messages

TOTAL TIME: 200-800ms depending on network and cache status
```

---

## 8. Security Mechanisms

### CORS (Cross-Origin Resource Sharing)
```python
# backend/server.py lines 344-346
CORSMiddleware(
    app,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,  # Allows cookies to be sent
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Impact**:
- Frontend at `cryptovault.vercel.app` can call backend at `cryptovault-api.onrender.com`
- Credentials (cookies) are allowed in cross-origin requests
- Browser enforces CORS; backend allows it

### HttpOnly Cookies
```python
# backend/routers/auth.py line 230
response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,  # JS cannot access via document.cookie
    secure=secure,  # HTTPS only in production
    samesite="Lax",  # CSRF protection
    max_age=15*60  # 15 minutes
)
```

**Security Benefits**:
- XSS attacks cannot steal tokens (JS can't access)
- CSRF attacks mitigated (SameSite=Lax)
- Tokens only sent over HTTPS in production

### Token Refresh Without User Interaction
```javascript
// frontend/src/lib/apiClient.ts (lines 110-139)
// If 401 received, automatically:
// 1. Call POST /api/auth/refresh (with refresh_token cookie)
// 2. Server creates new access_token, sets it in cookie
// 3. Retry original request
// → User doesn't need to log back in
```

### Rate Limiting
```python
# backend/server.py lines 304-305
limiter = Limiter(key_func=get_rate_limit_key)
@limiter.limit("60/minute")  # Per user/IP
```

**Key Function** (lines 268-291):
```python
def get_rate_limit_key(request: Request) -> str:
    # Priority: access_token > IP address
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split()[1][:20]  # Token prefix as key
    
    access_token_cookie = request.cookies.get("access_token")
    if access_token_cookie:
        return access_token_cookie[:20]  # Cookie-based user
    
    return request.client.host  # Fall back to IP address
```

**Effect**:
- Authenticated users: 60 requests/minute per user (shared across devices)
- Anonymous users: 60 requests/minute per IP address
- Rate limit is in backend, not frontend

---

## 9. Development vs Production

### Development Setup
```bash
# Terminal 1: Frontend
cd frontend
yarn dev
# Runs on http://localhost:3000
# Vite dev server with hot reload
# Proxy: /api → http://localhost:8000 (vite.config.ts)

# Terminal 2: Backend
python -m uvicorn backend.server:app --reload --port 8000
# Auto-reload on file changes
# CORS allows http://localhost:3000
# Email/SMS disabled (console output only)
```

**Frontend Dev Config** (`frontend/vite.config.ts` lines 67-75):
```typescript
proxy: {
  "/api": {
    target: "http://localhost:8000",
    changeOrigin: true,
    secure: false,
  },
}
```

**Backend Dev Config** (`backend/config.py`):
```python
if environment == "development":
    cors_origins = ["http://localhost:3000", "http://localhost:5173"]
    secure_cookies = False
    json_logging = False
```

### Production Setup
```
Frontend: Deployed to Vercel
  • Environment variables set in Vercel dashboard
  • VITE_API_BASE_URL=https://cryptovault-api.onrender.com
  • Requests: https://yourdomain.com/api → Vercel rewrites → https://cryptovault-api.onrender.com/api

Backend: Deployed to Render
  • Environment variables set in Render environment
  • CORS allows: https://yourdomain.com
  • Cookies set with Secure flag (HTTPS only)
  • Logging: JSON format to stdout (parsed by Render logs)
  • Auto-scaling: up to N dynos based on CPU/memory
```

**Vercel Rewrites** (`frontend/vercel.json` lines 8-35):
```json
{
  "rewrites": [
    {
      "source": "/api/:path+",
      "destination": "https://cryptovault-api.onrender.com/:path+"
    }
  ]
}
```

**Effect**:
- User browser: requests to `https://yourdomain.com/api/crypto`
- Vercel rewrites: to `https://cryptovault-api.onrender.com/crypto`
- Backend receives request from Vercel's IP (not user's IP)
- Response sent back through Vercel to user

---

## 10. Summary Table: File Responsibilities

| File | Responsibility | Key Functions |
|------|-----------------|----------------|
| **Frontend: API & Auth** |
| `frontend/src/lib/apiClient.ts` | HTTP client | axios instance, interceptors, API endpoints |
| `frontend/src/contexts/AuthContext.tsx` | Auth state | login, logout, session recovery, user state |
| `frontend/src/hooks/usePriceWebSocket.ts` | Real-time prices | WebSocket connection, price updates |
| `frontend/src/pages/Auth.tsx` | Login UI | Login form, password reset |
| `frontend/src/pages/Markets.tsx` | Markets display | Fetch crypto data, display with live prices |
| **Backend: Server & Config** |
| `backend/server.py` | App initialization | CORS, middleware, startup/shutdown, router mounting |
| `backend/config.py` | Configuration | Settings, environment validation |
| **Backend: Routers** |
| `backend/routers/auth.py` | Authentication | Login, logout, token refresh, 2FA |
| `backend/routers/crypto.py` | Crypto data | Fetch prices, history, market data |
| `backend/routers/websocket.py` | WebSocket | Client connections, price broadcasting |
| **Backend: Services** |
| `backend/services/price_stream.py` | Price stream | Connect to CoinCap/Binance, manage prices |
| `backend/coingecko_service.py` | External API | Fetch from CoinGecko, cache in Redis |
| **Backend: Data** |
| `backend/database.py` | MongoDB connection | Connect, health check, collection access |
| `backend/redis_cache.py` | Redis caching | Cache get/set with TTL |

---

## Connection Checklist

- ✅ Frontend and backend communicate via HTTPS REST API
- ✅ Authentication uses HttpOnly cookies (secure, XSS-proof)
- ✅ Token refresh automatic (no user logout needed on expiry)
- ✅ WebSocket provides real-time price updates
- ✅ CORS configured to allow frontend domain
- ✅ Rate limiting protects backend
- ✅ Error handling transforms backend errors into frontend messages
- ✅ Environment variables configure different behaviors (dev vs prod)
- ✅ Vercel rewrites API calls to backend
- ✅ Render hosts backend with auto-scaling
