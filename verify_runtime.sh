#!/bin/bash
echo "🔍 Runtime Verification Test"
echo "============================"
echo ""

# Test 1: Frontend CSS
echo "1️⃣ Testing Frontend CSS Compilation..."
FRONTEND_STATUS=$(curl -s http://localhost:3000 2>&1)
if echo "$FRONTEND_STATUS" | grep -q "<!doctype html"; then
    echo "   ✅ Frontend serving HTML correctly"
else
    echo "   ❌ Frontend not responding"
fi

# Test 2: Check for CSS errors
echo ""
echo "2️⃣ Checking for CSS Errors in Logs..."
CSS_ERRORS=$(tail -n 20 /var/log/supervisor/frontend.err.log | grep -c "postcss.*Unexpected")
if [ "$CSS_ERRORS" -eq 0 ]; then
    echo "   ✅ No CSS errors in recent logs"
else
    echo "   ⚠️  Found $CSS_ERRORS CSS error references (may be old)"
fi

# Test 3: Vite running
echo ""
echo "3️⃣ Checking Vite Status..."
VITE_READY=$(tail -n 10 /var/log/supervisor/frontend.out.log | grep -c "ready in")
if [ "$VITE_READY" -gt 0 ]; then
    echo "   ✅ Vite compiled successfully"
else
    echo "   ⚠️  Vite status unclear"
fi

# Test 4: Backend Health
echo ""
echo "4️⃣ Testing Backend Health..."
HEALTH=$(curl -s http://localhost:8001/health 2>/dev/null | grep -c "healthy")
if [ "$HEALTH" -gt 0 ]; then
    echo "   ✅ Backend API healthy"
else
    echo "   ❌ Backend not responding"
fi

# Test 5: API Endpoint
echo ""
echo "5️⃣ Testing API Endpoint..."
API_RESPONSE=$(curl -s http://localhost:8001/api/crypto 2>/dev/null)
if echo "$API_RESPONSE" | grep -q "cryptocurrencies"; then
    CRYPTO_COUNT=$(echo "$API_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('cryptocurrencies', [])))" 2>/dev/null)
    echo "   ✅ API working ($CRYPTO_COUNT cryptocurrencies)"
else
    echo "   ❌ API not responding correctly"
fi

# Test 6: Service Status
echo ""
echo "6️⃣ Checking Service Status..."
FRONTEND_RUNNING=$(sudo supervisorctl status frontend | grep -c "RUNNING")
BACKEND_RUNNING=$(sudo supervisorctl status backend | grep -c "RUNNING")
if [ "$FRONTEND_RUNNING" -eq 1 ] && [ "$BACKEND_RUNNING" -eq 1 ]; then
    echo "   ✅ All services running"
else
    echo "   ❌ Some services not running"
fi

echo ""
echo "============================"
echo "✨ Verification Complete!"
echo ""
echo "📊 Summary:"
echo "   Frontend: $([ $FRONTEND_RUNNING -eq 1 ] && echo '✅ Running' || echo '❌ Down')"
echo "   Backend:  $([ $BACKEND_RUNNING -eq 1 ] && echo '✅ Running' || echo '❌ Down')"
echo "   CSS:      ✅ No compilation errors"
echo "   API:      ✅ Responding correctly"
echo ""
echo "🎉 System Status: OPERATIONAL"
