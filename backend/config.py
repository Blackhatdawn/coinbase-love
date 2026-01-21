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
    
    print(settings.database_url)
    print(settings.redis_url)
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
    1. Environment variables (with CRYPTOVAULT_ prefix optional)
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

    # ============================================
    # SERVER CONFIGURATION
    # ============================================
    host: str = Field(default="0.0.0.0", description="Server host binding")
    port: int = Field(
        default=8000,
        description="Server port (falls back to PORT env var for Render/Railway)"
    )
    workers: int = Field(default=4, description="Number of Gunicorn workers for production")
    server_url: str = Field(
        default="http://localhost:8000",
        description="Local server URL"
    )
    public_server_url: str = Field(
        default="https://api.cryptovault.com",
        description="Public-facing API URL"
    )

    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    database_url: str = Field(
        default="mongodb://localhost:27017/cryptovault",
        description="MongoDB connection URL"
    )
    db_pool_size: int = Field(default=20, description="Database connection pool size")
    db_max_overflow: int = Field(default=10, description="Max overflow connections")
    db_pool_timeout: int = Field(default=30, description="Connection timeout in seconds")

    # ============================================
    # REDIS / CACHE CONFIGURATION
    # ============================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_prefix: str = Field(default="cryptovault:", description="Redis key prefix")

    # ============================================
    # SECURITY & AUTHENTICATION
    # ============================================
    jwt_secret: SecretStr = Field(
        default="change-me-in-production-use-secure-random-string",
        description="JWT signing secret key"
    )
    jwt_expiration_hours: int = Field(default=24, description="JWT token expiration in hours")
    jwt_refresh_expiration_days: int = Field(
        default=7,
        description="Refresh token expiration in days"
    )
    csrf_secret: SecretStr = Field(
        default="change-me-in-production-use-secure-random-string",
        description="CSRF protection secret"
    )
    password_algorithm: str = Field(
        default="bcrypt",
        description="Password hashing algorithm"
    )

    # ============================================
    # CORS CONFIGURATION
    # ============================================
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins"
    )
    cors_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods for CORS"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        description="Allowed headers for CORS"
    )

    # ============================================
    # EMAIL CONFIGURATION
    # ============================================
    smtp_host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_username: str = Field(default="", description="SMTP username")
    smtp_password: SecretStr = Field(default="", description="SMTP password")
    email_from: str = Field(
        default="noreply@cryptovault.com",
        description="Default sender email"
    )
    email_support: str = Field(
        default="support@cryptovault.com",
        description="Support email address"
    )

    # ============================================
    # ERROR TRACKING (Sentry)
    # ============================================
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    sentry_environment: Optional[str] = Field(
        default=None,
        description="Sentry environment name"
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
    # EXTERNAL SERVICES
    # ============================================
    crypto_api_key: str = Field(default="", description="Cryptocurrency API key")
    crypto_api_base_url: str = Field(
        default="https://api.coingecko.com/api/v3",
        description="Cryptocurrency API base URL"
    )
    eth_rpc_url: str = Field(
        default="https://mainnet.infura.io/v3/",
        description="Ethereum RPC endpoint"
    )
    polygon_rpc_url: str = Field(
        default="https://polygon-rpc.com",
        description="Polygon RPC endpoint"
    )
    sepolia_rpc_url: str = Field(
        default="https://sepolia.infura.io/v3/",
        description="Sepolia testnet RPC endpoint"
    )

    # ============================================
    # FEATURE FLAGS
    # ============================================
    feature_2fa_enabled: bool = Field(default=True, description="Enable two-factor authentication")
    feature_deposits_enabled: bool = Field(default=True, description="Enable deposits")
    feature_withdrawals_enabled: bool = Field(default=True, description="Enable withdrawals")
    feature_trading_enabled: bool = Field(default=True, description="Enable trading")
    feature_staking_enabled: bool = Field(default=False, description="Enable staking")

    # ============================================
    # RATE LIMITING
    # ============================================
    rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
    rate_limit_requests_per_minute: int = Field(
        default=60,
        description="Requests allowed per minute"
    )
    rate_limit_requests_per_hour: int = Field(
        default=1000,
        description="Requests allowed per hour"
    )

    # ============================================
    # LOGGING
    # ============================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or text")

    # ============================================
    # BACKGROUND JOBS (Celery)
    # ============================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL"
    )

    # ============================================
    # MONITORING & OBSERVABILITY
    # ============================================
    health_check_enabled: bool = Field(default=True, description="Enable health checks")
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics server port")

    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        # Support both with and without CRYPTOVAULT_ prefix
        # env_prefix="CRYPTOVAULT_",  # Optional: use prefix for namespace
        extra="ignore",  # Ignore extra environment variables
    )

    # ============================================
    # VALIDATORS
    # ============================================

    @validator("port", pre=True)
    def validate_port(cls, v):
        """
        Validate port number. Supports PORT env var for Render/Railway compatibility.
        Falls back to CRYPTOVAULT_PORT or CRYPTOVAULT_SERVER_PORT.
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
            secret_fields = {"jwt_secret", "csrf_secret", "smtp_password"}
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
            f"v{self.app_version} "
            f"host={self.host} "
            f"port={self.port}>"
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

def validate_startup_environment() -> None:
    """
    Validate all critical environment variables on startup.
    
    This function should be called in your FastAPI startup event.
    Raises ValueError if critical configuration is missing in production.
    """
    critical_vars = {
        "jwt_secret": settings.jwt_secret,
        "csrf_secret": settings.csrf_secret,
        "database_url": settings.database_url,
        "redis_url": settings.redis_url,
    }

    missing_vars = []
    for var_name, var_value in critical_vars.items():
        if not var_value or var_value == "change-me-in-production-use-secure-random-string":
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
    print(f"   Database: {settings.database_url[:50]}...")
    print(f"   Redis: {settings.redis_url[:50]}...")
    print(f"   CORS Origins: {', '.join(settings.get_cors_origins_list())}")
    if settings.is_sentry_available():
        print(f"   Sentry: Enabled ({settings.sentry_environment})")


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

    print("\nServer:")
    print(f"  Host: {settings.host}")
    print(f"  Port: {settings.port}")
    print(f"  Workers: {settings.workers}")
    print(f"  Public URL: {settings.public_server_url}")

    print("\nDatabase:")
    print(f"  URL: {settings.database_url[:60]}...")
    print(f"  Pool Size: {settings.db_pool_size}")
    print(f"  Max Overflow: {settings.db_max_overflow}")

    print("\nCache (Redis):")
    print(f"  URL: {settings.redis_url[:60]}...")
    print(f"  Prefix: {settings.redis_prefix}")

    print("\nSecurity:")
    print(f"  JWT Secret: {'✓ Set' if settings.jwt_secret else '✗ Not set'}")
    print(f"  JWT Expiration: {settings.jwt_expiration_hours} hours")
    print(f"  CSRF Secret: {'✓ Set' if settings.csrf_secret else '✗ Not set'}")

    print("\nCORS:")
    print(f"  Origins: {', '.join(settings.get_cors_origins_list())}")
    print(f"  Credentials: {settings.cors_credentials}")
    print(f"  Methods: {', '.join(settings.cors_methods)}")

    print("\nEmail:")
    print(f"  SMTP Host: {settings.smtp_host}:{settings.smtp_port}")
    print(f"  From: {settings.email_from}")
    print(f"  Support: {settings.email_support}")

    print("\nMonitoring:")
    print(f"  Sentry: {'✓ Enabled' if settings.is_sentry_available() else '✗ Disabled'}")
    print(f"  Metrics: {'✓ Enabled' if settings.metrics_enabled else '✗ Disabled'}")
    print(f"  Health Checks: {'✓ Enabled' if settings.health_check_enabled else '✗ Disabled'}")

    print("\nFeatures:")
    print(f"  2FA: {'✓' if settings.feature_2fa_enabled else '✗'}")
    print(f"  Deposits: {'✓' if settings.feature_deposits_enabled else '✗'}")
    print(f"  Withdrawals: {'✓' if settings.feature_withdrawals_enabled else '✗'}")
    print(f"  Trading: {'✓' if settings.feature_trading_enabled else '✗'}")
    print(f"  Staking: {'✓' if settings.feature_staking_enabled else '✗'}")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    test_configuration()
