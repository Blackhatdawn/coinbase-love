# 🏗️ Visual Architecture Summary

## 1. Complete System Architecture

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                         USER BROWSER                                     ┃
┃                                                                           ┃
┃  ┌───────────────────────────────────────────────────────────────┐      ┃
┃  │ React App (Vite)                                              │      ┃
┃  │ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │      ┃
┃  │ │ Pages        │  │ Components   │  │ Contexts     │         │      ┃
┃  │ │ - Markets    │  │ - Header     │  │ - AuthContext│         │      ┃
┃  │ │ - Dashboard  │  │ - Ticker     │  │ - Web3Context│         │      ┃
┃  │ │ - Trade      │  │ - Modal      │  │              │         │      ┃
┃  │ └──────────────┘  └──────────────┘  └──────────────┘         │      ┃
┃  │         │                                   ▲                 │      ┃
┃  │         └───────────────────────────────────┘                 │      ┃
┃  │                        │                                       │      ┃
┃  │  ┌────────────────────▼─────────────────────┐                 │      ┃
┃  │  │ Hooks                                     │                 │      ┃
┃  │  │ ┌──────────────────────────────────┐     │                 │      ┃
┃  │  │ │ usePriceWebSocket                │     │                 │      ┃
┃  │  │ ├─ WebSocket connection            │     │                 │      ┃
┃  │  │ ├─ Real-time price updates         │     │                 │      ┃
┃  │  │ ├─ Reconnection logic (max 10x)    │     │                 │      ┃
┃  │  │ └─ Keep-alive pings (30s)          │     │                 │      ┃
┃  │  └──────────────────────────────────┘     │                 │      ┃
┃  │  ┌──────────────────────────────────┐     │                 │      ┃
┃  │  │ useAuth (from AuthContext)        │     │                 │      ┃
┃  │  ├─ Login/logout functions           │     │                 │      ┃
┃  │  ├─ User state management            │     │                 │      ┃
┃  │  ├─ Session recovery                 │     │                 │      ┃
┃  │  └─ Token validation                 │     │                 │      ┃
┃  │  └──────────────────────────────────┘     │                 │      ┃
┃  │                        │                   │                 │      ┃
┃  └────────────────────────┼───────────────────┼─────────────────┘      ┃
┃                           │                   │                        ┃
┃  ┌────────────────────────▼───────────────────▼─────────────────┐     ┃
┃  │ API Client & Network Layer (apiClient.ts)                    │     ┃
┃  │ ┌──────────────────────────────────────────────────────────┐ │     ┃
┃  │ │ Axios Instance                                           │ │     ┃
┃  │ ├─ baseURL: import.meta.env.VITE_API_BASE_URL             │ │     ┃
┃  │ ├─ withCredentials: true (sends cookies)                  │ │     ┃
┃  │ ├─ timeout: 30 seconds                                    │ │     ┃
┃  │ └─ Headers: Content-Type: application/json                │ │     ┃
┃  │ ┌──────────────────────────────────────────────────────────┐ │     ┃
┃  │ │ Request Interceptor                                      │ │     ┃
┃  │ ├─ Adds request ID for tracking                           │ │     ┃
┃  │ └─ Adds timestamps                                        │ │     ┃
┃  │ ┌──────────────────────────────────────────────────────────┐ │     ┃
┃  │ │ Response Interceptor & Error Handling                    │ │     ┃
┃  │ ├─ Transforms axios errors → APIClientError               │ │     ┃
┃  │ ├─ Auto-refresh token on 401                              │ │     ┃
┃  │ ├─ Queues requests during refresh                         │ │     ┃
┃  │ ├─ Handles network errors, timeouts, rate limits          │ │     ┃
┃  │ └─ Extracts error details from backend                    │ │     ┃
┃  │ ┌──────────────────────────────────────────────────────────┐ │     ┃
┃  │ │ Typed API Methods                                        │ │     ┃
┃  │ ├─ api.auth.*         (login, logout, refresh, 2FA)       │ │     ┃
┃  │ ├─ api.crypto.*       (getAll, get, getHistory)           │ │     ┃
┃  │ ├─ api.portfolio.*    (get, addHolding, deleteHolding)    │ │     ┃
┃  │ ├─ api.trading.*      (getOrders, createOrder)            │ │     ┃
┃  │ ├─ api.wallet.*       (getBalance, deposit, withdraw)     │ │     ┃
┃  │ ├─ api.alerts.*       (get, create, update, delete)       │ │     ┃
┃  │ ├─ api.transactions.* (getAll, get, getStats)             │ │     ┃
┃  │ └─ api.admin.*        (getStats, getUsers, getAuditLogs)  │ │     ┃
┃  └──────────────────────────────────────────────────────────┘ │     ┃
┃                                                                   ┃
┃  Storage: Browser LocalStorage/SessionStorage (NOT used for tokens!)   ┃
┃           → Tokens stored in HttpOnly cookies only               ┃
┃           → Cookies auto-sent by browser with every request      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

                    HTTPS & WSS (Encrypted)
                           ││
                           ││
                           ││
┏━━━━━━━━━━━━━━━━━━━━━━━━━▼▼━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃              BACKEND (FastAPI + Python)                                 ┃
┃                                                                           ┃
┃  ┌───────────────────────────────────────────────────────────────┐      ┃
┃  │ Server (server.py) - App Initialization                       │      ┃
┃  │ ┌───────────────────────────────────────────────────────────┐ │      ┃
┃  │ │ Middleware Stack                                          │ │      ┃
┃  │ ├─ RequestIDMiddleware        (generates unique ID)         │ │      ┃
┃  │ ├─ SecurityHeadersMiddleware  (X-Frame-Options, HSTS, etc)  │ │      ┃
┃  │ ├─ CORSMiddleware             (allow_credentials=True)      │ │      ┃
┃  │ ├─ RateLimitHeadersMiddleware (X-RateLimit headers)         │ │      ┃
┃  │ ├─ TimeoutMiddleware          (30 second limit)             │ │      ┃
┃  │ └─ Sentry Integration         (error tracking)              │ │      ┃
┃  │ ┌───────────────────────────────────────────────────────────┐ │      ┃
┃  │ │ Router Mounting (Include Router Lines 372-383)             │ │      ┃
┃  │ ├─ auth.router        → /api/auth/*                        │ │      ┃
┃  │ ├─ crypto.router      → /api/crypto/*                      │ │      ┃
┃  │ ├─ portfolio.router   → /api/portfolio/*                   │ │      ┃
┃  │ ├─ trading.router     → /api/trading/*                     │ │      ┃
┃  │ ├─ prices.router      → /api/prices/*                      │ │      ┃
┃  │ ├─ wallet.router      → /api/wallet/*                      │ │      ┃
┃  │ ├─ alerts.router      → /api/alerts/*                      │ │      ┃
┃  │ ├─ transactions.router → /api/transactions/*               │ │      ┃
┃  │ ├─ admin.router       → /api/admin/*                       │ │      ┃
┃  │ └─ websocket.router   → /ws/prices, /ws/prices/{symbol}    │ │      ┃
┃  │ ┌───────────────────────────────────────────────────────────┐ │      ┃
┃  │ │ Startup Event (@app.on_event("startup"))                  │ │      ┃
┃  │ ├─ Validate environment config                             │ │      ┃
┃  │ ├─ Connect to MongoDB                                      │ │      ┃
┃  │ ├─ Create database indexes                                 │ │      ┃
┃  │ ├─ Start PriceStreamService (CoinCap/Binance connection)   │ │      ┃
┃  │ ├─ Start WebSocket price feed (fallback)                  │ │      ┃
┃  │ └─ Initialize Sentry                                       │ │      ┃
┃  │ ┌───────────────────────────────────────────────────────────┐ │      ┃
┃  │ │ Shutdown Event (@app.on_event("shutdown"))                │ │      ┃
┃  │ ├─ Stop PriceStreamService                                 │ │      ┃
┃  │ ├─ Disconnect from MongoDB                                │ │      ┃
┃  │ └─ Cleanup resources                                       │ │      ┃
┃  └───────────────────────────────────────────────────────────┘ │      ┃
┃           │                                       │              ┃      ┃
┃  ┌────────▼──────────────────────────────────────▼───┐          ┃      ┃
┃  │ Router Handlers                                    │          ┃      ┃
┃  │ ┌────────────────────────────────────────────────┐ │          ┃      ┃
┃  │ │ auth.py                                        │ │          ┃      ┃
┃  │ ├─ POST /auth/login      → validate, create JWT │ │          ┃      ┃
┃  │ ├─ POST /auth/logout     → blacklist token      │ │          ┃      ┃
┃  │ ├─ POST /auth/refresh    → new access_token     │ │          ┃      ┃
┃  │ ├─ GET /auth/me          → return user profile  │ │          ┃      ┃
┃  │ ├─ POST /auth/2fa/setup  → TOTP setup          │ │          ┃      ┃
┃  │ └─ ... 12 more endpoints                        │ │          ┃      ┃
┃  │ ┌────────────────────────────────────────────────┐ │          ┃      ┃
┃  │ │ crypto.py                                      │ │          ┃      ┃
┃  │ ├─ GET /crypto           → list all coins       │ │          ┃      ┃
┃  │ ├─ GET /crypto/:id       → get specific coin    │ │          ┃      ┃
┃  │ └─ GET /crypto/:id/history → price history     │ │          ┃      ┃
┃  │ ┌────────────────────────────────────────────────┐ │          ┃      ┃
┃  │ │ websocket.py                                   │ │          ┃      ┃
┃  │ ├─ WS /ws/prices         → all prices broadcast │ │          ┃      ┃
┃  │ ├─ WS /ws/prices/:symbol → single price stream  │ │          ┃      ┃
┃  │ ├─ PriceStreamManager    → manages connections  │ │          ┃      ┃
┃  │ └─ broadcast_loop()      → sends updates 1/sec  │ │          ┃      ┃
┃  │ ┌────────────────────────────────────────────────┐ │          ┃      ┃
┃  │ │ [Other routers omitted for brevity]            │ │          ┃      ┃
┃  │ ├─ portfolio.py, trading.py, wallet.py, etc     │ │          ┃      ┃
┃  │ └─ admin.py, prices.py, alerts.py               │ │          ┃      ┃
┃  └────────────────────────────────────────────────┘ │          ┃      ┃
┃           │                          │                │          ┃      ┃
┃  ┌────────▼──────────────────────────▼────────────┐  │          ┃      ┃
┃  │ Services & Background Tasks                    │  │          ┃      ┃
┃  │ ┌──────────────────────────────────────────────┐ │  │          ┃      ┃
┃  │ │ PriceStreamService (price_stream.py)         │ │  │          ┃      ┃
┃  │ ├─ Connects to CoinCap WS                      │ │  │          ┃      ┃
┃  │ │  (wss://ws.coincap.io/prices?assets=ALL)    │ │  │          ┃      ┃
┃  │ ├─ Fallback to Binance if CoinCap down >30s   │ │  │          ┃      ┃
┃  │ ├─ Maintains in-memory cache: self.prices     │ │  │          ┃      ┃
┃  │ ├─ Updates Redis cache (TTL: 30s)             │ │  │          ┃      ┃
┃  │ ├─ Auto-reconnects with exponential backoff   │ │  │          ┃      ┃
┃  │ └─ Provides: get_prices(), get_status()       │ │  │          ┃      ┃
┃  │ ┌──────────────────────────────────────────────┐ │  │          ┃      ┃
┃  │ │ CoinGeckoService (coingecko_service.py)      │ │  │          ┃      ┃
┃  │ ├─ REST API to CoinGecko                       │ │  │          ┃      ┃
┃  │ ├─ Caches results in Redis (5 min TTL)         │ │  │          ┃      ┃
┃  │ ├─ Provides: get_prices(), get_coin_details()│ │  │          ┃      ┃
┃  │ └─ Used by: crypto.py router                  │ │  │          ┃      ┃
┃  │ ┌──────────────────────────────────────────────┐ │  │          ┃      ┃
┃  │ │ DatabaseConnection (database.py)             │ │  │          ┃      ┃
┃  │ ├─ Motor (async MongoDB driver)                │ │  │          ┃      ┃
┃  │ ├─ Methods: connect, disconnect, health_check│ │  │          ┃      ┃
┃  │ └─ Provides: get_collection()                 │ │  │          ┃      ┃
┃  └──────────────────────────────────────────────┘ │  │          ┃      ┃
┃           │                          │             │  │          ┃      ┃
┃  ┌────────▼──────────────────────────▼─────────┐  │  │          ┃      ┃
┃  │ Data Layer                                   │  │  │          ┃      ┃
┃  ├─ MongoDB                                     │  │  │          ┃      ┃
┃  │  Collections: users, portfolios, orders,    │  │  │          ┃      ┃
┃  │              alerts, transactions, etc       │  │  │          ┃      ┃
┃  ├─ Redis                                       │  │  │          ┃      ┃
┃  │  Keys: crypto:price:*, prices:all, cache:*  │  │  │          ┃      ┃
┃  └──────────────────────────────────────────────┘  │  │          ┃      ┃
┃           │                       │                 │  │          ┃      ┃
┗───────────┼───────────────────────┼─────────────────┼──┼──────────────────┛
            │                       │                 │  │
            ▼                       ▼                 │  │
    ┌──────────────────┐  ┌──────────────────┐      │  │
    │    MongoDB       │  │     Redis        │      │  │
    │                  │  │                  │      │  │
    │ - User data      │  │ - Price cache    │      │  │
    │ - Portfolios     │  │ - Session cache  │      │  │
    │ - Orders         │  │ - TTL expiry     │      │  │
    │ - Transactions   │  │                  │      │  │
    │ - Alerts         │  │                  │      │  │
    └──────────────────┘  └──────────────────┘      │  │
                                                     │  │
    ┌──────────────────┐  ┌──────────────────┐      │  │
    │   CoinCap WS     │  │  CoinGecko API   │      │  │
    │                  │  │                  │      │  │
    │ Price stream     │  │ REST API         │      │  │
    │ Primary source   │  │ Fallback/detail  │      │  │
    └──────────────────┘  └──────────────────┘      │  │
                                                     │  │
    ┌──────────────────┐  ┌──────────────────┐      │  │
    │   Binance WS     │  │  External APIs   │      │  │
    │                  │  │  (Email, SMS)    │      │  │
    │ Fallback source  │  │                  │      │  │
    └──────────────────┘  └──────────────────┘      │  │
```

---

## 2. Request-Response Cycle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FRONTEND REQUEST LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────────────┘

STAGE 1: INITIATION
═══════════════════
User Action
    ↓
React Component calls: api.crypto.getAll()
    ↓
apiClient.get('/api/crypto')
    ↓
Axios prepares request
├─ Method: GET
├─ URL: https://cryptovault-api.onrender.com/api/crypto
├─ Headers: {
│    'Cookie': 'access_token=eyJ...; refresh_token=eyJ...',
│    'Content-Type': 'application/json'
│  }
├─ withCredentials: true (cookies included)
└─ Body: none

STAGE 2: NETWORK
════════════════
Browser sends HTTPS request
    ↓
Request reaches backend via internet/CDN

STAGE 3: BACKEND PROCESSING
═════════════════════════════
Middleware chain:
  1. RequestIDMiddleware
     └─ Generates: request_id = 'abc-123'
     
  2. SecurityHeadersMiddleware
     └─ Adds security headers to response
     
  3. CORSMiddleware
     └─ Verifies Origin header matches allowed CORS origins
     └─ Allows credentials (cookies)
     
  4. RateLimitHeadersMiddleware
     └─ get_rate_limit_key(request):
        ├─ Extracts access_token from cookie
        ├─ Uses token[:20] as rate limit key
        └─ Check: current_count < 60 per minute?
        
  5. TimeoutMiddleware
     └─ Sets 30 second timeout for endpoint

Routing:
  GET /api/crypto → crypto.router.get_all_cryptocurrencies()

Handler execution:
  get_all_cryptocurrencies():
    1. Extract access_token from request.cookies
    2. Decode JWT (verify signature & expiry)
    3. Extract user_id from token claims
    4. Call coingecko_service.get_prices()
       ├─ Check Redis cache for "prices:all"
       ├─ If fresh (< 5 min): return from cache ✓ FAST
       ├─ If stale/missing:
       │  ├─ Call external CoinGecko API (HTTP GET)
       │  ├─ Transform response to internal format
       │  ├─ Store in Redis with 5 min TTL
       │  └─ Return data ✓ SLOWER
    5. Build HTTP response:
       {
         "cryptocurrencies": [
           { "id": "bitcoin", "symbol": "BTC", "price": 45000.50, ... },
           { "id": "ethereum", "symbol": "ETH", "price": 2500.25, ... },
           ...
         ]
       }

Response headers:
├─ Content-Type: application/json
├─ X-Request-ID: abc-123
├─ X-RateLimit-Limit: 60
├─ X-RateLimit-Remaining: 59
├─ X-RateLimit-Reset: 1234567890
└─ [Security headers from middleware]

HTTP Status: 200 OK

STAGE 4: NETWORK
════════════════
Backend sends HTTPS response
    ↓
Response reaches browser

STAGE 5: FRONTEND PROCESSING
═════════════════════════════
Axios response interceptor:
  1. Status code: 200 (success)
  2. No error triggered
  3. Parse JSON: response.data = { cryptocurrencies: [...] }
  4. Promise resolves with data

Component receives data:
  Markets.tsx (line 45):
    const data = await api.crypto.getAll()
    ↓
  setMarketData(data.cryptocurrencies)
    ↓
  Component re-renders with new state

STAGE 6: RENDER
════════════════
React renders Markets page:
  ├─ Loading spinner hidden
  ├─ Market list displayed with data
  ├─ Each row shows: symbol, price, market cap, 24h change
  └─ User sees final result

STAGE 7: PARALLEL REALTIME UPDATES
═══════════════════════════════════
Meanwhile, WebSocket has been connected since app load:
  usePriceWebSocket() hook:
    ├─ Maintains open WebSocket to /ws/prices
    ├─ Every 1-10 seconds receives:
    │  {
    │    "type": "price_update",
    │    "prices": {
    │      "bitcoin": "45050.75",
    │      "ethereum": "2501.50"
    │    },
    │    "timestamp": "2024-01-16T10:30:15Z",
    │    "source": "coincap"
    │  }
    ├─ Updates hook state: setPrices(message.prices)
    └─ Triggers re-render of components using prices

Final render merges both:
  REST data (from GET /api/crypto):
    ├─ Cryptocurrency info (name, symbol, ID)
    ├─ Market cap, volume
    ├─ Last API price (cached, ~5 min fresh)
    └─ 24h change percentage
  
  WebSocket data (real-time):
    ├─ Current price from CoinCap stream
    ├─ Updates every 1-10 seconds
    └─ Shows live changing value

═══════════════════════════════════════════════════════════════════════════
TOTAL TIME: 200-800ms depending on:
  - Network latency
  - Cache hit/miss
  - External API response time
═══════════════════════════════════════════════════════════════════════════
```

---

## 3. Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AUTHENTICATION LIFECYCLE                           │
└─────────────────────────────────────────────────────────────────────────┘

FLOW 1: LOGIN
═════════════

User Input:
  Email: user@example.com
  Password: secretpass123
  
    ↓
Auth.tsx (line 109):
  const { signIn } = useAuth()
  await signIn(email, password)
  
    ↓
AuthContext.signIn():
  api.auth.login({ email, password })
  
    ↓
HTTP Request:
  POST /api/auth/login
  Body: { "email": "user@example.com", "password": "secretpass123" }
  
    ↓
Backend (auth.py line 141):
  1. Query MongoDB: users.findOne({ email: "user@example.com" })
  2. Verify password hash matches
  3. ✅ Valid credentials
  4. Create JWT tokens:
     access_token = create_access_token(user_id, expire_minutes=15)
     refresh_token = create_refresh_token(user_id, expire_days=7)
  5. Set HttpOnly cookies in response:
     Set-Cookie: access_token=<JWT>; HttpOnly; Secure; SameSite=Lax; Max-Age=900
     Set-Cookie: refresh_token=<JWT>; HttpOnly; Secure; SameSite=Lax; Max-Age=604800
  6. Return JSON:
     { "user": { "id": "...", "email": "...", "name": "...", ... } }
  
    ↓
Browser:
  Cookies auto-stored (HttpOnly means JS cannot access)
  
    ↓
Frontend:
  axios response succeeds
    ↓
  AuthContext.signIn():
    setUser(response.user)
    setIsAuthenticated(true)
    
    ↓
  Redirect: /auth → /dashboard
  
    ↓
✅ USER LOGGED IN


FLOW 2: KEEP LOGGED IN (Session Recovery)
═══════════════════════════════════════════

Page refresh / App reload
  
    ↓
AuthContext useEffect (line 26):
  checkSession()
    ↓
  api.auth.getProfile()
  
    ↓
HTTP Request:
  GET /api/auth/me
  Headers: Cookie: 'access_token=<JWT>; ...'
  (Browser auto-includes cookies with request)
  
    ↓
Backend:
  1. Extract access_token from request.cookies
  2. Decode JWT:
     ├─ Verify signature (using JWT_SECRET)
     ├─ Check exp timestamp (is it past?)
     └─ ✅ Token valid, extract user_id
  3. Query MongoDB: users.findOne({ _id: user_id })
  4. Return user data
  
    ↓
Frontend:
  setUser(response)
  setIsAuthenticated(true)
  
    ↓
✅ SESSION PRESERVED (no re-login needed)


FLOW 3: TOKEN REFRESH (Auto on 401)
════════════════════════════════════

15 minutes later, access_token expires
User clicks to fetch data: api.portfolio.get()

    ↓
HTTP Request:
  GET /api/portfolio
  Cookie: access_token=<EXPIRED_JWT>
  
    ↓
Backend:
  Decode access_token
  exp: 1234567890 (Jan 16, 10:15 AM)
  now: 1234569890 (Jan 16, 10:35 AM)
  ❌ Token expired!
  
    ↓
Return: HTTP 401 Unauthorized
  (Backend does NOT send new token, only error)
  
    ↓
Frontend axios interceptor (line 110):
  1. Detect: status === 401
  2. Check: originalRequest._retry not set
  3. Set: originalRequest._retry = true
  4. Call: apiClient.post('/api/auth/refresh')
  
    ↓
HTTP Request:
  POST /api/auth/refresh
  Cookie: refresh_token=<VALID_JWT>
  (Browser auto-includes refresh_token cookie)
  
    ↓
Backend (auth.py line 364):
  1. Extract refresh_token from request.cookies
  2. Decode refresh_token:
     exp: 1234800000 (Jan 23, 10:35 AM)
     now: 1234569890 (Jan 16, 10:35 AM)
     ✅ Still valid (7 days)
  3. Create NEW access_token (15 min expiry)
  4. Set new cookie in response:
     Set-Cookie: access_token=<NEW_JWT>; HttpOnly; ...
  5. Return: HTTP 200 OK
  
    ↓
Browser:
  Receives new access_token cookie
  Replaces old expired cookie with new one
  
    ↓
Frontend axios:
  1. Retry original request with NEW token:
     GET /api/portfolio
     Cookie: access_token=<NEW_JWT>
  
    ↓
Backend:
  Verify NEW access_token
  ✅ Valid!
  Return portfolio data
  
    ↓
Component receives data
User doesn't notice anything happened!
  
    ↓
✅ TOKEN REFRESHED, SESSION EXTENDED


FLOW 4: LOGOUT
══════════════

User clicks "Logout" button
  
    ↓
Header.tsx:
  const { signOut } = useAuth()
  await signOut()
  
    ↓
AuthContext.signOut() (line 117):
  api.auth.logout()
  
    ↓
HTTP Request:
  POST /api/auth/logout
  Cookie: access_token=<JWT>
  
    ↓
Backend (auth.py line 251):
  1. Extract access_token from request.cookies
  2. Add token to blacklist:
     blacklisted_tokens.insertOne({
       token_jti: <extracted from token>,
       expires_at: <token expiry time>
     })
  3. Delete cookies in response:
     Set-Cookie: access_token=; Max-Age=0; ...
     Set-Cookie: refresh_token=; Max-Age=0; ...
  4. Return: HTTP 200 OK
  
    ↓
Browser:
  Cookies deleted (Max-Age=0)
  
    ↓
Frontend:
  AuthContext.signOut():
    setUser(null)
    setIsAuthenticated(false)
    
    ↓
  Redirect: /dashboard → /auth
  
    ↓
Any future requests to /api/*:
  1. Cookie not sent (deleted)
  2. Backend returns 401
  3. Refresh attempt fails (no cookie)
  4. User redirected to /auth
  
    ↓
✅ USER LOGGED OUT


FLOW 5: TOKEN REFRESH FAILURE (Redirect to Login)
═══════════════════════════════════════════════════

Scenario: User's refresh_token expired (7 days passed)

    ↓
Access_token expired
Frontend detects 401
Attempts refresh: POST /api/auth/refresh
  
    ↓
Backend:
  Extract refresh_token
  Decode: exp: 1234000000 (7 days ago)
  ❌ Expired!
  Return: HTTP 401
  
    ↓
Frontend axios interceptor (line 174-183):
  Refresh failed
  Call: handleAuthFailure()
    ├─ Clear AuthContext (setUser(null))
    ├─ Dispatch custom event: 'auth:logout'
    ├─ Redirect to: window.location.href = '/auth'
  
    ↓
User lands on /auth page
Must log in again
  
    ↓
✅ SECURITY: Old sessions cannot be renewed


TOKEN LIFECYCLE DIAGRAM
═══════════════════════

Time: T=0 (Login)
  access_token created:  ━━━━━━━━━━━━ (15 min)
  refresh_token created: ══════════════════════════════════════ (7 days)

Time: T=15 min (access_token expires)
  api.portfolio.get() → 401
  → auto-refresh → new access_token: ━━━━━━━━━━━━ (15 min)
  
Time: T=7.5 days (refresh_token expires)
  api.portfolio.get() → 401
  → auto-refresh → 401 (refresh expired)
  → redirect to /auth
  → User must login again

```

---

## 4. Key Files Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│  CRITICAL FILES FOR FRONTEND-BACKEND CONNECTION                │
└─────────────────────────────────────────────────────────────────┘

┌─ FRONTEND ──────────────────────────────────────────────────────┐
│                                                                 │
│ API Communication (frontend/src/lib/)                           │
│  ├─ apiClient.ts          [★★★ MOST IMPORTANT]                 │
│  │  ├─ axios instance setup                                   │
│  │  ├─ request/response interceptors                          │
│  │  ├─ token refresh logic                                    │
│  │  ├─ error transformation                                   │
│  │  └─ all api.* endpoints exported                           │
│  │                                                             │
│  ├─ sentry.ts              [Error tracking]                    │
│  │  ├─ initSentry() setup                                     │
│  │  ├─ error capture                                          │
│  │  └─ user context                                           │
│  │                                                             │
│  └─ utils.ts               [Helper functions]                  │
│                                                             │
│ Authentication (frontend/src/contexts/)                        │
│  ├─ AuthContext.tsx        [★★★ MOST IMPORTANT]                │
│  │  ├─ signIn(email, password)                               │
│  │  ├─ signOut()                                              │
│  │  ├─ checkSession()                                         │
│  │  ├─ user state                                             │
│  │  └─ isAuthenticated flag                                   │
│  │                                                             │
│  └─ Web3Context.tsx        [Web3 wallet integration]           │
│                                                             │
│ Real-time (frontend/src/hooks/)                                │
│  ├─ usePriceWebSocket.ts   [★★ IMPORTANT]                      │
│  │  ├─ WebSocket connection                                   │
│  │  ├─ reconnection logic                                     │
│  │  ├─ price state                                            │
│  │  └─ connection status                                      │
│  │                                                             │
│  └─ other hooks            [Various utilities]                 │
│                                                             │
│ Components (frontend/src/components/)                          │
│  ├─ Header.tsx             [Navigation, logout button]         │
│  ├─ PriceStreamStatus.tsx   [WS connection indicator]          │
│  ├─ DebugApiStatus.tsx      [Dev only: API config debug]       │
│  └─ [others]               [Feature components]                │
│                                                             │
│ Pages (frontend/src/pages/)                                    │
│  ├─ Auth.tsx               [Login UI]                          │
│  ├─ Markets.tsx            [Crypto list, uses api.crypto.*]    │
│  ├─ Dashboard.tsx          [Portfolio, uses api.portfolio.*]   │
│  ├─ Trade.tsx              [Trading UI, uses api.orders.*]     │
│  └─ [others]               [Other pages]                       │
│                                                             │
└─────────────────────────────────────────────────────────────────┘

┌─ BACKEND ───────────────────────────────────────────────────────┐
│                                                                 │
│ Core (backend/)                                                 │
│  ├─ server.py              [★★★ MOST IMPORTANT]                │
│  │  ├─ App initialization                                     │
│  │  ├─ Middleware stack                                       │
│  │  ├─ Router mounting                                        │
│  │  ├─ Startup/shutdown events                                │
│  │  ├─ CORS configuration                                     │
│  │  └─ Rate limiting setup                                    │
│  │                                                             │
│  ├─ config.py              [★★ IMPORTANT]                      │
│  │  ├─ Settings class                                         │
│  │  ├─ Environment validation                                 │
│  │  └─ Configuration loading                                  │
│  │                                                             │
│  ├─ database.py            [★ Database]                        │
│  │  ├─ DatabaseConnection class                               │
│  │  ├─ MongoDB connection                                     │
│  │  └─ Collection access                                      │
│  │                                                             │
│  ├─ dependencies.py        [Dependency injection]              │
│  │  ├─ get_db()                                               │
│  │  └─ verify_token()                                         │
│  │                                                             │
│  └─ auth.py                [Authentication logic]              │
│     ├─ JWT creation/verification                              │
│     └─ Token blacklisting                                      │
│                                                             │
│ Routers (backend/routers/)                                     │
│  ├─ auth.py                [★★★ Login/token endpoints]         │
│  │  ├─ POST /auth/login                                       │
│  │  ├─ POST /auth/logout                                      │
│  │  ├─ POST /auth/refresh                                     │
│  │  ├─ GET /auth/me                                           │
│  │  └─ [more endpoints]                                       │
│  │                                                             │
│  ├─ websocket.py           [★★ Real-time]                      │
│  │  ├─ @router.websocket("/ws/prices")                        │
│  │  ├─ PriceStreamManager                                     │
│  │  ├─ Connection management                                  │
│  │  └─ Broadcasting                                           │
│  │                                                             │
│  ├─ crypto.py              [★ Market data]                     │
│  │  ├─ GET /crypto                                            │
│  │  ├─ GET /crypto/:coin_id                                   │
│  │  └─ GET /crypto/:coin_id/history                           │
│  │                                                             │
│  ├─ prices.py              [Price endpoints]                   │
│  ├─ portfolio.py            [Portfolio endpoints]              │
│  ├─ trading.py              [Trading endpoints]                │
│  ├─ wallet.py               [Wallet endpoints]                 │
│  ├─ alerts.py               [Alert endpoints]                  │
│  ├─ transactions.py         [Transaction endpoints]            │
│  ├─ admin.py                [Admin endpoints]                  │
│  └─ [others]                [Other routers]                    │
│                                                             │
│ Services (backend/services/)                                   │
│  ├─ price_stream.py        [★ Real-time pricing]               │
│  │  ├─ PriceStreamService class                               │
│  │  ├─ Connect to CoinCap WS                                  │
│  │  ├─ Fallback to Binance                                    │
│  │  ├─ In-memory + Redis cache                                │
│  │  └─ Auto-reconnection                                      │
│  │                                                             │
│  ├─ coingecko_service.py   [Crypto data API]                   │
│  │  ├─ get_prices()                                           │
│  │  ├─ get_coin_details()                                     │
│  │  └─ Redis caching                                          │
│  │                                                             │
│  └─ [others]               [Email, SMS, etc]                   │
│                                                             │
│ Data (backend/)                                                │
│  ├─ redis_cache.py         [Redis wrapper]                     │
│  │  ├─ get_cached_prices()                                    │
│  │  ├─ set() with TTL                                         │
│  │  └─ Cache invalidation                                     │
│  │                                                             │
│  └─ blacklist.py           [Token blacklist]                   │
│     └─ Tracks logged-out tokens                                │
│                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

This comprehensive visual summary shows:
1. **Complete system architecture** - all layers from browser to database
2. **Request-response cycle** - exact steps from user click to data display  
3. **Authentication lifecycle** - login, token refresh, logout
4. **File responsibilities** - which files handle what

For more details, see:
- `FRONTEND_BACKEND_ARCHITECTURE.md` (967 lines, comprehensive)
- `QUICK_API_REFERENCE.md` (509 lines, practical guide)
