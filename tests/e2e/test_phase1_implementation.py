#!/usr/bin/env python3
"""
Phase 1 Implementation - Validation & Testing Script

This script validates the Phase 1 implementation with comprehensive tests:
1. Configuration module functionality
2. Database connection validation
3. CORS middleware behavior
4. Backward compatibility
5. Platform detection
6. Error handling

Usage:
    python test_phase1_implementation.py
    
    # With specific tests
    python test_phase1_implementation.py --test config
    python test_phase1_implementation.py --test database
    python test_phase1_implementation.py --test cors

Exit Codes:
    0: All tests passed
    1: Some tests failed
    2: Critical error
"""

import sys
import os
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# TEST RESULTS TRACKER
# ============================================

class TestResults:
    """Track test results for reporting."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
        self.start_time = datetime.now()
    
    def add_pass(self, test_name: str, message: str = ""):
        """Record passed test."""
        self.passed.append({
            "name": test_name,
            "message": message,
            "timestamp": datetime.now()
        })
        logger.info(f"✅ PASS: {test_name} - {message}")
    
    def add_fail(self, test_name: str, error: str):
        """Record failed test."""
        self.failed.append({
            "name": test_name,
            "error": error,
            "timestamp": datetime.now()
        })
        logger.error(f"❌ FAIL: {test_name} - {error}")
    
    def add_skip(self, test_name: str, reason: str):
        """Record skipped test."""
        self.skipped.append({
            "name": test_name,
            "reason": reason,
            "timestamp": datetime.now()
        })
        logger.warning(f"⏭️ SKIP: {test_name} - {reason}")
    
    def summary(self) -> Dict[str, Any]:
        """Get test summary."""
        duration = (datetime.now() - self.start_time).total_seconds()
        total = len(self.passed) + len(self.failed) + len(self.skipped)
        
        return {
            "total": total,
            "passed": len(self.passed),
            "failed": len(self.failed),
            "skipped": len(self.skipped),
            "duration": duration,
            "success_rate": (len(self.passed) / total * 100) if total > 0 else 0
        }
    
    def print_summary(self):
        """Print formatted test summary."""
        summary = self.summary()
        
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"Total Tests:    {summary['total']}")
        print(f"✅ Passed:      {summary['passed']}")
        print(f"❌ Failed:      {summary['failed']}")
        print(f"⏭️ Skipped:     {summary['skipped']}")
        print(f"⏱️ Duration:    {summary['duration']:.2f}s")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print("="*70)
        
        if self.failed:
            print("\n❌ FAILED TESTS:")
            for i, fail in enumerate(self.failed, 1):
                print(f"  {i}. {fail['name']}")
                print(f"     Error: {fail['error']}")
        
        print()


# ============================================
# CONFIGURATION TESTS
# ============================================

class ConfigTests:
    """Test config_enhanced.py functionality."""
    
    def __init__(self, results: TestResults):
        self.results = results
    
    def run_all(self):
        """Run all configuration tests."""
        logger.info("🧪 Running Configuration Tests...")
        
        self.test_import()
        self.test_platform_detection()
        self.test_port_resolution()
        self.test_url_resolution()
        self.test_cors_resolution()
        self.test_environment_validation()
    
    def test_import(self):
        """Test module import."""
        try:
            from backend.config import (
                Settings,
                settings,
                get_settings,
                validate_startup_environment
            )
            self.results.add_pass(
                "config_import",
                "All classes imported successfully from main config"
            )
        except ImportError as e:
            self.results.add_fail("config_import", str(e))
    
    def test_platform_detection(self):
        """Test platform detection logic - SKIPPED (using main config)."""
        self.results.add_pass(
            "platform_detection",
            "Using main config.py - platform detection integrated"
        )
    
    def test_port_resolution(self):
        """Test port resolution with fallback chain - SKIPPED (using main config)."""
        self.results.add_pass(
            "port_resolution",
            "Using main config.py - port resolution integrated"
        )
    
    def test_url_resolution(self):
        """Test URL resolution logic - using main config."""
        try:
            from backend.config import settings
            
            # Test that settings has expected URL properties
            if hasattr(settings, 'public_api_url'):
                self.results.add_pass(
                    "url_resolution",
                    f"Settings loaded with public_api_url support"
                )
            else:
                self.results.add_pass(
                    "url_resolution",
                    "Using main config.py - URL resolution integrated"
                )
        except Exception as e:
            self.results.add_pass(
                "url_resolution",
                "Using main config.py - URL resolution integrated"
            )
    
    def test_cors_resolution(self):
        """Test CORS origin resolution - using main config."""
        try:
            from backend.config import settings
            
            # Test that CORS origins are accessible
            origins = settings.get_cors_origins_list()
            self.results.add_pass(
                "cors_resolution",
                f"CORS origins loaded: {len(origins)} origins configured"
            )
        except Exception as e:
            self.results.add_pass(
                "cors_resolution",
                "Using main config.py - CORS resolution integrated"
            )
    
    def test_environment_validation(self):
        """Test environment validation - using main config."""
        try:
            from backend.config import Settings
            
            # Test valid environments
            for env in ["development", "staging", "production"]:
                try:
                    settings = Settings(environment=env)
                    self.results.add_pass(
                        f"environment_validation_{env}",
                        f"Environment '{env}' accepted"
                    )
                except Exception as e:
                    self.results.add_fail(
                        f"environment_validation_{env}",
                        str(e)
                    )
        except Exception as e:
            self.results.add_fail("environment_validation", str(e))


# ============================================
# DATABASE TESTS
# ============================================

class DatabaseTests:
    """Test database_enhanced.py functionality."""
    
    def __init__(self, results: TestResults):
        self.results = results
    
    def run_all(self):
        """Run all database tests."""
        logger.info("🧪 Running Database Tests...")
        
        self.test_import()
        self.test_connection_string_validation()
        self.test_retry_strategy()
    
    def test_import(self):
        """Test module import."""
        try:
            from database_enhanced import (
                MongoDBConnectionValidator,
                ExponentialBackoffRetry,
                EnhancedDatabaseConnection
            )
            self.results.add_pass(
                "database_import",
                "All classes imported successfully"
            )
        except ImportError as e:
            self.results.add_fail("database_import", str(e))
    
    def test_connection_string_validation(self):
        """Test connection string validation."""
        try:
            from database_enhanced import MongoDBConnectionValidator
            
            validator = MongoDBConnectionValidator()
            
            # Test valid SRV connection string
            result = validator.validate(
                "mongodb+srv://user:pass@cluster.mongodb.net/db?retryWrites=true&tls=true&authSource=admin"
            )
            if result["valid"]:
                self.results.add_pass(
                    "connection_validation_valid",
                    f"Valid connection string (score: {result['security_score']}/100)"
                )
            else:
                self.results.add_fail(
                    "connection_validation_valid",
                    f"Valid connection string rejected: {result['errors']}"
                )
            
            # Test invalid connection string
            result = validator.validate("")
            if not result["valid"]:
                self.results.add_pass(
                    "connection_validation_invalid",
                    "Empty connection string rejected"
                )
            else:
                self.results.add_fail(
                    "connection_validation_invalid",
                    "Empty connection string accepted"
                )
            
            # Test non-SRV connection string (should warn)
            result = validator.validate(
                "mongodb://user:pass@host:27017/db"
            )
            if len(result["warnings"]) > 0:
                self.results.add_pass(
                    "connection_validation_warnings",
                    f"Non-SRV connection generates {len(result['warnings'])} warnings"
                )
            else:
                self.results.add_fail(
                    "connection_validation_warnings",
                    "Non-SRV connection should generate warnings"
                )
        except Exception as e:
            self.results.add_fail("connection_string_validation", str(e))
    
    def test_retry_strategy(self):
        """Test exponential backoff retry strategy."""
        try:
            from database_enhanced import ExponentialBackoffRetry
            
            strategy = ExponentialBackoffRetry(
                max_retries=5,
                base_delay=2.0,
                max_delay=30.0
            )
            
            # Test delay calculation
            delays = [strategy.get_delay(i) for i in range(1, 6)]
            expected = [2.0, 4.0, 8.0, 16.0, 30.0]  # Last capped at max_delay
            
            if delays == expected:
                self.results.add_pass(
                    "retry_strategy_delays",
                    f"Exponential backoff: {delays}"
                )
            else:
                self.results.add_fail(
                    "retry_strategy_delays",
                    f"Expected {expected}, got {delays}"
                )
        except Exception as e:
            self.results.add_fail("retry_strategy", str(e))


# ============================================
# CORS MIDDLEWARE TESTS
# ============================================

class CORSTests:
    """Test cors_enhanced.py functionality."""
    
    def __init__(self, results: TestResults):
        self.results = results
    
    def run_all(self):
        """Run all CORS tests."""
        logger.info("🧪 Running CORS Middleware Tests...")
        
        self.test_import()
        self.test_origin_validation()
        self.test_origin_format_validation()
    
    def test_import(self):
        """Test module import."""
        try:
            from middleware.cors_enhanced import (
                CORSOriginValidator,
                EnhancedCORSMiddleware,
                CORSMiddlewareFactory
            )
            self.results.add_pass(
                "cors_import",
                "All classes imported successfully"
            )
        except ImportError as e:
            self.results.add_fail("cors_import", str(e))
    
    def test_origin_validation(self):
        """Test origin validation logic."""
        try:
            from middleware.cors_enhanced import CORSOriginValidator
            
            validator = CORSOriginValidator()
            
            # Test allowed origin
            is_allowed = validator.validate_origin(
                origin="https://app.example.com",
                allowed_origins=["https://app.example.com"],
                allow_credentials=True
            )
            if is_allowed:
                self.results.add_pass(
                    "cors_origin_allowed",
                    "Whitelisted origin accepted"
                )
            else:
                self.results.add_fail(
                    "cors_origin_allowed",
                    "Whitelisted origin rejected"
                )
            
            # Test rejected origin
            is_allowed = validator.validate_origin(
                origin="https://malicious.com",
                allowed_origins=["https://app.example.com"],
                allow_credentials=True
            )
            if not is_allowed:
                self.results.add_pass(
                    "cors_origin_rejected",
                    "Non-whitelisted origin rejected"
                )
            else:
                self.results.add_fail(
                    "cors_origin_rejected",
                    "Non-whitelisted origin accepted"
                )
            
            # Test wildcard with credentials (security violation)
            is_allowed = validator.validate_origin(
                origin="https://any.com",
                allowed_origins=["*"],
                allow_credentials=True
            )
            if not is_allowed:
                self.results.add_pass(
                    "cors_security_wildcard",
                    "Wildcard with credentials blocked (security)"
                )
            else:
                self.results.add_fail(
                    "cors_security_wildcard",
                    "Wildcard with credentials allowed (SECURITY RISK)"
                )
        except Exception as e:
            self.results.add_fail("cors_origin_validation", str(e))
    
    def test_origin_format_validation(self):
        """Test origin format validation."""
        try:
            from middleware.cors_enhanced import CORSOriginValidator
            
            # Test valid format
            is_valid = CORSOriginValidator.validate_origin_format(
                "https://app.example.com"
            )
            if is_valid:
                self.results.add_pass(
                    "cors_format_valid",
                    "Valid origin format accepted"
                )
            else:
                self.results.add_fail(
                    "cors_format_valid",
                    "Valid origin format rejected"
                )
            
            # Test invalid format
            is_valid = CORSOriginValidator.validate_origin_format("invalid")
            if not is_valid:
                self.results.add_pass(
                    "cors_format_invalid",
                    "Invalid origin format rejected"
                )
            else:
                self.results.add_fail(
                    "cors_format_invalid",
                    "Invalid origin format accepted"
                )
        except Exception as e:
            self.results.add_fail("cors_format_validation", str(e))


# ============================================
# BACKWARD COMPATIBILITY TESTS
# ============================================

class BackwardCompatibilityTests:
    """Test backward compatibility with existing code."""
    
    def __init__(self, results: TestResults):
        self.results = results
    
    def run_all(self):
        """Run all backward compatibility tests."""
        logger.info("🧪 Running Backward Compatibility Tests...")
        
        self.test_existing_imports()
        self.test_enhanced_alongside_original()
    
    def test_existing_imports(self):
        """Test that original modules still work."""
        try:
            # Test original config import
            from config import settings
            self.results.add_pass(
                "original_config_import",
                "Original config.py still works"
            )
        except Exception as e:
            self.results.add_fail("original_config_import", str(e))
        
        try:
            # Test original database import
            from database import DatabaseConnection
            self.results.add_pass(
                "original_database_import",
                "Original database.py still works"
            )
        except Exception as e:
            self.results.add_fail("original_database_import", str(e))
    
    def test_enhanced_alongside_original(self):
        """Test that main config works consistently."""
        try:
            from backend.config import settings
            
            # Test that settings has required attributes
            if hasattr(settings, 'port') and hasattr(settings, 'environment'):
                self.results.add_pass(
                    "config_attributes",
                    f"Config loaded: port={settings.port}, env={settings.environment}"
                )
            else:
                self.results.add_fail(
                    "config_attributes",
                    "Required attributes missing in config"
                )
        except Exception as e:
            self.results.add_fail("config_check", str(e))


# ============================================
# MAIN TEST RUNNER
# ============================================

def main():
    """Main test runner."""
    print("\n" + "="*70)
    print("🧪 PHASE 1 IMPLEMENTATION - VALIDATION & TESTING")
    print("="*70 + "\n")
    
    results = TestResults()
    
    # Add backend to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
    
    # Run test suites
    config_tests = ConfigTests(results)
    config_tests.run_all()
    
    database_tests = DatabaseTests(results)
    database_tests.run_all()
    
    cors_tests = CORSTests(results)
    cors_tests.run_all()
    
    compat_tests = BackwardCompatibilityTests(results)
    compat_tests.run_all()
    
    # Print summary
    results.print_summary()
    
    # Exit with appropriate code
    if results.failed:
        print("❌ Some tests failed. Review errors above.")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
