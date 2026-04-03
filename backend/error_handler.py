"""
Enterprise Error Handling and Response Formatting

Standardized error responses, error codes, and HTTP status mappings.
Ensures consistent error handling across all endpoints.
"""

import logging
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime, timezone
from fastapi import HTTPException, status as http_status

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for API responses"""
    
    # Client Errors (4xx)
    BAD_REQUEST = ("BAD_REQUEST", 400)
    INVALID_INPUT = ("INVALID_INPUT", 400)
    UNAUTHORIZED = ("UNAUTHORIZED", 401)
    FORBIDDEN = ("FORBIDDEN", 403)
    NOT_FOUND = ("NOT_FOUND", 404)
    CONFLICT = ("CONFLICT", 409)
    VALIDATION_ERROR = ("VALIDATION_ERROR", 422)
    RATE_LIMIT_EXCEEDED = ("RATE_LIMIT_EXCEEDED", 429)
    
    # Server Errors (5xx)
    INTERNAL_ERROR = ("INTERNAL_ERROR", 500)
    SERVICE_UNAVAILABLE = ("SERVICE_UNAVAILABLE", 503)
    DATABASE_ERROR = ("DATABASE_ERROR", 503)
    EXTERNAL_SERVICE_ERROR = ("EXTERNAL_SERVICE_ERROR", 503)
    
    @property
    def code(self) -> str:
        return self.value[0]
    
    @property
    def status_code(self) -> int:
        return self.value[1]


class APIError(Exception):
    """Base exception for API errors"""
    
    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
        super().__init__(message)
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "error": {
                "code": self.error_code.code,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    @staticmethod
    def from_http_exception(exc: HTTPException, request_id: Optional[str] = None) -> "APIError":
        """Create APIError from HTTPException"""
        # Map HTTP status to error code
        status_to_code = {
            400: ErrorCode.BAD_REQUEST,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.CONFLICT,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE,
        }
        
        error_code = status_to_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
        return APIError(
            error_code=error_code,
            message=str(exc.detail) if exc.detail else "An error occurred",
            request_id=request_id
        )


class DatabaseError(APIError):
    """Database-related errors"""
    
    def __init__(self, message: str, request_id: Optional[str] = None):
        super().__init__(
            error_code=ErrorCode.DATABASE_ERROR,
            message=f"Database error: {message}",
            request_id=request_id
        )


class ExternalServiceError(APIError):
    """External service/API errors"""
    
    def __init__(
        self,
        service_name: str,
        message: str,
        request_id: Optional[str] = None
    ):
        super().__init__(
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            message=f"{service_name} error: {message}",
            request_id=request_id,
            details={"service": service_name}
        )


class ValidationError(APIError):
    """Validation errors"""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            request_id=request_id
        )


def error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response
    
    Args:
        error_code: ErrorCode enum
        message: Error message
        details: Additional error details
        request_id: Request ID for tracing
    
    Returns:
        Formatted error response dict
    """
    return {
        "error": {
            "code": error_code.code,
            "message": message,
            "details": details or {},
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }


def success_response(
    data: Any,
    message: str = "Success",
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response
    
    Args:
        data: Response data
        message: Success message
        request_id: Request ID for tracing
    
    Returns:
        Formatted success response dict
    """
    return {
        "data": data,
        "message": message,
        "request_id": request_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
