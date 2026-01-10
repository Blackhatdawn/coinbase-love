# Environment Configuration Guide

Complete guide to environment variables and configuration for CryptoVault.

---

## 📁 Environment Files Overview

```
/app
├── backend/.env              # Backend environment variables (DO NOT COMMIT)
├── backend/.env.example      # Backend template (safe to commit)
├── frontend/.env             # Frontend environment variables (DO NOT COMMIT)
└── frontend/.env.example     # Frontend template (safe to commit)
```

---

## 🔧 Backend Environment Variables

### Location: `/app/backend/.env`

```bash
# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="cryptovault_db"

# CORS Configuration
CORS_ORIGINS="*"

# Optional: JWT Secret (auto-generated if not provided)
# JWT_SECRET="your-super-secret-key"
```

### Variable Details

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGO_URL` | ✅ Yes | `mongodb://localhost:27017` | MongoDB connection string. Change for production MongoDB Atlas or remote instance. |
| `DB_NAME` | ✅ Yes | `cryptovault_db` | Database name for storing all collections (users, portfolios, orders, etc.) |
| `CORS_ORIGINS` | ✅ Yes | `*` | Comma-separated list of allowed origins. Use `*` for dev, specify domains in production. |
| `JWT_SECRET` | ❌ No | Auto-generated | Secret key for JWT signing. Auto-generated on startup if not provided. Set manually for production. |

### 🔒 **IMPORTANT - Protected Variables**

**DO NOT MODIFY** these unless you know what you're doing:
- The backend internally runs on **port 8001** (managed by supervisor)
- The host is set to **0.0.0.0** in the code
- These are mapped correctly by Kubernetes ingress

---

## 🎨 Frontend Environment Variables

### Location: `/app/frontend/.env`

```bash
# Backend API URL (automatically configured by platform)
REACT_APP_BACKEND_URL=https://wallet-hub-9.preview.emergentagent.com

# WebSocket port for HMR (Hot Module Replacement)
WDS_SOCKET_PORT=443

# Health check configuration
ENABLE_HEALTH_CHECK=false
```

### Variable Details

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REACT_APP_BACKEND_URL` | ✅ Yes | Platform URL | Backend API URL. **DO NOT MODIFY** - automatically set by platform. |
| `WDS_SOCKET_PORT` | ✅ Yes | `443` | WebSocket port for Vite HMR. Required for preview environments. |
| `ENABLE_HEALTH_CHECK` | ❌ No | `false` | Enable/disable health check endpoint. |
| `VITE_API_URL` | ❌ No | `/api` | Local dev proxy target. Only used if `REACT_APP_BACKEND_URL` not set. |

### 🔒 **IMPORTANT - Protected Variables**

**DO NOT MODIFY** `REACT_APP_BACKEND_URL`:
- This is automatically configured by the Emergent platform
- It points to the correct backend service URL
- Modifying it will break API communication

---

## 🚀 Environment Setup for Different Scenarios

### 1️⃣ **Local Development (Both Services on Localhost)**

**Backend** (`/app/backend/.env`):
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="cryptovault_dev"
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"
```

**Frontend** (`/app/frontend/.env`):
```bash
# Remove or comment out REACT_APP_BACKEND_URL to use proxy
# REACT_APP_BACKEND_URL=
VITE_API_URL=http://localhost:8001
```

### 2️⃣ **Platform Deployment (Current Setup)**

**Backend** (`/app/backend/.env`):
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="cryptovault_db"
CORS_ORIGINS="*"
```

**Frontend** (`/app/frontend/.env`):
```bash
REACT_APP_BACKEND_URL=https://wallet-hub-9.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

### 3️⃣ **Production Deployment**

**Backend** (`/app/backend/.env`):
```bash
MONGO_URL="mongodb+srv://user:password@cluster.mongodb.net/cryptovault?retryWrites=true&w=majority"
DB_NAME="cryptovault_production"
CORS_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
JWT_SECRET="super-secret-random-string-min-32-chars"
```

**Frontend** (`/app/frontend/.env`):
```bash
REACT_APP_BACKEND_URL=https://api.yourdomain.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=true
```

---

## 🔐 Security Best Practices

### ✅ DO:
1. **Keep `.env` files out of version control** (already in `.gitignore`)
2. **Use `.env.example` files** for templates
3. **Use strong JWT secrets** in production (min 32 characters)
4. **Restrict CORS origins** in production (no `*`)
5. **Use MongoDB authentication** in production
6. **Use environment-specific database names** (dev, staging, prod)

### ❌ DON'T:
1. **Don't commit `.env` files** to Git
2. **Don't use `CORS_ORIGINS="*"`** in production
3. **Don't share credentials** in documentation
4. **Don't modify platform-managed URLs** without understanding impact
5. **Don't use weak or default passwords**

---

## 🔄 How to Change Environment Variables

### Backend Variables:

1. Edit `/app/backend/.env`
2. Restart backend service:
   ```bash
   sudo supervisorctl restart backend
   ```
3. Verify changes in logs:
   ```bash
   tail -f /var/log/supervisor/backend.out.log
   ```

### Frontend Variables:

1. Edit `/app/frontend/.env`
2. Restart frontend service:
   ```bash
   sudo supervisorctl restart frontend
   ```
3. Verify in browser DevTools → Network tab

---

## 🧪 Testing Environment Configuration

### Test Backend Connection:
```bash
# Check if backend can connect to MongoDB
curl http://localhost:8001/api/

# Expected output:
# {"message":"CryptoVault API v1.0","status":"operational"}
```

### Test Frontend API Connection:
```bash
# Check if frontend can reach backend
curl http://localhost:3000

# In browser console:
fetch('/api/crypto').then(r => r.json()).then(console.log)
```

### Test Environment Variables:
```bash
# Backend - check loaded env vars
cd /app/backend
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('MONGO_URL:', os.environ.get('MONGO_URL')); print('DB_NAME:', os.environ.get('DB_NAME'))"

# Frontend - check Vite env vars
cd /app/frontend
cat .env
```

---

## 🐛 Troubleshooting

### Issue: "Cannot connect to MongoDB"
**Solution**: Check `MONGO_URL` in backend `.env`
```bash
# Test MongoDB connection
mongosh mongodb://localhost:27017
```

### Issue: "CORS error in browser"
**Solution**: Add frontend URL to `CORS_ORIGINS`
```bash
# In /app/backend/.env
CORS_ORIGINS="http://localhost:3000,https://your-frontend-url.com"
```

### Issue: "API calls return 404"
**Solution**: Verify `REACT_APP_BACKEND_URL` points to correct backend
```bash
# Check in browser DevTools → Network tab
# API calls should go to: https://wallet-hub-9.preview.emergentagent.com/api/*
```

### Issue: "JWT token invalid"
**Solution**: If you changed `JWT_SECRET`, all existing tokens are invalid
```bash
# Users need to log out and log back in
# Or clear cookies in browser
```

---

## 📝 Environment Variable Checklist

Before deployment, verify:

- [ ] ✅ MongoDB is accessible with `MONGO_URL`
- [ ] ✅ `DB_NAME` is set correctly for environment (dev/staging/prod)
- [ ] ✅ `CORS_ORIGINS` allows frontend domain
- [ ] ✅ `REACT_APP_BACKEND_URL` points to correct backend
- [ ] ✅ `JWT_SECRET` is set in production (auto-gen is fine for dev)
- [ ] ✅ `.env` files are in `.gitignore`
- [ ] ✅ `.env.example` files are committed
- [ ] ✅ Services restart after env changes

---

## 📚 Additional Resources

- [FastAPI Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [MongoDB Connection String](https://www.mongodb.com/docs/manual/reference/connection-string/)
- [CORS Configuration](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)

---

**Last Updated**: January 10, 2026  
**Platform**: Emergent Agent  
**Environment**: Development/Preview
