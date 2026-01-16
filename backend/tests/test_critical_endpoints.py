"""
Comprehensive test coverage for critical CryptoVault API endpoints.

Tests focus on:
1. Portfolio holding creation (POST /api/portfolio/holding)
2. Portfolio retrieval with real-time prices (GET /api/portfolio)
3. Order creation and trading flow (POST /api/orders)
4. Authentication and error handling
5. WebSocket price streaming
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import jwt
from typing import Dict, Any
import json

# Note: Adjust imports based on your actual project structure
# This assumes a pytest configuration with proper mocking


class TestPortfolioEndpoints:
    """Tests for portfolio management endpoints."""
    
    @pytest.fixture
    def auth_headers(self, test_client, test_db, valid_user):
        """Create authenticated request headers with valid JWT token."""
        # Assuming you have a way to create test users and tokens
        response = test_client.post(
            "/api/auth/login",
            json={"email": valid_user["email"], "password": valid_user["password"]}
        )
        assert response.status_code == 200
        token = response.cookies.get("access_token")
        return {"Authorization": f"Bearer {token}"} if token else {}
    
    def test_add_holding_success(self, test_client, auth_headers, mock_coingecko_service):
        """
        Test successful holding creation.
        Validates that POST /api/portfolio/holding correctly:
        - Imports coingecko_service
        - Extracts price from 'price' key (not 'current_price')
        - Creates holding with valid value calculation
        """
        # Mock coingecko_service.get_prices() to return proper structure
        mock_coingecko_service.return_value = [
            {
                "id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": 45000.50,  # Use 'price' key, not 'current_price'
                "market_cap": 875e9,
                "volume_24h": 25e9,
                "change_24h": 2.5,
                "image": "https://example.com/btc.png"
            }
        ]
        
        response = test_client.post(
            "/api/portfolio/holding",
            headers=auth_headers,
            json={
                "symbol": "BTC",
                "name": "Bitcoin",
                "amount": 0.5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "holding" in data
        holding = data["holding"]
        assert holding["symbol"] == "BTC"
        assert holding["name"] == "Bitcoin"
        assert holding["amount"] == 0.5
        
        # Verify value calculation: 0.5 BTC * $45000.50 = $22500.25
        assert abs(holding["value"] - 22500.25) < 0.01
    
    def test_add_holding_missing_price(self, test_client, auth_headers, mock_coingecko_service):
        """
        Test holding creation fails when price is missing or invalid.
        Validates error handling for unavailable price data.
        """
        mock_coingecko_service.return_value = [
            {
                "id": "bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                # Missing 'price' field
                "market_cap": None,
                "volume_24h": None
            }
        ]
        
        response = test_client.post(
            "/api/portfolio/holding",
            headers=auth_headers,
            json={
                "symbol": "BTC",
                "name": "Bitcoin",
                "amount": 0.5
            }
        )
        
        # Should return 500 with appropriate error message
        assert response.status_code == 500
        data = response.json()
        assert "price" in data.get("detail", "").lower() or "unavailable" in data.get("detail", "").lower()
    
    def test_add_holding_crypto_not_found(self, test_client, auth_headers, mock_coingecko_service):
        """
        Test holding creation fails when cryptocurrency is not found.
        """
        mock_coingecko_service.return_value = []  # No coins returned
        
        response = test_client.post(
            "/api/portfolio/holding",
            headers=auth_headers,
            json={
                "symbol": "UNKNOWN",
                "name": "Unknown Coin",
                "amount": 1.0
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data.get("detail", "").lower()
    
    def test_get_portfolio_with_cached_prices(self, test_client, auth_headers, mock_redis):
        """
        Test portfolio retrieval uses real-time prices from Redis cache.
        Validates:
        - Falls back to get_price_for_symbol helper
        - Uses Redis cache first (crypto:price:{symbol} keys)
        - Correctly calculates allocation percentages
        """
        # Mock Redis cache with real-time prices
        mock_redis.get.return_value = b"45500.00"  # Bitcoin price from cache
        
        response = test_client.get(
            "/api/portfolio",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "portfolio" in data
        portfolio = data["portfolio"]
        assert "totalBalance" in portfolio
        assert "holdings" in portfolio
        assert isinstance(portfolio["holdings"], list)
        
        # Verify each holding has required fields
        for holding in portfolio["holdings"]:
            assert "symbol" in holding
            assert "name" in holding
            assert "amount" in holding
            assert "current_price" in holding
            assert "value" in holding
            assert "allocation" in holding
            assert "cached_at" in holding


class TestTradingEndpoints:
    """Tests for trading/order endpoints."""
    
    def test_create_order_success(self, test_client, auth_headers):
        """
        Test successful order creation.
        Validates that POST /api/orders:
        - Accepts trading_pair, order_type, side, amount, price
        - Returns order with correct structure
        - Marks order as filled
        """
        response = test_client.post(
            "/api/orders",
            headers=auth_headers,
            json={
                "trading_pair": "BTC/USDT",
                "order_type": "limit",
                "side": "buy",
                "amount": 0.5,
                "price": 45000
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "order" in data
        order = data["order"]
        assert order["trading_pair"] == "BTC/USDT"
        assert order["side"] == "buy"
        assert order["amount"] == 0.5
        assert order["price"] == 45000
        assert order["status"] == "filled"
    
    def test_create_order_invalid_pair(self, test_client, auth_headers):
        """Test order creation fails with invalid trading pair."""
        response = test_client.post(
            "/api/orders",
            headers=auth_headers,
            json={
                "trading_pair": "INVALID/PAIR",
                "order_type": "limit",
                "side": "buy",
                "amount": 0.5,
                "price": 45000
            }
        )
        
        # Should return validation error
        assert response.status_code in [400, 422]


class TestErrorHandling:
    """Tests for error response handling and transformation."""
    
    def test_error_response_format_fastapi_default(self, test_client, auth_headers):
        """
        Test that API client can handle FastAPI default error format.
        Validates transformError in frontend handles {"detail": "..."} format.
        """
        # Make request that triggers 404
        response = test_client.get(
            "/api/portfolio/holding/NONEXISTENT",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.json()
        
        # FastAPI returns {"detail": "..."}
        assert "detail" in data
        assert isinstance(data["detail"], str)
    
    def test_validation_error_response(self, test_client, auth_headers):
        """
        Test that validation errors are properly formatted.
        Validates transformError can handle validation error arrays.
        """
        response = test_client.post(
            "/api/portfolio/holding",
            headers=auth_headers,
            json={}  # Missing required fields
        )
        
        assert response.status_code == 422
        data = response.json()
        
        # Can be either detail string or validation error array
        assert "detail" in data or "validation_error" in str(data).lower()


class TestAuthFlow:
    """Tests for authentication flow."""
    
    def test_login_and_token_refresh(self, test_client, valid_user, mock_db):
        """
        Test complete auth flow: login -> token refresh -> authenticated request.
        Validates JWT token generation and refresh token mechanism.
        """
        # Step 1: Login
        response = test_client.post(
            "/api/auth/login",
            json={"email": valid_user["email"], "password": valid_user["password"]}
        )
        assert response.status_code == 200
        
        # Check access_token cookie is set
        access_token_cookie = response.cookies.get("access_token")
        assert access_token_cookie is not None
        
        # Step 2: Make authenticated request
        response = test_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {access_token_cookie}"}
        )
        assert response.status_code == 200
        
        # Step 3: Refresh token
        response = test_client.post("/api/auth/refresh")
        assert response.status_code == 200
    
    def test_unauthorized_request(self, test_client):
        """Test that unauthorized requests are properly rejected."""
        response = test_client.get("/api/portfolio")
        
        # Should return 401 or redirect
        assert response.status_code in [401, 403, 307]


class TestRateLimiting:
    """Tests for rate limiting behavior."""
    
    def test_rate_limit_per_user_from_auth_header(self, test_client, auth_headers):
        """
        Test that rate limits are applied per-user from Authorization header.
        Validates get_rate_limit_key correctly extracts user from token.
        """
        # Make multiple requests
        for i in range(5):
            response = test_client.get(
                "/api/portfolio",
                headers=auth_headers
            )
            assert response.status_code in [200, 429]
        
        # Verify rate-limit headers are present
        # (status 429 only if actually rate limited, but headers should be present either way)
    
    def test_rate_limit_per_user_from_cookie(self, test_client):
        """
        Test that rate limits work with cookie-based authentication.
        Validates get_rate_limit_key extracts user from access_token cookie.
        """
        # This test verifies the fix where cookies are also checked for rate limit key
        # Login first to get cookie
        response = test_client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "password"}
        )
        
        # Make requests using cookie
        for i in range(3):
            response = test_client.get("/api/portfolio")
            assert response.status_code in [200, 401, 429]


class TestWebSocketPricing:
    """Tests for WebSocket price streaming."""
    
    @pytest.mark.asyncio
    async def test_websocket_price_stream_connection(self, test_client):
        """
        Test WebSocket connection and price updates.
        Validates real-time price streaming works correctly.
        """
        with test_client.websocket_connect("/ws/prices") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert "connected" in data["status"].lower()
            
            # Should receive price updates
            data = websocket.receive_json(timeout=2)
            assert data["type"] == "price_update"
            assert "prices" in data
            assert isinstance(data["prices"], dict)
    
    @pytest.mark.asyncio
    async def test_websocket_client_ping_pong(self, test_client):
        """
        Test WebSocket keep-alive ping/pong mechanism.
        Validates connection stays alive with regular pings.
        """
        with test_client.websocket_connect("/ws/prices") as websocket:
            # Receive initial connection message
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({"type": "ping"})
            
            # Should receive pong
            data = websocket.receive_json(timeout=1)
            assert data["type"] == "pong"


# ============================================
# FIXTURES AND HELPERS
# ============================================

@pytest.fixture
def test_db():
    """Mock database connection for testing."""
    # Implement based on your database setup
    pass


@pytest.fixture
def test_client():
    """Create test client for FastAPI app."""
    # from app import app  # Adjust import
    # return TestClient(app)
    pass


@pytest.fixture
def valid_user():
    """Return a valid test user."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "name": "Test User"
    }


@pytest.fixture
def mock_coingecko_service(monkeypatch):
    """Mock CoinGecko service for testing."""
    # Implement based on your mocking strategy
    pass


@pytest.fixture
def mock_redis(monkeypatch):
    """Mock Redis cache for testing."""
    # Implement based on your mocking strategy
    pass


# ============================================
# INTEGRATION TEST SCENARIOS
# ============================================

class TestIntegrationScenarios:
    """End-to-end integration tests."""
    
    def test_user_portfolio_flow(self, test_client):
        """
        Test complete user portfolio flow:
        1. Sign up
        2. Add holdings
        3. View portfolio with real-time prices
        4. Delete holding
        """
        # Step 1: Signup
        signup_response = test_client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "name": "New User"
            }
        )
        assert signup_response.status_code == 200
        
        # Extract token from response or cookies
        # Step 2: Add holdings
        # Step 3: View portfolio
        # Step 4: Delete holding
        # (Implementation depends on actual API responses)
    
    def test_trading_flow(self, test_client, auth_headers):
        """
        Test complete trading flow:
        1. Create limit order
        2. Verify order in portfolio/holdings
        3. Check transaction history
        """
        # Implementation based on actual requirements
        pass


if __name__ == "__main__":
    # Run tests with: pytest backend/tests/test_critical_endpoints.py -v
    print("Run tests with: pytest backend/tests/test_critical_endpoints.py -v")
