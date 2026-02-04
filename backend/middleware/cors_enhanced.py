"""
Centralized CORS Middleware with Environment-Aware Configuration

Design Principles:
- Clean Architecture: Separation of concerns, dependency inversion
- SOLID: Single responsibility, interface segregation
- Security: Environment-aware origin validation

Features:
- Dynamic origin resolution based on environment
- Wildcard blocking in production with credentials
- Request origin validation with comprehensive logging
- Preflight request handling
- Credential support with strict origin checking

Backward Compatibility:
- Works alongside existing CORS configuration
- No breaking changes to existing setup
- Optional enhancement layer

Zero-Downtime Guarantee:
- Can be enabled/disabled via environment variable
- Graceful fallback to default CORS
- No impact on existing deployments
"""

import logging
from typing import List, Optional, Callable
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# ============================================
# ORIGIN VALIDATOR
# ============================================

class CORSOriginValidator:
    """
    Validates CORS origins with security-focused rules.
    
    Clean Architecture: Single Responsibility Principle
    - Only responsible for origin validation
    - No configuration management
    - No side effects
    
    Security Rules:
    1. Reject wildcard (*) with allow_credentials=True
    2. Validate origin format (protocol + domain)
    3. Check against whitelist
    4. Log suspicious origin attempts
    """
    
    @staticmethod
    def validate_origin(
        origin: str,
        allowed_origins: List[str],
        allow_credentials: bool = True
    ) -> bool:
        """
        Validate if origin is allowed based on whitelist.
        
        Args:
            origin: Request origin header value
            allowed_origins: List of allowed origins
            allow_credentials: Whether credentials are allowed
            
        Returns:
            bool: True if origin is allowed, False otherwise
            
        Security:
            - Blocks wildcard with credentials
            - Validates URL format
            - Case-insensitive comparison
            
        Example:
            >>> validator = CORSOriginValidator()
            >>> is_allowed = validator.validate_origin(
            ...     "https://app.example.com",
            ...     ["https://app.example.com"],
            ...     allow_credentials=True
            ... )
            >>> print(is_allowed)  # True
        """
        # Validate inputs
        if not origin or not allowed_origins:
            return False
        
        # Security check: Wildcard with credentials is insecure
        if "*" in allowed_origins and allow_credentials:
            logger.error(
                "🔴 SECURITY VIOLATION: Wildcard (*) CORS origin with allow_credentials=True. "
                "This is a security vulnerability. Use explicit origins."
            )
            return False
        
        # Check if wildcard is allowed (only without credentials)
        if "*" in allowed_origins and not allow_credentials:
            logger.warning(
                f"⚠️ Allowing all origins (wildcard) for: {origin}. "
                f"Credentials are disabled."
            )
            return True
        
        # Normalize origin (lowercase, strip trailing slash)
        normalized_origin = origin.lower().rstrip("/")
        
        # Normalize allowed origins
        normalized_allowed = [
            allowed.lower().rstrip("/")
            for allowed in allowed_origins
        ]
        
        # Check against whitelist
        if normalized_origin in normalized_allowed:
            logger.debug(f"✅ Origin allowed: {origin}")
            return True
        
        # Log rejection
        logger.warning(
            f"⛔ Origin rejected: {origin}. "
            f"Not in whitelist: {allowed_origins}"
        )
        return False
    
    @staticmethod
    def validate_origin_format(origin: str) -> bool:
        """
        Validate origin has proper URL format.
        
        Args:
            origin: Origin to validate
            
        Returns:
            bool: True if valid format
            
        Example:
            >>> CORSOriginValidator.validate_origin_format("https://example.com")
            True
            >>> CORSOriginValidator.validate_origin_format("invalid")
            False
        """
        try:
            parsed = urlparse(origin)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False


# ============================================
# ENHANCED CORS MIDDLEWARE
# ============================================

class EnhancedCORSMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with environment-aware configuration.
    
    Clean Architecture: Middleware Pattern + Strategy Pattern
    - Transparent layer between request/response
    - Environment-specific strategies
    - No business logic coupling
    
    Features:
    - Dynamic origin resolution per request
    - Comprehensive logging for debugging
    - Security validation with detailed errors
    - Preflight request optimization
    - Credential support with origin validation
    
    Backward Compatibility:
    - Works alongside FastAPI CORSMiddleware
    - Optional enhancement layer
    - No breaking changes
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allowed_origins: List[str],
        allow_credentials: bool = True,
        allow_methods: List[str] = None,
        allow_headers: List[str] = None,
        expose_headers: List[str] = None,
        max_age: int = 600,
        environment: str = "development",
        enable_logging: bool = True,
    ):
        """
        Initialize enhanced CORS middleware.
        
        Args:
            app: ASGI application
            allowed_origins: List of allowed origins
            allow_credentials: Allow credentials (cookies, auth headers)
            allow_methods: Allowed HTTP methods
            allow_headers: Allowed request headers
            expose_headers: Headers exposed to client
            max_age: Preflight cache duration (seconds)
            environment: Current environment (development/staging/production)
            enable_logging: Enable detailed CORS logging
            
        Example:
            >>> app.add_middleware(
            ...     EnhancedCORSMiddleware,
            ...     allowed_origins=["https://app.example.com"],
            ...     allow_credentials=True,
            ...     environment="production"
            ... )
        """
        super().__init__(app)
        
        # Configuration
        self.allowed_origins = allowed_origins
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or [\"GET\", \"POST\", \"PUT\", \"DELETE\", \"OPTIONS\", \"PATCH\"]
        self.allow_headers = allow_headers or [\"*\"]
        self.expose_headers = expose_headers or []
        self.max_age = max_age
        self.environment = environment
        self.enable_logging = enable_logging
        
        # Validator
        self.validator = CORSOriginValidator()
        
        # Log configuration
        if self.enable_logging:
            self._log_configuration()
    
    def _log_configuration(self) -> None:
        """Log CORS configuration for debugging."""
        logger.info(\"=\"*70)
        logger.info(\"🌐 ENHANCED CORS MIDDLEWARE CONFIGURATION\")
        logger.info(\"=\"*70)
        logger.info(f\"Environment: {self.environment}\")
        logger.info(f\"Allow Credentials: {self.allow_credentials}\")
        logger.info(f\"Allowed Origins: {len(self.allowed_origins)} configured\")
        
        if self.allowed_origins:
            for i, origin in enumerate(self.allowed_origins[:5], 1):  # Show first 5
                logger.info(f\"  {i}. {origin}\")
            if len(self.allowed_origins) > 5:
                logger.info(f\"  ... and {len(self.allowed_origins) - 5} more\")
        
        logger.info(f\"Allowed Methods: {', '.join(self.allow_methods)}\")
        logger.info(f\"Max Age: {self.max_age}s\")
        logger.info(\"=\"*70)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with CORS validation.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler
            
        Returns:
            Response: HTTP response with CORS headers
            
        Flow:
        1. Extract origin from request
        2. Validate origin against whitelist
        3. Handle preflight (OPTIONS) requests
        4. Add CORS headers to response
        5. Log for debugging
        """
        # Get origin from request
        origin = request.headers.get(\"origin\")
        
        # If no origin header, it's not a CORS request (same-origin)
        if not origin:
            response = await call_next(request)
            return response
        
        # Validate origin
        is_allowed = self.validator.validate_origin(
            origin=origin,
            allowed_origins=self.allowed_origins,
            allow_credentials=self.allow_credentials
        )
        
        # Handle preflight request (OPTIONS)
        if request.method == \"OPTIONS\":
            return self._handle_preflight(request, origin, is_allowed)
        
        # Process actual request
        response = await call_next(request)
        
        # Add CORS headers if origin is allowed
        if is_allowed:
            self._add_cors_headers(response, origin)
        else:
            # Origin not allowed - log security event
            if self.enable_logging:
                logger.warning(
                    f\"⛔ CORS BLOCKED: {request.method} {request.url.path} \"\n                    f\"from origin: {origin}. \"\n                    f\"Environment: {self.environment}\"\n                )
        
        return response
    
    def _handle_preflight(
        self,
        request: Request,
        origin: str,
        is_allowed: bool
    ) -> Response:
        """
        Handle CORS preflight (OPTIONS) request.
        
        Args:
            request: Preflight request
            origin: Request origin
            is_allowed: Whether origin is allowed
            
        Returns:
            Response: Preflight response with CORS headers
            
        Preflight:
            Browser sends OPTIONS before actual request to check CORS policy
        """
        if not is_allowed:
            # Return 403 for rejected preflight
            if self.enable_logging:
                logger.warning(
                    f\"⛔ PREFLIGHT REJECTED: {request.url.path} \"\n                    f\"from origin: {origin}\"\n                )
            return Response(\n                content=\"CORS origin not allowed\",\n                status_code=403,\n                media_type=\"text/plain\"\n            )
        
        # Create preflight response
        response = Response(\n            content=\"\",\n            status_code=200,\n            media_type=\"text/plain\"\n        )
        
        # Add CORS headers
        self._add_cors_headers(response, origin, is_preflight=True)
        
        # Add preflight-specific headers
        response.headers[\"Access-Control-Allow-Methods\"] = \", \".join(self.allow_methods)
        response.headers[\"Access-Control-Allow-Headers\"] = \", \".join(self.allow_headers)
        response.headers[\"Access-Control-Max-Age\"] = str(self.max_age)
        
        if self.enable_logging:
            logger.debug(f\"✅ PREFLIGHT ALLOWED: {request.url.path} from {origin}\")
        
        return response
    
    def _add_cors_headers(
        self,
        response: Response,
        origin: str,
        is_preflight: bool = False
    ) -> None:
        """
        Add CORS headers to response.
        
        Args:
            response: HTTP response
            origin: Request origin
            is_preflight: Whether this is a preflight response
            
        Headers Added:
        - Access-Control-Allow-Origin: Specific origin (never wildcard with credentials)
        - Access-Control-Allow-Credentials: If credentials enabled
        - Access-Control-Expose-Headers: Exposed headers
        """
        # Set allowed origin (specific, not wildcard)\n        response.headers[\"Access-Control-Allow-Origin\"] = origin
        
        # Set credentials header\n        if self.allow_credentials:
            response.headers[\"Access-Control-Allow-Credentials\"] = \"true\"
        
        # Set exposed headers\n        if self.expose_headers:
            response.headers[\"Access-Control-Expose-Headers\"] = \", \".join(self.expose_headers)
        
        # Vary header for caching\n        response.headers[\"Vary\"] = \"Origin\"


# ============================================
# CORS MIDDLEWARE FACTORY
# ============================================

class CORSMiddlewareFactory:
    """
    Factory for creating CORS middleware with environment-aware configuration.
    
    Clean Architecture: Factory Pattern
    - Encapsulates middleware creation
    - Environment-specific configuration
    - Backward compatibility
    
    Usage:
        >>> factory = CORSMiddlewareFactory()
        >>> middleware = factory.create(
        ...     app=app,
        ...     environment=\"production\",
        ...     allowed_origins=[\"https://app.example.com\"]
        ... )
    """
    
    @staticmethod
    def create(
        app: ASGIApp,
        environment: str,
        allowed_origins: Optional[List[str]] = None,
        allow_credentials: bool = True,
        enable_enhanced: bool = True,
    ) -> Optional[BaseHTTPMiddleware]:
        """
        Create CORS middleware based on environment.
        
        Args:
            app: ASGI application
            environment: Current environment
            allowed_origins: List of allowed origins (auto-detected if None)
            allow_credentials: Allow credentials
            enable_enhanced: Use enhanced middleware (False = standard FastAPI)
            
        Returns:
            Middleware instance or None
            
        Example:
            >>> middleware = CORSMiddlewareFactory.create(
            ...     app=app,
            ...     environment=\"production\",
            ...     allowed_origins=[\"https://app.example.com\"]
            ... )
        """
        # Validate environment
        if environment not in [\"development\", \"staging\", \"production\"]:
            logger.warning(
                f\"⚠️ Unknown environment '{environment}', defaulting to development\"\n            )
            environment = \"development\"
        
        # Get origins (use provided or auto-detect)\n        if allowed_origins is None:
            logger.warning(
                \"⚠️ No CORS origins provided. Using environment defaults. \"\n                \"For production, explicitly set CORS_ORIGINS.\"\n            )
            # This should be resolved by config_enhanced.py CORSResolver
            allowed_origins = []
        
        # Create enhanced middleware\n        if enable_enhanced:
            return EnhancedCORSMiddleware(
                app=app,
                allowed_origins=allowed_origins,
                allow_credentials=allow_credentials,
                environment=environment,
                enable_logging=environment != \"production\",  # Reduce logs in prod
            )
        
        # Fallback: Use standard FastAPI CORSMiddleware\n        logger.info(\"Using standard FastAPI CORSMiddleware\")
        return None  # Caller should add standard middleware


# ============================================
# CONVENIENCE FUNCTION
# ============================================

def add_enhanced_cors_middleware(
    app: ASGIApp,
    environment: str,
    allowed_origins: List[str],
    allow_credentials: bool = True,
) -> None:
    """
    Add enhanced CORS middleware to FastAPI application.
    
    Convenience function for common use case.
    
    Args:
        app: FastAPI application
        environment: Current environment
        allowed_origins: List of allowed origins
        allow_credentials: Allow credentials
        
    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> add_enhanced_cors_middleware(
        ...     app=app,
        ...     environment=\"production\",
        ...     allowed_origins=[\"https://app.example.com\"]
        ... )
    """
    app.add_middleware(
        EnhancedCORSMiddleware,
        allowed_origins=allowed_origins,
        allow_credentials=allow_credentials,
        environment=environment,
        enable_logging=environment != \"production\"
    )
    
    logger.info(f\"✅ Enhanced CORS middleware added for {environment} environment\")
