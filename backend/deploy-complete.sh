#!/bin/bash
set -euo pipefail

echo "🚀 CryptoVault backend deployment helper"
echo "This project deploys backend on Render; use CI workflow or Render dashboard deploy trigger."
echo ""
echo "Preflight checklist:"
echo "  1) Render secrets configured (MONGO_URL, JWT_SECRET, CSRF_SECRET, etc.)"
echo "  2) PUBLIC_API_URL=https://cryptovault-api.onrender.com"
echo "  3) PUBLIC_WS_URL=wss://cryptovault-api.onrender.com"
echo "  4) UVICORN_LOOP=asyncio"
echo "  5) PYTHON_VERSION=3.11.11"
echo ""
echo "Health checks:"
curl -fsS https://cryptovault-api.onrender.com/ping && echo "  ✅ /ping"
curl -fsS https://cryptovault-api.onrender.com/health && echo "  ✅ /health"
echo ""
echo "✅ Deployment preflight completed"
