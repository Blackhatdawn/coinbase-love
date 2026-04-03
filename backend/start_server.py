#!/usr/bin/env python3
"""Production startup for CryptoVault.

Uses gunicorn with uvicorn workers for production.
Loads environment variables from .env file.
Falls back to uvicorn if gunicorn is unavailable.
"""

import os
import sys
import subprocess
from pathlib import Path

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            print(f"[startup] Loaded environment from {env_file}")
        except ImportError:
            print("[startup] python-dotenv not installed, environment variables may not be loaded")
            # Manual loading as fallback
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip().strip('"\'')

def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def main() -> None:
    # Load environment variables
    load_env_file()

    host = os.getenv("HOST", "0.0.0.0")
    port = _env_int("PORT", 8000)  # Default to 8000 instead of 10000
    workers = _env_int("WORKERS", 1)

    print(f"[startup] Python: {sys.version.split()[0]}")
    print(f"[startup] Host/Port: {host}:{port}")
    print(f"[startup] Workers: {workers}")
    print(f"[startup] Environment: {os.getenv('ENVIRONMENT', 'development')}")

    # Use gunicorn with uvicorn workers (production)
    cmd = [
        sys.executable, "-m", "gunicorn",
        "-k", "uvicorn.workers.UvicornWorker",
        "-b", f"{host}:{port}",
        "--workers", str(workers),
        "--timeout", "120",
        "--access-logfile", "-",
        "--log-level", "info",
        "server:app",
    ]

    print(f"[startup] Command: {' '.join(cmd)}")
    os.execvp(sys.executable, cmd)


if __name__ == "__main__":
    main()
