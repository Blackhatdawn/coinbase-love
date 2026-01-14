"""
Configuration module with environment variable validation and structured settings.
Modern Pydantic V2 style using pydantic-settings for auto-loading, type safety, and no deprecations.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

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

    # CORS Configuration
    cors_origins: str = "*"

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8001
    environment: str = "development"

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
    email_from: str = "noreply@cryptovault.com"
    email_from_name: str = "CryptoVault"
    app_url: str = "http://localhost:3000"

    # CoinGecko API Configuration
    coingecko_api_key: Optional[str] = None
    use_mock_prices: bool = False

    # Redis Configuration (Upstash)
    use_redis: bool = True
    upstash_redis_rest_url: Optional[str] = None
    upstash_redis_rest_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore unknown env vars
        env_prefix="CRYPTOVAULT_",  # Add prefix for environment variables
    )

    def is_redis_available(self) -> bool:
        """Check if Redis is properly configured and should be used."""
        return self.use_redis and bool(self.upstash_redis_rest_url) and bool(self.upstash_redis_rest_token)

    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


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
    logger.debug(f"CoinGecko API: {'configured' if settings.coingecko_api_key else 'not configured'}")
    logger.debug(f"Use Mock Prices: {settings.use_mock_prices}")
    redis_status = "enabled" if settings.is_redis_available() else "disabled"
    logger.debug(f"Redis: {redis_status}")
    if settings.is_redis_available():
        logger.debug(f"Redis URL: {settings.upstash_redis_rest_url[:30]}...***")
except Exception as e:
    logger.critical(f"❌ Failed to load/validate settings: {str(e)}")
    raise
