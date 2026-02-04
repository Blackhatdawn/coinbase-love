# 🚀 Render.com Deployment Guide for CryptoVault Backend

## 📋 Prerequisites

1. **Render Account**: Sign up at https://render.com
2. **GitHub Repository**: Push this code to GitHub
3. **MongoDB Atlas**: Running cluster (already configured)
4. **Domain**: `cryptovault.financial` (DNS configured)

---

## 🎯 Quick Deploy (5 Minutes)

### Method 1: Using render.yaml (Recommended)

1. **Push to GitHub**:
   ```bash
   git add .
   git commit -m "Render deployment config"
   git push origin main
   ```

2. **Connect to Render**:
   - Go to https://dashboard.render.com
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`
   - Click "Apply"

3. **Set Environment Secrets**:
   Go to your service → "Environment" and add these secrets:
   ```bash
   MONGO_URL=mongodb+srv://team_db_user:mWPe3V6ZhoNNEWUk@cryptovaultcluster.vobw2w8.mongodb.net/?appName=CryptoVaultCluster
   JWT_SECRET=jmZgXmsOEx10hwWOIE6EvhCft56jew6PVSiSweq-JQI
   CSRF_SECRET=fintech-architect-4
   SENDGRID_API_KEY=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
   TELEGRAM_BOT_TOKEN=8436666880:AAH4W6mmysV4FjbGcYw3to3_Tfcd3qJEpAk
   ADMIN_TELEGRAM_CHAT_ID=5639295577
   COINCAP_API_KEY=68aa5a01aa84e5704a10f5d6f730dadd9381901161e06d07085fcca8587f41e3
   NOWPAYMENTS_API_KEY=ZKDVT1B-4WTMVAZ-KZ7E38G-GPNE8Q7
   NOWPAYMENTS_IPN_SECRET=bEEgqlb1q+TF6ygQfNJ+fUJyWvARDJwp
   UPSTASH_REDIS_REST_URL=https://emerging-sponge-14455.upstash.io
   UPSTASH_REDIS_REST_TOKEN=ATh3AAIncDE5OTMzNjFiM2M4NzA0NmEzOWQwOWE2MjgwODczMDNlM3AxMTQ0NTU
   SENTRY_DSN=https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/4510716879503360
   ```

4. **Deploy**: Click "Manual Deploy" → "Deploy latest commit"

---

### Method 2: Manual Setup (Alternative)

1. **Create New Web Service**:
   - Go to https://dashboard.render.com
   - Click "New" → "Web Service"
   - Connect GitHub repository

2. **Configure Service**:
   ```
   Name: cryptovault-backend
   Runtime: Python 3
   Region: Oregon (or closest to users)
   Branch: main
   Root Directory: backend
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT --workers 2
   Plan: Starter ($7/month) or Free (with limitations)
   ```

3. **Set Environment Variables**: Same as Method 1 above

4. **Health Check**:
   - Path: `/api/health`
   - Initial delay: 30 seconds

5. **Deploy**: Click "Create Web Service"

---

## 🔧 Post-Deployment Configuration

### 1. Custom Domain Setup

1. **In Render Dashboard**:
   - Go to your service → "Settings" → "Custom Domains"
   - Add: `api.cryptovault.financial`

2. **In Your DNS (Cloudflare/Namecheap)**:
   - Add CNAME record:
     ```
     Type: CNAME
     Name: api
     Value: cryptovault-backend.onrender.com
     TTL: Auto
     ```

3. **Wait for SSL**:
   - Render auto-provisions Let's Encrypt SSL (5-10 minutes)
   - Status will show "Active" when ready

### 2. Update Frontend URLs

Update `/app/frontend/.env`:
```bash
VITE_API_BASE_URL=https://api.cryptovault.financial
# or
VITE_API_BASE_URL=https://cryptovault-backend.onrender.com
```

### 3. Update CORS Origins

In Render dashboard, update `CORS_ORIGINS`:
```json
["https://www.cryptovault.financial","https://cryptovault.financial","https://api.cryptovault.financial"]
```

---

## ✅ Verify Deployment

### 1. Health Check
```bash
curl https://api.cryptovault.financial/api/health
# Expected: {"status":"healthy","timestamp":"..."}
```

### 2. Database Connection
```bash
curl https://api.cryptovault.financial/api/monitoring/database
# Expected: {"status":"connected","latency_ms":...}
```

### 3. Telegram Bot
```bash
# Send test message to your Telegram
curl -X POST https://api.cryptovault.financial/api/admin/test-telegram
```

### 4. Admin OTP Login
- Go to: https://www.cryptovault.financial/admin/login
- Enter admin credentials
- Should receive OTP email via SendGrid

---

## 📊 Monitoring & Logs

### View Logs
```bash
# In Render dashboard:
Service → Logs → Live logs
```

### Metrics
```bash
# In Render dashboard:
Service → Metrics
- CPU usage
- Memory usage
- Response times
- Request counts
```

### Sentry Error Tracking
- Errors automatically sent to Sentry
- View at: https://sentry.io/organizations/your-org/

---

## 🔄 Auto-Deploy Setup

### Enable Auto-Deploy from GitHub

1. **In Render Dashboard**:
   - Service → "Settings" → "Auto-Deploy"
   - Enable "Auto-Deploy" for main branch

2. **Now whenever you push to GitHub**:
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin main
   ```
   Render will automatically build and deploy!

---

## 🚀 Performance Optimization

### 1. Increase Workers (Starter Plan+)

In `render.yaml` or dashboard, update start command:
```bash
uvicorn server:app --host 0.0.0.0 --port $PORT --workers 4
```

### 2. Enable HTTP/2
- Automatic on Render with SSL

### 3. Add CDN (Cloudflare)
1. Point domain to Cloudflare
2. Cloudflare proxies traffic (orange cloud)
3. Automatic caching + DDoS protection

---

## 💰 Pricing

### Render Plans

| Plan | Price | Resources | Best For |
|------|-------|-----------|----------|
| Free | $0 | 512MB RAM, sleeps after 15min | Development/Testing |
| Starter | $7/month | 512MB RAM, always on | MVP/Small apps |
| Standard | $25/month | 2GB RAM, more CPU | Production (recommended) |
| Pro | $85/month | 4GB RAM, dedicated CPU | High traffic |

**Recommendation**: Start with **Starter ($7/month)**, upgrade to **Standard ($25/month)** when you get real users.

---

## 🔐 Security Checklist

- ✅ All secrets in Render environment (not in code)
- ✅ HTTPS enforced (automatic with Render)
- ✅ CORS restricted to your domains only
- ✅ Rate limiting enabled (60 req/min)
- ✅ JWT secrets are strong (256-bit)
- ✅ MongoDB connection uses SSL
- ✅ SendGrid email authenticated
- ✅ Admin OTP enabled

---

## 🆘 Troubleshooting

### Service Won't Start

1. **Check Logs**:
   ```bash
   # In Render dashboard → Logs
   # Look for error messages
   ```

2. **Common Issues**:
   - Missing environment variables
   - MongoDB connection timeout (check IP whitelist)
   - Port binding (Render uses `$PORT`, not 8000)

### MongoDB Connection Failed

1. **MongoDB Atlas IP Whitelist**:
   - Go to MongoDB Atlas → Network Access
   - Add: `0.0.0.0/0` (allow all IPs)
   - Or add Render's IP ranges

2. **Check Connection String**:
   ```bash
   # In Render dashboard → Environment
   # Verify MONGO_URL is correct
   ```

### Slow Performance

1. **Upgrade Plan**: Starter → Standard
2. **Increase Workers**: 2 → 4
3. **Add Redis Caching**: Already configured (Upstash)

### Domain Not Working

1. **Check DNS Propagation**: https://dnschecker.org
2. **Verify CNAME**: Should point to `*.onrender.com`
3. **Wait for SSL**: Can take 10-15 minutes

---

## 📞 Support

### Render Support
- Docs: https://render.com/docs
- Community: https://community.render.com
- Email: support@render.com

### CryptoVault Support
- Check logs first: Render Dashboard → Logs
- Sentry: https://sentry.io (for backend errors)
- MongoDB: https://cloud.mongodb.com (for database issues)

---

## 🎉 Success Checklist

After deployment, verify:

- [ ] Backend is running: `https://api.cryptovault.financial/api/health`
- [ ] Database connected: Check logs for MongoDB connection
- [ ] Redis working: Check Upstash dashboard
- [ ] SendGrid emails: Test admin OTP login
- [ ] Telegram bot: Test with `/info` command
- [ ] NOWPayments: Test crypto deposit (sandbox or small amount)
- [ ] Frontend connects: Check browser console for API calls
- [ ] Admin panel works: Login with OTP
- [ ] CORS configured: No CORS errors in browser
- [ ] SSL certificate active: HTTPS padlock icon visible

---

## 🚀 Go Live!

Once all checks pass:

1. **Announce Launch**: Social media, email list, etc.
2. **Monitor Closely**: First 24 hours, watch logs for errors
3. **Scale as Needed**: Upgrade Render plan if traffic increases
4. **Backup Database**: MongoDB Atlas has automated backups

**Congratulations! CryptoVault is now live on Render! 🎉**

---

## 📚 Additional Resources

- Render Python Docs: https://render.com/docs/deploy-fastapi
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- MongoDB Atlas: https://www.mongodb.com/docs/atlas/
- Render Status: https://status.render.com
