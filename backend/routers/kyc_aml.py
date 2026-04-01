"""
KYC/AML Integration Endpoints for CryptoVault.

Provides placeholder endpoints and hooks for future KYC/AML service integration:
- Document upload (to S3 or local storage)
- KYC status checking
- AML screening hooks
- Compliance reporting

These are integration-ready hooks that can be connected to providers like:
- Jumio, Onfido, Sumsub, Veriff for KYC
- Chainalysis, Elliptic, CipherTrace for AML

Currently uses manual admin approval workflow with S3 document storage.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends, UploadFile, File, Form
from pydantic import BaseModel

from dependencies import get_current_user_id, get_db
from services.audit_service import AuditAction, log_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kyc", tags=["kyc"])

def _ensure_kyc_enabled() -> None:
    from config import settings
    if not settings.feature_kyc_enabled:
        raise HTTPException(status_code=503, detail="KYC services are currently disabled")


class KYCSubmission(BaseModel):
    # Personal Details
    full_name: str
    date_of_birth: str
    phone_number: str
    occupation: str

    # Address Info
    country: str
    city: str
    address: str
    postal_code: str

    # Documents (S3 keys)
    id_type: str  # passport, national_id, drivers_license
    id_front_key: str
    id_back_key: Optional[str] = None
    proof_of_address_key: str
    selfie_key: str


class PresignedUrlRequest(BaseModel):
    file_name: str
    content_type: str
    document_type: str  # id_front, id_back, address_proof, selfie


class AMLScreeningResult(BaseModel):
    """Placeholder model for AML screening results."""
    user_id: str
    risk_level: str = "low"  # low, medium, high
    screening_provider: str = "manual"
    flags: list = []
    screened_at: Optional[str] = None


# ============================================
# KYC ENDPOINTS
# ============================================

@router.post("/presigned-url")
async def get_presigned_url(
    request: Request,
    payload: PresignedUrlRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Generate a pre-signed URL for direct-to-S3 upload.
    """
    _ensure_kyc_enabled()
    from services.s3_service import generate_presigned_url
    import uuid

    # Validate document type
    valid_types = ["id_front", "id_back", "address_proof", "selfie"]
    if payload.document_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid document type")

    # Generate unique key: kyc/{user_id}/{document_type}_{uuid}_{filename}
    ext = payload.file_name.split(".")[-1] if "." in payload.file_name else "bin"
    key = f"kyc/{user_id}/{payload.document_type}_{uuid.uuid4().hex}.{ext}"

    try:
        result = await generate_presigned_url(
            key=key,
            content_type=payload.content_type,
        )
        return result
    except Exception as e:
        logger.error(f"Failed to generate pre-signed URL: {e}")
        raise HTTPException(status_code=500, detail="Could not generate upload URL")


@router.post("/submit")
async def submit_kyc(
    request: Request,
    payload: KYCSubmission,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """
    Final KYC submission after documents are uploaded to S3.
    """
    _ensure_kyc_enabled()

    # Age validation (>= 20)
    try:
        dob = datetime.strptime(payload.date_of_birth, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age = now.year - dob.year - ((now.month, now.day) < (dob.month, dob.day))
        if age < 20:
            logger.warning(f"KYC Rejected: User {user_id} age is {age} (below required 20)")
            raise HTTPException(status_code=400, detail="You must be at least 20 years old to complete identity verification.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date of birth format. Use YYYY-MM-DD.")

    users_collection = db.get_collection("users")

    # Verify user exists
    user = await users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user record with KYC data
    kyc_docs = [
        {"type": "id_front", "key": payload.id_front_key},
        {"type": "address_proof", "key": payload.proof_of_address_key},
        {"type": "selfie", "key": payload.selfie_key},
    ]
    if payload.id_back_key:
        kyc_docs.append({"type": "id_back", "key": payload.id_back_key})

    update_data = {
        "full_name": payload.full_name,
        "date_of_birth": payload.date_of_birth,
        "phone_number": payload.phone_number,
        "occupation": payload.occupation,
        "country": payload.country,
        "city": payload.city,
        "address": payload.address,
        "postal_code": payload.postal_code,
        "kyc_status": "pending",
        "kyc_tier": 1,
        "kyc_submitted_at": datetime.now(timezone.utc),
        "kyc_docs": kyc_docs,
        "kyc_id_type": payload.id_type,
    }

    await users_collection.update_one(
        {"id": user_id},
        {"$set": update_data}
    )

    # Audit log
    await log_audit_event(
        db=db,
        action=AuditAction.KYC_DOCUMENT_UPLOADED, # Reusing for submission
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        resource_type="kyc_submission",
        resource_id=user_id,
        details={"status": "pending", "id_type": payload.id_type},
    )

    # Notify admin via Telegram
    try:
        from services.telegram_bot import telegram_bot
        await telegram_bot.notify_new_kyc_submission(user_id, update_data)
    except Exception as e:
        logger.warning(f"Failed to send Telegram notification: {e}")

    return {
        "success": True,
        "message": "KYC application submitted successfully. Our team will review it within 24 hours.",
        "status": "pending"
    }


@router.post("/upload-mock")
async def upload_mock(request: Request):
    """
    Mock endpoint for local development without S3.
    Receives multipart/form-data and just returns success.
    """
    from config import settings
    if settings.environment == "production":
        raise HTTPException(status_code=404)

    # In a real mock, we might save the file locally, but for now just acknowledge
    return {"success": True, "message": "Mock upload successful"}


@router.post("/documents/upload")
async def upload_kyc_document(
    request: Request,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """
    Upload a KYC document (ID proof, address proof, selfie).
    Stores in S3 if configured, otherwise local filesystem.
    """
    from services.s3_service import upload_document

    # Validate document type
    valid_types = ["id_front", "id_back", "passport", "selfie", "address_proof", "utility_bill"]
    if document_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid document type. Valid: {', '.join(valid_types)}")

    # Validate file size (max 10MB)
    file_data = await file.read()
    if len(file_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}")

    # Upload document
    result = await upload_document(
        file_data=file_data,
        filename=file.filename or f"{document_type}.bin",
        content_type=file.content_type or "application/octet-stream",
        folder="kyc",
        user_id=user_id,
    )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to upload document")

    # Store reference in user's KYC docs
    users_collection = db.get_collection("users")
    doc_record = {
        "type": document_type,
        "key": result["key"],
        "storage": result.get("storage", "unknown"),
        "filename": file.filename,
        "content_type": file.content_type,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }

    await users_collection.update_one(
        {"id": user_id},
        {
            "$push": {"kyc_docs": doc_record},
            "$set": {
                "kyc_status": "pending",
                "kyc_submitted_at": datetime.now(timezone.utc),
            },
        },
    )

    # Audit log
    await log_audit_event(
        db=db,
        action=AuditAction.KYC_DOCUMENT_UPLOADED,
        user_id=user_id,
        ip_address=request.client.host if request.client else None,
        resource_type="kyc_document",
        resource_id=result["key"],
        details={"document_type": document_type, "storage": result.get("storage")},
    )

    return {
        "success": True,
        "document_type": document_type,
        "key": result["key"],
        "storage": result.get("storage"),
        "message": "Document uploaded successfully. KYC review will be completed within 24 hours.",
    }


# ============================================
# KYC STATUS
# ============================================

@router.get("/status")
async def get_kyc_status(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """Get user's KYC verification status and tier."""
    _ensure_kyc_enabled()
    users_collection = db.get_collection("users")
    user = await users_collection.find_one({"id": user_id}, {"_id": 0})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "kyc_status": user.get("kyc_status", "pending"),
        "kyc_tier": user.get("kyc_tier", 0),
        "submitted_at": user.get("kyc_submitted_at"),
        "approved_at": user.get("kyc_approved_at"),
        "rejected_at": user.get("kyc_rejected_at"),
        "rejection_reason": user.get("kyc_rejection_reason"),
        "documents_count": len(user.get("kyc_docs", [])),
    }


# ============================================
# AML SCREENING HOOKS (PLACEHOLDER)
# ============================================

@router.post("/aml/screen")
async def aml_screening_hook(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """
    AML screening placeholder endpoint.

    In production, this would integrate with:
    - Chainalysis KYT for transaction screening
    - Elliptic for wallet risk scoring
    - CipherTrace for compliance checks

    Currently returns a manual review placeholder.
    """
    users_collection = db.get_collection("users")
    user = await users_collection.find_one({"id": user_id}, {"_id": 0})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Placeholder: return current fraud risk data
    return {
        "user_id": user_id,
        "screening_status": "manual_review",
        "risk_level": user.get("fraud_risk_level", "low"),
        "risk_score": user.get("fraud_risk_score", 0),
        "provider": "manual",
        "message": "AML screening integration pending. Currently using manual review.",
        "integration_ready": True,
        "supported_providers": ["chainalysis", "elliptic", "ciphertrace", "sumsub"],
    }


# ============================================
# COMPLIANCE REPORT (PLACEHOLDER)
# ============================================

@router.get("/compliance/report")
async def get_compliance_report(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    """
    Generate compliance report for a user.
    Includes KYC status, transaction summary, and risk assessment.
    """
    users_collection = db.get_collection("users")
    user = await users_collection.find_one({"id": user_id}, {"_id": 0})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get transaction summary
    transactions_collection = db.get_collection("transactions")
    tx_count = await transactions_collection.count_documents({"user_id": user_id})

    return {
        "user_id": user_id,
        "kyc": {
            "status": user.get("kyc_status", "pending"),
            "tier": user.get("kyc_tier", 0),
            "documents_count": len(user.get("kyc_docs", [])),
        },
        "risk": {
            "level": user.get("fraud_risk_level", "low"),
            "score": user.get("fraud_risk_score", 0),
        },
        "activity": {
            "total_transactions": tx_count,
            "account_created": user.get("created_at").isoformat() if user.get("created_at") else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
