"""
Enhanced Configuration Management for Multi-Platform Deployment

Design Principles:
- Backward Compatibility: All existing configurations continue to work
- Progressive Enhancement: New features activate with new environment variables
- Clean Architecture: Separation of concerns, dependency inversion
- SOLID: Single responsibility, interface segregation

Platform Support:
- Fly.io (Legacy): PUBLIC_API_URL, port (lowercase)
- Render.com (New): RENDER_EXTERNAL_URL, PORT (uppercase)
- Local Development: Intelligent defaults

Zero-Downtime Guarantee:
This module is 100% backward compatible with existing config.py.
It adds new functionality while preserving all existing behavior.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from functools import lru_cache
from pathlib import Path
from enum import Enum

from pydantic import Field, validator, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


# ============================================
# DEPLOYMENT PLATFORM DETECTION
# ============================================

class DeploymentPlatform(str, Enum):
    """
    Enum for supported deployment platforms.
    Enables platform-specific configuration logic.
    """
    FLY_IO = "fly_io"
    RENDER = "render"
    RAILWAY = "railway"
    LOCAL = "local"
    UNKNOWN = "unknown"


class PlatformDetector:
    """
    Detects the current deployment platform based on environment variables.
    
    Clean Architecture: Single Responsibility Principle
    - Only responsible for platform detection
    - No configuration logic
    - No side effects
    
    Detection Logic:
    1. Check for Render-specific vars (RENDER_EXTERNAL_URL, RENDER_SERVICE_NAME)
    2. Check for Fly.io-specific vars (FLY_APP_NAME, FLY_REGION)
    3. Check for Railway-specific vars (RAILWAY_ENVIRONMENT)
    4. Default to LOCAL for development
    """
    
    @staticmethod
    def detect() -> DeploymentPlatform:
        """
        Detect current deployment platform.
        
        Returns:
            DeploymentPlatform: Detected platform enum
            
        Example:
            >>> platform = PlatformDetector.detect()
            >>> if platform == DeploymentPlatform.RENDER:
            ...     print("Running on Render")
        """
        # Render.com detection
        if os.getenv("RENDER_EXTERNAL_URL") or os.getenv("RENDER_SERVICE_NAME"):
            logger.info("🎯 Platform detected: Render.com")
            return DeploymentPlatform.RENDER
        
        # Fly.io detection
        if os.getenv("FLY_APP_NAME") or os.getenv("FLY_REGION"):
            logger.info("🎯 Platform detected: Fly.io")
            return DeploymentPlatform.FLY_IO
        
        # Railway detection
        if os.getenv("RAILWAY_ENVIRONMENT"):
            logger.info("🎯 Platform detected: Railway")
            return DeploymentPlatform.RAILWAY
        
        # Local development
        logger.info("🎯 Platform detected: Local Development")
        return DeploymentPlatform.LOCAL
    
    @staticmethod
    def is_cloud_deployment() -> bool:
        """
        Check if running in cloud (not local).
        
        Returns:
            bool: True if cloud deployment, False if local
        """
        platform = PlatformDetector.detect()
        return platform not in [DeploymentPlatform.LOCAL, DeploymentPlatform.UNKNOWN]


# ============================================
# PORT CONFIGURATION STRATEGY
# ============================================

class PortResolver:
    """
    Resolves server port from multiple sources with intelligent fallback.
    
    Clean Architecture: Strategy Pattern
    - Each platform has its own port resolution strategy
    - Fallback chain ensures backward compatibility
    - No side effects, pure function
    
    Priority Chain:
    1. Render: PORT (uppercase) - Render injects this
    2. Railway: PORT (uppercase) - Railway injects this
    3. Fly.io: port (lowercase) - Legacy behavior
    4. Explicit: port from .env file
    5. Development: 8000 (default)
    """
    
    @staticmethod
    def resolve(explicit_value: Optional[int] = None) -> int:
        """
        Resolve port number from environment with multi-source fallback.
        
        Args:
            explicit_value: Explicitly configured port (from .env)
            
        Returns:
            int: Resolved port number (1-65535)
            
        Raises:
            ValueError: If port is invalid
            
        Example:
            >>> port = PortResolver.resolve()
            >>> print(f"Server will bind to port {port}")
        """
        # Priority 1: Explicit value from config
        if explicit_value is not None:
            logger.debug(f"Port from explicit config: {explicit_value}")
            return PortResolver._validate_port(explicit_value)
        
        # Priority 2: Render/Railway PORT (uppercase)
        render_port = os.getenv("PORT")
        if render_port:
            port = int(render_port)
            logger.info(f"✅ Port from Render/Railway: {port}")
            return PortResolver._validate_port(port)
        
        # Priority 3: Fly.io port (lowercase) - LEGACY
        legacy_port = os.getenv("port")
        if legacy_port:
            port = int(legacy_port)
            logger.warning(
                f"⚠️ Using legacy 'port' variable (lowercase): {port}. "
                f"Consider migrating to uppercase 'PORT' for consistency."
            )
            return PortResolver._validate_port(port)
        
        # Priority 4: Development default
        default_port = 8000
        logger.debug(f"Port from development default: {default_port}")
        return default_port
    
    @staticmethod
    def _validate_port(port: int) -> int:
        """
        Validate port number is in valid range.
        
        Args:
            port: Port number to validate
            
        Returns:
            int: Validated port number
            
        Raises:
            ValueError: If port is out of valid range (1-65535)
        """
        if not (1 <= port <= 65535):
            raise ValueError(
                f"Invalid port {port}. Port must be between 1 and 65535. "
                f"Check your PORT environment variable."
            )
        return port


# ============================================
# URL CONFIGURATION STRATEGY
# ============================================

class URLResolver:
    """
    Resolves public API URLs with platform-aware logic.
    
    Clean Architecture: Strategy Pattern
    - Platform-specific URL resolution
    - Intelligent fallback chain
    - Development-friendly defaults
    
    Priority Chain:
    1. Explicit: PUBLIC_API_URL from config (highest priority)
    2. Render: RENDER_EXTERNAL_URL (auto-injected)
    3. Fly.io: Construct from FLY_APP_NAME
    4. Development: http://localhost:{port}
    """
    
    @staticmethod
    def resolve_api_url(
        explicit_url: Optional[str] = None,
        port: int = 8000
    ) -> str:
        """
        Resolve public API URL with multi-source fallback.
        
        Args:
            explicit_url: Explicitly configured URL
            port: Server port for localhost fallback
            
        Returns:
            str: Resolved public API URL
            
        Example:
            >>> url = URLResolver.resolve_api_url(port=8000)
            >>> print(f"API accessible at: {url}")
        """
        # Priority 1: Explicit configuration
        if explicit_url:
            logger.debug(f"API URL from explicit config: {explicit_url}")
            return explicit_url
        
        # Priority 2: Render RENDER_EXTERNAL_URL
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if render_url:
            logger.info(f"✅ API URL from Render: {render_url}")
            return render_url
        
        # Priority 3: Fly.io FLY_APP_NAME
        fly_app = os.getenv("FLY_APP_NAME")
        if fly_app:
            fly_url = f"https://{fly_app}.fly.dev"
            logger.info(f"✅ API URL from Fly.io: {fly_url}")
            return fly_url
        
        # Priority 4: Development localhost
        localhost_url = f"http://localhost:{port}"
        logger.debug(f"API URL from development default: {localhost_url}")
        return localhost_url
    
    @staticmethod
    def resolve_websocket_url(api_url: str) -> str:
        """
        Derive WebSocket URL from API URL.
        
        Args:
            api_url: Base API URL
            
        Returns:
            str: WebSocket URL (wss:// or ws://)
            
        Example:
            >>> api_url = "https://api.example.com"
            >>> ws_url = URLResolver.resolve_websocket_url(api_url)
            >>> print(ws_url)  # "wss://api.example.com"
        """
        if api_url.startswith("https://"):
            return api_url.replace("https://", "wss://")
        elif api_url.startswith("http://"):
            return api_url.replace("http://", "ws://")
        else:
            return f"wss://{api_url}"


# ============================================
# CORS ORIGINS STRATEGY
# ============================================

class CORSResolver:
    """
    Resolves CORS origins with environment-aware defaults.
    
    Clean Architecture: Strategy Pattern + Factory Pattern
    - Environment-specific strategies
    - Development-friendly defaults
    - Production security enforcement
    
    Logic:
    - If CORS_ORIGINS explicitly set → Use it (highest priority)
    - If development → Auto-include localhost variants
    - If production → Require explicit FRONTEND_PROD_URLS
    - Else → Empty list (fail-safe)
    """
    
    @staticmethod
    def resolve(
        explicit_origins: Optional[List[str]] = None,
        environment: str = "development"
    ) -> List[str]:
        """
        Resolve CORS origins with environment-aware logic.
        
        Args:
            explicit_origins: Explicitly configured origins
            environment: Current environment (development/staging/production)
            
        Returns:
            List[str]: Resolved CORS origins
            
        Example:
            >>> origins = CORSResolver.resolve(environment="development")
            >>> print(origins)  # ["http://localhost:3000", ...]
        """
        # Priority 1: Explicit configuration (backward compatibility)
        if explicit_origins and len(explicit_origins) > 0:
            logger.debug(f"CORS origins from explicit config: {len(explicit_origins)} origin(s)")
            return explicit_origins
        
        # Priority 2: Environment-aware defaults
        if environment.lower() == "development":
            origins = CORSResolver._get_development_origins()
            logger.info(f"✅ CORS origins for development: {len(origins)} origins")
            return origins
        
        elif environment.lower() == "staging":
            origins = CORSResolver._get_staging_origins()
            logger.info(f"✅ CORS origins for staging: {len(origins)} origins")
            return origins
        
        elif environment.lower() == "production":
            origins = CORSResolver._get_production_origins()
            if not origins:
                logger.error(
                    "❌ PRODUCTION: No CORS origins configured! "
                    "Set FRONTEND_PROD_URLS or CORS_ORIGINS environment variable."
                )
            else:
                logger.info(f"✅ CORS origins for production: {len(origins)} origins")
            return origins
        
        # Fallback: empty list (fail-safe)
        logger.warning(f"⚠️ Unknown environment '{environment}', using empty CORS origins")
        return []
    
    @staticmethod
    def _get_development_origins() -> List[str]:
        """
        Get default CORS origins for development environment.
        
        Returns:
            List[str]: Development CORS origins
        """
        return [
            "http://localhost:3000",
            "http://localhost:5173",  # Vite default
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "http://localhost:8080",  # Alternative port
        ]
    
    @staticmethod
    def _get_staging_origins() -> List[str]:
        """
        Get CORS origins for staging environment.
        
        Returns:
            List[str]: Staging CORS origins from FRONTEND_STAGING_URL
        """
        staging_url = os.getenv("FRONTEND_STAGING_URL")
        if staging_url:
            return [staging_url.strip()]
        
        logger.warning(
            "⚠️ STAGING: FRONTEND_STAGING_URL not set. "
            "Using development origins as fallback."
        )
        return CORSResolver._get_development_origins()
    
    @staticmethod
    def _get_production_origins() -> List[str]:
        """
        Get CORS origins for production environment.
        
        Returns:
            List[str]: Production CORS origins from FRONTEND_PROD_URLS
        """
        # Check FRONTEND_PROD_URLS (comma-separated)
        prod_urls = os.getenv("FRONTEND_PROD_URLS", "")
        if prod_urls:
            origins = [
                url.strip() 
                for url in prod_urls.split(",") 
                if url.strip()
            ]
            return origins
        
        # Fallback: Check old APP_URL variable
        app_url = os.getenv("APP_URL")
        if app_url:
            logger.warning(
                f"⚠️ Using APP_URL as CORS origin: {app_url}. "
                f"Consider setting FRONTEND_PROD_URLS explicitly."
            )
            return [app_url.strip()]
        
        # No configuration found
        return []


# ============================================
# ENHANCED SETTINGS CLASS
# ============================================

class EnhancedSettings(BaseSettings):
    """
    Enhanced settings with multi-platform support.
    
    Clean Architecture Principles:
    - Dependency Inversion: Uses resolver interfaces
    - Single Responsibility: Each resolver handles one concern
    - Open/Closed: Extended without modifying base
    
    Backward Compatibility:
    - All existing fields preserved
    - New resolvers add functionality
    - No breaking changes to API
    """
    
    # ============================================
    # APPLICATION CONFIGURATION
    # ============================================
    app_name: str = Field(default="CryptoVault", description="Application name")
    app_version: str = Field(
        default_factory=lambda: get_version_from_file(),
        description="Application version"
    )
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # ============================================
    # DEPLOYMENT PLATFORM (NEW)
    # ============================================
    deployment_platform: Optional[str] = Field(
        default=None,
        description="Deployment platform (auto-detected if not set)"
    )
    
    # ============================================
    # SERVER CONFIGURATION (ENHANCED)
    # ============================================
    host: str = Field(default="0.0.0.0", description="Server host binding")
    port: int = Field(
        default=8000,
        description="Server port (auto-detects Render/Railway PORT)"
    )
    workers: int = Field(default=4, description="Number of workers for production")
    
    # ============================================
    # URL CONFIGURATION (ENHANCED)
    # ============================================
    public_api_url: Optional[str] = Field(
        default=None,
        description="Public API URL (auto-detects Render/Fly.io)"
    )
    public_ws_url: Optional[str] = Field(
        default=None,
        description="Public WebSocket URL (derived from API URL)"
    )
    app_url: str = Field(
        default="https://www.cryptovault.financial",
        description="Frontend application URL"
    )
    
    # ============================================
    # CORS CONFIGURATION (ENHANCED)
    # ============================================
    cors_origins: List[str] = Field(
        default=[],
        description="CORS origins (auto-detected per environment)"
    )
    
    # ============================================
    # DATABASE CONFIGURATION
    # ============================================
    mongo_url: str = Field(
        default="",
        description="MongoDB connection URL (SRV format required)"
    )
    db_name: str = Field(default="cryptovault", description="Database name")
    
    # ============================================
    # SECURITY
    # ============================================
    jwt_secret: SecretStr = Field(
        default="change-me-in-production",
        description="JWT signing secret"
    )
    csrf_secret: SecretStr = Field(
        default="change-me-in-production",
        description="CSRF protection secret"
    )
    
    # Pydantic configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ============================================
    # VALIDATORS (ENHANCED)
    # ============================================
    
    @field_validator("port", mode="before")
    @classmethod
    def validate_port(cls, v):
        """
        Validate and resolve port with multi-source fallback.
        
        Priority:
        1. Explicit value from config
        2. Render/Railway PORT (uppercase)
        3. Fly.io port (lowercase)
        4. Development default (8000)
        
        Returns:
            int: Validated port number
            
        Raises:
            ValueError: If port is invalid
        """
        try:
            # Use PortResolver with backward compatibility
            resolved_port = PortResolver.resolve(explicit_value=v if v else None)
            return resolved_port
        except ValueError as e:
            logger.error(f"Port validation failed: {e}")
            raise
    
    @field_validator("public_api_url", mode="before")
    @classmethod
    def validate_public_api_url(cls, v, info):
        """
        Validate and resolve public API URL.
        
        Priority:
        1. Explicit PUBLIC_API_URL
        2. Render RENDER_EXTERNAL_URL
        3. Fly.io FLY_APP_NAME
        4. Localhost (development)
        
        Returns:
            str: Resolved public API URL
        """
        # Get port for localhost fallback
        port = info.data.get("port", 8000)
        
        # Use URLResolver with backward compatibility
        resolved_url = URLResolver.resolve_api_url(
            explicit_url=v,
            port=port
        )
        return resolved_url
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v, info):
        """
        Validate and resolve CORS origins with environment awareness.
        
        Priority:
        1. Explicit CORS_ORIGINS
        2. Environment-aware defaults
        
        Returns:
            List[str]: Resolved CORS origins
        """
        # Parse if string (comma-separated or JSON)
        if isinstance(v, str):
            if not v.strip():
                parsed_origins = []
            elif v.startswith("[") and v.endswith("]"):
                # JSON array
                try:
                    import json
                    parsed_origins = json.loads(v)
                except json.JSONDecodeError:
                    parsed_origins = []
            else:
                # Comma-separated
                parsed_origins = [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            parsed_origins = v
        else:
            parsed_origins = []
        
        # Get environment for auto-detection
        environment = info.data.get("environment", "development")
        
        # Use CORSResolver with backward compatibility
        resolved_origins = CORSResolver.resolve(
            explicit_origins=parsed_origins if parsed_origins else None,
            environment=environment
        )
        
        return resolved_origins
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment is one of valid values."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}, got {v}")
        return v.lower()
    
    # ============================================
    # PROPERTIES (ENHANCED)
    # ============================================
    
    @property
    def platform(self) -> DeploymentPlatform:
        """
        Get detected deployment platform.
        
        Returns:
            DeploymentPlatform: Current platform
        """
        if self.deployment_platform:
            try:
                return DeploymentPlatform(self.deployment_platform)
            except ValueError:
                pass
        return PlatformDetector.detect()
    
    @property
    def is_cloud_deployment(self) -> bool:
        """Check if running in cloud."""
        return PlatformDetector.is_cloud_deployment()
    
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
    
    def get_websocket_url(self) -> str:
        """
        Get WebSocket URL derived from API URL.
        
        Returns:
            str: WebSocket URL (wss:// or ws://)
        """
        if self.public_ws_url:
            return self.public_ws_url
        return URLResolver.resolve_websocket_url(self.public_api_url)
    
    def get_cors_origins_list(self) -> List[str]:
        """
        Get CORS origins as list (backward compatible).
        
        Returns:
            List[str]: CORS origins
        """
        return self.cors_origins


# ============================================
# GLOBAL SETTINGS INSTANCE
# ============================================

@lru_cache()
def get_enhanced_settings() -> EnhancedSettings:
    """
    Get cached enhanced settings instance.
    
    Returns:
        EnhancedSettings: Singleton settings instance
    """
    return EnhancedSettings()


# Create global instance
enhanced_settings = get_enhanced_settings()


# ============================================
# STARTUP VALIDATION
# ============================================

def validate_enhanced_configuration() -> Dict[str, Any]:
    """
    Validate enhanced configuration on startup.
    
    Returns:
        Dict[str, Any]: Validation results
        
    Raises:
        ValueError: If critical configuration is missing in production
    """
    logger.info("="*70)
    logger.info("🔍 ENHANCED CONFIGURATION VALIDATION")
    logger.info("="*70)
    
    # Detect platform
    platform = enhanced_settings.platform
    logger.info(f"Platform: {platform.value}")
    logger.info(f"Environment: {enhanced_settings.environment}")
    logger.info(f"Port: {enhanced_settings.port}")
    logger.info(f"API URL: {enhanced_settings.public_api_url}")
    logger.info(f"CORS Origins: {len(enhanced_settings.cors_origins)} configured")
    
    # Validate production requirements
    if enhanced_settings.is_production:
        critical_checks = [
            ("JWT_SECRET", enhanced_settings.jwt_secret.get_secret_value() != "change-me-in-production"),
            ("CSRF_SECRET", enhanced_settings.csrf_secret.get_secret_value() != "change-me-in-production"),
            ("MONGO_URL", bool(enhanced_settings.mongo_url)),
            ("CORS_ORIGINS", len(enhanced_settings.cors_origins) > 0),
        ]
        
        failed_checks = [name for name, passed in critical_checks if not passed]
        
        if failed_checks:
            error_msg = (
                f"❌ PRODUCTION VALIDATION FAILED:\n"
                f"   Missing: {', '.join(failed_checks)}\n"
                f"   Set these in environment variables before deploying."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    logger.info("✅ Enhanced configuration validated successfully")
    logger.info("="*70)
    
    return {
        "status": "success",
        "platform": platform.value,
        "environment": enhanced_settings.environment,
        "port": enhanced_settings.port,
    }
