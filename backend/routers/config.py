"""
Public runtime configuration endpoint.
Provides frontend-safe settings from backend .env.
"""

from fastapi import APIRouter, Request
from typing import Dict, Any

from config import settings

router = APIRouter(prefix="/config", tags=["config"])


def normalize_base_url(value: str) -> str:
    """Normalize base URLs by removing trailing slashes."""
    return value.rstrip("/") if value else value


def derive_request_base_url(request: Request) -> str:
    """Resolve request base URL, respecting proxy headers if present."""
    forwarded_proto = request.headers.get("x-forwarded-proto")
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_proto and forwarded_host:
        return normalize_base_url(f"{forwarded_proto}://{forwarded_host}")
    return normalize_base_url(str(request.base_url))


def derive_ws_base_url(api_base_url: str) -> str:
    """Resolve WS base URL from settings or API base URL."""
    if settings.public_ws_url:
        return normalize_base_url(settings.public_ws_url)
    if api_base_url.startswith("https://"):
        return "wss://" + api_base_url[len("https://"):]
    if api_base_url.startswith("http://"):
        return "ws://" + api_base_url[len("http://"):]
    return api_base_url


@router.get("")
async def get_public_config(request: Request) -> Dict[str, Any]:
    """
    Return frontend-safe runtime configuration.
    This endpoint intentionally excludes secrets.
    """
    request_base_url = derive_request_base_url(request)
    api_base_url = normalize_base_url(settings.public_api_url or "")
    prefer_relative_api = not bool(api_base_url)
    ws_base_url = derive_ws_base_url(settings.public_ws_url or api_base_url or request_base_url)
    app_url = normalize_base_url(settings.app_url)
    logo_url = settings.public_logo_url or f"{app_url}/favicon.svg"
    support_email = settings.public_support_email or settings.email_from

    return {
        "appUrl": app_url,
        "apiBaseUrl": api_base_url,
        "preferRelativeApi": prefer_relative_api,
        "wsBaseUrl": ws_base_url,
        "socketIoPath": settings.public_socket_io_path,
        "environment": settings.environment,
        "version": "1.0.0",
        "sentry": {
            "dsn": settings.public_sentry_dsn or "",
            "enabled": bool(settings.public_sentry_dsn),
            "environment": settings.environment,
        },
        "branding": {
            "siteName": settings.public_site_name,
            "logoUrl": logo_url,
            "supportEmail": support_email,
        },
    }
