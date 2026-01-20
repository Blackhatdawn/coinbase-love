"""
Configuration module with environment variable validation and structured settings.
Modern Pydantic V2 style using pydantic-settings for auto-loading, type safety, and no deprecations.

Enterprise-grade configuration with:
- Zero hardcoded sensitive values
- Environment-based CORS origins
- Crash-safe validation at startup
- Production-ready defaults
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Load environment variables from .env file in backend directory
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    logger.debug("No backend .env file found at %s - relying on environment variables", env_path)


class EnvironmentValidationError(Exception):
    """Raised when critical environment variables are missing or invalid."""
    pass


# ============================================
# PRODUCTION CORS ORIGINS
# ============================================
# These are the allowed origins for production deployments
# Update these to match your actual deployment URLs

PRODUCTION_CORS_ORIGINS = [
    "https://cryptovault.financial",
    "https://www.cryptovault.financial",
    "https://cryptovault.vercel.app",
    "https://cryptovault-git-main-blackhatdawn.vercel.app",
]

STAGING_CORS_ORIGINS = [
    "https://staging.cryptovault.financial",
    "https://cryptovault-staging.vercel.app",
]

DEVELOPMENT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


def get_default_cors_origins(environment: str) -> str:
    """Get default CORS origins based on environment."""
    if environment == "production":
        return ",".join(PRODUCTION_CORS_ORIGINS)
    elif environment == "staging":
        return ",".join(STAGING_CORS_ORIGINS + DEVELOPMENT_CORS_ORIGINS)
    else:
        # Development - allow all for convenience
        return "*"


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    # MongoDB Configuration
    mongo_url: str
    db_name: str

    # Security Configuration
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    csrf_secret: Optional[str] = None

    # CORS Configuration
    # In production, this should be set to specific frontend origins
    cors_origins: str = "*"
    # Enable cross-site cookies (needed when frontend and API are different origins)
    use_cross_site_cookies: bool = False

    # Server Configuration
    # HOST: Always bind to 0.0.0.0 for container deployments
    host: str = "0.0.0.0"
    # PORT: Use $PORT env var (required by Render, Heroku, etc.) or default to 8001
    port: int = int(os.environ.get("PORT", "8001"))
    environment: str = "development"
    
    # Performance & Security
    request_timeout_seconds: int = 30
    max_request_size_mb: int = 10
    enable_compression: bool = True
    enable_https_redirect: bool = False
    
    # Feature Flags
    enable_email_verification: bool = True
    enable_2fa: bool = False
    enable_api_docs: bool = True

    # MongoDB Connection Pool Settings
    mongo_max_pool_size: int = 50
    mongo_min_pool_size: int = 10
    mongo_server_selection_timeout_ms: int = 5000

    # Rate Limiting
    rate_limit_per_minute: int = 60  # Default rate limit for general endpoints
    rate_limit_auth_per_minute: int = 5  # Stricter limit for authentication endpoints
    rate_limit_signup_per_minute: int = 3  # Very strict limit for signup to prevent abuse
    rate_limit_password_reset_per_minute: int = 2  # Strict limit for password reset
    request_timeout_seconds: int = 30  # Request timeout in seconds
    max_request_size_mb: int = 10  # Maximum request size in MB

    # Email Configuration
    email_service: str = "mock"
    sendgrid_api_key: Optional[str] = None
    email_from: str = "noreply@cryptovault.com"
    email_from_name: str = "CryptoVault"
    app_url: str = "http://localhost:3000"

    # Public Runtime Configuration (exposed via /api/config)
    public_api_url: Optional[str] = None
    public_ws_url: Optional[str] = None
    public_socket_io_path: str = "/socket.io/"
    public_site_name: str = "CryptoVault"
    public_logo_url: Optional[str] = None
    public_support_email: Optional[str] = None
    public_sentry_dsn: Optional[str] = None

    # Cryptocurrency Price API Configuration
    # CoinCap is the primary source (200 req/min free tier)
    coincap_api_key: Optional[str] = None
    
    # Use mock prices for development/testing
    use_mock_prices: bool = False
    
    # NowPayments Configuration
    nowpayments_api_key: Optional[str] = None
    nowpayments_ipn_secret: Optional[str] = None
    nowpayments_sandbox: bool = True
    
    # Firebase Configuration
    firebase_credentials_path: Optional[str] = None
    
    # Email Configuration
    email_verification_url: Optional[str] = None

    # Redis Configuration (Upstash)
    use_redis: bool = True
    upstash_redis_rest_url: Optional[str] = None
    upstash_redis_rest_token: Optional[str] = None

    # Sentry Configuration (Error Tracking)
    sentry_dsn: Optional[str] = None
    sentry_traces_sample_rate: float = 0.1
    sentry_profiles_sample_rate: float = 0.1
    sentry_environment: str = "development"

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars
    )

    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Ensure JWT secret is sufficiently long for security."""
        if len(v) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters long for security')
        return v

    @field_validator('mongo_url')
    @classmethod
    def validate_mongo_url(cls, v: str) -> str:
        """Ensure MongoDB URL is valid."""
        if not v or not (v.startswith('mongodb://') or v.startswith('mongodb+srv://')):
            raise ValueError('MONGO_URL must be a valid MongoDB connection string')
        return v

    @model_validator(mode='after')
    def validate_environment_configuration(self):
        """Validate environment-specific configurations."""
        if self.environment == 'production':
            # CRITICAL: Prevent wildcard CORS with credential-based auth
            if self.cors_origins == '*':
                raise ValueError(
                    "🛑 PRODUCTION ERROR: CORS_ORIGINS cannot be '*' when using credential-based authentication. "
                    "Browsers will reject credentialed requests with wildcard CORS. "
                    "Set CORS_ORIGINS to specific frontend origin(s) in production. "
                    "Example: CORS_ORIGINS=https://app.my-domain.com,https://app-staging.my-domain.com"
                )

            if not self.sentry_dsn:
                logger.warning("⚠️ Sentry DSN not configured in production - error tracking will be disabled")

            if self.use_mock_prices:
                logger.warning("⚠️ Mock prices enabled in production - should use real data")

            if self.email_service == 'mock':
                raise ValueError(
                    "🛑 PRODUCTION ERROR: EMAIL_SERVICE cannot be 'mock'. Configure SendGrid or disable email workflows."
                )

            if self.email_service == 'sendgrid' and not self.sendgrid_api_key:
                raise ValueError(
                    "🛑 PRODUCTION ERROR: SENDGRID_API_KEY must be set when EMAIL_SERVICE=sendgrid."
                )

            if self.use_redis and not self.is_redis_available():
                raise ValueError(
                    "🛑 PRODUCTION ERROR: Redis caching is enabled but UPSTASH credentials are missing. "
                    "Set USE_REDIS=false or provide UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN."
                )

            if not self.app_url.startswith("https://"):
                logger.warning("⚠️ APP_URL should use https:// in production environments")

        if self.email_service == 'sendgrid' and not self.sendgrid_api_key:
            logger.warning(
                "⚠️ EMAIL_SERVICE is set to sendgrid but SENDGRID_API_KEY is missing - defaulting to mock mode"
            )

        # Development environment defaults
        if self.environment == 'development' and self.cors_origins == '*':
            logger.info("✅ CORS set to '*' for development - this allows all origins")

        return self

    def is_redis_available(self) -> bool:
        """Check if Redis is properly configured and should be used."""
        return self.use_redis and bool(self.upstash_redis_rest_url) and bool(self.upstash_redis_rest_token)

    def is_sentry_available(self) -> bool:
        """Check if Sentry is properly configured."""
        return bool(self.sentry_dsn)

    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        if not self.cors_origins:
            return []
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def validate_critical_settings(self) -> List[str]:
        """
        Validate critical settings on startup.
        Returns list of warnings/errors.
        """
        issues = []
        
        # Check MongoDB
        if not self.mongo_url:
            issues.append("CRITICAL: MONGO_URL is not set")
        
        # Check JWT
        if not self.jwt_secret:
            issues.append("CRITICAL: JWT_SECRET is not set")
        elif len(self.jwt_secret) < 32:
            issues.append("WARNING: JWT_SECRET should be at least 32 characters")
        
        # Email configuration
        if self.email_service == 'sendgrid' and not self.sendgrid_api_key:
            issues.append("CRITICAL: SENDGRID_API_KEY is required when EMAIL_SERVICE=sendgrid")

        # Redis configuration
        if self.use_redis and not self.is_redis_available():
            issues.append("WARNING: Redis is enabled but UPSTASH credentials are missing")

        # Check environment
        if self.environment not in ['development', 'staging', 'production']:
            issues.append(f"WARNING: Unknown environment '{self.environment}'")

        return issues


def validate_startup_environment() -> dict:
    """
    Validate environment variables at startup.
    Logs warnings and raises errors for critical issues.
    
    Returns:
        dict: Validation result with status and details
    """
    validation_result = {
        "status": "success",
        "environment": settings.environment,
        "issues": [],
        "warnings": [],
        "validated_at": None
    }
    
    from datetime import datetime
    validation_result["validated_at"] = datetime.utcnow().isoformat()
    
    issues = settings.validate_critical_settings()
    
    for issue in issues:
        if issue.startswith("CRITICAL"):
            logger.critical(issue)
            validation_result["issues"].append(issue)
        else:
            logger.warning(issue)
            validation_result["warnings"].append(issue)
    
    critical_issues = [i for i in issues if i.startswith("CRITICAL")]
    if critical_issues:
        validation_result["status"] = "failed"
        raise EnvironmentValidationError(
            f"Critical configuration issues found: {', '.join(critical_issues)}"
        )
    
    # Professional startup validation message
    logger.info("=" * 60)
    logger.info("🔐 ENVIRONMENT VALIDATED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info(f"   Environment: {settings.environment.upper()}")
    logger.info(f"   Host: {settings.host}")
    logger.info(f"   Port: {settings.port}")
    logger.info(f"   Database: {settings.db_name}")
    logger.info(f"   CORS Origins: {'RESTRICTED' if settings.cors_origins != '*' else 'OPEN (dev mode)'}")
    logger.info(f"   Redis: {'ENABLED' if settings.is_redis_available() else 'DISABLED'}")
    logger.info(f"   Sentry: {'ENABLED' if settings.is_sentry_available() else 'DISABLED'}")
    logger.info(f"   Rate Limit: {settings.rate_limit_per_minute} req/min")
    if validation_result["warnings"]:
        logger.info(f"   Warnings: {len(validation_result['warnings'])}")
    logger.info("=" * 60)
    
    return validation_result


def get_required_env_vars() -> List[str]:
    """
    Get list of required environment variables.
    Used for documentation and validation.
    """
    return [
        "MONGO_URL",
        "DB_NAME", 
        "JWT_SECRET",
    ]


def get_optional_env_vars() -> List[str]:
    """
    Get list of optional environment variables with their purposes.
    """
    return [
        "PORT",                    # Server port (default: 8000)
        "ENVIRONMENT",             # development/staging/production
        "CORS_ORIGINS",            # Comma-separated allowed origins
        "SENDGRID_API_KEY",        # For email functionality
        "SENTRY_DSN",              # For error tracking
        "UPSTASH_REDIS_REST_URL",  # For Redis caching
        "UPSTASH_REDIS_REST_TOKEN",
        "COINCAP_API_KEY",         # For cryptocurrency price data (primary source)
        "PUBLIC_API_URL",          # Base URL exposed to frontend
        "PUBLIC_WS_URL",           # WebSocket base URL exposed to frontend
        "PUBLIC_SOCKET_IO_PATH",   # Socket.IO path exposed to frontend
        "PUBLIC_SITE_NAME",        # Brand name for public config
        "PUBLIC_LOGO_URL",         # Brand logo URL for public config
        "PUBLIC_SUPPORT_EMAIL",    # Support email for public config
        "PUBLIC_SENTRY_DSN",       # Frontend Sentry DSN (public)
    ]


# Global settings instance (auto-loads and validates .env)
try:
    settings = Settings()
    logger.info("✅ Environment variables loaded and validated successfully")
    logger.debug(f"MONGO_URL: {settings.mongo_url[:20]}...***")
    logger.debug(f"DB_NAME: {settings.db_name}")
    logger.debug(f"ENVIRONMENT: {settings.environment}")
    logger.debug(f"CORS_ORIGINS: {settings.cors_origins}")
    logger.debug(f"JWT_SECRET: ***[{len(settings.jwt_secret)} chars]***")
    logger.debug(f"MongoDB Pool: {settings.mongo_min_pool_size}-{settings.mongo_max_pool_size}")
    logger.debug(f"Rate Limit: {settings.rate_limit_per_minute} req/min")
    logger.debug(f"Email Service: {settings.email_service}")
    logger.debug(f"App URL: {settings.app_url}")
    logger.debug(f"CoinCap API: {'configured' if settings.coincap_api_key else 'not configured (using free tier)'}")
    logger.debug(f"Use Mock Prices: {settings.use_mock_prices}")
    redis_status = "enabled" if settings.is_redis_available() else "disabled"
    logger.debug(f"Redis: {redis_status}")
    if settings.is_redis_available():
        logger.debug(f"Redis URL: {settings.upstash_redis_rest_url[:30]}...***")
    sentry_status = "enabled" if settings.is_sentry_available() else "disabled"
    logger.debug(f"Sentry: {sentry_status}")
except Exception as e:
    logger.critical(f"❌ Failed to load/validate settings: {str(e)}")
    raise
