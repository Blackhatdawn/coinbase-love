# CryptoVault Backend - Enterprise Production Hardening Guide

## Overview

The CryptoVault backend has been hardened to enterprise-grade production standards with comprehensive error handling, health checks, graceful degradation, and monitoring capabilities.

## ✅ Completed Hardening Measures

### 1. **Environment Configuration & Validation**
- ✅ Comprehensive startup validation in `config.py`
- ✅ Structured validation results with detailed error reporting
- ✅ `startup.py` - Enterprise health check system
- ✅ Validation of critical environment variables
- ✅ Frontend/Backend configuration sync checks

**Status**: All critical env vars checked on startup. Server won't start if critical requirements are missing.

### 2. **Database Resilience**
- ✅ Connection pooling (10-50 connections)
- ✅ Exponential backoff retry logic (5 retries)
- ✅ Health check with 10-second timeout
- ✅ Graceful connection cleanup
- ✅ Query timeout protection (10 seconds default)
- ✅ MongoDB Atlas SSL configured
- ✅ Proper error logging and monitoring

**Commands**:
```bash
# MongoDB connection string format
MONGO_URL=mongodb+srv://user:password@cluster.mongodb.net/?appName=AppName

# Connection pool settings
MONGO_MAX_POOL_SIZE=10      # Connections to maintain
MONGO_TIMEOUT_MS=5000        # Server selection timeout
```

### 3. **Error Handling & Response Standardization**
- ✅ Centralized error codes (`error_handler.py`)
- ✅ Standardized error response format
- ✅ Request tracing with X-Request-ID
- ✅ Structured JSON logging in production
- ✅ Global exception handlers for all errors
- ✅ Sentry integration for error tracking

**Error Response Format**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input provided",
    "details": { "field": "value could not be parsed" },
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-04-03T10:30:00Z"
  }
}
```

### 4. **Security & Rate Limiting**
- ✅ Advanced rate limiter with burst protection
- ✅ IP-based and user-based rate limiting
- ✅ 15-minute IP blocking for burst attacks
- ✅ CORS configuration with origin validation
- ✅ Security headers (HSTS, CSP, X-Frame-Options, etc.)
- ✅ CSRF token generation and validation
- ✅ Input sanitization against NoSQL/XSS attacks
- ✅ Geo-blocking middleware (optional)

**Rate Limiting Configuration**:
```bash
RATE_LIMIT_PER_MINUTE=60        # Requests per minute
RATE_LIMIT_ENABLED=true         # Enable rate limiting
```

### 5. **Health Checks & Monitoring**
- ✅ Liveness probe (`/health/live`) - Fast, no dependencies
- ✅ Readiness probe (`/health/ready`) - Full dependency check
- ✅ Parallel health check execution with timeouts
- ✅ Metrics collection and Prometheus compatibility
- ✅ Request latency tracking
- ✅ Error rate monitoring

**Health Check Endpoints**:
```bash
GET /health/live    # Liveness probe (200 if process alive)
GET /health/ready   # Readiness probe (200 if dependencies healthy)
GET /api/health     # Full status
GET /ping          # Keep-alive endpoint
```

### 6. **Redis/Caching**
- ✅ Supports standard Redis and Upstash REST API
- ✅ Automatic fallback to in-memory cache
- ✅ TTL-based cache invalidation
- ✅ Response caching for expensive operations
- ✅ Token blacklist caching
- ✅ Price data caching

**Configuration**:
```bash
# Standard Redis
REDIS_URL=redis://user:password@host:port

# OR Upstash REST API (serverless)
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...

# Disable Redis
USE_REDIS=false    # Falls back to in-memory
```

### 7. **Graceful Degradation**
- ✅ Database unavailable: Returns 503 with retry headers
- ✅ Redis unavailable: Falls back to in-memory cache
- ✅ Telegram unavailable: Logs warning, continues
- ✅ Price stream unavailable: Uses cached prices
- ✅ External APIs: Circuit breaker pattern prevents cascade failures

### 8. **Performance Optimization**
- ✅ Database indexes for common queries
- ✅ Connection pooling to reduce overhead
- ✅ Response caching with TTL
- ✅ Async/await throughout for concurrency
- ✅ Request compression (GZip)
- ✅ Efficient WebSocket management

### 9. **Logging & Observability**
- ✅ JSON structured logging in production
- ✅ Request ID correlation across logs
- ✅ Sentry integration for error aggregation
- ✅ Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ Contextual information in every log entry

**Log Configuration**:
```bash
LOG_LEVEL=info                  # Production setting
LOG_FORMAT=json                 # JSON for log aggregation
SENTRY_DSN=https://...         # Error tracking
```

### 10. **Startup Sequence**
The new `startup.py` module provides comprehensive health checks:

```
1. Configuration Validation
   - Check JWT_SECRET, CSRF_SECRET, MONGO_URL
   - Validate email service configuration
   - Check frontend/backend CORS sync
   
2. MongoDB Connection
   - Test connectivity with timeout
   - Verify database access
   
3. Redis Connection
   - Test if configured
   - Provide warning if unavailable
   
4. External Services
   - Price stream service
   - Telegram bot (if configured)
   - Sentry error tracking

Result: Pass/Warn/Fail with structured output
```

## 🚀 Starting the Server

### Production (with gunicorn)
```bash
# Using the production startup script
./start_production.sh

# Manual command
export PORT=8000
export WORKERS=4
python start_server.py

# Or directly with gunicorn
gunicorn -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120 \
  server:app
```

### Development (with uvicorn)
```bash
python run_server.py
```

## 📊 Environment Setup for Production

### Required Environment Variables

```bash
# Core Configuration
ENVIRONMENT=production
FULL_PRODUCTION_CONFIGURATION=true
PORT=8000
HOST=0.0.0.0
WORKERS=4

# Database
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/?appName=AppName
DB_NAME=cryptovault
MONGO_MAX_POOL_SIZE=10
MONGO_TIMEOUT_MS=5000

# Security
JWT_SECRET=<32+ char random string>
CSRF_SECRET=<32+ char random string>
JWT_ALGORITHM=HS256

# Email (SMTP example)
EMAIL_SERVICE=smtp
SMTP_HOST=mail.example.com
SMTP_PORT=465
SMTP_USERNAME=user@example.com
SMTP_PASSWORD=<password>
SMTP_USE_SSL=true

# CORS & Frontend Integration
APP_URL=https://www.example.com
PUBLIC_API_URL=https://api.example.com
PUBLIC_WS_URL=wss://api.example.com
CORS_ORIGINS='["https://www.example.com"]'

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_ENABLED=true

# Optional Services
USE_REDIS=false                           # Or configure Redis/Upstash
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=<token>
ADMIN_TELEGRAM_CHAT_ID=<chat_id>
SENTRY_DSN=https://<key>@sentry.io/<project>
```

## 🔍 Monitoring & Debugging

### Health Check Response Example
```bash
curl https://api.example.com/health/ready

{
  "status": "healthy",
  "api": "running",
  "database": "connected",
  "redis": "connected",
  "environment": "production",
  "version": "1.0.0"
}
```

### Logs (JSON format in production)
```bash
# Follow logs with structured format
tail -f logs.json | jq '.'

# Filter by request ID
jq 'select(.request_id == "550e8400...")' logs.json
```

### Common Issues & Solutions

**Port already in use**:
```bash
# Check what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Database connection timeout**:
```
1. Verify MONGO_URL is correct
2. Check MongoDB cluster firewall rules (IP whitelist)
3. Verify network connectivity: ping cluster
4. Increase MONGO_TIMEOUT_MS if needed
```

**Redis connection fails** (automatically falls back):
```
Just start server - in-memory cache will be used
Later configure Redis/Upstash with:
  REDIS_URL=... OR UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN
```

## 📈 Performance Tuning

### Connection Pool Sizing
```bash
# Conservative (small apps)
MONGO_MAX_POOL_SIZE=5

# Standard (medium apps)
MONGO_MAX_POOL_SIZE=10

# Large scale
MONGO_MAX_POOL_SIZE=50
```

### Worker Configuration
```bash
# Development
WORKERS=1

# Production (4-8 per CPU core)
WORKERS=4

# High-load
WORKERS=8
```

### Cache Settings
- Response cache TTL: 60 seconds
- Price data cache: 45 seconds
- Token blacklist cache: Based on token expiry

## 🔐 Security Best Practices

1. **Never use default secrets**
   - Generate random JWT_SECRET (32+ chars)
   - Generate random CSRF_SECRET (32+ chars)

2. **Use environment variables**
   - Store secrets in .env (development only)
   - Use platform secrets management (production)

3. **Enable HTTPS**
   - HSTS enabled (forces HTTPS)
   - CSP headers configured
   - Secure cookies (SameSite=Lax)

4. **Monitor access**
   - Check request logs for suspicious patterns
   - Monitor error rates for anomalies
   - Use Sentry for critical errors

5. **Rate limiting**
   - Default 60 req/min per client
   - Burst protection (10 req/sec = block 15 min)
   - IP-based and user-based tracking

## 🎯 Deployment Checklist

- [ ] PORT environment variable set
- [ ] MONGO_URL configured and tested
- [ ] JWT_SECRET set (not default)
- [ ] CSRF_SECRET set (not default)
- [ ] CORS_ORIGINS configured for frontend domain
- [ ] EMAIL_SERVICE configured
- [ ] ENVIRONMENT=production
- [ ] FULL_PRODUCTION_CONFIGURATION=true
- [ ] Health check passes: `GET /health/ready` → 200
- [ ] All startup health checks pass
- [ ] Monitoring/logging configured
- [ ] Error handling tested
- [ ] Rate limiting tested
- [ ] HTTPS/TLS configured

## 📚 Additional Resources

- [Configuration Guide](./config.py)
- [Error Handler](./error_handler.py)
- [Startup Module](./startup.py)
- [Security Hardening](./security_hardening.py)
- [Performance Optimizations](./performance_optimizations.py)
- [Middleware](./middleware/)
