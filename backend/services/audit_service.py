"""
Comprehensive Audit Logging Service for CryptoVault.

Provides structured audit logging for all financial actions:
- Deposits, withdrawals, transfers, trades
- Admin approvals, KYC actions
- Login/logout events
- Configuration changes

Every log entry includes request_id, user_id, IP, timestamp, and action details.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class AuditAction:
    """Constants for audit action types."""
    # Auth
    LOGIN = "AUTH_LOGIN"
    LOGOUT = "AUTH_LOGOUT"
    LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    PASSWORD_CHANGE = "AUTH_PASSWORD_CHANGE"
    PASSWORD_RESET = "AUTH_PASSWORD_RESET"
    TWO_FACTOR_ENABLED = "AUTH_2FA_ENABLED"
    TWO_FACTOR_DISABLED = "AUTH_2FA_DISABLED"

    # Financial
    DEPOSIT_INITIATED = "FINANCIAL_DEPOSIT_INITIATED"
    DEPOSIT_COMPLETED = "FINANCIAL_DEPOSIT_COMPLETED"
    DEPOSIT_FAILED = "FINANCIAL_DEPOSIT_FAILED"
    WITHDRAWAL_REQUESTED = "FINANCIAL_WITHDRAWAL_REQUESTED"
    WITHDRAWAL_APPROVED = "FINANCIAL_WITHDRAWAL_APPROVED"
    WITHDRAWAL_REJECTED = "FINANCIAL_WITHDRAWAL_REJECTED"
    WITHDRAWAL_COMPLETED = "FINANCIAL_WITHDRAWAL_COMPLETED"
    TRANSFER_SENT = "FINANCIAL_TRANSFER_SENT"
    TRANSFER_RECEIVED = "FINANCIAL_TRANSFER_RECEIVED"
    TRADE_EXECUTED = "FINANCIAL_TRADE_EXECUTED"
    TRADE_CANCELLED = "FINANCIAL_TRADE_CANCELLED"

    # Admin
    ADMIN_WITHDRAWAL_APPROVAL = "ADMIN_WITHDRAWAL_APPROVAL"
    ADMIN_WITHDRAWAL_REJECTION = "ADMIN_WITHDRAWAL_REJECTION"
    ADMIN_KYC_APPROVAL = "ADMIN_KYC_APPROVAL"
    ADMIN_KYC_REJECTION = "ADMIN_KYC_REJECTION"
    ADMIN_USER_LOCK = "ADMIN_USER_LOCK"
    ADMIN_USER_UNLOCK = "ADMIN_USER_UNLOCK"
    ADMIN_CONFIG_CHANGE = "ADMIN_CONFIG_CHANGE"

    # KYC
    KYC_SUBMITTED = "KYC_SUBMITTED"
    KYC_DOCUMENT_UPLOADED = "KYC_DOCUMENT_UPLOADED"
    KYC_APPROVED = "KYC_APPROVED"
    KYC_REJECTED = "KYC_REJECTED"


async def log_audit_event(
    db,
    action: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    severity: str = "info",
):
    """
    Log a comprehensive audit event to MongoDB and structured logger.

    Args:
        db: Database connection
        action: Action type from AuditAction constants
        user_id: ID of the user performing the action
        request_id: Correlation ID for the request
        ip_address: Client IP address
        user_agent: Client user agent string
        resource_type: Type of resource affected (e.g., 'withdrawal', 'user')
        resource_id: ID of the resource affected
        details: Additional action-specific details
        severity: Log severity (info, warning, error, critical)
    """
    audit_entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "user_id": user_id,
        "request_id": request_id or str(uuid.uuid4()),
        "ip_address": ip_address,
        "user_agent": user_agent,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details or {},
        "severity": severity,
        "created_at": datetime.now(timezone.utc),
    }

    # Structured log output
    logger.log(
        _severity_to_level(severity),
        "AUDIT: %s | user=%s | resource=%s/%s | ip=%s",
        action,
        user_id or "system",
        resource_type or "-",
        resource_id or "-",
        ip_address or "-",
        extra={
            "type": "audit",
            "action": action,
            "user_id": user_id,
            "request_id": audit_entry["request_id"],
            "resource_type": resource_type,
            "resource_id": resource_id,
        },
    )

    # Persist to MongoDB
    try:
        if db:
            collection = db.get_collection("audit_logs")
            await collection.insert_one(audit_entry)
    except Exception as exc:
        logger.error("Failed to persist audit log: %s", exc)


def _severity_to_level(severity: str) -> int:
    mapping = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    return mapping.get(severity, logging.INFO)
