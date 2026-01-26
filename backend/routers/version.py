"""
Version Management and Sync Module

Provides:
1. Version endpoint for frontend compatibility checks
2. Automatic version mismatch detection
3. Feature flag management
4. Deployment metadata
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/version", tags=["version"])

# Version configuration
APP_VERSION = "1.0.0"
API_VERSION = "v1"
MIN_FRONTEND_VERSION = "1.0.0"
MIN_BACKEND_VERSION = "1.0.0"


class VersionInfo(BaseModel):
    """Version information model"""
    version: str
    api_version: str
    build_timestamp: str
    git_commit: str
    environment: str
    min_frontend_version: str
    min_backend_version: str
    features: Dict[str, bool]


class CompatibilityCheck(BaseModel):
    """Compatibility check result"""
    compatible: bool
    message: str
    server_version: str
    client_version: str
    upgrade_required: bool


def get_build_info() -> Dict[str, Any]:
    """Get build information from environment or version file"""
    # Try to read from version.json
    version_file = "/app/version.json"
    if os.path.exists(version_file):
        try:
            with open(version_file, "r") as f:
                return json.load(f)
        except Exception:
            pass
    
    # Fallback to environment variables
    return {
        "version": os.environ.get("APP_VERSION", APP_VERSION),
        "api_version": os.environ.get("API_VERSION", API_VERSION),
        "build_timestamp": os.environ.get("BUILD_TIMESTAMP", datetime.utcnow().isoformat()),
        "git_commit": os.environ.get("GIT_COMMIT", os.environ.get("FLY_IMAGE_REF", "unknown")),
    }


def compare_versions(version1: str, version2: str) -> int:
    """
    Compare two semantic versions.
    Returns: -1 if v1 < v2, 0 if equal, 1 if v1 > v2
    """
    try:
        v1_parts = [int(x) for x in version1.split(".")]
        v2_parts = [int(x) for x in version2.split(".")]
        
        # Pad shorter version with zeros
        while len(v1_parts) < 3:
            v1_parts.append(0)
        while len(v2_parts) < 3:
            v2_parts.append(0)
        
        for i in range(3):
            if v1_parts[i] < v2_parts[i]:
                return -1
            elif v1_parts[i] > v2_parts[i]:
                return 1
        return 0
    except (ValueError, AttributeError):
        return 0


@router.get("", response_model=VersionInfo)
async def get_version():
    """
    Get current backend version and capabilities.
    
    Used by frontend for:
    - Compatibility checking
    - Feature flag detection
    - Cache busting
    """
    build_info = get_build_info()
    
    return VersionInfo(
        version=build_info.get("version", APP_VERSION),
        api_version=build_info.get("api_version", API_VERSION),
        build_timestamp=build_info.get("build_timestamp", datetime.utcnow().isoformat()),
        git_commit=build_info.get("git_commit", "unknown"),
        environment=os.environ.get("ENVIRONMENT", "production"),
        min_frontend_version=MIN_FRONTEND_VERSION,
        min_backend_version=MIN_BACKEND_VERSION,
        features={
            "trading": True,
            "wallet": True,
            "p2p_transfer": True,
            "price_alerts": True,
            "two_factor_auth": True,
            "admin_dashboard": True,
            "websocket": True,
            "crypto_payments": True,
        }
    )


@router.get("/check")
async def check_compatibility(client_version: Optional[str] = None):
    """
    Check if client version is compatible with server.
    
    Args:
        client_version: Frontend version string (e.g., "1.0.0")
    
    Returns:
        Compatibility status and any required actions
    """
    build_info = get_build_info()
    server_version = build_info.get("version", APP_VERSION)
    
    if not client_version:
        return CompatibilityCheck(
            compatible=True,
            message="No client version provided, assuming compatible",
            server_version=server_version,
            client_version="unknown",
            upgrade_required=False
        )
    
    # Check if client meets minimum version
    comparison = compare_versions(client_version, MIN_FRONTEND_VERSION)
    
    if comparison < 0:
        return CompatibilityCheck(
            compatible=False,
            message=f"Client version {client_version} is below minimum required {MIN_FRONTEND_VERSION}. Please refresh or clear cache.",
            server_version=server_version,
            client_version=client_version,
            upgrade_required=True
        )
    
    return CompatibilityCheck(
        compatible=True,
        message="Client version is compatible",
        server_version=server_version,
        client_version=client_version,
        upgrade_required=False
    )


@router.get("/features")
async def get_features():
    """
    Get available feature flags.
    
    Used by frontend to conditionally enable/disable features.
    """
    return {
        "features": {
            "trading": True,
            "wallet": True,
            "p2p_transfer": True,
            "price_alerts": True,
            "two_factor_auth": True,
            "admin_dashboard": True,
            "websocket": True,
            "crypto_payments": True,
        },
        "deprecated": [],
        "experimental": []
    }


@router.get("/deployment")
async def get_deployment_info():
    """
    Get deployment information for debugging.
    
    Returns Fly.io-specific metadata when deployed.
    """
    return {
        "platform": "fly.io",
        "app_name": os.environ.get("FLY_APP_NAME", "coinbase-love"),
        "region": os.environ.get("FLY_REGION", "unknown"),
        "machine_id": os.environ.get("FLY_MACHINE_ID", "unknown"),
        "alloc_id": os.environ.get("FLY_ALLOC_ID", "unknown"),
        "image_ref": os.environ.get("FLY_IMAGE_REF", "unknown"),
        "public_url": os.environ.get("PUBLIC_API_URL", "https://coinbase-love.fly.dev"),
        "environment": os.environ.get("ENVIRONMENT", "production"),
        "timestamp": datetime.utcnow().isoformat()
    }
