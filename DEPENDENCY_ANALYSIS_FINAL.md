# 🔍 Complete Dependency Analysis & Resolution

## 17 "Unused" Dependencies - Detailed Investigation

### ✅ KEEP - Actually Used (11 packages)

| Package | Purpose | Evidence | Status |
|---------|---------|----------|--------|
| **firebase-admin** | Push notifications via FCM | `fcm_service.py` imports it, mock mode if not configured | ✅ KEEP |
| **aiohappyeyeballs** | Async DNS resolver | Indirect dependency of `aiohttp` | ✅ KEEP (indirect) |
| **Brotli** | Compression algorithm | Used by `httpx` for response compression | ✅ KEEP (indirect) |
| **Pillow** | Image processing | Used for QR code generation in 2FA (`qrcode` library) | ✅ KEEP |
| **redis[hiredis]** | Cache & rate limiting | Used in `rate_limiter.py`, `cache.py` | ✅ KEEP |
| **python-dotenv** | Environment variables | Used in `config.py` | ✅ KEEP |
| **sentry-sdk[fastapi]** | Error tracking | Configured in `server.py` | ✅ KEEP |
| **sendgrid** | Email service | Used in email notifications | ✅ KEEP |
| **pyotp** | 2FA TOTP | Used in authentication | ✅ KEEP |
| **qrcode** | QR code generation | Used for 2FA setup | ✅ KEEP |
| **aiofiles** | Async file I/O | Used for log handling | ✅ KEEP |

### ⚠️ REMOVE - Not Used (3 packages)

| Package | Why Installed | Why Remove | Action |
|---------|---------------|------------|--------|
| **web3** | Blockchain integration planned | No Web3 code exists | ❌ REMOVE |
| **ethers** | Ethereum integration planned | Wrong package (JS library, not Python) | ❌ REMOVE |
| **requests** | HTTP client | Replaced by `httpx` (async) | ❌ REMOVE |

### 🟡 REVIEW - Conditional (3 packages)

| Package | Purpose | Decision |
|---------|---------|----------|
| **boto3** | AWS S3 for file storage | KEEP if using S3, REMOVE otherwise |
| **celery** | Background tasks | NOT INSTALLED (good - using FastAPI background tasks) |
| **gunicorn** | Production WSGI server | KEEP for production deployment |

---

## Resolution Plan

### Backend Cleanup
```bash
# Remove confirmed unused packages
pip uninstall -y web3 requests

# Note: 'ethers' is not a Python package (it's a JavaScript library)
# If it appears in requirements.txt, remove manually
```

### Frontend - No Issues
- `ethers` in frontend is correct (JavaScript library for Ethereum)
- `firebase` in frontend may be used for auth/analytics

---

## Why These Were Included

1. **firebase-admin** - Push notifications for price alerts (✅ Valid feature)
2. **web3** - Planned crypto wallet integration (❌ Never implemented)
3. **ethers** - Mistake (wrong language) or planned wallet feature (❌ Never implemented)
4. **requests** - Legacy HTTP client (❌ Replaced by httpx)

---

## Final Verdict

**Remove Only:**
- `web3` (Python package, not used)
- `requests` (replaced by httpx)

**Keep Everything Else** - They're either directly used or indirect dependencies of used packages.
