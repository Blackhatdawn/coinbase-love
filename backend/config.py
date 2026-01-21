"""
Environment Configuration Management for CryptoVault Backend

This module loads and validates environment variables from .env file.
Uses python-dotenv to load from .env, with fallback to OS environment variables.

Usage:
    from config import settings
    
    print(settings.DATABASE_URL)
    print(settings.REDIS_URL)
    print(settings.JWT_SECRET)
"""

import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    raise ImportError(
        "python-dotenv is required. Install with: pip install python-dotenv"
    )


class Settings:
    """
    Application settings loaded from environment variables.
    
    Priority order:
    1. .env file in project root or backend directory
    2. Environment variables
    3. Hardcoded defaults (for development only)
    """

    def __init__(self):
        """Initialize settings by loading .env file"""
        self._load_env_file()
        self._validate_required_vars()

    def _load_env_file(self) -> None:
        """
        Load environment variables from .env file.
        
        Searches in order:
        1. ./backend/.env
        2. ./.env
        3. ~/.env (home directory)
        """
        env_paths = [
            Path(__file__).parent / ".env",  # backend/.env
            Path.cwd() / ".env",  # project root .env
            Path.home() / ".env",  # home directory .env
        ]

        loaded_from = None
        for env_path in env_paths:
            if env_path.exists():
                print(f"✅ Loading environment from: {env_path}")
                load_dotenv(env_path, override=True)
                loaded_from = env_path
                break

        if loaded_from is None:
            print(
                "⚠️ Warning: No .env file found. Using system environment variables or defaults."
            )
        else:
            print(f"✅ Environment loaded from: {loaded_from}")

    def _validate_required_vars(self) -> None:
        """Validate that required environment variables are set"""
        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "JWT_SECRET",
            "CORS_ORIGINS",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars and os.getenv("ENVIRONMENT", "development") == "production":
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please set these in your .env file or environment."
            )
        elif missing_vars:
            print(f"⚠️ Missing optional variables: {', '.join(missing_vars)}")

    # ============================================
    # APPLICATION SETTINGS
    # ============================================

    @property
    def APP_NAME(self) -> str:
        return os.getenv("APP_NAME", "CryptoVault")

    @property
    def APP_VERSION(self) -> str:
        return os.getenv("APP_VERSION", "2.0.0")

    @property
    def ENVIRONMENT(self) -> str:
        """Current environment: development, staging, production"""
        return os.getenv("ENVIRONMENT", "development")

    @property
    def DEBUG(self) -> bool:
        """Debug mode flag"""
        return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"

    @property
    def IS_DEVELOPMENT(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"

    # ============================================
    # SERVER CONFIGURATION
    # ============================================

    @property
    def HOST(self) -> str:
        return os.getenv("HOST", "0.0.0.0")

    @property
    def PORT(self) -> int:
        return int(os.getenv("PORT", "8000"))

    @property
    def WORKERS(self) -> int:
        return int(os.getenv("WORKERS", "4"))

    @property
    def SERVER_URL(self) -> str:
        return os.getenv("SERVER_URL", f"http://{self.HOST}:{self.PORT}")

    @property
    def PUBLIC_SERVER_URL(self) -> str:
        return os.getenv(
            "PUBLIC_SERVER_URL", "https://api.cryptovault.com"
        )

    # ============================================
    # DATABASE CONFIGURATION
    # ============================================

    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL connection URL"""
        return os.getenv(
            "DATABASE_URL",
            "postgresql://user:password@localhost:5432/cryptovault",
        )

    @property
    def DB_POOL_SIZE(self) -> int:
        return int(os.getenv("DB_POOL_SIZE", "20"))

    @property
    def DB_MAX_OVERFLOW(self) -> int:
        return int(os.getenv("DB_MAX_OVERFLOW", "10"))

    @property
    def DB_POOL_TIMEOUT(self) -> int:
        return int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # ============================================
    # REDIS / CACHE CONFIGURATION
    # ============================================

    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL"""
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")

    @property
    def REDIS_PREFIX(self) -> str:
        return os.getenv("REDIS_PREFIX", "cryptovault:")

    # ============================================
    # SECURITY & AUTHENTICATION
    # ============================================

    @property
    def JWT_SECRET(self) -> str:
        """JWT secret key for signing tokens"""
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret and self.IS_PRODUCTION:
            raise ValueError(
                "JWT_SECRET must be set in .env or environment for production"
            )
        return jwt_secret or "change-me-in-production"

    @property
    def JWT_EXPIRATION_HOURS(self) -> int:
        return int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    @property
    def JWT_REFRESH_EXPIRATION_DAYS(self) -> int:
        return int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

    @property
    def CSRF_SECRET(self) -> str:
        """CSRF secret for token generation"""
        csrf_secret = os.getenv("CSRF_SECRET")
        if not csrf_secret and self.IS_PRODUCTION:
            raise ValueError(
                "CSRF_SECRET must be set in .env or environment for production"
            )
        return csrf_secret or "change-me-in-production"

    @property
    def PASSWORD_ALGORITHM(self) -> str:
        return os.getenv("PASSWORD_ALGORITHM", "bcrypt")

    # ============================================
    # CORS CONFIGURATION
    # ============================================

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """List of allowed CORS origins"""
        origins_str = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000",
        )
        return [origin.strip() for origin in origins_str.split(",")]

    # ============================================
    # EMAIL CONFIGURATION
    # ============================================

    @property
    def SMTP_HOST(self) -> str:
        return os.getenv("SMTP_HOST", "smtp.gmail.com")

    @property
    def SMTP_PORT(self) -> int:
        return int(os.getenv("SMTP_PORT", "587"))

    @property
    def SMTP_USERNAME(self) -> str:
        return os.getenv("SMTP_USERNAME", "")

    @property
    def SMTP_PASSWORD(self) -> str:
        return os.getenv("SMTP_PASSWORD", "")

    @property
    def EMAIL_FROM(self) -> str:
        return os.getenv("EMAIL_FROM", "noreply@cryptovault.com")

    @property
    def EMAIL_SUPPORT(self) -> str:
        return os.getenv("EMAIL_SUPPORT", "support@cryptovault.com")

    # ============================================
    # SENTRY CONFIGURATION
    # ============================================

    @property
    def SENTRY_DSN(self) -> Optional[str]:
        return os.getenv("SENTRY_DSN")

    @property
    def SENTRY_ENVIRONMENT(self) -> str:
        return os.getenv("SENTRY_ENVIRONMENT", self.ENVIRONMENT)

    @property
    def SENTRY_TRACES_SAMPLE_RATE(self) -> float:
        return float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1"))

    # ============================================
    # EXTERNAL SERVICES
    # ============================================

    @property
    def CRYPTO_API_KEY(self) -> str:
        return os.getenv("CRYPTO_API_KEY", "")

    @property
    def CRYPTO_API_BASE_URL(self) -> str:
        return os.getenv(
            "CRYPTO_API_BASE_URL", "https://api.coingecko.com/api/v3"
        )

    @property
    def ETH_RPC_URL(self) -> str:
        return os.getenv("ETH_RPC_URL", "https://mainnet.infura.io/v3/")

    @property
    def POLYGON_RPC_URL(self) -> str:
        return os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")

    @property
    def SEPOLIA_RPC_URL(self) -> str:
        return os.getenv("SEPOLIA_RPC_URL", "https://sepolia.infura.io/v3/")

    # ============================================
    # FEATURE FLAGS
    # ============================================

    @property
    def FEATURE_2FA_ENABLED(self) -> bool:
        return os.getenv("FEATURE_2FA_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    @property
    def FEATURE_DEPOSITS_ENABLED(self) -> bool:
        return os.getenv("FEATURE_DEPOSITS_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    @property
    def FEATURE_WITHDRAWALS_ENABLED(self) -> bool:
        return os.getenv("FEATURE_WITHDRAWALS_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    @property
    def FEATURE_TRADING_ENABLED(self) -> bool:
        return os.getenv("FEATURE_TRADING_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    @property
    def FEATURE_STAKING_ENABLED(self) -> bool:
        return os.getenv("FEATURE_STAKING_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    # ============================================
    # RATE LIMITING
    # ============================================

    @property
    def RATE_LIMIT_ENABLED(self) -> bool:
        return os.getenv("RATE_LIMIT_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    @property
    def RATE_LIMIT_REQUESTS_PER_MINUTE(self) -> int:
        return int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))

    @property
    def RATE_LIMIT_REQUESTS_PER_HOUR(self) -> int:
        return int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000"))

    # ============================================
    # LOGGING CONFIGURATION
    # ============================================

    @property
    def LOG_LEVEL(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def LOG_FORMAT(self) -> str:
        return os.getenv("LOG_FORMAT", "json")

    # ============================================
    # WORKER / BACKGROUND JOBS
    # ============================================

    @property
    def CELERY_BROKER_URL(self) -> str:
        return os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

    # ============================================
    # MONITORING & OBSERVABILITY
    # ============================================

    @property
    def HEALTH_CHECK_ENABLED(self) -> bool:
        return os.getenv("HEALTH_CHECK_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    @property
    def METRICS_ENABLED(self) -> bool:
        return os.getenv("METRICS_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    @property
    def METRICS_PORT(self) -> int:
        return int(os.getenv("METRICS_PORT", "9090"))

    # ============================================
    # UTILITY METHODS
    # ============================================

    def __repr__(self) -> str:
        """String representation of settings"""
        return (
            f"<Settings environment={self.ENVIRONMENT} "
            f"app={self.APP_NAME} v{self.APP_VERSION}>"
        )

    def to_dict(self) -> dict:
        """
        Convert settings to dictionary (excludes secrets).
        
        Useful for logging and debugging.
        """
        return {
            "APP_NAME": self.APP_NAME,
            "APP_VERSION": self.APP_VERSION,
            "ENVIRONMENT": self.ENVIRONMENT,
            "DEBUG": self.DEBUG,
            "HOST": self.HOST,
            "PORT": self.PORT,
            "SERVER_URL": self.PUBLIC_SERVER_URL,
            "CORS_ORIGINS": self.CORS_ORIGINS,
            "LOG_LEVEL": self.LOG_LEVEL,
            "RATE_LIMIT_ENABLED": self.RATE_LIMIT_ENABLED,
            "SENTRY_ENABLED": bool(self.SENTRY_DSN),
            # Secrets are intentionally excluded
        }


# Create global settings instance
settings = Settings()


def test_env_loading():
    """
    Test that environment variables are loaded correctly.
    Run this to verify .env file setup.
    """
    print("\n" + "=" * 60)
    print("ENVIRONMENT CONFIGURATION TEST")
    print("=" * 60)
    print(f"\nSettings instance: {settings}\n")

    print("Application:")
    print(f"  Name: {settings.APP_NAME}")
    print(f"  Version: {settings.APP_VERSION}")
    print(f"  Environment: {settings.ENVIRONMENT}")
    print(f"  Debug: {settings.DEBUG}")

    print("\nServer:")
    print(f"  Host: {settings.HOST}")
    print(f"  Port: {settings.PORT}")
    print(f"  Public URL: {settings.PUBLIC_SERVER_URL}")

    print("\nDatabase:")
    print(f"  URL: {settings.DATABASE_URL[:50]}...")
    print(f"  Pool Size: {settings.DB_POOL_SIZE}")

    print("\nCache:")
    print(f"  Redis URL: {settings.REDIS_URL[:50]}...")

    print("\nSecurity:")
    print(f"  JWT Secret: {'✓ Set' if settings.JWT_SECRET else '✗ Not set'}")
    print(f"  JWT Expiration: {settings.JWT_EXPIRATION_HOURS} hours")

    print("\nCORS:")
    print(f"  Allowed Origins: {settings.CORS_ORIGINS}")

    print("\nMonitoring:")
    print(f"  Sentry: {'✓ Enabled' if settings.SENTRY_DSN else '✗ Disabled'}")
    print(f"  Metrics: {'✓ Enabled' if settings.METRICS_ENABLED else '✗ Disabled'}")

    print("\nFeatures:")
    print(f"  2FA: {'✓ Enabled' if settings.FEATURE_2FA_ENABLED else '✗ Disabled'}")
    print(
        f"  Deposits: {'✓ Enabled' if settings.FEATURE_DEPOSITS_ENABLED else '✗ Disabled'}"
    )
    print(
        f"  Withdrawals: {'✓ Enabled' if settings.FEATURE_WITHDRAWALS_ENABLED else '✗ Disabled'}"
    )
    print(
        f"  Trading: {'✓ Enabled' if settings.FEATURE_TRADING_ENABLED else '✗ Disabled'}"
    )
    print(
        f"  Staking: {'✓ Enabled' if settings.FEATURE_STAKING_ENABLED else '✗ Disabled'}"
    )

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    # Run test when executed directly
    test_env_loading()
