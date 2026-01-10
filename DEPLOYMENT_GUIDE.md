# 🚀 CryptoVault Production Deployment Guide

Complete guide to deploying CryptoVault to Vercel (Frontend) and Render (Backend).

---

## 📋 Prerequisites

### Required Accounts:
1. ✅ [Vercel Account](https://vercel.com/signup) (Free tier available)
2. ✅ [Render Account](https://render.com/register) (Free tier available)
3. ✅ [MongoDB Atlas Account](https://www.mongodb.com/cloud/atlas/register) (Free M0 cluster)
4. ✅ [GitHub Account](https://github.com/signup) (for repository)

### Required Tools:
- Git
- Node.js 18+
- Python 3.11+

---

## 🗂️ Step 1: Set Up MongoDB Atlas

### 1.1 Create MongoDB Cluster

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Click **"Build a Database"**
3. Choose **M0 (Free)** tier
4. Select region closest to your Render backend (e.g., Oregon)
5. Name your cluster: `cryptovault-cluster`
6. Click **"Create"**

### 1.2 Configure Database Access

1. Go to **Database Access** → **Add New Database User**
2. Username: `cryptovault_admin`
3. Password: Generate secure password (save this!)
4. User Privileges: **Read and write to any database**
5. Click **"Add User"**

### 1.3 Configure Network Access

1. Go to **Network Access** → **Add IP Address**
2. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ This is needed for Render's dynamic IPs
3. Click **"Confirm"**

### 1.4 Get Connection String

1. Go to **Database** → **Connect**
2. Choose **"Connect your application"**
3. Driver: **Python** / Version: **3.11 or later**
4. Copy connection string:
   ```
   mongodb+srv://cryptovault_admin:<password>@cryptovault-cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password
6. Add database name at the end:
   ```
   mongodb+srv://cryptovault_admin:YOUR_PASSWORD@cryptovault-cluster.xxxxx.mongodb.net/cryptovault_production?retryWrites=true&w=majority
   ```

---

## 🖥️ Step 2: Deploy Backend to Render

### 2.1 Prepare Repository

```bash
# Commit your code
git add .
git commit -m "Ready for production deployment"
git push origin main
```

### 2.2 Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure service:
   - **Name**: `cryptovault-backend`
   - **Region**: Oregon (or nearest)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`

### 2.3 Set Environment Variables

In Render dashboard, go to **Environment** and add:

| Key | Value |
|-----|-------|
| `PYTHON_VERSION` | `3.11.0` |
| `ENVIRONMENT` | `production` |
| `MONGO_URL` | Your MongoDB Atlas connection string |
| `DB_NAME` | `cryptovault_production` |
| `JWT_SECRET` | Click "Generate" for secure random value |
| `CORS_ORIGINS` | `https://your-project.vercel.app` (update after Vercel deploy) |
| `MONGO_MAX_POOL_SIZE` | `50` |
| `MONGO_MIN_POOL_SIZE` | `10` |
| `MONGO_TIMEOUT_MS` | `5000` |
| `RATE_LIMIT_PER_MINUTE` | `60` |

### 2.4 Configure Health Check

1. In Render dashboard, go to **Settings**
2. **Health Check Path**: `/health`
3. Click **"Save Changes"**

### 2.5 Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (~3-5 minutes)
3. Your backend will be at: `https://cryptovault-backend.onrender.com`

### 2.6 Verify Backend

Test your backend:
```bash
# Health check
curl https://cryptovault-backend.onrender.com/health

# API status
curl https://cryptovault-backend.onrender.com/api/

# Crypto data
curl https://cryptovault-backend.onrender.com/api/crypto
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "environment": "production",
  "version": "1.0.0"
}
```

---

## 🌐 Step 3: Deploy Frontend to Vercel

### 3.1 Prepare Frontend

Update environment for production:

```bash
cd frontend

# Create production env file
cat > .env.production << EOF
VITE_API_URL=https://cryptovault-backend.onrender.com
EOF
```

### 3.2 Test Build Locally

```bash
# Build for production
yarn build

# Preview production build
yarn preview
```

Visit `http://localhost:4173` and verify it works.

### 3.3 Deploy to Vercel

#### Option A: Using Vercel CLI (Recommended)

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
cd frontend
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? cryptovault
# - Directory? ./
# - Override settings? No

# Deploy to production
vercel --prod
```

#### Option B: Using Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your Git repository
4. Configure project:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `yarn build`
   - **Output Directory**: `build`
   - **Install Command**: `yarn install`

5. **Environment Variables** → Add:
   ```
   VITE_API_URL=https://cryptovault-backend.onrender.com
   ```

6. Click **"Deploy"**
7. Wait for deployment (~2-3 minutes)

### 3.4 Get Your Vercel URL

Your app will be at:
```
https://cryptovault.vercel.app
```
Or your custom domain if configured.

---

## 🔄 Step 4: Update CORS Configuration

Now that you have your Vercel URL, update the backend:

1. Go to Render Dashboard → Your backend service
2. Go to **Environment**
3. Update `CORS_ORIGINS` to:
   ```
   https://cryptovault.vercel.app,https://your-custom-domain.com
   ```
   (Comma-separated, no spaces, no wildcards)
4. Click **"Save Changes"**
5. Service will automatically redeploy

---

## ✅ Step 5: Verify Production Deployment

### 5.1 Test Backend

```bash
# Health check
curl https://cryptovault-backend.onrender.com/health

# Should return:
{
  "status": "healthy",
  "database": "connected",
  "environment": "production"
}
```

### 5.2 Test Frontend

1. Open your Vercel URL: `https://cryptovault.vercel.app`
2. Check browser console for API connection
3. Try signing up with a test account
4. Verify you can:
   - ✅ Sign up
   - ✅ Log in
   - ✅ View markets (crypto data)
   - ✅ Access dashboard
   - ✅ Add portfolio holdings
   - ✅ Create orders

### 5.3 Test Full Flow

```bash
# Sign up
curl -X POST https://cryptovault-backend.onrender.com/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@production.com",
    "password": "SecurePass123!",
    "name": "Test User"
  }'

# Check MongoDB Atlas
# Go to Database → Browse Collections
# Should see: users, portfolios collections
```

---

## 🔒 Step 6: Security Hardening

### 6.1 Update CORS (Critical!)

❌ **Never use** `CORS_ORIGINS="*"` in production

✅ **Always specify** exact domains:
```
CORS_ORIGINS=https://cryptovault.vercel.app,https://www.cryptovault.com
```

### 6.2 Environment Variables Checklist

Backend (Render):
- ✅ `JWT_SECRET` - Auto-generated by Render
- ✅ `MONGO_URL` - Atlas connection string (not committed to git)
- ✅ `CORS_ORIGINS` - Exact Vercel domain
- ✅ `ENVIRONMENT=production`

Frontend (Vercel):
- ✅ `VITE_API_URL` - Render backend URL

### 6.3 MongoDB Security

1. ✅ Strong database password
2. ✅ Limited user privileges
3. ✅ Network access configured
4. ✅ Monitoring enabled

### 6.4 Additional Security

1. Enable HTTPS (automatic on Vercel & Render)
2. Set secure cookie flags (already configured)
3. Rate limiting (configured at 60 req/min)
4. Input validation (Pydantic models)

---

## 📊 Step 7: Monitoring & Maintenance

### 7.1 Set Up Monitoring

**Render Backend:**
1. Dashboard → Metrics
2. Monitor: CPU, Memory, Response time
3. Set up alerts for downtime

**Vercel Frontend:**
1. Analytics → Enable
2. Monitor: Page views, Performance

**MongoDB Atlas:**
1. Alerts → Configure
2. Monitor: Connections, Storage, Operations

### 7.2 Log Monitoring

**Backend Logs (Render):**
```bash
# View in dashboard or CLI
render logs -s cryptovault-backend --tail
```

**Frontend Logs (Vercel):**
- Dashboard → Deployments → View logs

### 7.3 Health Checks

Set up uptime monitoring:
- [UptimeRobot](https://uptimerobot.com/) (Free)
- [Pingdom](https://www.pingdom.com/)
- [Better Uptime](https://betteruptime.com/)

Monitor:
```
https://cryptovault-backend.onrender.com/health
```

---

## 🔄 Step 8: Continuous Deployment

### 8.1 Automatic Deployments

**Render (Backend):**
- Automatically deploys on `git push` to main branch
- Configure in: Settings → Build & Deploy

**Vercel (Frontend):**
- Automatically deploys on `git push` to main branch
- Preview deployments for PRs

### 8.2 Deployment Workflow

```bash
# Make changes
git add .
git commit -m "Add new feature"
git push origin main

# Render automatically deploys backend (~3 min)
# Vercel automatically deploys frontend (~2 min)

# Verify deployments
curl https://cryptovault-backend.onrender.com/health
open https://cryptovault.vercel.app
```

---

## 🐛 Troubleshooting

### Backend Issues

**"Database not connected"**
- Check MongoDB Atlas IP whitelist (0.0.0.0/0)
- Verify connection string in `MONGO_URL`
- Check MongoDB Atlas cluster is running

**"CORS error in browser"**
- Update `CORS_ORIGINS` to exact Vercel URL
- No trailing slashes
- No wildcards in production
- Redeploy backend after change

**"Health check failing"**
- Check Render logs
- Verify `/health` endpoint returns 200
- Check MongoDB connection

### Frontend Issues

**"API calls failing"**
- Check `VITE_API_URL` is correct Render URL
- Verify backend is running
- Check browser network tab for CORS errors

**"Build failing on Vercel"**
- Check build logs
- Verify `yarn build` works locally
- Check Node.js version compatibility

**"Environment variables not working"**
- Ensure variables start with `VITE_`
- Redeploy after adding variables
- Check Vercel dashboard → Settings → Environment Variables

### MongoDB Issues

**"Authentication failed"**
- Check username/password in connection string
- Verify user has correct privileges

**"Network timeout"**
- Check IP whitelist includes 0.0.0.0/0
- Verify cluster is running
- Check MongoDB Atlas status

---

## 📈 Step 9: Scaling Considerations

### When to Upgrade

**Render (Backend):**
- Free tier: Good for development
- Starter ($7/mo): Better for production
  - Faster builds
  - More resources
  - Better uptime

**MongoDB Atlas:**
- M0 (Free): 512MB storage
- M10 ($9/mo): 10GB, better performance
- Upgrade when: >100 active users

**Vercel (Frontend):**
- Hobby (Free): Good for most use cases
- Pro ($20/mo): Custom domains, analytics

### Performance Optimization

1. Enable CDN (Vercel automatic)
2. Implement caching (Redis)
3. Optimize images
4. Add database indexes
5. Monitor slow queries

---

## 🎯 Deployment Checklist

### Pre-Deployment
- [ ] All code committed to Git
- [ ] MongoDB Atlas cluster created
- [ ] Environment variables prepared
- [ ] Local build tested
- [ ] CORS origins documented

### Backend (Render)
- [ ] Service created
- [ ] Environment variables set
- [ ] Health check configured
- [ ] Deployment successful
- [ ] `/health` endpoint returns 200
- [ ] API endpoints accessible

### Frontend (Vercel)
- [ ] Project created
- [ ] Environment variables set
- [ ] Build successful
- [ ] Site accessible
- [ ] API calls working

### Post-Deployment
- [ ] CORS updated with Vercel URL
- [ ] Full authentication flow tested
- [ ] Database operations verified
- [ ] Monitoring configured
- [ ] Backup strategy in place

---

## 📚 Additional Resources

### Documentation
- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [MongoDB Atlas Docs](https://docs.atlas.mongodb.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vite Production Build](https://vitejs.dev/guide/build.html)

### Support
- Render: https://community.render.com/
- Vercel: https://vercel.com/support
- MongoDB: https://www.mongodb.com/community/forums/

---

## 🎉 Success!

If all checks pass, your CryptoVault is now live in production!

**URLs:**
- Frontend: `https://cryptovault.vercel.app`
- Backend: `https://cryptovault-backend.onrender.com`
- Health: `https://cryptovault-backend.onrender.com/health`

**Next Steps:**
1. Set up custom domain (optional)
2. Configure monitoring alerts
3. Plan backup strategy
4. Document API for team
5. Add analytics

---

**Need Help?**
- Check troubleshooting section
- Review service logs
- Test locally first
- Contact platform support

**Last Updated**: January 10, 2026  
**Version**: 1.0.0 Production
