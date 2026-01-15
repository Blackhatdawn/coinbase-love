# CryptoVault Architecture

## System Overview

CryptoVault is a full-stack cryptocurrency trading platform built with modern web technologies and cloud-native architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Browser    │  │    Mobile    │  │   Desktop    │         │
│  │   (React)    │  │   (Future)   │  │   (Future)   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │ HTTPS
┌──────────────────────────┼──────────────────────────────────────┐
│                    CDN / EDGE LAYER                              │
│                    ┌──────▼────────┐                            │
│                    │    Vercel     │                            │
│                    │   (Frontend)  │                            │
│                    └──────┬────────┘                            │
└───────────────────────────┼──────────────────────────────────────┘
                            │ API Calls
┌───────────────────────────▼──────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │               FastAPI Application (Render)                 │ │
│  │                                                            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│  │  │   Auth   │ │Portfolio │ │ Trading  │ │  Admin   │    │ │
│  │  │  Router  │ │  Router  │ │  Router  │ │  Router  │    │ │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘    │ │
│  │       │            │            │            │            │ │
│  │  ┌────▼────────────▼────────────▼────────────▼─────┐    │ │
│  │  │          Middleware Layer                       │    │ │
│  │  │  - Rate Limiting                                │    │ │
│  │  │  - Request ID                                   │    │ │
│  │  │  - Security Headers                             │    │ │
│  │  │  - CORS                                         │    │ │
│  │  └─────────────────────────────────────────────────┘    │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────┬──────────────────────┬───────────────────────────┘
                │                      │
      ┌─────────▼──────┐    ┌─────────▼──────┐
      │  Service Layer │    │  Service Layer │
      └─────────┬──────┘    └─────────┬──────┘
                │                      │
┌───────────────▼──────────────────────▼───────────────────────────┐
│                      DATA LAYER                                   │
│                                                                   │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐   │
│  │   MongoDB      │  │     Redis      │  │   External APIs │   │
│  │   (Atlas)      │  │   (Upstash)    │  │  - CoinGecko    │   │
│  │                │  │                │  │  - SendGrid     │   │
│  │  - Users       │  │  - Cache       │  │  - NOWPayments  │   │
│  │  - Portfolios  │  │  - Sessions    │  └─────────────────┘   │
│  │  - Orders      │  │  - OTPs        │                         │
│  │  - Audit Logs  │  └────────────────┘                         │
│  └────────────────┘                                              │
└───────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Frontend (React + Vite)

**Purpose**: User interface and client-side logic

**Key Technologies**:
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS + Shadcn/UI
- React Router for navigation
- Zustand for state management
- Axios for HTTP requests

**Key Features**:
- Server-side rendering ready
- Code splitting and lazy loading
- Responsive mobile-first design
- Real-time updates via WebSocket
- JWT token management
- Error boundary handling

### 2. Backend (FastAPI)

**Purpose**: API server and business logic

**Key Technologies**:
- FastAPI (Python 3.11+)
- Pydantic for data validation
- Motor for async MongoDB
- Redis for caching
- JWT for authentication

**Architecture Pattern**: Modular Router-Based

```python
backend/
├── routers/
│   ├── auth.py       # Authentication endpoints
│   ├── portfolio.py  # Portfolio management
│   ├── trading.py    # Trading & orders
│   ├── crypto.py     # Market data
│   └── admin.py      # Admin functions
├── services/
│   ├── email_service.py      # Email operations
│   ├── coingecko_service.py  # Market data
│   └── redis_cache.py        # Caching layer
├── models.py         # Pydantic models
├── dependencies.py   # Dependency injection
└── server.py         # Application entry
```

### 3. Database Layer

#### MongoDB (Primary Database)

**Collections**:

```javascript
// users
{
  _id: ObjectId,
  id: UUID,                    // Application ID
  email: String (unique),
  password_hash: String,
  name: String,
  email_verified: Boolean,
  two_factor_enabled: Boolean,
  created_at: DateTime,
  last_login: DateTime,
  failed_login_attempts: Number,
  locked_until: DateTime?
}

// portfolios
{
  _id: ObjectId,
  id: UUID,
  user_id: UUID (indexed),
  holdings: [
    {
      symbol: String,
      name: String,
      amount: Number,
      value: Number,
      allocation: Number
    }
  ],
  updated_at: DateTime
}

// orders
{
  _id: ObjectId,
  id: UUID,
  user_id: UUID (indexed),
  trading_pair: String,
  order_type: String,
  side: String,  // buy/sell
  amount: Number,
  price: Number,
  status: String,
  created_at: DateTime (indexed),
  filled_at: DateTime?
}

// audit_logs
{
  _id: ObjectId,
  id: UUID,
  user_id: UUID (indexed),
  action: String (indexed),
  resource: String?,
  ip_address: String,
  timestamp: DateTime (indexed),
  details: Object
}
```

**Indexes**:
```javascript
// Performance indexes
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ last_login: 1 })
db.portfolios.createIndex({ user_id: 1 }, { unique: true })
db.orders.createIndex({ user_id: 1, created_at: -1 })
db.audit_logs.createIndex({ user_id: 1, timestamp: -1 })

// TTL indexes for auto-cleanup
db.login_attempts.createIndex(
  { timestamp: 1 }, 
  { expireAfterSeconds: 2592000 }  // 30 days
)
db.blacklisted_tokens.createIndex(
  { expires_at: 1 }, 
  { expireAfterSeconds: 0 }
)
```

#### Redis (Cache & Sessions)

**Key Structure**:
```
cryptovault:otp:{email}           - OTP codes (TTL: 10 min)
cryptovault:prices:all            - Cached price data (TTL: 30 sec)
cryptovault:portfolio:{user_id}   - Portfolio cache (TTL: 15 sec)
cryptovault:blacklist:{token}     - Blacklisted tokens
```

## Data Flow

### Authentication Flow

```
┌──────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│Client│     │ Backend  │     │  Redis  │     │ SendGrid │
└───┬──┘     └────┬─────┘     └────┬────┘     └────┬─────┘
    │             │                │               │
    │ POST /signup│                │               │
    ├────────────>│                │               │
    │             │ Generate OTP   │               │
    │             ├───────────────>│               │
    │             │                │               │
    │             │ Send Email     │               │
    │             ├───────────────────────────────>│
    │             │                │               │
    │<────────────┤ 200 OK         │               │
    │             │                │               │
    │ POST /verify│                │               │
    ├────────────>│                │               │
    │             │ Verify OTP     │               │
    │             ├───────────────>│               │
    │             │<───────────────┤               │
    │             │ Issue JWT      │               │
    │<────────────┤                │               │
    │ (Set Cookie)│                │               │
```

### Trading Flow

```
┌──────┐     ┌──────────┐     ┌─────────┐     ┌──────────┐
│Client│     │ Backend  │     │ MongoDB │     │CoinGecko │
└───┬──┘     └────┬─────┘     └────┬────┘     └────┬─────┘
    │             │                │               │
    │ POST /orders│                │               │
    ├────────────>│                │               │
    │             │ Validate JWT   │               │
    │             │                │               │
    │             │ Get Price      │               │
    │             ├───────────────────────────────>│
    │             │<───────────────────────────────┤
    │             │                │               │
    │             │ Create Order   │               │
    │             ├───────────────>│               │
    │             │                │               │
    │             │ Update Portfolio                │
    │             ├───────────────>│               │
    │             │                │               │
    │             │ Log Audit      │               │
    │             ├───────────────>│               │
    │             │                │               │
    │<────────────┤ 200 OK         │               │
    │  Order Info │                │               │
```

## Security Architecture

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────┐
│              Security Layers                        │
├─────────────────────────────────────────────────────┤
│  1. HTTPS/TLS (Transport Layer)                    │
│     - Managed by Vercel/Render                     │
│     - Certificate auto-renewal                     │
├─────────────────────────────────────────────────────┤
│  2. CORS (Cross-Origin)                            │
│     - Whitelist specific origins                   │
│     - Credentials allowed                          │
├─────────────────────────────────────────────────────┤
│  3. Security Headers                                │
│     - HSTS, CSP, X-Frame-Options                   │
│     - X-Content-Type-Options                       │
├─────────────────────────────────────────────────────┤
│  4. Rate Limiting                                   │
│     - Per-IP tracking                              │
│     - Per-user limits                              │
│     - Different limits per endpoint type           │
├─────────────────────────────────────────────────────┤
│  5. JWT Authentication                              │
│     - Access token (30 min)                        │
│     - Refresh token (7 days)                       │
│     - HttpOnly cookies                             │
├─────────────────────────────────────────────────────┤
│  6. Input Validation                                │
│     - Pydantic models                              │
│     - Type checking                                │
│     - Sanitization                                 │
├─────────────────────────────────────────────────────┤
│  7. Password Security                               │
│     - bcrypt hashing                               │
│     - Min 8 characters                             │
│     - Account lockout after 5 failed attempts      │
└─────────────────────────────────────────────────────┘
```

### Token Flow

```
Access Token (30 min):                Refresh Token (7 days):
┌─────────────────┐                   ┌─────────────────┐
│  Header         │                   │  Header         │
│  {              │                   │  {              │
│    alg: HS256   │                   │    alg: HS256   │
│    typ: JWT     │                   │    typ: JWT     │
│  }              │                   │  }              │
├─────────────────┤                   ├─────────────────┤
│  Payload        │                   │  Payload        │
│  {              │                   │  {              │
│    sub: user_id │                   │    sub: user_id │
│    type: access │                   │    type: refresh│
│    exp: ...     │                   │    exp: ...     │
│  }              │                   │  }              │
├─────────────────┤                   ├─────────────────┤
│  Signature      │                   │  Signature      │
└─────────────────┘                   └─────────────────┘
        │                                     │
        │ Sent with every API request         │
        │ (Authorization header or cookie)    │
        │                                     │
        └─────────────────────────────────────┘
                         │
              Used to get new access token
              when current one expires
```

## Caching Strategy

```
┌────────────────────────────────────────────────────┐
│              Request Flow with Cache               │
└────────────────────────────────────────────────────┘

  Client Request
       │
       ▼
  ┌─────────┐
  │ FastAPI │
  └────┬────┘
       │
       ▼
  ┌──────────────┐     Cache Hit?
  │ Redis Cache  ├─────────Yes───> Return Data
  └──────┬───────┘
         │
         No (Cache Miss)
         │
         ▼
  ┌──────────────┐
  │  MongoDB or  │
  │ External API │
  └──────┬───────┘
         │
         ├─> Store in Cache (with TTL)
         │
         └─> Return Data
```

**Cache TTLs**:
- Price data: 30 seconds
- Portfolio: 15 seconds
- OTP codes: 10 minutes
- Blacklisted tokens: Until JWT expiry

## Scalability Considerations

### Horizontal Scaling

- **Frontend**: Automatically scaled by Vercel CDN
- **Backend**: Can scale via Render's instance manager
- **Database**: MongoDB Atlas auto-sharding
- **Cache**: Redis can be clustered

### Vertical Scaling

- Increase instance size on Render
- Upgrade MongoDB Atlas tier
- Optimize database queries with proper indexing

### Future Improvements

1. **Message Queue** (Celery + RabbitMQ)
   - Background email sending
   - Async order processing
   - Scheduled tasks

2. **CDN for Static Assets**
   - Cloudflare or AWS CloudFront
   - Image optimization

3. **Read Replicas**
   - MongoDB read replicas for heavy read operations
   - Separate analytics database

4. **Microservices**
   - Split into: Auth Service, Trading Service, Market Data Service
   - API Gateway for routing

## Monitoring & Observability

### Logging

```python
# Structured JSON logging
{
  "timestamp": "2025-01-15T14:30:00Z",
  "level": "INFO",
  "logger": "backend.routers.trading",
  "message": "Order created",
  "request_id": "abc-123",
  "user_id": "user-456",
  "order_id": "order-789",
  "duration_ms": 45.2
}
```

### Metrics to Track

- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (5xx responses)
- Database connection pool usage
- Cache hit/miss ratio
- Active WebSocket connections
- Trade volume ($/hour)

### Health Checks

```python
# /health endpoint checks:
✓ Database connectivity
✓ Redis connectivity
✓ External API availability (CoinGecko)
✓ Memory usage
✓ CPU usage
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│              Production Environment             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐         ┌──────────┐            │
│  │  Vercel  │◄────────┤  GitHub  │            │
│  │ (Frontend)         │           │            │
│  └──────────┘         └─────┬────┘            │
│                              │                  │
│                              │ Auto-deploy      │
│  ┌──────────┐               │                  │
│  │  Render  │◄──────────────┘                  │
│  │ (Backend)│                                   │
│  └──────────┘                                   │
│       │                                         │
│       │                                         │
│  ┌────▼─────┐  ┌──────────┐  ┌──────────┐    │
│  │ MongoDB  │  │  Redis   │  │ SendGrid │    │
│  │  Atlas   │  │ Upstash  │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘    │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Error Handling

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "request_id": "abc-123",
    "timestamp": "2025-01-15T14:30:00Z",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

### Error Codes

- `VALIDATION_ERROR` (400)
- `AUTHENTICATION_ERROR` (401)
- `AUTHORIZATION_ERROR` (403)
- `NOT_FOUND` (404)
- `RATE_LIMIT_EXCEEDED` (429)
- `INTERNAL_ERROR` (500)
- `SERVICE_UNAVAILABLE` (503)

---

**Last Updated**: January 2025  
**Version**: 1.0.0
