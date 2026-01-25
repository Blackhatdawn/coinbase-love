#!/bin/bash
# ============================================
# FLY.IO DEPLOYMENT SCRIPT
# CryptoVault Backend
# ============================================
# Usage: ./deploy-fly.sh [staging|production]
# ============================================

set -e

ENVIRONMENT=${1:-staging}
APP_NAME="cryptovault-api"

echo "======================================"
echo "🚀 CryptoVault Fly.io Deployment"
echo "Environment: $ENVIRONMENT"
echo "======================================"

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ flyctl not found. Install: curl -L https://fly.io/install.sh | sh"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "❌ Not logged in. Run: flyctl auth login"
    exit 1
fi

# Navigate to backend directory
cd "$(dirname "$0")"

# Step 1: Check if app exists
echo ""
echo "📋 Step 1: Checking Fly.io app..."
if flyctl apps list | grep -q "$APP_NAME"; then
    echo "✅ App '$APP_NAME' exists"
else
    echo "⚠️ App '$APP_NAME' not found. Creating..."
    flyctl apps create "$APP_NAME" --org personal
    echo "✅ App created"
fi

# Step 2: Set secrets (if not already set)
echo ""
echo "🔐 Step 2: Verifying secrets..."
echo "   Run 'flyctl secrets list' to check existing secrets"
echo "   Set missing secrets with: flyctl secrets set KEY=VALUE"
echo ""

# List required secrets
REQUIRED_SECRETS=(
    "MONGO_URL"
    "JWT_SECRET"
    "CSRF_SECRET"
    "SENDGRID_API_KEY"
    "UPSTASH_REDIS_REST_URL"
    "UPSTASH_REDIS_REST_TOKEN"
    "COINCAP_API_KEY"
    "SENTRY_DSN"
)

echo "   Required secrets:"
for secret in "${REQUIRED_SECRETS[@]}"; do
    echo "   - $secret"
done

read -p "   Have you set all secrets? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please set all secrets first"
    echo ""
    echo "Example:"
    echo "  flyctl secrets set MONGO_URL='mongodb+srv://...' JWT_SECRET='...' ..."
    exit 1
fi

# Step 3: Deploy
echo ""
echo "🚢 Step 3: Deploying to Fly.io..."
if [ "$ENVIRONMENT" = "production" ]; then
    echo "   Production deployment - using fly.toml"
    flyctl deploy --config fly.toml --strategy rolling
else
    echo "   Staging deployment - using fly.toml"
    flyctl deploy --config fly.toml --strategy immediate
fi

# Step 4: Check status
echo ""
echo "📊 Step 4: Checking deployment status..."
flyctl status

# Step 5: Health check
echo ""
echo "🏥 Step 5: Running health check..."
sleep 10  # Wait for app to start
HEALTH_URL="https://$APP_NAME.fly.dev/health"
echo "   Checking: $HEALTH_URL"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed!"
    curl -s "$HEALTH_URL" | python3 -m json.tool
else
    echo "⚠️ Health check returned status: $HTTP_STATUS"
    echo "   Check logs: flyctl logs"
fi

# Step 6: Summary
echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "📍 URLs:"
echo "   API:    https://$APP_NAME.fly.dev"
echo "   Health: https://$APP_NAME.fly.dev/health"
echo "   Docs:   https://$APP_NAME.fly.dev/api/docs"
echo ""
echo "📝 Next Steps:"
echo "   1. Verify all endpoints work"
echo "   2. Update Vercel env var: VITE_API_BASE_URL=https://$APP_NAME.fly.dev"
echo "   3. Update Vercel rewrites in vercel.json (already done)"
echo "   4. Redeploy Vercel frontend"
echo "   5. Monitor logs: flyctl logs -f"
echo ""
echo "🔧 Useful Commands:"
echo "   flyctl status         - Check app status"
echo "   flyctl logs -f        - Stream logs"
echo "   flyctl ssh console    - SSH into container"
echo "   flyctl scale count 2  - Scale to 2 instances"
echo "   flyctl restart        - Restart app"
echo ""
