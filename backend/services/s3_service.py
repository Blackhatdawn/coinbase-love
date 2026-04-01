"""
S3 Storage Service for CryptoVault.

Handles document uploads/downloads for:
- KYC documents (ID proofs, address proofs, selfies)
- Audit reports and compliance exports
- User profile documents

Supports S3-compatible providers (AWS S3, MinIO, Hostkey, etc.).
Falls back to local file storage if S3 credentials are not configured.

Configuration via environment variables:
- S3_ENDPOINT_URL: S3-compatible endpoint
- S3_ACCESS_KEY_ID: Access key
- S3_SECRET_ACCESS_KEY: Secret key
- S3_REGION: Region
- S3_BUCKET_NAME: Default bucket name
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

from config import settings

logger = logging.getLogger(__name__)

# S3 configuration from settings
S3_ENDPOINT_URL = settings.s3_endpoint_url
S3_ACCESS_KEY_ID = settings.s3_access_key_id
S3_SECRET_ACCESS_KEY = settings.s3_secret_access_key
S3_REGION = settings.s3_region
S3_BUCKET_KYC = settings.s3_bucket_kyc
S3_BUCKET_AUDIT = settings.s3_bucket_audit

# Local fallback directory
LOCAL_UPLOAD_DIR = Path("/tmp/cryptovault-uploads")

# Check if S3 is configured
S3_CONFIGURED = bool(S3_ACCESS_KEY_ID and S3_SECRET_ACCESS_KEY)

if not S3_CONFIGURED:
    logger.warning(
        "S3 not configured - KYC documents will be saved locally. "
        "Set S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY in environment."
    )
    LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def upload_document(
    file_data: bytes,
    filename: str,
    content_type: str = "application/octet-stream",
    bucket: str = "",
    folder: str = "kyc",
    user_id: Optional[str] = None,
) -> dict:
    """
    Upload a document to S3 or local storage.

    Args:
        file_data: Raw file bytes
        filename: Original filename
        content_type: MIME type
        bucket: S3 bucket name (defaults to KYC bucket)
        folder: Folder/prefix within bucket
        user_id: User ID for organizing uploads

    Returns:
        dict with upload result: {"success": bool, "key": str, "storage": str, "url": str}
    """
    # Generate unique key
    ext = Path(filename).suffix or ".bin"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    key = f"{folder}/{user_id or 'anonymous'}/{unique_name}"

    if S3_CONFIGURED:
        return await _upload_to_s3(file_data, key, content_type, bucket or S3_BUCKET_KYC)
    else:
        return _upload_to_local(file_data, key)


async def download_document(
    key: str,
    bucket: str = "",
) -> Optional[bytes]:
    """
    Download a document from S3 or local storage.

    Args:
        key: Document key/path
        bucket: S3 bucket name

    Returns:
        File bytes or None if not found
    """
    if S3_CONFIGURED:
        return await _download_from_s3(key, bucket or S3_BUCKET_KYC)
    else:
        return _download_from_local(key)


async def delete_document(
    key: str,
    bucket: str = "",
) -> bool:
    """Delete a document from S3 or local storage."""
    if S3_CONFIGURED:
        return await _delete_from_s3(key, bucket or S3_BUCKET_KYC)
    else:
        return _delete_from_local(key)


async def generate_presigned_url(
    key: str,
    content_type: str,
    bucket: str = "",
    expiration: int = 3600,
) -> Dict[str, Any]:
    """
    Generate a pre-signed URL for direct-to-S3 upload.

    Args:
        key: Object key
        content_type: MIME type of the file
        bucket: S3 bucket name
        expiration: URL expiration in seconds (default 1 hour)

    Returns:
        dict: {"url": str, "fields": dict, "key": str}
    """
    if not S3_CONFIGURED:
        # For local development without S3, return a mock URL
        # The frontend will need to handle this fallback
        return {
            "url": f"{settings.public_api_url or 'http://localhost:8001'}/api/kyc/upload-mock",
            "fields": {"key": key, "Content-Type": content_type},
            "key": key,
            "mock": True
        }

    try:
        import boto3
        from botocore.config import Config

        s3_client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL if S3_ENDPOINT_URL else None,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
            config=Config(signature_version="s3v4"),
        )

        bucket_name = bucket or S3_BUCKET_KYC

        # Enforce server-side encryption and least privilege
        response = s3_client.generate_presigned_post(
            Bucket=bucket_name,
            Key=key,
            Fields={
                "Content-Type": content_type,
                "x-amz-server-side-encryption": "AES256"
            },
            Conditions=[
                {"Content-Type": content_type},
                {"x-amz-server-side-encryption": "AES256"},
                ["content-length-range", 1, 10 * 1024 * 1024],  # 1B to 10MB
            ],
            ExpiresIn=expiration,
        )

        return {
            "url": response["url"],
            "fields": response["fields"],
            "key": key,
            "mock": False
        }

    except Exception as exc:
        logger.error("Failed to generate pre-signed URL: %s", exc)
        raise RuntimeError(f"Could not generate upload URL: {str(exc)}")


# ============================================
# S3 OPERATIONS
# ============================================

async def _upload_to_s3(file_data: bytes, key: str, content_type: str, bucket: str) -> dict:
    """Upload file to S3-compatible storage using aioboto3."""
    try:
        import aioboto3

        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        ) as s3_client:
            await s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
            )

        logger.info("S3 upload successful: %s/%s", bucket, key)
        return {
            "success": True,
            "key": key,
            "bucket": bucket,
            "storage": "s3",
            "url": f"{S3_ENDPOINT_URL}/{bucket}/{key}",
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("S3 upload failed for %s: %s", key, exc)
        # Fallback to local on S3 failure
        logger.warning("Falling back to local storage for %s", key)
        return _upload_to_local(file_data, key)


async def _download_from_s3(key: str, bucket: str) -> Optional[bytes]:
    """Download file from S3-compatible storage."""
    try:
        import aioboto3

        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        ) as s3_client:
            response = await s3_client.get_object(Bucket=bucket, Key=key)
            data = await response["Body"].read()
            return data

    except Exception as exc:
        logger.error("S3 download failed for %s: %s", key, exc)
        return None


async def _delete_from_s3(key: str, bucket: str) -> bool:
    """Delete file from S3-compatible storage."""
    try:
        import aioboto3

        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        ) as s3_client:
            await s3_client.delete_object(Bucket=bucket, Key=key)
            return True

    except Exception as exc:
        logger.error("S3 delete failed for %s: %s", key, exc)
        return False


# ============================================
# LOCAL STORAGE FALLBACK
# ============================================

def _upload_to_local(file_data: bytes, key: str) -> dict:
    """Upload file to local filesystem (fallback)."""
    try:
        file_path = LOCAL_UPLOAD_DIR / key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(file_data)

        logger.info("Local upload successful: %s", file_path)
        return {
            "success": True,
            "key": key,
            "storage": "local",
            "path": str(file_path),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Local upload failed for %s: %s", key, exc)
        return {"success": False, "key": key, "error": str(exc)}


def _download_from_local(key: str) -> Optional[bytes]:
    """Download file from local filesystem."""
    try:
        file_path = LOCAL_UPLOAD_DIR / key
        if file_path.exists():
            return file_path.read_bytes()
        return None
    except Exception as exc:
        logger.error("Local download failed for %s: %s", key, exc)
        return None


def _delete_from_local(key: str) -> bool:
    """Delete file from local filesystem."""
    try:
        file_path = LOCAL_UPLOAD_DIR / key
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    except Exception as exc:
        logger.error("Local delete failed for %s: %s", key, exc)
        return False
