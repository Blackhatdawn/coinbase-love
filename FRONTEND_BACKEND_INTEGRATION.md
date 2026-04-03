# Frontend-Backend Integration Guide

## Overview

This guide ensures CryptoVault frontend and backend work seamlessly together in production with proper API communication, configuration sharing, and error handling.

## 📍 API Base URLs Configuration

### Frontend Configuration

The frontend must point to the correct backend API. Set these in your deployment platform:

**Vercel Environment Variables**:
```bash
VITE_API_BASE_URL=https://api.example.com
VITE_WS_URL=wss://api.example.com
VITE_SOCKET_IO_PATH=/socket.io/
```

### Backend Configuration

The backend must know the frontend origin for CORS:

```bash
# Backend .env
APP_URL=https://www.example.com
PUBLIC_API_URL=https://api.example.com
PUBLIC_WS_URL=wss://api.example.com
CORS_ORIGINS='["https://www.example.com","https://www.example.com"]'
PUBLIC_SOCKET_IO_PATH=/socket.io/
```

### URL Mapping Example

```
Frontend Domain     →    Backend API URL
www.example.com    →    api.example.com
app.example.com    →    api.example.com
localhost:3000     →    localhost:8000
```

## 🔄 Data Flow & Communication

### 1. RESTful API Calls from Frontend → Backend

**Standard Request Pattern**:
```typescript
// Frontend (React)
const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken  // From /api/csrf endpoint
  },
  credentials: 'include',  // Include cookies (JWT)
  body: JSON.stringify({ email, password })
});

const data = await response.json();
// Response format (backend):
// {
//   "data": { user, token },
//   "message": "Success",
//   "request_id": "...",
//   "timestamp": "..."
// }
```

**Backend Response**:
```python
# FastAPI endpoint
@router.post("/login")
async def login(request: LoginRequest):
    # Process login
    return {
        "data": {
            "user_id": user.id,
            "token": access_token,
            "refresh_token": refresh_token
        },
        "message": "Login successful"
    }
```

### 2. WebSocket Real-time Updates

**Frontend Connection**:
```typescript
import { io } from 'socket.io-client';

const socket = io(WS_URL, {
  path: SOCKET_IO_PATH,           // /socket.io/
  auth: {
    token: accessToken
  },
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});

socket.on('price_update', (prices) => {
  // Handle real-time price updates
});
```

**Backend Emission**:
```python
# Backend
from socketio_server import socketio_manager

await socketio_manager.emit_to_user(
    user_id='user123',
    event='price_update',
    data={'BTC': 45000, 'ETH': 2500}
)
```

### 3. Authentication Token Flow

```
1. Frontend calls POST /api/auth/login
2. Backend returns access_token + refresh_token
3. Frontend stores in memory (access_token) + httpOnly cookie (refresh_token)
4. Frontend sends Authorization header on API calls
5. Backend validates JWT token
6. When expired, Frontend calls POST /api/auth/refresh
7. Backend returns new access_token
```

**Token Headers**:
```bash
Authorization: Bearer <access_token>
X-CSRF-Token: <csrf_token>
Cookie: refresh_token=<refresh_token>; access_token=<access_token>
```

## 🔐 Security Integration

### CSRF Protection

1. **Frontend gets CSRF token on app load**:
```typescript
// On app initialization
const response = await fetch(`${API_BASE_URL}/api/csrf`, {
  credentials: 'include'
});
const { csrf_token } = await response.json();
// Store in state (not localStorage!)
```

2. **Frontend includes CSRF token in requests**:
```typescript
// For POST/PUT/PATCH/DELETE requests
headers: {
  'X-CSRF-Token': csrfToken
}
```

### CORS Configuration

**Backend validates origin**:
```python
# Frontend origin must be in CORS_ORIGINS
CORS_ORIGINS='["https://www.example.com"]'

# Frontend can make credentialed requests:
fetch(url, {
  credentials: 'include'  // Send cookies
})
```

### Security Headers Validation

**Frontend should check**:
```typescript
// Verify security headers are present
const headers = response.headers;
console.assert(headers.get('strict-transport-security')); // HSTS
console.assert(headers.get('x-frame-options')); // Clickjacking protection
console.assert(headers.get('x-content-type-options')); // MIME sniffing
```

## ⚠️ Error Handling

### Standardized Error Format

Both frontend and backend use same error structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": { "field": "email" },
    "request_id": "550e8400-...",
    "timestamp": "2026-04-03T10:30:00Z"
  }
}
```

### Frontend Error Handling

```typescript
async function apiCall(endpoint: string, options: any) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    
    if (!response.ok) {
      const errorData = await response.json();
      // errorData.error.code, errorData.error.message, etc.
      throw new APIError(errorData.error);
    }
    
    return await response.json();
  } catch (error) {
    // Log error with request_id for backend investigation
    logError(error.request_id);
    // Show user-friendly message
    showError(error.message);
  }
}
```

### Status Code Mapping

| Code | Meaning | Frontend Action |
|------|---------|-----------------|
| 200 | Success | Process data |
| 400 | Bad Request | Show validation error |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show permission denied |
| 404 | Not Found | Show 404 error |
| 429 | Rate Limited | Show retry message |
| 500 | Server Error | Show error, retry later |
| 503 | Service Unavailable | Show maintenance message |

## 📊 Configuration Endpoints

### Get Runtime Configuration

**Frontend calls**:
```bash
GET /api/config
```

**Backend response**:
```json
{
  "api_url": "https://api.example.com",
  "ws_url": "wss://api.example.com",
  "socket_io_path": "/socket.io/",
  "features": {
    "kyc_enabled": true,
    "2fa_enabled": true,
    "deposits_enabled": true,
    "withdrawals_enabled": true
  },
  "sentry_dsn": "https://...",
  "maintenance_mode": false
}
```

This allows frontend to adapt to different backend environments without rebuilds.

## 🎯 Common Integration Issues & Solutions

### Issue: CORS Error in Browser

**Solution**:
```
1. Check backend CORS_ORIGINS includes frontend domain
2. Verify frontend is using exact domain (https, www, port)
3. Check Access-Control-Allow-Credentials header present
4. Check if credentials: 'include' in fetch options
```

**Debugging**:
```bash
# In browser DevTools > Network tab, check response headers:
Access-Control-Allow-Origin: https://www.example.com
Access-Control-Allow-Credentials: true
```

### Issue: JWT Token Not Persisting

**Solution**:
```typescript
// Don't use localStorage for tokens (XSS vulnerability)
// Use httpOnly cookies instead (set by backend)

// Frontend can store in memory
let accessToken = null;

socket.on('auth', (data) => {
  accessToken = data.token;  // In memory only!
});
```

### Issue: WebSocket Reconnection Fails

**Solution**:
```typescript
// Configure socket with proper reconnection settings
const socket = io(WS_URL, {
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: 5,
  auth: {
    token: accessToken
  }
});

socket.on('connect_error', (error) => {
  console.error('Connection error:', error);
  // Show user-friendly connection status
});
```

### Issue: Stale Data After Server Restart

**Solution**:
```typescript
// Implement version checking
let dataVersion = 0;

socket.on('data_update', (data) => {
  if (data.version > dataVersion) {
    dataVersion = data.version;
    // Update state
  }
});
```

## 🚀 Deployment Checklist

### Before Frontend Deployment

- [ ] Update VITE_API_BASE_URL to production backend URL
- [ ] Update VITE_WS_URL to WebSocket URL
- [ ] Verify API_BASE_URL doesn't have trailing slash
- [ ] Check Sentry DSN for error tracking
- [ ] Test CORS by making sample API call
- [ ] Verify JWT token storage (memory + httpOnly cookies)

### Before Backend Deployment

- [ ] Set CORS_ORIGINS to include all frontend domains
- [ ] Verify APP_URL matches frontend domain
- [ ] Set PUBLIC_API_URL and PUBLIC_WS_URL
- [ ] Test /api/config endpoint returns correct values
- [ ] Verify health check passes
- [ ] Test authentication flow (login → token → api call)
- [ ] Test WebSocket connection

### After Deployment Testing

```bash
# Test API connectivity
curl -H "Origin: https://www.example.com" \
  -H "Access-Control-Request-Method: POST" \
  https://api.example.com/api/health

# Test CSRF token endpoint
curl -v https://api.example.com/api/csrf

# Test WebSocket
wscat -c wss://api.example.com/socket.io/
```

## 📈 Performance Optimization

### Request Batching

```typescript
// Frontend batching multiple API calls
const [users, posts] = await Promise.all([
  fetch(`${API_BASE_URL}/api/users`),
  fetch(`${API_BASE_URL}/api/posts`)
]);
```

### Response Caching

```typescript
// Frontend should cache API responses
const cache = new Map();

async function cachedFetch(url: string, ttl: number = 60000) {
  if (cache.has(url)) {
    return cache.get(url);
  }
  const response = await fetch(url);
  const data = await response.json();
  cache.set(url, data);
  setTimeout(() => cache.delete(url), ttl);
  return data;
}
```

### WebSocket Optimization

```typescript
// Only subscribe to needed events
socket.emit('subscribe', ['price_updates', 'portfolio_changes']);

// Unsubscribe when leaving page
socket.emit('unsubscribe', ['price_updates']);

// Listen for connection quality
socket.on('ping', () => {
  // Measure latency
});
```

## 🔍 Monitoring Integration

### Frontend Error Reporting

```typescript
// Send errors to Sentry (via frontend DSN)
Sentry.captureException(error, {
  tags: {
    request_id: response.request_id,
    endpoint: endpoint,
  }
});
```

### Backend Request Tracing

```python
# Correlate frontend requests in backend logs
logger.info(
    "API request",
    extra={
        "request_id": request.headers.get('X-Request-ID'),
        "endpoint": request.url.path,
        "status": response.status_code
    }
)
```

## 📚 Related Documentation

- [Backend Production Hardening](./PRODUCTION_HARDENING.md)
- [API Documentation](./docs/API.md)
- [Security Audit Report](./docs/SECURITY_AUDIT_REPORT.md)
