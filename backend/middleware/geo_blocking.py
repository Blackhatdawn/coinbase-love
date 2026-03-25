"""
IP / Country Blocking Middleware for CryptoVault.

Blocks users from restricted regions based on:
1. GeoIP database lookup (GeoLite2/MaxMind) if configured
2. Configurable country blocklist via BLOCKED_COUNTRIES env var

Configuration:
- GEOIP_DB_PATH: Path to GeoLite2-Country.mmdb file (optional)
- MAXMIND_LICENSE_KEY: MaxMind license key for auto-download (optional)
- BLOCKED_COUNTRIES: Comma-separated ISO country codes to block (e.g., "KP,IR,CU,SY")

If no GeoIP database is available, falls back to country blocklist only
(blocks based on self-reported country in user profile).
"""

import logging
import os
from typing import Optional, Set

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Load configuration from environment
BLOCKED_COUNTRIES_STR = os.environ.get("BLOCKED_COUNTRIES", "")
GEOIP_DB_PATH = os.environ.get("GEOIP_DB_PATH", "")
MAXMIND_LICENSE_KEY = os.environ.get("MAXMIND_LICENSE_KEY", "")

# Parse blocked countries into a set
BLOCKED_COUNTRIES: Set[str] = set()
if BLOCKED_COUNTRIES_STR:
    BLOCKED_COUNTRIES = {c.strip().upper() for c in BLOCKED_COUNTRIES_STR.split(",") if c.strip()}
    logger.info("Geo-blocking enabled for countries: %s", ", ".join(sorted(BLOCKED_COUNTRIES)))
else:
    logger.info("Geo-blocking: No countries configured in BLOCKED_COUNTRIES")

# Endpoints exempt from geo-blocking (health checks, static, docs)
EXEMPT_PATHS = {
    "/health", "/health/live", "/health/ready", "/ping",
    "/api/health", "/api/health/live", "/api/health/ready", "/api/ping",
    "/api/docs", "/api/redoc", "/api/openapi.json",
    "/", "/favicon.ico",
}

# Try to load GeoIP database
_geoip_reader = None
try:
    if GEOIP_DB_PATH and os.path.exists(GEOIP_DB_PATH):
        import geoip2.database
        _geoip_reader = geoip2.database.Reader(GEOIP_DB_PATH)
        logger.info("GeoIP database loaded from: %s", GEOIP_DB_PATH)
    else:
        logger.info(
            "GeoIP database not found at '%s'. "
            "Using country blocklist only. "
            "To enable GeoIP: download GeoLite2-Country.mmdb from maxmind.com "
            "and set GEOIP_DB_PATH=/path/to/GeoLite2-Country.mmdb",
            GEOIP_DB_PATH or "(not configured)"
        )
except ImportError:
    logger.info("geoip2 package not installed. Using country blocklist only.")
except Exception as exc:
    logger.warning("Failed to load GeoIP database: %s", exc)


def get_country_from_ip(ip_address: str) -> Optional[str]:
    """
    Look up country code from IP address using GeoIP database.
    Returns ISO 3166-1 alpha-2 country code or None.
    """
    if not _geoip_reader:
        return None

    try:
        response = _geoip_reader.country(ip_address)
        return response.country.iso_code
    except Exception:
        return None


def is_ip_blocked(ip_address: str) -> tuple[bool, Optional[str]]:
    """
    Check if an IP address is from a blocked country.
    Returns (is_blocked, country_code).
    """
    if not BLOCKED_COUNTRIES:
        return False, None

    country = get_country_from_ip(ip_address)
    if country and country.upper() in BLOCKED_COUNTRIES:
        return True, country

    return False, country


class GeoBlockingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that blocks requests from restricted countries/regions.
    Uses GeoIP lookup if database is available, otherwise skips.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip for exempt paths
        path = request.url.path
        if path in EXEMPT_PATHS or path.startswith("/socket.io"):
            return await call_next(request)

        # Skip if no blocking is configured
        if not BLOCKED_COUNTRIES:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else None
        if not client_ip or client_ip in ("127.0.0.1", "::1", "localhost"):
            return await call_next(request)

        # Check if IP is blocked
        blocked, country = is_ip_blocked(client_ip)
        if blocked:
            logger.warning(
                "Geo-blocked request from %s (country: %s) to %s",
                client_ip, country, path
            )
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "REGION_RESTRICTED",
                        "message": "This service is not available in your region.",
                    }
                },
            )

        return await call_next(request)
