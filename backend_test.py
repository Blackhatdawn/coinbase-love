#!/usr/bin/env python3
"""
CryptoVault Backend API Testing Suite
Tests all requirements from review request: domain correction, S3 config, health endpoints, admin protection
"""

import requests
import sys
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path

class CryptoVaultAPITester:
    def __init__(self, base_url: str = "https://secure-trading-api.preview.emergentagent.com"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.timeout = 30
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results: List[Dict[str, Any]] = []

    def log_test(self, name: str, success: bool, details: Dict[str, Any] = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details and not success:
            print(f"    Details: {details}")

    def test_health_endpoints(self):
        """Test health check endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        
        # Test /health/live
        try:
            response = self.session.get(f"{self.base_url}/health/live")
            success = (response.status_code == 200 and 
                      response.json().get("status") == "ok")
            self.log_test(
                "GET /health/live returns {status: ok} with 200",
                success,
                {"status_code": response.status_code, "response": response.json()}
            )
        except Exception as e:
            self.log_test(
                "GET /health/live returns {status: ok} with 200",
                False,
                {"error": str(e)}
            )

        # Test /health/ready
        try:
            response = self.session.get(f"{self.base_url}/health/ready")
            success = response.status_code == 200
            response_data = response.json()
            
            # Check for required checks
            checks = response_data.get("checks", {})
            has_mongodb = "mongodb" in checks
            has_redis = "redis" in checks  
            has_price_stream = "price_stream" in checks
            
            success = success and has_mongodb and has_redis and has_price_stream
            
            self.log_test(
                "GET /health/ready returns mongodb/redis/price_stream checks with 200",
                success,
                {
                    "status_code": response.status_code,
                    "has_mongodb": has_mongodb,
                    "has_redis": has_redis,
                    "has_price_stream": has_price_stream,
                    "checks": list(checks.keys())
                }
            )
        except Exception as e:
            self.log_test(
                "GET /health/ready returns mongodb/redis/price_stream checks with 200",
                False,
                {"error": str(e)}
            )

    def test_admin_endpoints_unauthorized(self):
        """Test admin endpoints return 401 without authentication"""
        print("\n🔍 Testing Admin Endpoints (Unauthorized)...")
        
        admin_endpoints = [
            ("GET", "/api/admin/withdrawals/pending", "GET /api/admin/withdrawals/pending returns 401 without admin auth"),
            ("GET", "/api/admin/withdrawals/stats", "GET /api/admin/withdrawals/stats returns 401 without admin auth"),
        ]
        
        for method, endpoint, test_name in admin_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.request(method, f"{self.base_url}{endpoint}")
                
                success = response.status_code in [401, 403]  # Both indicate unauthorized
                self.log_test(
                    test_name,
                    success,
                    {"status_code": response.status_code, "endpoint": endpoint}
                )
            except Exception as e:
                self.log_test(
                    test_name,
                    False,
                    {"error": str(e), "endpoint": endpoint}
                )

    def test_wallet_endpoints_unauthorized(self):
        """Test wallet withdrawal endpoints return 401 without authentication"""
        print("\n🔍 Testing Wallet Endpoints (Unauthorized)...")
        
        # Use dummy withdrawal ID for testing
        dummy_withdrawal_id = "test-withdrawal-id-123"
        
        wallet_endpoints = [
            ("POST", f"/api/wallet/withdraw/{dummy_withdrawal_id}/approve", f"POST /api/wallet/withdraw/{{id}}/approve returns 401 without auth"),
            ("POST", f"/api/wallet/withdraw/{dummy_withdrawal_id}/reject", f"POST /api/wallet/withdraw/{{id}}/reject returns 401 without auth"),
        ]
        
        for method, endpoint, test_name in wallet_endpoints:
            try:
                headers = {"Content-Type": "application/json"}
                response = self.session.request(method, f"{self.base_url}{endpoint}", headers=headers)
                success = response.status_code in [401, 403]  # Both indicate unauthorized
                self.log_test(
                    test_name,
                    success,
                    {"status_code": response.status_code, "endpoint": endpoint}
                )
            except Exception as e:
                self.log_test(
                    test_name,
                    False,
                    {"error": str(e), "endpoint": endpoint}
                )

    def test_kyc_endpoints_unauthorized(self):
        """Test KYC endpoints return 401 without authentication"""
        print("\n🔍 Testing KYC Endpoints (Unauthorized)...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/kyc/status")
            success = response.status_code == 401
            self.log_test(
                "GET /api/kyc/status returns 401 without auth",
                success,
                {"status_code": response.status_code}
            )
        except Exception as e:
            self.log_test(
                "GET /api/kyc/status returns 401 without auth",
                False,
                {"error": str(e)}
            )

    def test_domain_references(self):
        """Test that all files use cryptovaultpro.finance domain (NOT .financial)"""
        print("\n🔍 Testing Domain References...")
        
        # Files to check for domain references
        files_to_check = [
            "/app/backend/.env",
            "/app/backend/config.py", 
            "/app/backend/services/s3_service.py",
            "/app/frontend/index.html",
            "/app/frontend/public/sitemap.xml",
            "/app/frontend/src/pages/AdminLogin.tsx"
        ]
        
        incorrect_domains = []
        correct_domains = []
        
        for file_path in files_to_check:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for incorrect .financial domain
                    financial_matches = re.findall(r'cryptovaultpro\.financial', content, re.IGNORECASE)
                    if financial_matches:
                        incorrect_domains.append({
                            "file": file_path,
                            "matches": len(financial_matches),
                            "type": "incorrect (.financial)"
                        })
                    
                    # Check for correct .finance domain
                    finance_matches = re.findall(r'cryptovaultpro\.finance', content, re.IGNORECASE)
                    if finance_matches:
                        correct_domains.append({
                            "file": file_path,
                            "matches": len(finance_matches),
                            "type": "correct (.finance)"
                        })
                        
            except Exception as e:
                print(f"    Error checking {file_path}: {e}")
        
        # Test passes if no incorrect domains found
        success = len(incorrect_domains) == 0
        
        self.log_test(
            "All files use cryptovaultpro.finance domain (NOT .financial)",
            success,
            {
                "incorrect_domains": incorrect_domains,
                "correct_domains": correct_domains,
                "files_checked": len(files_to_check)
            }
        )

    def test_s3_configuration(self):
        """Test S3 Hostkey configuration in backend .env"""
        print("\n🔍 Testing S3 Configuration...")
        
        env_file = "/app/backend/.env"
        s3_config = {}
        
        try:
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.startswith('S3_'):
                                s3_config[key] = value
                
                # Check required S3 configuration
                required_s3_vars = {
                    'S3_ENDPOINT_URL': 'https://s3-nl.hostkey.com',
                    'S3_ACCESS_KEY_ID': None,  # Should exist but we don't check value
                    'S3_SECRET_ACCESS_KEY': None,  # Should exist but we don't check value
                    'S3_REGION': 'nl',
                    'S3_BUCKET_KYC': None,  # Should exist
                    'S3_BUCKET_AUDIT': None  # Should exist
                }
                
                config_correct = True
                config_details = {}
                
                for var, expected_value in required_s3_vars.items():
                    if var in s3_config:
                        config_details[var] = "present"
                        if expected_value and s3_config[var] != expected_value:
                            config_details[var] = f"incorrect (expected: {expected_value}, got: {s3_config[var]})"
                            config_correct = False
                    else:
                        config_details[var] = "missing"
                        config_correct = False
                
                # Specific check for Hostkey endpoint
                hostkey_correct = s3_config.get('S3_ENDPOINT_URL') == 'https://s3-nl.hostkey.com'
                
                self.log_test(
                    "Backend .env has correct S3 credentials (S3_ENDPOINT_URL=https://s3-nl.hostkey.com)",
                    hostkey_correct and config_correct,
                    {
                        "s3_endpoint_correct": hostkey_correct,
                        "all_s3_vars_present": config_correct,
                        "s3_config": config_details
                    }
                )
                
            else:
                self.log_test(
                    "Backend .env has correct S3 credentials (S3_ENDPOINT_URL=https://s3-nl.hostkey.com)",
                    False,
                    {"error": "Backend .env file not found"}
                )
                
        except Exception as e:
            self.log_test(
                "Backend .env has correct S3 credentials (S3_ENDPOINT_URL=https://s3-nl.hostkey.com)",
                False,
                {"error": str(e)}
            )

    def test_email_domain_configuration(self):
        """Test that EMAIL_FROM uses cryptovaultpro.finance domain"""
        print("\n🔍 Testing Email Domain Configuration...")
        
        env_file = "/app/backend/.env"
        
        try:
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Find EMAIL_FROM line
                email_from_match = re.search(r'EMAIL_FROM=(.+)', content)
                if email_from_match:
                    email_from = email_from_match.group(1).strip()
                    success = 'cryptovaultpro.finance' in email_from
                    
                    self.log_test(
                        "Backend .env EMAIL_FROM uses cryptovaultpro.finance",
                        success,
                        {
                            "email_from": email_from,
                            "uses_correct_domain": success
                        }
                    )
                else:
                    self.log_test(
                        "Backend .env EMAIL_FROM uses cryptovaultpro.finance",
                        False,
                        {"error": "EMAIL_FROM not found in .env"}
                    )
            else:
                self.log_test(
                    "Backend .env EMAIL_FROM uses cryptovaultpro.finance",
                    False,
                    {"error": "Backend .env file not found"}
                )
                
        except Exception as e:
            self.log_test(
                "Backend .env EMAIL_FROM uses cryptovaultpro.finance",
                False,
                {"error": str(e)}
            )

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting CryptoVault Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run test suites
        self.test_health_endpoints()
        self.test_domain_references()
        self.test_s3_configuration()
        self.test_email_domain_configuration()
        self.test_admin_endpoints_unauthorized()
        self.test_wallet_endpoints_unauthorized()
        self.test_kyc_endpoints_unauthorized()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        # Save detailed results
        results = {
            "summary": {
                "tests_run": self.tests_run,
                "tests_passed": self.tests_passed,
                "tests_failed": self.tests_run - self.tests_passed,
                "success_rate": round(self.tests_passed / self.tests_run * 100, 1),
                "timestamp": datetime.utcnow().isoformat(),
                "base_url": self.base_url
            },
            "test_results": self.test_results
        }
        
        with open("/app/test_reports/backend_api_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /app/test_reports/backend_api_test_results.json")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test execution"""
    tester = CryptoVaultAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {tester.tests_run - tester.tests_passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())