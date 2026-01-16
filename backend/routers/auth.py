"""Authentication and user management endpoints."""

from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import uuid
import bcrypt
from typing import Optional
import logging

from models import (
    User, UserCreate, UserLogin, UserResponse,
    VerifyEmailRequest, ResendVerificationRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    TwoFactorSetup, TwoFactorVerify, BackupCodes
)
from config import settings
from email_service import (
    email_service,
    generate_verification_code,
    generate_verification_token,
    generate_password_reset_token,
    get_token_expiration
)
from auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, generate_backup_codes, generate_2fa_secret,
    generate_device_fingerprint, verify_2fa_code
)
from dependencies import get_current_user_id, get_db, get_limiter
from blacklist import blacklist_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """
    Set authentication cookies with proper SameSite and Secure attributes.

    When frontend and API are on different origins (cross-site), use SameSite=None with Secure=True.
    When on same origin, use SameSite=Lax for better security.

    Configuration:
    - Set USE_CROSS_SITE_COOKIES=true in environment if frontend and API are on different origins
    - For production cross-site auth: requires CORS_ORIGINS to be specific (not '*') and HTTPS
    """
    # Determine SameSite policy based on configuration
    same_site = "none" if settings.use_cross_site_cookies else "lax"
    # For SameSite=None, Secure must be True (only over HTTPS)
    secure = settings.environment == 'production' or settings.use_cross_site_cookies

    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )

    # Set refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path="/"
    )


async def log_audit(
    db, user_id: str, action: str, 
    resource: Optional[str] = None,
    ip_address: Optional[str] = None, 
    details: Optional[dict] = None,
    request_id: Optional[str] = None
):
    """Log audit event."""
    from models import AuditLog
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Audit log: {action}",
        extra={
            "type": "audit_log",
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "ip_address": ip_address,
            "request_id": request_id
        }
    )
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        details=details
    )
    await db.get_collection("audit_logs").insert_one(audit_log.dict())


@router.post("/signup")
async def signup(
    user_data: UserCreate, 
    request: Request,
    db = Depends(get_db)
):
    """Register a new user with email verification."""
    users_collection = db.get_collection("users")
    portfolios_collection = db.get_collection("portfolios")

    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    verification_code = generate_verification_code()
    verification_token = generate_verification_token()
    verification_expires = get_token_expiration(hours=24)

    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=get_password_hash(user_data.password),
        email_verified=False,
        email_verification_code=verification_code,
        email_verification_token=verification_token,
        email_verification_expires=verification_expires
    )

    await users_collection.insert_one(user.dict())

    from models import Portfolio
    portfolio = Portfolio(user_id=user.id)
    await portfolios_collection.insert_one(portfolio.dict())

    app_url = settings.app_url
    subject, html_content, text_content = email_service.get_verification_email(
        name=user.name,
        code=verification_code,
        token=verification_token,
        app_url=app_url
    )

    email_sent = await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    await log_audit(
        db, user.id, "USER_SIGNUP", 
        ip_address=request.client.host,
        request_id=getattr(request.state, "request_id", "unknown")
    )

    return {
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict(),
        "message": "Account created! Please check your email to verify your account.",
        "emailSent": email_sent,
        "verificationRequired": True
    }


@router.post("/login")
async def login(
    credentials: UserLogin, 
    request: Request,
    db = Depends(get_db)
):
    """Login user with account lockout protection."""
    users_collection = db.get_collection("users")

    user_doc = await users_collection.find_one({"email": credentials.email})
    if not user_doc:
        verify_password("dummy_password", bcrypt.gensalt().decode())
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = User(**user_doc)

    if user.locked_until and user.locked_until > datetime.utcnow():
        minutes_left = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=429,
            detail=f"Account locked due to too many failed attempts. Try again in {minutes_left} minutes."
        )

    device_fingerprint = generate_device_fingerprint(request)
    login_attempt = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "email": credentials.email,
        "ip_address": request.client.host,
        "device_fingerprint": device_fingerprint,
        "timestamp": datetime.utcnow(),
        "success": False
    }
    if not verify_password(credentials.password, user.password_hash):
        failed_attempts = user.failed_login_attempts + 1
        update_data = {
            "failed_login_attempts": failed_attempts,
            "last_failed_attempt": datetime.utcnow()
        }
        
        if failed_attempts >= 5:
            update_data["locked_until"] = datetime.utcnow() + timedelta(minutes=15)
            await users_collection.update_one({"id": user.id}, {"$set": update_data})
            await db.get_collection("login_attempts").insert_one(login_attempt)
            await log_audit(db, user.id, "ACCOUNT_LOCKED", ip_address=request.client.host)
            raise HTTPException(
                status_code=429,
                detail="Account locked for 15 minutes due to too many failed login attempts."
            )
        
        await users_collection.update_one({"id": user.id}, {"$set": update_data})
        await db.get_collection("login_attempts").insert_one(login_attempt)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.email_verified:
        raise HTTPException(
            status_code=401,
            detail="Email not verified. Please check your email and verify your account."
        )

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login": datetime.utcnow()
        }}
    )

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    await log_audit(db, user.id, "USER_LOGIN", ip_address=request.client.host)

    logger.info(f"Setting cookies - access_token length: {len(access_token)}, refresh_token length: {len(refresh_token)}")

    response = JSONResponse(content={
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    })
    
    # Set auth cookies with proper SameSite and Secure attributes
    set_auth_cookies(response, access_token, refresh_token)
    
    logger.info(f"Response headers: {dict(response.headers)}")
    return response


@router.post("/logout")
async def logout(
    request: Request, 
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Secure logout: Blacklist tokens and delete cookies."""
    refresh_token = request.cookies.get("refresh_token")
    access_token = request.cookies.get("access_token")

    if refresh_token:
        payload = decode_token(refresh_token)
        if payload and payload.get("type") == "refresh":
            expires_in = int(payload["exp"] - datetime.utcnow().timestamp())
            await blacklist_token(refresh_token, max(expires_in, 60))

    if access_token:
        payload = decode_token(access_token)
        if payload and payload.get("type") == "access":
            expires_in = int(payload["exp"] - datetime.utcnow().timestamp())
            await blacklist_token(access_token, max(expires_in, 60))

    await log_audit(db, user_id, "USER_LOGOUT", ip_address=request.client.host)

    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response


@router.get("/me")
async def get_current_user_profile(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get current user profile."""
    users_collection = db.get_collection("users")
    user_doc = await users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    user = User(**user_doc)
    return {
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    }


@router.put("/profile")
async def update_profile(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Update user profile."""
    users_collection = db.get_collection("users")
    body = await request.json()
    name = body.get("name")
    if not name or len(name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Name must be at least 2 characters")
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"name": name.strip()}}
    )
    user_doc = await users_collection.find_one({"id": user_id})
    user = User(**user_doc)
    await log_audit(db, user_id, "PROFILE_UPDATED", ip_address=request.client.host)
    return {
        "message": "Profile updated successfully",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    }


@router.post("/change-password")
async def change_password(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Change user password."""
    users_collection = db.get_collection("users")
    body = await request.json()
    current_password = body.get("current_password")
    new_password = body.get("new_password")
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current and new password are required")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    user_doc = await users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    user = User(**user_doc)
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hashed_password = get_password_hash(new_password)
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"password_hash": new_hashed_password}}
    )
    await log_audit(db, user_id, "PASSWORD_CHANGED", ip_address=request.client.host)
    return {"message": "Password changed successfully"}


@router.post("/refresh")
async def refresh_token(request: Request):
    """Refresh access token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    access_token = create_access_token(data={"sub": user_id})

    response = JSONResponse(content={"message": "Token refreshed"})
    # Determine SameSite policy based on configuration
    same_site = "none" if settings.use_cross_site_cookies else "lax"
    secure = settings.environment == 'production' or settings.use_cross_site_cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=same_site,
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )
    return response


@router.post("/verify-email")
async def verify_email(
    data: VerifyEmailRequest, 
    request: Request,
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Verify email with code or token."""
    users_collection = db.get_collection("users")

    user_doc = await users_collection.find_one({
        "$or": [
            {"email_verification_code": data.token},
            {"email_verification_token": data.token}
        ]
    })

    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user = User(**user_doc)

    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    if user.email_verification_expires < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="Verification code expired. Please request a new one."
        )

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "email_verified": True,
            "email_verification_code": None,
            "email_verification_token": None,
            "email_verification_expires": None
        }}
    )

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    await log_audit(db, user.id, "EMAIL_VERIFIED")

    subject, html_content, text_content = email_service.get_welcome_email(
        name=user.name,
        app_url=settings.app_url
    )
    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    response = JSONResponse(content={
        "message": "Email verified successfully!",
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            createdAt=user.created_at.isoformat()
        ).dict()
    })

    # Set auth cookies with proper SameSite and Secure attributes
    set_auth_cookies(response, access_token, refresh_token)

    return response


@router.post("/resend-verification")
async def resend_verification(
    data: ResendVerificationRequest, 
    request: Request,
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Resend verification email."""
    users_collection = db.get_collection("users")

    user_doc = await users_collection.find_one({"email": data.email})
    if not user_doc:
        return {"message": "If this email is registered, a verification email has been sent."}

    user = User(**user_doc)

    if user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    verification_code = generate_verification_code()
    verification_token = generate_verification_token()
    verification_expires = get_token_expiration(hours=24)

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "email_verification_code": verification_code,
            "email_verification_token": verification_token,
            "email_verification_expires": verification_expires
        }}
    )

    subject, html_content, text_content = email_service.get_verification_email(
        name=user.name,
        code=verification_code,
        token=verification_token,
        app_url=settings.app_url
    )

    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    return {"message": "Verification email sent! Please check your inbox."}


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest, 
    request: Request,
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Request password reset email."""
    # Temporarily disable rate limiting to fix the issue
    # 
    users_collection = db.get_collection("users")

    user_doc = await users_collection.find_one({"email": data.email})

    if not user_doc:
        return {"message": "If this email is registered, a password reset link has been sent."}

    user = User(**user_doc)

    reset_token = generate_password_reset_token()
    reset_expires = get_token_expiration(hours=1)

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "password_reset_token": reset_token,
            "password_reset_expires": reset_expires
        }}
    )

    reset_link = f"{settings.app_url}/reset-password?token={reset_token}"

    subject, html_content, text_content = email_service.get_password_reset_email(
        name=user.name,
        reset_link=reset_link
    )

    await email_service.send_email(
        to_email=user.email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

    await log_audit(db, user.id, "PASSWORD_RESET_REQUESTED")

    return {"message": "If this email is registered, a password reset link has been sent."}


@router.get("/validate-reset-token/{token}")
async def validate_reset_token(token: str, db = Depends(get_db)):
    """Validate if password reset token is valid."""
    users_collection = db.get_collection("users")

    user_doc = await users_collection.find_one({"password_reset_token": token})

    if not user_doc:
        return {"valid": False, "message": "Invalid reset token"}

    user = User(**user_doc)

    if user.password_reset_expires < datetime.utcnow():
        return {"valid": False, "message": "Reset token expired"}

    return {"valid": True, "message": "Token is valid"}


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest, 
    request: Request,
    db = Depends(get_db),
    limiter = Depends(get_limiter)
):
    """Reset password with valid token."""
    users_collection = db.get_collection("users")

    user_doc = await users_collection.find_one({"password_reset_token": data.token})

    if not user_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = User(**user_doc)

    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Reset token expired. Please request a new one.")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    new_password_hash = get_password_hash(data.new_password)

    await users_collection.update_one(
        {"id": user.id},
        {"$set": {
            "password_hash": new_password_hash,
            "password_reset_token": None,
            "password_reset_expires": None,
            "failed_login_attempts": 0,
            "locked_until": None
        }}
    )

    await log_audit(db, user.id, "PASSWORD_RESET_COMPLETED")

    return {"message": "Password reset successfully! You can now log in with your new password."}


# 2FA Endpoints
@router.post("/2fa/setup")
async def setup_2fa(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Setup 2FA for user."""
    users_collection = db.get_collection("users")
    secret = generate_2fa_secret()

    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"two_factor_secret": secret}}
    )

    return {
        "secret": secret,
        "qr_code_url": f"otpauth://totp/CryptoVault:{user_id}?secret={secret}&issuer=CryptoVault"
    }


@router.post("/2fa/verify")
async def verify_2fa(
    data: TwoFactorVerify, 
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Verify 2FA code and enable 2FA if valid."""
    users_collection = db.get_collection("users")

    if len(data.code) != 6 or not data.code.isdigit():
        raise HTTPException(status_code=400, detail="Invalid code format")

    # Get user to retrieve the 2FA secret
    user_doc = await users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    # Check if 2FA secret exists
    secret = user_doc.get("two_factor_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="2FA setup not initiated. Please setup 2FA first.")
    # Verify the TOTP code
    if not verify_2fa_code(secret, data.code):
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Generate backup codes and enable 2FA
    backup_codes = generate_backup_codes()
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {
            "two_factor_enabled": True,
            "backup_codes": backup_codes
        }}
    )

    return {
        "message": "2FA enabled successfully",
        "backup_codes": backup_codes
    }


@router.get("/2fa/status")
async def get_2fa_status(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Get 2FA status."""
    users_collection = db.get_collection("users")
    user_doc = await users_collection.find_one({"id": user_id})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    return {"enabled": user_doc.get("two_factor_enabled", False)}


@router.post("/2fa/disable")
async def disable_2fa(
    data: dict, 
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Disable 2FA."""
    users_collection = db.get_collection("users")
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {
            "two_factor_enabled": False,
            "two_factor_secret": None,
            "backup_codes": []
        }}
    )

    return {"message": "2FA disabled successfully"}


@router.post("/2fa/backup-codes")
async def get_backup_codes(
    user_id: str = Depends(get_current_user_id),
    db = Depends(get_db)
):
    """Generate new backup codes."""
    users_collection = db.get_collection("users")
    backup_codes = generate_backup_codes()
    await users_collection.update_one(
        {"id": user_id},
        {"$set": {"backup_codes": backup_codes}}
    )

    return {"codes": backup_codes}
