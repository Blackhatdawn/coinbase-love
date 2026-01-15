#!/usr/bin/env python3
"""
Wrapper script to run the CryptoVault server with proper Python path configuration.
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Now import and run the server
from server import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=["backend"]
    )
