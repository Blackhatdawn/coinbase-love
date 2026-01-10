"""
Configuration module with environment variable validation and structured settings.
Follows production best practices with type safety and validation.
"""
import os
import secrets
from typing import Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
from pathlib import Path


# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')


class Settings(BaseModel):
    """Application settings with validation and defaults."""
    
    # MongoDB Configuration
    mongo_url: str = Field(..., env='MONGO_URL')
    db_name: str = Field(..., env='DB_NAME')
    
    # Security Configuration
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env='JWT_SECRET')
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    # CORS Configuration
    cors_origins: str = Field(default="*", env='CORS_ORIGINS')
    
    # Server Configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8001)
    environment: str = Field(default="development", env='ENVIRONMENT')
    
    # MongoDB Connection Pool Settings
    mongo_max_pool_size: int = Field(default=50, env='MONGO_MAX_POOL_SIZE')
    mongo_min_pool_size: int = Field(default=10, env='MONGO_MIN_POOL_SIZE')
    mongo_server_selection_timeout_ms: int = Field(default=5000, env='MONGO_TIMEOUT_MS')
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, env='RATE_LIMIT_PER_MINUTE')
    
    # Email Configuration
    email_service: str = Field(default="mock", env='EMAIL_SERVICE')
    email_from: str = Field(default="noreply@cryptovault.com", env='EMAIL_FROM')
    email_from_name: str = Field(default="CryptoVault", env='EMAIL_FROM_NAME')
    app_url: str = Field(default="http://localhost:3000", env='APP_URL')
    
    # CoinGecko API Configuration
    coingecko_api_key: Optional[str] = Field(default=None, env='COINGECKO_API_KEY')
    use_mock_prices: bool = Field(default=False, env='USE_MOCK_PRICES')
    
    # Redis Configuration (Upstash)
    use_redis: bool = Field(default=True, env='USE_REDIS')
    upstash_redis_rest_url: Optional[str] = Field(default=None, env='UPSTASH_REDIS_REST_URL')
    upstash_redis_rest_token: Optional[str] = Field(default=None, env='UPSTASH_REDIS_REST_TOKEN')
    
    @validator('mongo_url')
    def validate_mongo_url(cls, v):
        if not v or not v.startswith('mongodb'):
            raise ValueError('MONGO_URL must be a valid MongoDB connection string')
        return v
    
    @validator('db_name')
    def validate_db_name(cls, v):
        if not v or len(v) < 3:
            raise ValueError('DB_NAME must be at least 3 characters')
        return v
    
    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters for security')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        allowed = ['development', 'staging', 'production']
        if v not in allowed:
            raise ValueError(f'ENVIRONMENT must be one of: {allowed}')
        return v
    
    @validator('email_service')
    def validate_email_service(cls, v):
        allowed = ['mock', 'sendgrid', 'resend', 'ses', 'smtp']
        if v not in allowed:
            raise ValueError(f'EMAIL_SERVICE must be one of: {allowed}')
        return v
    
    @validator('use_redis', always=True)
    def validate_redis_config(cls, v, values, **kwargs):
        """Ensure Redis URL and token are provided if use_redis is True"""
        # Only validate if use_redis is True
        if not v:
            return v
        # Check if Redis credentials are provided
        upstash_url = values.get('upstash_redis_rest_url')
        upstash_token = values.get('upstash_redis_rest_token')
        if not upstash_url or not upstash_token:
            # Gracefully disable Redis if credentials are missing
            import logging
            logging.warning("⚠️ Redis enabled but credentials missing. Falling back to in-memory cache.")
            return False
        return v
    
    def get_cors_origins_list(self) -> list:
        """Parse CORS origins string into list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(',')]
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


def load_and_validate_settings() -> Settings:
    """
    Load and validate all environment variables.
    Raises detailed errors if validation fails.
    """
    try:
        # Load from environment
        settings_dict = {
            'mongo_url': os.environ.get('MONGO_URL'),
            'db_name': os.environ.get('DB_NAME'),
            'jwt_secret': os.environ.get('JWT_SECRET'),
            'cors_origins': os.environ.get('CORS_ORIGINS', '*'),
            'environment': os.environ.get('ENVIRONMENT', 'development'),
            'mongo_max_pool_size': int(os.environ.get('MONGO_MAX_POOL_SIZE', '50')),
            'mongo_min_pool_size': int(os.environ.get('MONGO_MIN_POOL_SIZE', '10')),
            'mongo_server_selection_timeout_ms': int(os.environ.get('MONGO_TIMEOUT_MS', '5000')),
            'rate_limit_per_minute': int(os.environ.get('RATE_LIMIT_PER_MINUTE', '60')),
            # Email settings
            'email_service': os.environ.get('EMAIL_SERVICE', 'mock'),
            'email_from': os.environ.get('EMAIL_FROM', 'noreply@cryptovault.com'),
            'email_from_name': os.environ.get('EMAIL_FROM_NAME', 'CryptoVault'),
            'app_url': os.environ.get('APP_URL', 'http://localhost:3000'),
            # CoinGecko settings
            'coingecko_api_key': os.environ.get('COINGECKO_API_KEY'),
            'use_mock_prices': os.environ.get('USE_MOCK_PRICES', 'false').lower() == 'true',
            # Redis settings
            'use_redis': os.environ.get('USE_REDIS', 'true').lower() == 'true',
            'upstash_redis_rest_url': os.environ.get('UPSTASH_REDIS_REST_URL'),
            'upstash_redis_rest_token': os.environ.get('UPSTASH_REDIS_REST_TOKEN'),
        }
        
        # Remove None values to use defaults
        settings_dict = {k: v for k, v in settings_dict.items() if v is not None}
        
        settings = Settings(**settings_dict)
        
        # Log successful load (with redaction)
        print("✅ Environment variables loaded successfully:")
        print(f"   MONGO_URL: {settings.mongo_url[:20]}...***")
        print(f"   DB_NAME: {settings.db_name}")
        print(f"   ENVIRONMENT: {settings.environment}")
        print(f"   CORS_ORIGINS: {settings.cors_origins}")
        print(f"   JWT_SECRET: ***[{len(settings.jwt_secret)} chars]***")
        print(f"   MongoDB Pool: {settings.mongo_min_pool_size}-{settings.mongo_max_pool_size}")
        print(f"   Rate Limit: {settings.rate_limit_per_minute} req/min")
        print(f"   Email Service: {settings.email_service}")
        print(f"   App URL: {settings.app_url}")
        print(f"   CoinGecko API: {'configured' if settings.coingecko_api_key else 'not configured'}")
        print(f"   Use Mock Prices: {settings.use_mock_prices}")
        print(f"   Redis: {'enabled' if settings.use_redis else 'disabled'}")
        if settings.use_redis:
            print(f"   Redis URL: {settings.upstash_redis_rest_url[:30]}...***")
        
        return settings
        
    except ValueError as e:
        print(f"❌ Configuration Error: {str(e)}")
        raise SystemExit(1)
    except Exception as e:
        print(f"❌ Failed to load environment variables: {str(e)}")
        raise SystemExit(1)


# Global settings instance
settings = load_and_validate_settings()
