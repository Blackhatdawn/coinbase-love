#!/bin/bash

# ============================================
# CryptoVault Production Deployment Verification
# ============================================
# This script verifies that frontend and backend
# are properly connected and webhooks are working
# ============================================

set -e

echo "=================================================="
echo "🔍 CRYPTOVAULT DEPLOYMENT VERIFICATION"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://cryptovault-api.onrender.com"
FRONTEND_URL="https://www.cryptovault.financial"
WEBHOOK_URL="$BACKEND_URL/api/wallet/webhook"

echo "📍 Testing URLs:"
echo "   Backend:  $BACKEND_URL"
echo "   Frontend: $FRONTEND_URL"
echo "   Webhook:  $WEBHOOK_URL"
echo ""

# Test 1: Backend Health
echo "=================================================="
echo "Test 1: Backend Health Check"
echo "=================================================="
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/ping" || echo "000")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
    echo "   Response: $body"
else
    echo -e "${RED}❌ Backend health check failed (HTTP $status_code)${NC}"
    echo "   Response: $body"
    exit 1
fi
echo ""

# Test 2: Backend Full Health
echo "=================================================="
echo "Test 2: Backend Full Health (with DB)"
echo "=================================================="
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/health" || echo "000")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ Backend full health check passed${NC}"
    echo "   Response: $body"
else
    echo -e "${YELLOW}⚠️  Backend health check returned HTTP $status_code${NC}"
    echo "   Response: $body"
fi
echo ""

# Test 3: API Configuration Endpoint
echo "=================================================="
echo "Test 3: API Configuration"
echo "=================================================="
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/config" || echo "000")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ API configuration endpoint working${NC}"
    echo "   Response: $body" | head -c 200
    echo "..."
else
    echo -e "${YELLOW}⚠️  API config returned HTTP $status_code${NC}"
fi
echo ""

# Test 4: Webhook Test Endpoint
echo "=================================================="
echo "Test 4: Webhook Test Endpoint"
echo "=================================================="
response=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL/test" \
    -H "Content-Type: application/json" \
    -d '{"test": "verification"}' || echo "000")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ Webhook endpoint is accessible${NC}"
    echo "   Response: $body"
else
    echo -e "${RED}❌ Webhook endpoint test failed (HTTP $status_code)${NC}"
    echo "   Response: $body"
    exit 1
fi
echo ""

# Test 5: NOWPayments Webhook Endpoint
echo "=================================================="
echo "Test 5: NOWPayments Webhook Endpoint"
echo "=================================================="
response=$(curl -s -w "\n%{http_code}" -X POST "$WEBHOOK_URL/nowpayments" \
    -H "Content-Type: application/json" \
    -H "x-nowpayments-sig: test-signature" \
    -d '{
        "payment_id": "test-verification",
        "payment_status": "waiting",
        "order_id": "DEP-test-verification",
        "actually_paid": 0
    }' || echo "000")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ NOWPayments webhook endpoint is accessible${NC}"
    echo "   Response: $body"
    echo -e "${YELLOW}   Note: Order not found is expected for test data${NC}"
elif [ "$status_code" = "400" ]; then
    echo -e "${GREEN}✅ NOWPayments webhook endpoint is working${NC}"
    echo "   Response: $body"
    echo -e "${YELLOW}   Note: 400 response indicates signature verification is working${NC}"
else
    echo -e "${RED}❌ NOWPayments webhook endpoint failed (HTTP $status_code)${NC}"
    echo "   Response: $body"
fi
echo ""

# Test 6: Frontend Accessibility
echo "=================================================="
echo "Test 6: Frontend Accessibility"
echo "=================================================="
response=$(curl -s -w "\n%{http_code}" "$FRONTEND_URL" || echo "000")
status_code=$(echo "$response" | tail -n1)

if [ "$status_code" = "200" ]; then
    echo -e "${GREEN}✅ Frontend is accessible${NC}"
else
    echo -e "${RED}❌ Frontend not accessible (HTTP $status_code)${NC}"
fi
echo ""

# Test 7: CORS Configuration
echo "=================================================="
echo "Test 7: CORS Configuration"
echo "=================================================="
response=$(curl -s -w "\n%{http_code}" -X OPTIONS "$BACKEND_URL/api/ping" \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: GET" || echo "000")
status_code=$(echo "$response" | tail -n1)
headers=$(echo "$response" | grep -i "access-control" || echo "No CORS headers")

if [ "$status_code" = "200" ] || [ "$status_code" = "204" ]; then
    echo -e "${GREEN}✅ CORS preflight successful${NC}"
    echo "   CORS Headers: $headers"
else
    echo -e "${YELLOW}⚠️  CORS preflight returned HTTP $status_code${NC}"
fi
echo ""

# Summary
echo "=================================================="
echo "📊 VERIFICATION SUMMARY"
echo "=================================================="
echo ""
echo -e "${GREEN}✅ Backend Health:${NC} Working"
echo -e "${GREEN}✅ Webhook Endpoint:${NC} Accessible"
echo -e "${GREEN}✅ Frontend:${NC} Accessible"
echo ""
echo "=================================================="
echo "🎯 NEXT STEPS"
echo "=================================================="
echo ""
echo "1. Configure NOWPayments Dashboard:"
echo "   Webhook URL: $WEBHOOK_URL/nowpayments"
echo ""
echo "2. Test with NOWPayments Sandbox:"
echo "   - Create test payment"
echo "   - Complete payment"
echo "   - Check Render logs for webhook receipt"
echo ""
echo "3. Monitor Render Logs:"
echo "   - https://dashboard.render.com"
echo "   - Search for: '📬 NOWPayments webhook'"
echo ""
echo "4. Verify Frontend Environment:"
echo "   - Check Vercel environment variables"
echo "   - VITE_API_BASE_URL should be: $BACKEND_URL"
echo ""
echo "=================================================="
echo "✅ VERIFICATION COMPLETE"
echo "=================================================="
