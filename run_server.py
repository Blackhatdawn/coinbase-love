#!/usr/bin/env python3
"""
Wrapper script to run the CryptoVault server with proper Python path configuration.
Now with Socket.IO and HTTP/2 support for production-grade performance.
"""
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Now import and run the server
from server import socket_app  # Use socket_app instead of app for Socket.IO support

if __name__ == "__main__":
    import uvicorn
    
    # For development: HTTP/1.1 with reload
    # For production: Use HTTP/2 with workers
    # uvicorn server:socket_app --host 0.0.0.0 --port 8001 --http h2 --workers 4
    
    uvicorn.run(
        "server:socket_app",  # Use socket_app for Socket.IO
        host="0.0.0.0",
        port=8001,
        reload=True,
        reload_dirs=["backend"],
        # http="h2",  # Uncomment for HTTP/2 in development
    )
