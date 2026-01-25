#!/bin/bash
# ============================================
# FLY.IO POST-DEPLOYMENT VERIFICATION
# CryptoVault Backend
# ============================================
# Run this after deployment to verify all systems are working
# Usage: ./verify-fly-deployment.sh [APP_URL]
# ============================================

set -e

# Default to fly.dev URL
APP_URL=${1:-"https://cryptovault-api.fly.dev"}

echo "======================================"
echo "🔍 CryptoVault Fly.io Deployment Verification"
echo "======================================"
echo "Target: $APP_URL"
echo "Time: $(date)"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

check_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "  Checking $name... "
    
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 10 || echo "000")
    
    if [ "$HTTP_STATUS" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_STATUS)"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $HTTP_STATUS, expected $expected_status)"
        ((FAIL++))
        return 1
    fi
}

check_json_field() {
    local name=$1
    local url=$2
    local field=$3
    local expected=$4
    
    echo -n "  Checking $name... "
    
    RESPONSE=$(curl -s "$url" --max-time 10 || echo "{}")
    VALUE=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$field', 'NOT_FOUND'))" 2>/dev/null || echo "ERROR")
    
    if [ "$VALUE" = "$expected" ]; then
        echo -e "${GREEN}✓ PASS${NC} ($field=$VALUE)"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} ($field=$VALUE, expected $expected)"
        ((FAIL++))
        return 1
    fi
}

# ============================================
# 1. BASIC HEALTH CHECKS
# ============================================
echo "📋 1. Basic Health Checks"
echo "-------------------------------------------"

check_endpoint "Root endpoint" "$APP_URL/"
check_endpoint "Health endpoint" "$APP_URL/health"
check_endpoint "Ping endpoint" "$APP_URL/ping"
check_endpoint "API Health" "$APP_URL/api/health"
check_endpoint "API Ping" "$APP_URL/api/ping"

echo ""

# ============================================
# 2. API ENDPOINTS
# ============================================
echo "📋 2. API Endpoints"
echo "-------------------------------------------"

check_endpoint "Crypto list" "$APP_URL/api/crypto"
check_endpoint "API Docs" "$APP_URL/api/docs"
check_endpoint "OpenAPI spec" "$APP_URL/api/openapi.json"
check_endpoint "CSRF token" "$APP_URL/api/csrf"

echo ""

# ============================================
# 3. MONITORING ENDPOINTS
# ============================================
echo "📋 3. Monitoring & Observability"
echo "-------------------------------------------"

check_endpoint "Metrics (JSON)" "$APP_URL/api/monitoring/metrics/json"
check_endpoint "Liveness probe" "$APP_URL/api/monitoring/health/live"
check_endpoint "Readiness probe" "$APP_URL/api/monitoring/health/ready"
check_endpoint "Deep investigation" "$APP_URL/api/deep-investigation"

echo ""

# ============================================
# 4. FLY.IO SPECIFIC
# ============================================
echo "📋 4. Fly.io Deployment Status"
echo "-------------------------------------------"

check_endpoint "Fly status" "$APP_URL/api/fly/status"
check_endpoint "Fly region" "$APP_URL/api/fly/region"
check_endpoint "Fly instances" "$APP_URL/api/fly/instances"
check_endpoint "Fly health" "$APP_URL/api/fly/health/fly"

echo ""

# ============================================
# 5. RESPONSE VALIDATION
# ============================================
echo "📋 5. Response Validation"
echo "-------------------------------------------"

check_json_field "Health status" "$APP_URL/health" "status" "healthy"
check_json_field "Ping response" "$APP_URL/ping" "message" "pong"
check_json_field "Environment" "$APP_URL/api/health" "environment" "production"

echo ""

# ============================================
# 6. CORS HEADERS
# ============================================
echo "📋 6. CORS Headers"
echo "-------------------------------------------"

echo -n "  Checking CORS headers... "
CORS_HEADER=$(curl -s -I -H "Origin: https://www.cryptovault.financial" "$APP_URL/api/health" 2>/dev/null | grep -i "access-control-allow-origin" || echo "")

if [[ "$CORS_HEADER" == *"cryptovault.financial"* ]]; then
    echo -e "${GREEN}✓ PASS${NC} (CORS configured)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (CORS header not detected - may be OK for same-origin)"
fi

echo ""

# ============================================
# 7. SECURITY HEADERS
# ============================================
echo "📋 7. Security Headers"
echo "-------------------------------------------"

echo -n "  Checking security headers... "
SECURITY_HEADERS=$(curl -s -I "$APP_URL/health" 2>/dev/null)

HSTS=$(echo "$SECURITY_HEADERS" | grep -i "strict-transport-security" || echo "")
XFO=$(echo "$SECURITY_HEADERS" | grep -i "x-frame-options" || echo "")
XCTO=$(echo "$SECURITY_HEADERS" | grep -i "x-content-type-options" || echo "")

if [[ -n "$HSTS" && -n "$XFO" && -n "$XCTO" ]]; then
    echo -e "${GREEN}✓ PASS${NC} (HSTS, X-Frame-Options, X-Content-Type-Options)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (Some security headers missing)"
fi

echo ""

# ============================================
# 8. LATENCY CHECK
# ============================================
echo "📋 8. Latency Check"
echo "-------------------------------------------"

echo -n "  Measuring response time... "
LATENCY=$(curl -s -o /dev/null -w "%{time_total}" "$APP_URL/ping" --max-time 10 || echo "999")
LATENCY_MS=$(echo "$LATENCY * 1000" | bc 2>/dev/null || echo "N/A")

if (( $(echo "$LATENCY < 2" | bc -l 2>/dev/null || echo 0) )); then
    echo -e "${GREEN}✓ PASS${NC} (${LATENCY_MS}ms)"
    ((PASS++))
else
    echo -e "${YELLOW}⚠ WARN${NC} (${LATENCY_MS}ms - consider checking cold start)"
fi

echo ""

# ============================================
# SUMMARY
# ============================================
echo "======================================"
echo "📊 VERIFICATION SUMMARY"
echo "======================================"
echo ""
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo ""

TOTAL=$((PASS + FAIL))
if [ $TOTAL -gt 0 ]; then
    PERCENTAGE=$((PASS * 100 / TOTAL))
    echo "  Success Rate: ${PERCENTAGE}%"
fi

echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo ""
    echo "🎉 Deployment verified successfully!"
    echo ""
    echo "📍 Your API is live at: $APP_URL"
    echo "📖 API Docs: $APP_URL/api/docs"
    echo "📊 Metrics: $APP_URL/api/monitoring/metrics/json"
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED${NC}"
    echo ""
    echo "Please review the failed checks above."
    echo ""
    echo "Troubleshooting commands:"
    echo "  flyctl logs -a cryptovault-api"
    echo "  flyctl status -a cryptovault-api"
    echo "  flyctl ssh console -a cryptovault-api"
    exit 1
fi
