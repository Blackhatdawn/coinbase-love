"""
Enterprise-Grade Configuration Management for CryptoVault Backend

Uses pydantic-settings for robust environment variable handling with:
- Type validation
- Default values
- Custom validators
- Environment variable override support
- Production-ready startup validation

Usage:
    from config import settings, validate_startup_environment
    
    # Validate on startup
    validate_startup_environment()
    
    print(settings.mongo_url)
    print(settings.upstash_redis_rest_url)
"""

from typing import Optional, List
from functools import lru_cache
from pathlib import Path

from pydantic import Field, validator, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings using pydantic BaseSettings.
    
    Environment variables override defaults.
    Priority order:
    1. Environment variables
    2. .env file values
    3. Hardcoded defaults
    """

    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    app_name: str = Field(default="CryptoVault", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    app_url: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )

    # ============================================
    # SERVER CONFIGURATION
    # ============================================
    host: str = Field(default="0.0.0.0", description="Server host binding")
    port: int = Field(
        default=8000,
        description="Server port (falls back to PORT env var for Render/Railway)"
    )
    workers: int = Field(default=4, description="Number of Gunicorn workers for production")

    # ============================================
    # MONGODB CONFIGURATION
    # ============================================
    mongo_url: str = Field(
        default="mongodb://localhost:27017/cryptovault",
        description="MongoDB Atlas connection URL"
    )
    db_name: str = Field(default="cryptovault", description="Database name")
    mongo_max_pool_size: int = Field(default=10, description="MongoDB connection pool size")
    mongo_timeout_ms: int = Field(default=5000, description="MongoDB connection timeout in ms")

    # ============================================
    # REDIS / CACHE CONFIGURATION
    # ============================================
    use_redis: bool = Field(default=True, description="Enable Redis caching")
    upstash_redis_rest_url: Optional[str] = Field(
        default=None,
        description="Upstash Redis REST API URL (for serverless environments)"
    )
    upstash_redis_rest_token: Optional[str] = Field(
        default=None,
        description="Upstash Redis REST API token"
    )
    redis_url: Optional[str] = Field(
        default=None,
        description="Traditional Redis URL (if not using Upstash)"
    )
    redis_prefix: str = Field(default="cryptovault:", description="Redis key prefix")

    # ============================================
    # SECURITY & AUTHENTICATION
    # ============================================
    jwt_secret: SecretStr = Field(
        default="change-me-in-production",
        description="JWT signing secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration in days")
    
    csrf_secret: SecretStr = Field(
        default="change-me-in-production",
        description="CSRF protection secret"
    )
    use_cross_site_cookies: bool = Field(
        default=False,
        description="Enable cross-site cookies for development"
    )

    # ============================================
    # CORS CONFIGURATION
    # ============================================
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins"
    )

    # ============================================
    # EMAIL CONFIGURATION
    # ============================================
    email_service: str = Field(default="sendgrid", description="Email service provider")
    sendgrid_api_key: Optional[SecretStr] = Field(
        default=None,
        description="SendGrid API key"
    )
    email_from: str = Field(
        default="noreply@cryptovault.financial",
        description="Default sender email"
    )
    email_from_name: str = Field(
        default="CryptoVault Financial",
        description="Default sender name"
    )
    email_verification_url: str = Field(
        default="https://cryptovault.financial/verify",
        description="Email verification URL"
    )

    # ============================================
    # EXTERNAL CRYPTO SERVICES
    # ============================================
    coincap_api_key: Optional[str] = Field(
        default=None,
        description="CoinCap API key"
    )
    coincap_rate_limit: int = Field(default=50, description="CoinCap API rate limit")
    use_mock_prices: bool = Field(default=False, description="Use mock price data for testing")
    
    # NowPayments (Payment Processing)
    nowpayments_api_key: Optional[SecretStr] = Field(
        default=None,
        description="NowPayments API key"
    )
    nowpayments_ipn_secret: Optional[SecretStr] = Field(
        default=None,
        description="NowPayments IPN secret"
    )
    nowpayments_sandbox: bool = Field(default=False, description="Use NowPayments sandbox")

    # ============================================
    # FIREBASE CONFIGURATION
    # ============================================
    firebase_credentials_path: Optional[str] = Field(
        default=None,
        description="Path to Firebase credentials JSON file"
    )
    firebase_credential: Optional[str] = Field(
        default=None,
        description="Firebase credentials as JSON string (alternative to file)"
    )

    # ============================================
    # ERROR TRACKING (Sentry)
    # ============================================
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    sentry_traces_sample_rate: float = Field(
        default=0.1,
        description="Sentry tracing sample rate (0.0-1.0)"
    )
    sentry_profiles_sample_rate: float = Field(
        default=0.1,
        description="Sentry profiling sample rate (0.0-1.0)"
    )

    # ============================================
    # RATE LIMITING
    # ============================================
    rate_limit_per_minute: int = Field(
        default=60,
        description="Requests allowed per minute"
    )

    # ============================================
    # LOGGING
    # ============================================
    log_level: str = Field(default="INFO", description="Logging level")

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # ============================================
    # VALIDATORS
    # ============================================

    @validator("port", pre=True)
    def validate_port(cls, v):
        """
        Validate port number. Supports PORT env var for Render/Railway compatibility.
        """
        if v is None:
            return 8000
        port = int(v)
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got {port}")
        return port

    @validator("cors_origins", pre=True)
    def validate_cors_origins(cls, v):
        """Parse comma-separated CORS origins into a list."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return []

    @validator("environment")
    def validate_environment(cls, v):
        """Ensure environment is one of valid values."""
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}, got {v}")
        return v.lower()

    @validator("log_level")
    def validate_log_level(cls, v):
        """Ensure log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}, got {v}")
        return v.upper()

    # ============================================
    # PROPERTIES
    # ============================================

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.environment == "staging"

    def get_cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.cors_origins, str):
            return [origin.strip() for origin in self.cors_origins.split(",")]
        return self.cors_origins

    def is_sentry_available(self) -> bool:
        """Check if Sentry is configured."""
        return bool(self.sentry_dsn)

    def get_redis_url(self) -> Optional[str]:
        """
        Get Redis URL from Upstash REST API or traditional Redis.
        
        Priority:
        1. Upstash REST API (for serverless)
        2. Traditional Redis URL
        """
        if self.upstash_redis_rest_url and self.upstash_redis_rest_token:
            return self.upstash_redis_rest_url
        return self.redis_url

    def to_dict(self, include_secrets: bool = False) -> dict:
        """
        Convert settings to dictionary.
        
        Args:
            include_secrets: If True, include secret values (use with caution)
        
        Returns:
            Dictionary representation of settings
        """
        data = self.model_dump(exclude_unset=False)
        
        if not include_secrets:
            # Redact secrets
            secret_fields = {
                "jwt_secret",
                "csrf_secret",
                "sendgrid_api_key",
                "nowpayments_api_key",
                "nowpayments_ipn_secret",
                "upstash_redis_rest_token",
                "firebase_credential"
            }
            for field in secret_fields:
                if field in data:
                    data[field] = "***REDACTED***"
        
        return data

    def __repr__(self) -> str:
        """String representation of settings."""
        return (
            f"<Settings "
            f"environment={self.environment} "
            f"app={self.app_name} "
            f"v={self.app_version} "
            f"host={self.host}:{self.port}>"
        )


# ============================================
# GLOBAL SETTINGS INSTANCE
# ============================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure only one instance is created.
    """
    return Settings()


# Create global settings instance
settings = get_settings()


# ============================================
# STARTUP VALIDATION
# ============================================

def validate_startup_environment() -> dict:
    """
    Validate all critical environment variables on startup.
    
    This function should be called in your FastAPI startup event.
    Raises ValueError if critical configuration is missing in production.
    
    Returns:
        Dictionary with validation results
    """
    critical_vars = {
        "jwt_secret": settings.jwt_secret,
        "csrf_secret": settings.csrf_secret,
        "mongo_url": settings.mongo_url,
    }

    missing_vars = []
    for var_name, var_value in critical_vars.items():
        if not var_value or var_value == "change-me-in-production":
            if settings.is_production:
                missing_vars.append(var_name)

    if missing_vars:
        error_msg = (
            f"❌ STARTUP FAILED: Critical environment variables not configured:\n"
            f"   {', '.join(missing_vars)}\n\n"
            f"   Please set these in your environment or .env file:\n"
        )
        for var in missing_vars:
            error_msg += f"   - {var.upper()}\n"
        raise ValueError(error_msg)

    # Log successful validation
    print("✅ Environment Validated")
    print(f"   Environment: {settings.environment}")
    print(f"   App: {settings.app_name} v{settings.app_version}")
    print(f"   Host: {settings.host}:{settings.port}")
    print(f"   Database: {settings.db_name}")
    print(f"   Redis: {'Enabled (Upstash)' if settings.upstash_redis_rest_url else 'Enabled (Standard)' if settings.redis_url else 'Disabled'}")
    print(f"   Email Service: {settings.email_service}")
    print(f"   CORS Origins: {', '.join(settings.get_cors_origins_list())}")
    if settings.is_sentry_available():
        print(f"   Sentry: Enabled")
    
    return {
        "status": "success",
        "environment": settings.environment,
        "app_name": settings.app_name,
        "database": settings.db_name
    }


# ============================================
# TEST UTILITIES
# ============================================

def test_configuration() -> None:
    """
    Test configuration loading and display all settings.
    Run with: python -m backend.config
    """
    print("\n" + "=" * 70)
    print("CRYPTOVAULT CONFIGURATION TEST")
    print("=" * 70)

    print("\nApplication:")
    print(f"  Name: {settings.app_name}")
    print(f"  Version: {settings.app_version}")
    print(f"  Environment: {settings.environment}")
    print(f"  Debug: {settings.debug}")
    print(f"  Frontend URL: {settings.app_url}")

    print("\nServer:")
    print(f"  Host: {settings.host}")
    print(f"  Port: {settings.port}")
    print(f"  Workers: {settings.workers}")

    print("\nDatabase (MongoDB):")
    print(f"  URL: {settings.mongo_url[:60]}...")
    print(f"  Database: {settings.db_name}")
    print(f"  Max Pool Size: {settings.mongo_max_pool_size}")
    print(f"  Timeout: {settings.mongo_timeout_ms}ms")

    print("\nCache (Redis):")
    if settings.use_redis:
        if settings.upstash_redis_rest_url:
            print(f"  Provider: Upstash REST API")
            print(f"  URL: {settings.upstash_redis_rest_url[:60]}...")
        elif settings.redis_url:
            print(f"  Provider: Standard Redis")
            print(f"  URL: {settings.redis_url[:60]}...")
        else:
            print(f"  Status: Redis disabled (use_redis=false)")
    else:
        print(f"  Status: Redis disabled")
    print(f"  Prefix: {settings.redis_prefix}")

    print("\nSecurity:")
    print(f"  JWT Algorithm: {settings.jwt_algorithm}")
    print(f"  JWT Secret: {'✓ Set' if settings.jwt_secret else '✗ Not set'}")
    print(f"  Access Token Expiry: {settings.access_token_expire_minutes} minutes")
    print(f"  Refresh Token Expiry: {settings.refresh_token_expire_days} days")
    print(f"  CSRF Secret: {'✓ Set' if settings.csrf_secret else '✗ Not set'}")

    print("\nCORS:")
    print(f"  Origins: {', '.join(settings.get_cors_origins_list())}")

    print("\nEmail:")
    print(f"  Service: {settings.email_service}")
    print(f"  From: {settings.email_from}")
    print(f"  From Name: {settings.email_from_name}")
    print(f"  Verification URL: {settings.email_verification_url}")
    if settings.sendgrid_api_key:
        print(f"  SendGrid: ✓ Configured")

    print("\nExternal Services:")
    print(f"  CoinCap API: {'✓ Configured' if settings.coincap_api_key else '✗ Not configured'}")
    print(f"  NowPayments: {'✓ Configured' if settings.nowpayments_api_key else '✗ Not configured'}")
    print(f"  Firebase: {'✓ Configured' if (settings.firebase_credentials_path or settings.firebase_credential) else '✗ Not configured'}")
    print(f"  Mock Prices: {settings.use_mock_prices}")

    print("\nRate Limiting:")
    print(f"  Requests/Minute: {settings.rate_limit_per_minute}")

    print("\nMonitoring:")
    print(f"  Sentry: {'✓ Enabled' if settings.is_sentry_available() else '✗ Disabled'}")
    if settings.is_sentry_available():
        print(f"  Traces Sample Rate: {settings.sentry_traces_sample_rate}")
        print(f"  Profiles Sample Rate: {settings.sentry_profiles_sample_rate}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    test_configuration()
