import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import httpx
from server import app

@pytest.mark.anyio
async def test_root():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "CryptoVault API is live" in response.json()["message"]

@pytest.mark.anyio
async def test_health():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        await asyncio.sleep(0.1)
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["database"] == "connected"

@pytest.mark.anyio
async def test_signup_login_logout_flow():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        await asyncio.sleep(0.1)
        # Unique email to avoid duplicates
        unique_email = f"test_{os.urandom(4).hex()}@example.com"

        # Signup
        signup_resp = await client.post("/api/auth/signup", json={
            "email": unique_email,
            "name": "Test User",
            "password": "strongpass123"
        })
        assert signup_resp.status_code == 200
        assert "Account created" in signup_resp.json()["message"]

        # Login (if verification required, skip or mock – adjust if needed)
        login_resp = await client.post("/api/auth/login", json={
            "email": unique_email,
            "password": "strongpass123"
        })
        assert login_resp.status_code == 200

        # Portfolio (protected)
        portfolio_resp = await client.get("/api/portfolio")
        assert portfolio_resp.status_code == 200

        # Logout
        logout_resp = await client.post("/api/auth/logout")
        assert logout_resp.status_code == 200
        assert "Logged out successfully" in logout_resp.json()["message"]

        # Revoked token check
        revoked_resp = await client.get("/api/portfolio")
        assert revoked_resp.status_code == 401
