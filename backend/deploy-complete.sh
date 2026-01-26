#!/bin/bash
# ============================================
# FLY.IO COMPLETE DEPLOYMENT SCRIPT
# CryptoVault Backend
# ============================================

set -e

APP_NAME="coinbase-love"

echo "======================================"
echo "🚀 CryptoVault Fly.io Complete Deployment"
echo "======================================"

# Step 1: Set ALL secrets
echo ""
echo "📌 Step 1: Setting Secrets..."
flyctl secrets set \
  MONGO_URL="mongodb+srv://team_db_user:mWPe3V6ZhoNNEWUk@cryptovaultcluster.vobw2w8.mongodb.net/?appName=CryptoVaultCluster" \
  JWT_SECRET="jmZgXmsOEx10hwWOIE6EvhCft56jew6PVSiSweq-JQI" \
  CSRF_SECRET="9f5cb48d-aa6b-4923-a760-ce8065e4238d" \
  SENDGRID_API_KEY="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" \
  COINCAP_API_KEY="68aa5a01aa84e5704a10f5d6f730dadd9381901161e06d07085fcca8587f41e3" \
  NOWPAYMENTS_API_KEY="ZKDVT1B-4WTMVAZ-KZ7E38G-GPNE8Q7" \
  NOWPAYMENTS_IPN_SECRET="bEEgqlb1q+TF6ygQfNJ+fUJyWvARDJwp" \
  UPSTASH_REDIS_REST_URL="https://emerging-sponge-14455.upstash.io" \
  UPSTASH_REDIS_REST_TOKEN="ATh3AAIncDE5OTMzNjFiM2M4NzA0NmEzOWQwOWE2MjgwODczMDNlM3AxMTQ0NTU" \
  SENTRY_DSN="https://bcb7c3a730f99e6fa758cd3e25edc327@o4510716875505664.ingest.us.sentry.io/4510716879503360" \
  CORS_ORIGINS='["https://www.cryptovault.financial","https://cryptovault.financial","https://coinbase-love.fly.dev"]' \
  --app "$APP_NAME"

echo "✅ Secrets configured"

# Step 2: Deploy
echo ""
echo "📌 Step 2: Deploying to Fly.io..."
flyctl deploy --app "$APP_NAME" --strategy rolling

# Step 3: Verify
echo ""
echo "📌 Step 3: Verifying deployment..."
sleep 10

echo ""
echo "Health check..."
curl -s "https://$APP_NAME.fly.dev/health" | python3 -m json.tool || echo "Health check pending..."

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "URLs:"
echo "  API: https://$APP_NAME.fly.dev"
echo "  Health: https://$APP_NAME.fly.dev/health"
echo "  Docs: https://$APP_NAME.fly.dev/api/docs"
echo ""
echo "Commands:"
echo "  flyctl logs --app $APP_NAME"
echo "  flyctl status --app $APP_NAME"
echo ""
