#!/usr/bin/env python3
"""Production startup wrapper for Render deployments.

This script prevents startup failures when uvloop isn't available (e.g. on some
Python 3.13 builds) by automatically falling back to asyncio.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import uvicorn


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _detect_loop() -> str:
    forced_loop = os.getenv("UVICORN_LOOP", "").strip().lower()
    if forced_loop:
        if forced_loop == "uvloop" and importlib.util.find_spec("uvloop") is None:
            print("[startup] UVICORN_LOOP=uvloop requested but uvloop is not installed. Falling back to asyncio.")
            return "asyncio"
        return forced_loop

    # Default to asyncio for predictable cross-platform production behavior.
    # uvloop is only used when explicitly requested via UVICORN_LOOP=uvloop.
    return "asyncio"


def main() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = _env_int("PORT", 8001)
    workers = _env_int("WORKERS", 4)
    app_path = os.getenv("APP_PATH", "server:app")
    loop = _detect_loop()

    # Keep startup output explicit for deployment logs.
    print(f"[startup] Python: {sys.version.split()[0]}")
    print(f"[startup] App: {app_path}")
    print(f"[startup] Host/Port: {host}:{port}")
    print(f"[startup] Workers: {workers}")
    print(f"[startup] Event loop: {loop}")

    uvicorn.run(
        app_path,
        host=host,
        port=port,
        workers=workers,
        loop=loop,
        http="h11",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
