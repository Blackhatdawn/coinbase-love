# 🚀 CryptoVault - Production Quick Start

Get your CryptoVault deployed to production in 30 minutes.

---

## ⚡ Express Deployment (30 minutes)

### Step 1: MongoDB Atlas (5 minutes)

```bash
1. Go to https://cloud.mongodb.com/
2. Create account → Build Database → M0 Free
3. Create database user:
   - Username: cryptovault_admin
   - Password: [generate secure password]
4. Network Access → Allow 0.0.0.0/0
5. Database → Connect → Copy connection string:
   mongodb+srv://cryptovault_admin:PASSWORD@cluster.mongodb.net/cryptovault_production?retryWrites=true&w=majority
```

### Step 2: Deploy Backend to Render (10 minutes)

```bash
1. Go to https://dashboard.render.com/
2. New + → Web Service
3. Connect your GitHub repo
4. Configure:
   - Name: cryptovault-backend
   - Root Directory: backend
   - Runtime: Python 3
   - Build: pip install -r requirements.txt
   - Start: uvicorn server:app --host 0.0.0.0 --port $PORT
   - Health Check: /health

5. Environment Variables:
   PYTHON_VERSION=3.11.0
   ENVIRONMENT=production
   MONGO_URL=<your-atlas-connection-string>
   DB_NAME=cryptovault_production
   JWT_SECRET=[click Generate]
   CORS_ORIGINS=*  (update after Vercel deploy)
   MONGO_MAX_POOL_SIZE=50
   MONGO_MIN_POOL_SIZE=10

6. Create Web Service → Wait ~5 min
7. Copy your Render URL: https://cryptovault-backend.onrender.com
```

### Step 3: Deploy Frontend to Vercel (10 minutes)

```bash
# Option A: Vercel CLI
npm install -g vercel
cd frontend
vercel login
vercel

# Set env var when prompted:
VITE_API_URL=https://cryptovault-backend.onrender.com

vercel --prod

# Option B: Vercel Dashboard
1. Go to https://vercel.com/dashboard
2. New Project → Import Git repo
3. Configure:
   - Framework: Vite
   - Root Directory: frontend
   - Build: yarn build
   - Output: build
   
4. Environment Variables:
   VITE_API_URL=https://cryptovault-backend.onrender.com

5. Deploy → Wait ~3 min
6. Copy your Vercel URL: https://cryptovault.vercel.app
```

### Step 4: Update CORS (5 minutes)

```bash
1. Go to Render dashboard → your backend service
2. Environment → Update CORS_ORIGINS:
   CORS_ORIGINS=https://cryptovault.vercel.app
3. Save Changes → Wait for redeploy
```

### Step 5: Test Everything (5 minutes)

```bash
# Test backend
curl https://cryptovault-backend.onrender.com/health

# Test frontend
open https://cryptovault.vercel.app
# Try: Sign up → Login → View Markets → Add Portfolio
```

---

## ✅ Deployment Complete!

**Your URLs:**
- 🌐 Frontend: https://cryptovault.vercel.app
- 🖥️ Backend: https://cryptovault-backend.onrender.com
- ❤️ Health: https://cryptovault-backend.onrender.com/health

---

## 🔧 Common Issues & Fixes

### "Database not connected"
```bash
# Check MongoDB Atlas:
1. Cluster is running (not paused)
2. Network access allows 0.0.0.0/0
3. User password is correct in MONGO_URL
```

### "CORS error"
```bash
# Update CORS in Render:
1. Exact Vercel URL (no trailing slash)
2. Include https://
3. Save and wait for redeploy
```

### "API calls failing"
```bash
# Check VITE_API_URL in Vercel:
1. Should be your Render backend URL
2. Redeploy frontend after adding
```

---

## 📚 Full Documentation

- **Complete Guide**: `/app/DEPLOYMENT_GUIDE.md`
- **Checklist**: `/app/PRODUCTION_CHECKLIST.md`
- **Environment Setup**: `/app/ENVIRONMENT_SETUP.md`

---

## 🆘 Need Help?

1. Check logs in Render/Vercel dashboards
2. Review full deployment guide
3. Contact platform support

---

**Ready to scale?**
- Add custom domain
- Upgrade to paid tiers
- Set up monitoring
- Enable analytics

🎉 **You're live!**
