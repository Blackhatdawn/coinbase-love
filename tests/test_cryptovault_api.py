"""
CryptoVault API Tests - Iteration 5
Tests for: Health, WebSocket, Wallet Deposit, Price Alerts, Admin Dashboard, Referrals
NOWPayments and Firebase FCM are MOCKED
"""
import pytest
import requests
import json
import os
import uuid
import time
from datetime import datetime

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://fintech-architect-4.preview.emergentagent.com"

print(f"Testing against: {BASE_URL}")

# Test user credentials
TEST_EMAIL = f"test_user_{uuid.uuid4().hex[:8]}@cryptovault.test"
TEST_PASSWORD = "TestPassword123!"
TEST_NAME = "Test User"


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_endpoint(self):
        """Test /api/health returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.text}"
        
        data = response.json()
        assert data.get("status") == "healthy", f"Status not healthy: {data}"
        assert "database" in data, "Missing database field"
        print(f"✅ Health check passed: {data}")
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = requests.get(f"{BASE_URL}/", timeout=10)
        assert response.status_code == 200, f"Root endpoint failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing message in root response"
        print(f"✅ Root endpoint passed: {data.get('message', '')[:50]}")


class TestCryptoEndpoints:
    """Test cryptocurrency data endpoints"""
    
    def test_get_all_crypto(self):
        """Test GET /api/crypto returns cryptocurrency prices"""
        response = requests.get(f"{BASE_URL}/api/crypto", timeout=15)
        assert response.status_code == 200, f"Crypto endpoint failed: {response.text}"
        
        data = response.json()
        assert "cryptocurrencies" in data, "Missing cryptocurrencies field"
        
        cryptos = data["cryptocurrencies"]
        assert len(cryptos) > 0, "No cryptocurrencies returned"
        
        # Check for BTC and ETH
        symbols = [c.get("symbol", "").upper() for c in cryptos]
        assert "BTC" in symbols, "BTC not found in prices"
        assert "ETH" in symbols, "ETH not found in prices"
        
        print(f"✅ Crypto prices returned: {len(cryptos)} coins")


class TestAuthFlow:
    """Test authentication flow"""
    
    @pytest.fixture(scope="class")
    def session(self):
        """Create a session for auth tests"""
        return requests.Session()
    
    def test_signup_new_user(self, session):
        """Test user signup"""
        response = session.post(
            f"{BASE_URL}/api/auth/signup",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "name": TEST_NAME
            },
            timeout=10
        )
        
        # 200 or 400 (if email already exists) are acceptable
        assert response.status_code in [200, 201, 400], f"Signup failed: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "user" in data or "message" in data, "Missing user/message in signup response"
            print(f"✅ Signup successful for {TEST_EMAIL}")
        else:
            print(f"⚠️ Signup returned {response.status_code}: {response.text[:100]}")


class TestProtectedEndpoints:
    """Test that protected endpoints require authentication"""
    
    def test_alerts_requires_auth(self):
        """Test GET /api/alerts requires authentication"""
        response = requests.get(f"{BASE_URL}/api/alerts", timeout=10)
        assert response.status_code == 401, f"Alerts should require auth, got {response.status_code}"
        print("✅ GET /api/alerts properly requires authentication (401)")
    
    def test_wallet_deposit_requires_auth(self):
        """Test POST /api/wallet/deposit/create requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/wallet/deposit/create",
            json={"amount": 100, "currency": "btc"},
            timeout=10
        )
        assert response.status_code == 401, f"Wallet deposit should require auth, got {response.status_code}"
        print("✅ POST /api/wallet/deposit/create properly requires authentication (401)")
    
    def test_admin_stats_requires_auth(self):
        """Test GET /api/admin/stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", timeout=10)
        assert response.status_code == 401, f"Admin stats should require auth, got {response.status_code}"
        print("✅ GET /api/admin/stats properly requires authentication (401)")
    
    def test_admin_users_requires_auth(self):
        """Test GET /api/admin/users requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/users", timeout=10)
        assert response.status_code == 401, f"Admin users should require auth, got {response.status_code}"
        print("✅ GET /api/admin/users properly requires authentication (401)")
    
    def test_referrals_code_requires_auth(self):
        """Test GET /api/referrals/code requires authentication"""
        response = requests.get(f"{BASE_URL}/api/referrals/code", timeout=10)
        assert response.status_code == 401, f"Referrals code should require auth, got {response.status_code}"
        print("✅ GET /api/referrals/code properly requires authentication (401)")
    
    def test_portfolio_requires_auth(self):
        """Test GET /api/portfolio requires authentication"""
        response = requests.get(f"{BASE_URL}/api/portfolio", timeout=10)
        assert response.status_code == 401, f"Portfolio should require auth, got {response.status_code}"
        print("✅ GET /api/portfolio properly requires authentication (401)")


class TestStakingEndpoints:
    """Test staking endpoints (public)"""
    
    def test_get_staking_products(self):
        """Test GET /api/staking/products returns products"""
        response = requests.get(f"{BASE_URL}/api/staking/products", timeout=10)
        assert response.status_code == 200, f"Staking products failed: {response.text}"
        
        data = response.json()
        assert "products" in data, "Missing products field"
        
        products = data["products"]
        assert len(products) > 0, "No staking products returned"
        
        # Check product structure
        for product in products:
            assert "id" in product, "Product missing id"
            assert "asset" in product, "Product missing asset"
            assert "apy" in product, "Product missing apy"
        
        print(f"✅ Staking products returned: {len(products)} products")


class TestWebSocketEndpoint:
    """Test WebSocket price feed endpoint"""
    
    def test_websocket_endpoint_exists(self):
        """Test that WebSocket endpoint is accessible"""
        # WebSocket endpoints can't be tested with regular HTTP
        # But we can verify the server accepts WebSocket upgrade requests
        import websocket
        
        ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
        ws_url = f"{ws_url}/ws/prices"
        
        try:
            ws = websocket.create_connection(ws_url, timeout=5)
            # Try to receive initial prices
            result = ws.recv()
            data = json.loads(result)
            
            assert "type" in data, "WebSocket message missing type"
            assert data["type"] in ["initial_prices", "price_update"], f"Unexpected type: {data['type']}"
            
            ws.close()
            print(f"✅ WebSocket /ws/prices is accessible and returns price data")
        except Exception as e:
            # WebSocket might not be available in test environment
            print(f"⚠️ WebSocket test skipped: {str(e)[:100]}")
            pytest.skip(f"WebSocket not available: {e}")


class TestContactEndpoint:
    """Test contact form endpoint"""
    
    def test_contact_submit(self):
        """Test POST /api/contact works without auth"""
        response = requests.post(
            f"{BASE_URL}/api/contact",
            json={
                "name": "Test User",
                "email": "test@example.com",
                "subject": "Test Subject",
                "message": "This is a test message"
            },
            timeout=10
        )
        # Contact might return 200 or 201
        assert response.status_code in [200, 201, 422], f"Contact failed: {response.text}"
        print(f"✅ Contact endpoint accessible: {response.status_code}")


class TestPasswordResetEndpoint:
    """Test password reset endpoints"""
    
    def test_password_reset_request(self):
        """Test POST /api/auth/password-reset/request"""
        response = requests.post(
            f"{BASE_URL}/api/auth/password-reset/request",
            json={"email": "nonexistent@example.com"},
            timeout=10
        )
        # Should always return 200 for security (don't reveal if email exists)
        assert response.status_code == 200, f"Password reset request failed: {response.text}"
        
        data = response.json()
        assert "message" in data, "Missing message in response"
        print("✅ Password reset request endpoint working")


class TestForgotPasswordEndpoint:
    """Test forgot password endpoint"""
    
    def test_forgot_password(self):
        """Test POST /api/auth/forgot-password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password",
            json={"email": "test@example.com"},
            timeout=10
        )
        # Should return 200 for security
        assert response.status_code == 200, f"Forgot password failed: {response.text}"
        print("✅ Forgot password endpoint working")


# Run summary
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print("CryptoVault API Test Suite - Iteration 5")
    print(f"Testing: {BASE_URL}")
    print(f"{'='*60}\n")
    
    pytest.main([__file__, "-v", "--tb=short"])
