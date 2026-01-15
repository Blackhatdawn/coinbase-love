# 🚀 CryptoVault Production Deployment Guide

Complete step-by-step guide for deploying CryptoVault to production using Vercel (Frontend) and Render (Backend).

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Backend Deployment (Render)](#backend-deployment-render)
4. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
5. [Domain Configuration](#domain-configuration)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Environment Variables Reference](#environment-variables-reference)
8. [Troubleshooting](#troubleshooting)
9. [Alternative Deployment Options](#alternative-deployment-options)

---

## 🎯 Prerequisites

Before deploying, ensure you have:

### Accounts
- ✅ **GitHub Account** (repository hosting)
- ✅ **Vercel Account** ([vercel.com](https://vercel.com))
- ✅ **Render Account** ([render.com](https://render.com))
- ✅ **MongoDB Atlas Account** ([mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas))
- ✅ **Upstash Account** ([upstash.com](https://upstash.com)) - for Redis
- ✅ **SendGrid Account** ([sendgrid.com](https://sendgrid.com)) - for emails
- ✅ **CoinGecko API Key** ([coingecko.com/en/api](https://www.coingecko.com/en/api))

### Repository Setup
- ✅ Code pushed to GitHub repository
- ✅ `.env` files NOT committed (use `.env.example` as template)
- ✅ All dependencies listed in `requirements.txt` and `package.json`

---

## ✔️ Pre-Deployment Checklist

### 1. Code Preparation

```bash
# Ensure all code is committed
git status
git add .
git commit -m \"feat: prepare for production deployment\"
git push origin main
```

### 2. Database Setup (MongoDB Atlas)

#### Step 1: Create MongoDB Atlas Cluster

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign in / Create account
3. Click **"Build a Database"**
4. Select **"M0 Free"** tier
5. Choose your preferred cloud provider and region
6. Name your cluster (e.g., `cryptovault-cluster`)
7. Click **"Create"**

#### Step 2: Configure Database Access

1. Go to **Database Access** in sidebar
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Username: `cryptovault_user`
5. Password: Generate a strong password (save it!)
6. Database User Privileges: **"Read and write to any database"**
7. Click **"Add User"**

#### Step 3: Configure Network Access

1. Go to **Network Access** in sidebar
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (0.0.0.0/0)
   - ⚠️ For production, use specific IPs from Render
4. Click **"Confirm"**

#### Step 4: Get Connection String

1. Go to **Database** in sidebar
2. Click **"Connect"** on your cluster
3. Choose **"Connect your application"**
4. Copy the connection string:
   ```
   mongodb+srv://cryptovault_user:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
   ```
5. Replace `<password>` with your actual password
6. Save this connection string (needed for deployment)

### 3. Redis Setup (Upstash)

1. Go to [Upstash](https://upstash.com/)
2. Sign in / Create account
3. Click **"Create Database"**
4. Name: `cryptovault-redis`
5. Region: Choose closest to your backend
6. Click **"Create"**
7. Copy **"UPSTASH_REDIS_REST_URL"** and **"UPSTASH_REDIS_REST_TOKEN"**

### 4. SendGrid Setup

1. Go to [SendGrid](https://sendgrid.com/)
2. Sign in / Create account
3. Go to **Settings** → **API Keys**
4. Click **"Create API Key"**
5. Name: `CryptoVault Production`
6. Select **"Full Access"**
7. Click **"Create & View"**
8. **Copy the API key** (you won't see it again!)
9. Go to **Settings** → **Sender Authentication**
10. Verify your sender email address

### 5. CoinGecko API Key

1. Go to [CoinGecko](https://www.coingecko.com/en/api)
2. Sign in / Create account
3. Go to **Dashboard** → **API Keys**
4. Copy your API key
5. Free tier: 10-30 calls/minute (sufficient for testing)

### 6. Generate JWT Secret

```bash
# Generate a secure JWT secret (32+ characters)
openssl rand -hex 32
# Or use Python
python3 -c \"import secrets; print(secrets.token_hex(32))\"
```

Save this secret - you'll need it for deployment!

---

## 🖥️ Backend Deployment (Render)

### Step 1: Create Render Account

1. Go to [Render](https://render.com/)
2. Sign in with **GitHub**
3. Authorize Render to access your repositories

### Step 2: Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. If repository not visible:
   - Click **"Configure account"**
   - Grant access to your repository

### Step 3: Configure Web Service

Fill in the following settings:

#### Basic Settings
- **Name**: `cryptovault-backend` (or your preferred name)
- **Region**: Choose closest to your users
- **Branch**: `main` (or your deployment branch)
- **Root Directory**: `backend`

#### Build Settings
- **Runtime**: `Python 3`
- **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  gunicorn server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
  ```

#### Instance Settings
- **Instance Type**: 
  - **Free** (for testing) - ⚠️ Spins down after inactivity
  - **Starter** ($7/month) - Recommended for production
  - **Standard** ($25/month) - For higher traffic

### Step 4: Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"**

Add ALL of the following variables:

```env
# Database
MONGO_URL=mongodb+srv://cryptovault_user:YOUR_PASSWORD@cluster.mongodb.net/?retryWrites=true&w=majority
DB_NAME=cryptovault_db

# Security
JWT_SECRET=YOUR_GENERATED_SECRET_HERE_32_CHARS_MINIMUM
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS (will update after Vercel deployment)
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# Email
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=SG.YOUR_SENDGRID_API_KEY
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=CryptoVault Financial
APP_URL=https://your-frontend.vercel.app

# CoinGecko
COINGECKO_API_KEY=CG-YOUR_COINGECKO_API_KEY
USE_MOCK_PRICES=false

# Redis
USE_REDIS=true
UPSTASH_REDIS_REST_URL=https://your-redis.upstash.io
UPSTASH_REDIS_REST_TOKEN=YOUR_UPSTASH_TOKEN

# NOWPayments (optional)
NOWPAYMENTS_API_KEY=
NOWPAYMENTS_IPN_SECRET=

# Environment
ENVIRONMENT=production

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
REQUEST_TIMEOUT_SECONDS=30

# Monitoring (optional)
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

### Step 5: Create Service

1. Review all settings
2. Click **"Create Web Service"**
3. Wait for deployment (3-5 minutes)
4. Monitor build logs for any errors

### Step 6: Verify Backend Deployment

Once deployed, your backend will be available at:
```
https://cryptovault-backend.onrender.com
```

Test the health endpoint:
```bash
curl https://cryptovault-backend.onrender.com/health
```

Expected response:
```json
{
  \"status\": \"healthy\",
  \"database\": \"connected\",
  \"environment\": \"production\",
  \"version\": \"1.0.0\"
}
```

### Step 7: Copy Backend URL

Copy your backend URL (e.g., `https://cryptovault-backend.onrender.com`)
You'll need this for the frontend deployment!

---

## 🌐 Frontend Deployment (Vercel)

### Step 1: Create Vercel Account

1. Go to [Vercel](https://vercel.com/)
2. Sign in with **GitHub**
3. Authorize Vercel to access your repositories

### Step 2: Import Project

1. Click **"Add New..."** → **"Project"**
2. Import your GitHub repository
3. If repository not visible:
   - Click **"Adjust GitHub App Permissions"**
   - Grant access to your repository

### Step 3: Configure Project

#### Framework Preset
- Select **"Vite"** (auto-detected)

#### Root Directory
- Click **"Edit"**
- Set to: `frontend`

#### Build Settings
- **Build Command**: `yarn build` (auto-filled)
- **Output Directory**: `build` (auto-filled)
- **Install Command**: `yarn install` (auto-filled)

#### Environment Variables

Click **"Environment Variables"** and add:

```env
VITE_API_BASE_URL=https://cryptovault-backend.onrender.com
```

⚠️ **IMPORTANT**: Replace with YOUR actual backend URL from Render!

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for deployment (2-3 minutes)
3. Monitor build logs

### Step 5: Verify Frontend Deployment

Once deployed, your frontend will be available at:
```
https://your-project.vercel.app
```

Test the deployment:
1. Open the URL in browser
2. You should see the CryptoVault homepage
3. Try navigating to different pages
4. Check browser console for errors

### Step 6: Update Backend CORS

Now update the backend CORS settings on Render:

1. Go back to Render dashboard
2. Select your backend service
3. Go to **"Environment"**
4. Update `CORS_ORIGINS` variable:
   ```
   https://your-project.vercel.app,https://www.yourdomain.com
   ```
5. Update `APP_URL` variable:
   ```
   https://your-project.vercel.app
   ```
6. Click **"Save Changes"**
7. Wait for auto-redeploy

---

## 🌍 Domain Configuration

### Custom Domain for Frontend (Vercel)

1. Go to Vercel dashboard → Your project
2. Click **"Settings"** → **"Domains"**
3. Click **"Add"**
4. Enter your domain (e.g., `cryptovault.com`)
5. Follow DNS configuration instructions:
   - **A Record**: Point to Vercel's IP
   - **CNAME**: `cname.vercel-dns.com`
6. Wait for DNS propagation (5-60 minutes)
7. Vercel automatically provisions SSL certificate

### Custom Domain for Backend (Render)

1. Go to Render dashboard → Your service
2. Click **"Settings"**
3. Scroll to **"Custom Domain"**
4. Click **"Add Custom Domain"**
5. Enter subdomain (e.g., `api.cryptovault.com`)
6. Add DNS records as instructed:
   - **CNAME**: Point to your Render URL
7. Wait for DNS propagation
8. Render automatically provisions SSL certificate

### Update Environment Variables

After adding custom domains:

**Backend (Render)**:
- Update `CORS_ORIGINS`: `https://cryptovault.com`
- Update `APP_URL`: `https://cryptovault.com`

**Frontend (Vercel)**:
- Update `VITE_API_BASE_URL`: `https://api.cryptovault.com`

---

## ✅ Post-Deployment Verification

### 1. Test Authentication Flow

```bash
# Test signup
curl -X POST https://api.cryptovault.com/api/auth/signup \\
  -H \"Content-Type: application/json\" \\
  -d '{\"email\":\"test@example.com\",\"password\":\"Test123!\",\"name\":\"Test User\"}'

# Expected: 200 OK with user data
```

### 2. Test Cryptocurrency Prices

```bash
# Test crypto endpoint
curl https://api.cryptovault.com/api/crypto

# Expected: Array of cryptocurrencies with prices
```

### 3. Test Frontend Pages

Visit and verify:
- ✅ Homepage loads correctly
- ✅ Markets page shows live prices
- ✅ Signup/Login forms work
- ✅ Protected pages redirect to login
- ✅ Trading charts render correctly
- ✅ No console errors

### 4. Test Email Delivery

1. Sign up with a real email
2. Check if verification email arrives
3. Verify email can be clicked
4. Test password reset email

### 5. Monitor Logs

**Render (Backend)**:
- Go to your service → **"Logs"**
- Check for errors
- Verify successful requests

**Vercel (Frontend)**:
- Go to your project → **"Deployments"** → **"Runtime Logs"**
- Check for errors
- Verify page loads

### 6. Performance Testing

Use [GTmetrix](https://gtmetrix.com/) or [WebPageTest](https://www.webpagetest.org/):
- Test page load speed
- Check performance metrics
- Verify mobile responsiveness

---

## 📚 Environment Variables Reference

### Backend (Render)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MONGO_URL` | ✅ Yes | MongoDB connection string | `mongodb+srv://...` |
| `DB_NAME` | ✅ Yes | Database name | `cryptovault_db` |
| `JWT_SECRET` | ✅ Yes | Secret key for JWT (32+ chars) | `your-secret-here` |
| `CORS_ORIGINS` | ✅ Yes | Allowed origins (comma-separated) | `https://app.com` |
| `SENDGRID_API_KEY` | ✅ Yes | SendGrid API key | `SG.xxx` |
| `EMAIL_FROM` | ✅ Yes | Sender email address | `noreply@app.com` |
| `COINGECKO_API_KEY` | ✅ Yes | CoinGecko API key | `CG-xxx` |
| `UPSTASH_REDIS_REST_URL` | ⚠️ Recommended | Redis URL | `https://xxx.upstash.io` |
| `UPSTASH_REDIS_REST_TOKEN` | ⚠️ Recommended | Redis token | `xxx` |
| `APP_URL` | ✅ Yes | Frontend URL | `https://app.com` |
| `ENVIRONMENT` | ✅ Yes | Environment | `production` |
| `NOWPAYMENTS_API_KEY` | ❌ Optional | NOWPayments API key | `xxx` |
| `SENTRY_DSN` | ❌ Optional | Sentry error tracking | `https://xxx` |

### Frontend (Vercel)

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `VITE_API_BASE_URL` | ✅ Yes | Backend API URL | `https://api.app.com` |

---

## 🔧 Troubleshooting

### Backend Issues

#### Issue: Build Fails on Render

**Symptoms**: Build logs show dependency errors

**Solutions**:
```bash
# 1. Verify requirements.txt is complete
cd backend
pip freeze > requirements.txt
git add requirements.txt
git commit -m \"fix: update requirements.txt\"
git push

# 2. Check Python version
# Render uses Python 3.11 by default
# Ensure your code is compatible
```

#### Issue: Database Connection Failed

**Symptoms**: \"Database connection failed\" in logs

**Solutions**:
1. Verify MongoDB Atlas connection string is correct
2. Check password doesn't contain special characters (URL encode if needed)
3. Ensure IP whitelist includes 0.0.0.0/0 or Render IPs
4. Test connection locally first:
   ```bash
   mongosh \"mongodb+srv://user:pass@cluster.mongodb.net/\"
   ```

#### Issue: CORS Errors

**Symptoms**: Browser shows CORS errors

**Solutions**:
1. Verify `CORS_ORIGINS` includes your Vercel URL
2. Ensure no trailing slash in URL
3. Check protocol (https vs http)
4. Restart backend service after updating

#### Issue: 503 Service Unavailable

**Symptoms**: API returns 503

**Solutions**:
1. Free tier on Render spins down after inactivity
2. First request takes 30-60s to wake up
3. Upgrade to paid tier for always-on
4. Or implement warming strategy

### Frontend Issues

#### Issue: Build Fails on Vercel

**Symptoms**: Build logs show errors

**Solutions**:
```bash
# 1. Test build locally
cd frontend
yarn build

# 2. Fix any TypeScript errors
yarn tsc --noEmit

# 3. Check all dependencies are in package.json
yarn install
```

#### Issue: API Calls Fail

**Symptoms**: Network errors in console

**Solutions**:
1. Verify `VITE_API_BASE_URL` is set correctly
2. Check backend is running (test health endpoint)
3. Verify CORS is configured correctly
4. Check browser console for exact error

#### Issue: Environment Variable Not Working

**Symptoms**: Variable shows as undefined

**Solutions**:
1. **MUST** prefix with `VITE_` (e.g., `VITE_API_BASE_URL`)
2. Redeploy after adding variables
3. Clear cache and hard reload browser
4. Check variable is set in Vercel dashboard

#### Issue: White Screen / Blank Page

**Symptoms**: Page doesn't load

**Solutions**:
1. Check browser console for errors
2. Verify build output directory is correct (`build`)
3. Check index.html exists in build directory
4. Test locally: `yarn build && yarn preview`

---

## 🌟 Alternative Deployment Options

### Option 1: AWS (Backend)

**AWS Elastic Beanstalk**:
1. Install AWS CLI and EB CLI
2. Create `Dockerfile` in backend:
   ```dockerfile
   FROM python:3.11
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD [\"uvicorn\", \"server:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]
   ```
3. Deploy:
   ```bash
   eb init -p docker cryptovault-backend
   eb create cryptovault-prod
   eb setenv MONGO_URL=xxx JWT_SECRET=xxx ...
   ```

### Option 2: Railway (Backend)

1. Go to [Railway.app](https://railway.app/)
2. Connect GitHub repository
3. Select `backend` directory
4. Add environment variables
5. Deploy automatically

### Option 3: Netlify (Frontend)

Similar to Vercel:
1. Go to [Netlify](https://www.netlify.com/)
2. Import GitHub repository
3. Set build command: `yarn build`
4. Set publish directory: `frontend/build`
5. Add environment variables
6. Deploy

### Option 4: DigitalOcean App Platform

**Backend + Frontend together**:
1. Go to [DigitalOcean](https://www.digitalocean.com/)
2. Create new App
3. Connect GitHub repository
4. Configure two components:
   - **Backend**: Python, port 8001
   - **Frontend**: Static Site
5. Add environment variables
6. Deploy

---

## 📊 Post-Deployment Monitoring

### Setup Monitoring

1. **Uptime Monitoring**:
   - [UptimeRobot](https://uptimerobot.com/) (Free)
   - Monitor `/health` endpoint every 5 minutes

2. **Error Tracking**:
   - Add Sentry DSN to backend
   - Automatically track errors

3. **Performance**:
   - Vercel Analytics (built-in)
   - Google Analytics
   - PostHog

4. **Logs**:
   - Render: Real-time logs in dashboard
   - Vercel: Runtime logs in dashboard

---

## 🎯 Production Best Practices

### Security
- ✅ Use HTTPS only (enforced by Vercel/Render)
- ✅ Keep secrets in environment variables
- ✅ Enable CORS only for your domain
- ✅ Use strong JWT secret (32+ characters)
- ✅ Enable rate limiting
- ✅ Regular security updates

### Performance
- ✅ Enable caching (Redis)
- ✅ Use CDN for static assets (Vercel automatic)
- ✅ Optimize images
- ✅ Monitor response times
- ✅ Scale backend workers as needed

### Reliability
- ✅ Set up database backups (MongoDB Atlas automatic)
- ✅ Monitor uptime
- ✅ Have rollback plan
- ✅ Test disaster recovery
- ✅ Document runbooks

---

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs First**:
   - Render: Service → Logs
   - Vercel: Project → Deployments → Logs

2. **Common Issues**:
   - Review [Troubleshooting](#troubleshooting) section
   - Search GitHub Issues

3. **Community Support**:
   - GitHub Discussions
   - Discord community

4. **Professional Support**:
   - Email: support@cryptovault.com

---

## ✅ Deployment Checklist

Print this and check off as you complete each step:

### Pre-Deployment
- [ ] Code pushed to GitHub
- [ ] MongoDB Atlas cluster created
- [ ] Upstash Redis database created
- [ ] SendGrid account setup
- [ ] CoinGecko API key obtained
- [ ] JWT secret generated
- [ ] All environment variables documented

### Backend Deployment (Render)
- [ ] Render account created
- [ ] Web service created
- [ ] Build/start commands configured
- [ ] All environment variables added
- [ ] Service deployed successfully
- [ ] Health endpoint tested
- [ ] Backend URL copied

### Frontend Deployment (Vercel)
- [ ] Vercel account created
- [ ] Project imported
- [ ] Root directory set to `frontend`
- [ ] Environment variables added
- [ ] Deployment successful
- [ ] Frontend URL verified
- [ ] Backend CORS updated

### Post-Deployment
- [ ] Custom domains configured (optional)
- [ ] SSL certificates active
- [ ] Authentication flow tested
- [ ] API endpoints tested
- [ ] Email delivery tested
- [ ] Performance tested
- [ ] Monitoring setup
- [ ] Backups verified
- [ ] Documentation updated

---

**Congratulations! 🎉 CryptoVault is now live in production!**

For ongoing maintenance and updates, see the [README.md](README.md).
