"""
Fly.io Deployment Status Endpoint

Provides deployment-specific information for Fly.io monitoring and debugging.
"""

from fastapi import APIRouter
from datetime import datetime
import os
import socket
from typing import Dict, Any

from config import settings

router = APIRouter(prefix="/fly", tags=["fly.io"])


def get_fly_metadata() -> Dict[str, Any]:
    """
    Get Fly.io-specific environment metadata.
    These environment variables are automatically set by Fly.io.
    """
    return {
        "app_name": os.environ.get("FLY_APP_NAME", "unknown"),
        "region": os.environ.get("FLY_REGION", "unknown"),
        "alloc_id": os.environ.get("FLY_ALLOC_ID", "unknown"),
        "machine_id": os.environ.get("FLY_MACHINE_ID", "unknown"),
        "public_ip": os.environ.get("FLY_PUBLIC_IP", "unknown"),
        "private_ip": os.environ.get("FLY_PRIVATE_IP", "unknown"),
        "image_ref": os.environ.get("FLY_IMAGE_REF", "unknown"),
        "machine_version": os.environ.get("FLY_MACHINE_VERSION", "unknown"),
    }


@router.get("/status")
async def fly_status():
    """
    Fly.io deployment status endpoint.
    
    Returns deployment information useful for:
    - Multi-region routing verification
    - Instance identification
    - Debugging auto-scaling behavior
    """
    fly_meta = get_fly_metadata()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "deployment": {
            "platform": "fly.io",
            "app_name": fly_meta["app_name"],
            "region": fly_meta["region"],
            "machine_id": fly_meta["machine_id"],
            "alloc_id": fly_meta["alloc_id"],
        },
        "network": {
            "public_ip": fly_meta["public_ip"],
            "private_ip": fly_meta["private_ip"],
            "hostname": socket.gethostname(),
        },
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
        "image": {
            "ref": fly_meta["image_ref"],
            "machine_version": fly_meta["machine_version"],
        }
    }


@router.get("/region")
async def fly_region():
    """
    Quick region check for latency testing.
    Returns the current Fly.io region.
    """
    region = os.environ.get("FLY_REGION", "unknown")
    machine_id = os.environ.get("FLY_MACHINE_ID", "unknown")
    
    return {
        "region": region,
        "machine_id": machine_id,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/instances")
async def fly_instances():
    """
    Returns information about this instance for debugging auto-scaling.
    Useful for verifying load balancing across multiple instances.
    """
    return {
        "instance": {
            "machine_id": os.environ.get("FLY_MACHINE_ID", "unknown"),
            "alloc_id": os.environ.get("FLY_ALLOC_ID", "unknown"),
            "region": os.environ.get("FLY_REGION", "unknown"),
            "private_ip": os.environ.get("FLY_PRIVATE_IP", "unknown"),
        },
        "request_served_at": datetime.utcnow().isoformat(),
        "hostname": socket.gethostname(),
    }


@router.get("/health/fly")
async def fly_health():
    """
    Fly.io-specific health check that returns instance info.
    Used by Fly.io health checks and load balancer.
    """
    return {
        "status": "healthy",
        "region": os.environ.get("FLY_REGION", "unknown"),
        "machine_id": os.environ.get("FLY_MACHINE_ID", "unknown"),
        "timestamp": datetime.utcnow().isoformat()
    }
