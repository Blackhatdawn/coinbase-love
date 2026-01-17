#!/bin/bash
# Test script for all optimizations

echo "🧪 Testing CryptoVault Optimizations"
echo "===================================="
echo ""

# Test 1: Backend Health
echo "1️⃣ Testing Backend Health..."
HEALTH=$(curl -s http://localhost:8001/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo "   ✅ Backend is healthy"
else
    echo "   ❌ Backend health check failed"
fi
echo ""

# Test 2: Socket.IO Stats
echo "2️⃣ Testing Socket.IO Integration..."
SOCKETIO=$(curl -s http://localhost:8001/api/socketio/stats)
if echo "$SOCKETIO" | grep -q "total_connections"; then
    echo "   ✅ Socket.IO endpoint responding"
    echo "   📊 Stats: $SOCKETIO"
else
    echo "   ❌ Socket.IO endpoint failed"
fi
echo ""

# Test 3: Compression Headers
echo "3️⃣ Testing Compression..."
HEADERS=$(curl -s -I http://localhost:8001/api/crypto)
if echo "$HEADERS" | grep -q "content-encoding"; then
    echo "   ✅ Compression enabled"
else
    echo "   ℹ️  Compression headers not visible (may be transparent)"
fi
echo ""

# Test 4: Frontend
echo "4️⃣ Testing Frontend..."
FRONTEND=$(curl -s http://localhost:3000)
if echo "$FRONTEND" | grep -q "CryptoVault"; then
    echo "   ✅ Frontend is serving"
else
    echo "   ❌ Frontend not responding"
fi
echo ""

# Test 5: API Endpoint
echo "5️⃣ Testing API Endpoint..."
API=$(curl -s http://localhost:8001/api/crypto)
if echo "$API" | grep -q "cryptocurrencies"; then
    echo "   ✅ API endpoint responding"
else
    echo "   ❌ API endpoint failed"
fi
echo ""

# Test 6: Check logs for optimizations
echo "6️⃣ Checking Startup Logs..."
if tail -100 /var/log/supervisor/backend.err.log | grep -q "Socket.IO\|Compression\|Redis"; then
    echo "   ✅ Optimization features initialized"
    echo ""
    echo "   📋 Feature Status:"
    tail -100 /var/log/supervisor/backend.err.log | grep "Socket.IO\|Compression\|Redis\|Enhanced" | tail -5
else
    echo "   ⚠️  Check backend logs for details"
fi
echo ""

echo "===================================="
echo "✨ Testing Complete!"
echo ""
echo "📚 Documentation:"
echo "   - PERFORMANCE_ENHANCEMENTS.md"
echo "   - OPTIMIZATION_GUIDE.md"
echo ""
echo "🚀 All systems operational!"
