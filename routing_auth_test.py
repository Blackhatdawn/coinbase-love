#!/usr/bin/env python3
"""
CryptoVault Routing and Authentication Testing Suite
Specifically tests frontend, admin, and private routing and connectivity
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class RoutingAuthTester:
    def __init__(self, base_url: str = "https://cryptovault-api.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        
        # Authentication storage
        self.user_token = None
        self.admin_token = None

    def log_result(self, test_name: str, passed: bool, response_code: int = None, 
                   error: str = None, details: Dict = None):
        """Log test result"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            
        result = {
            "test": test_name,
            "passed": passed,
            "status_code": response_code,
            "error": error,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name} [{response_code}]")
        if error:
            print(f"    Error: {error}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    # =============================================================================
    # PUBLIC ROUTES - Should be accessible without authentication
    # =============================================================================

    def test_public_health_endpoint(self):
        """Test: GET /api/health should be accessible without auth"""
        try:
            response = self.make_request('GET', '/api/health')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Public Route: /api/health", True, response.status_code,
                              details={"status": data.get('status', 'unknown')})
                return True
            else:
                self.log_result("Public Route: /api/health", False, response.status_code,
                              f"Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Public Route: /api/health", False, 0, str(e))
            return False

    def test_public_crypto_endpoint(self):
        """Test: GET /api/crypto should be accessible without auth"""
        try:
            response = self.make_request('GET', '/api/crypto')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Public Route: /api/crypto", True, response.status_code,
                              details={"data_type": type(data).__name__, "length": len(data) if isinstance(data, list) else None})
                return True
            else:
                self.log_result("Public Route: /api/crypto", False, response.status_code,
                              f"Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Public Route: /api/crypto", False, 0, str(e))
            return False

    def test_public_prices_endpoint(self):
        """Test: GET /api/prices should be accessible without auth"""
        try:
            response = self.make_request('GET', '/api/prices')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Public Route: /api/prices", True, response.status_code,
                              details={"data_type": type(data).__name__})
                return True
            else:
                self.log_result("Public Route: /api/prices", False, response.status_code,
                              f"Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Public Route: /api/prices", False, 0, str(e))
            return False

    def test_public_config_endpoint(self):
        """Test: GET /api/config should be accessible without auth"""
        try:
            response = self.make_request('GET', '/api/config')
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Public Route: /api/config", True, response.status_code,
                              details={"has_config": isinstance(data, dict) and len(data) > 0})
                return True
            else:
                self.log_result("Public Route: /api/config", False, response.status_code,
                              f"Expected 200, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Public Route: /api/config", False, 0, str(e))
            return False

    # =============================================================================
    # PROTECTED USER ROUTES - Should return 401 without authentication
    # =============================================================================

    def test_protected_auth_me(self):
        """Test: GET /api/auth/me should return 401 without auth"""
        try:
            response = self.make_request('GET', '/api/auth/me')
            
            if response.status_code == 401:
                self.log_result("Protected Route: /api/auth/me returns 401", True, response.status_code)
                return True
            else:
                self.log_result("Protected Route: /api/auth/me returns 401", False, response.status_code,
                              f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Protected Route: /api/auth/me returns 401", False, 0, str(e))
            return False

    def test_protected_wallet_balance(self):
        """Test: GET /api/wallet/balance should return 401 without auth"""
        try:
            response = self.make_request('GET', '/api/wallet/balance')
            
            if response.status_code == 401:
                self.log_result("Protected Route: /api/wallet/balance returns 401", True, response.status_code)
                return True
            else:
                self.log_result("Protected Route: /api/wallet/balance returns 401", False, response.status_code,
                              f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Protected Route: /api/wallet/balance returns 401", False, 0, str(e))
            return False

    def test_protected_portfolio(self):
        """Test: GET /api/portfolio should return 401 without auth"""
        try:
            response = self.make_request('GET', '/api/portfolio')
            
            if response.status_code == 401:
                self.log_result("Protected Route: /api/portfolio returns 401", True, response.status_code)
                return True
            else:
                self.log_result("Protected Route: /api/portfolio returns 401", False, response.status_code,
                              f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Protected Route: /api/portfolio returns 401", False, 0, str(e))
            return False

    def test_protected_alerts(self):
        """Test: GET /api/alerts should return 401 without auth"""
        try:
            response = self.make_request('GET', '/api/alerts')
            
            if response.status_code == 401:
                self.log_result("Protected Route: /api/alerts returns 401", True, response.status_code)
                return True
            else:
                self.log_result("Protected Route: /api/alerts returns 401", False, response.status_code,
                              f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Protected Route: /api/alerts returns 401", False, 0, str(e))
            return False

    # =============================================================================
    # ADMIN ROUTES - Should return 401 without authentication
    # =============================================================================

    def test_admin_me_endpoint(self):
        """Test: GET /api/admin/me should return 401 without auth"""
        try:
            response = self.make_request('GET', '/api/admin/me')
            
            if response.status_code == 401:
                self.log_result("Admin Route: /api/admin/me returns 401", True, response.status_code)
                return True
            else:
                self.log_result("Admin Route: /api/admin/me returns 401", False, response.status_code,
                              f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Route: /api/admin/me returns 401", False, 0, str(e))
            return False

    def test_admin_dashboard_stats(self):
        """Test: GET /api/admin/dashboard/stats should return 401 without auth"""
        try:
            response = self.make_request('GET', '/api/admin/dashboard/stats')
            
            if response.status_code == 401:
                self.log_result("Admin Route: /api/admin/dashboard/stats returns 401", True, response.status_code)
                return True
            else:
                self.log_result("Admin Route: /api/admin/dashboard/stats returns 401", False, response.status_code,
                              f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Route: /api/admin/dashboard/stats returns 401", False, 0, str(e))
            return False

    def test_admin_users_endpoint(self):
        """Test: GET /api/admin/users should return 401 without auth"""
        try:
            response = self.make_request('GET', '/api/admin/users')
            
            if response.status_code == 401:
                self.log_result("Admin Route: /api/admin/users returns 401", True, response.status_code)
                return True
            else:
                self.log_result("Admin Route: /api/admin/users returns 401", False, response.status_code,
                              f"Expected 401, got {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Route: /api/admin/users returns 401", False, 0, str(e))
            return False

    # =============================================================================
    # USER AUTHENTICATION FLOW
    # =============================================================================

    def test_user_signup_flow(self):
        """Test: User signup flow works correctly"""
        try:
            # Generate unique email
            timestamp = int(time.time())
            email = f"routingtest{timestamp}@example.com"
            
            response = self.make_request('POST', '/api/auth/signup', json={
                "email": email,
                "password": "TestPassword123!",
                "name": "Routing Test User"
            })
            
            if response.status_code == 200:
                data = response.json()
                has_user_data = 'user' in data
                self.log_result("User Signup Flow", has_user_data, response.status_code,
                              None if has_user_data else "No user data in response",
                              {"email": email, "response_keys": list(data.keys())})
                return has_user_data, email
            else:
                self.log_result("User Signup Flow", False, response.status_code,
                              response.text[:200])
                return False, None
        except Exception as e:
            self.log_result("User Signup Flow", False, 0, str(e))
            return False, None

    def test_user_login_flow(self, email: str, password: str = "TestPassword123!"):
        """Test: User login flow works correctly"""
        try:
            response = self.make_request('POST', '/api/auth/login', json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                has_access_token = 'access_token' in data
                has_user = 'user' in data
                
                if has_access_token:
                    self.user_token = data['access_token']
                
                success = has_access_token and has_user
                self.log_result("User Login Flow", success, response.status_code,
                              None if success else "Missing access_token or user data",
                              {"has_access_token": has_access_token, "has_user": has_user})
                return success
            else:
                self.log_result("User Login Flow", False, response.status_code,
                              response.text[:200])
                return False
        except Exception as e:
            self.log_result("User Login Flow", False, 0, str(e))
            return False

    def test_protected_routes_with_valid_token(self):
        """Test: After login, protected routes accessible with valid token"""
        if not self.user_token:
            self.log_result("Protected Routes with Valid Token", False, 0, "No user token available")
            return False

        # Test multiple protected endpoints
        endpoints_to_test = [
            '/api/auth/me',
            '/api/wallet/balance',
            '/api/portfolio'
        ]
        
        all_passed = True
        endpoint_results = {}
        
        for endpoint in endpoints_to_test:
            try:
                headers = {"Authorization": f"Bearer {self.user_token}"}
                response = self.make_request('GET', endpoint, headers=headers)
                
                # Success is 200 or any non-401 code (some endpoints might return different success codes)
                success = response.status_code != 401
                endpoint_results[endpoint] = {
                    "status": response.status_code,
                    "success": success
                }
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                endpoint_results[endpoint] = {
                    "status": 0,
                    "success": False,
                    "error": str(e)
                }
                all_passed = False
        
        self.log_result("Protected Routes with Valid Token", all_passed, None,
                       None if all_passed else "Some endpoints still returned 401",
                       {"endpoint_results": endpoint_results})
        return all_passed

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🔬 CRYPTOVAULT ROUTING & AUTH TEST SUMMARY")
        print("="*60)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print("="*60)
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"  - {result['test']}: {result['error'] or 'See details'}")
        
        print(f"\n📋 Full results saved to routing_auth_test_results.json")
        
        # Save results to file
        with open('/app/test_reports/routing_auth_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.tests_run,
                    "passed_tests": self.tests_passed,
                    "failed_tests": self.tests_run - self.tests_passed,
                    "success_rate": (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "results": self.results
            }, f, indent=2)
        
        return self.tests_passed == self.tests_run

def main():
    print("🚀 Starting CryptoVault Routing & Authentication Tests")
    print("🌐 Testing against: https://cryptovault-api.onrender.com")
    print("-" * 60)
    
    tester = RoutingAuthTester()
    
    # Test public routes (should be accessible)
    print("\n📖 TESTING PUBLIC ROUTES")
    tester.test_public_health_endpoint()
    tester.test_public_crypto_endpoint()
    tester.test_public_prices_endpoint()
    tester.test_public_config_endpoint()
    
    # Test protected user routes (should return 401)
    print("\n🔒 TESTING PROTECTED USER ROUTES (Should return 401)")
    tester.test_protected_auth_me()
    tester.test_protected_wallet_balance()
    tester.test_protected_portfolio()
    tester.test_protected_alerts()
    
    # Test admin routes (should return 401)
    print("\n👑 TESTING ADMIN ROUTES (Should return 401)")
    tester.test_admin_me_endpoint()
    tester.test_admin_dashboard_stats()
    tester.test_admin_users_endpoint()
    
    # Test authentication flow
    print("\n🔐 TESTING AUTHENTICATION FLOW")
    signup_success, test_email = tester.test_user_signup_flow()
    if signup_success and test_email:
        login_success = tester.test_user_login_flow(test_email)
        if login_success:
            tester.test_protected_routes_with_valid_token()
    
    # Print summary
    all_passed = tester.print_summary()
    
    # Return appropriate exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())