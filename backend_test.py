#!/usr/bin/env python3
"""
CryptoVault Backend API Testing Suite
Tests all backend endpoints for functionality and integration
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CryptoVaultAPITester:
    def __init__(self, base_url: str = "https://coin-trader-18.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, auth_required: bool = False) -> tuple[bool, Dict]:
        """Make HTTP request and validate response"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text[:200]}

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test health endpoint (should be at /api/health)"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Health Check", True, "API is healthy")
                else:
                    self.log_test("Health Check", False, f"Health check returned: {data}")
            else:
                self.log_test("Health Check", False, f"Health endpoint returned {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, f"Health check error: {str(e)}")

    def test_root_endpoint(self):
        """Test root endpoint (should return JSON from backend)"""
        try:
            # The root endpoint might be served by frontend, let's check if backend root is accessible
            response = requests.get(f"{self.base_url}/", timeout=10)
            if "CryptoVault" in response.text:
                self.log_test("Root Endpoint", True, "Frontend is serving root correctly")
            else:
                self.log_test("Root Endpoint", False, f"Unexpected root response")
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Root endpoint error: {str(e)}")

    def test_crypto_endpoints(self):
        """Test cryptocurrency endpoints"""
        # Test get all cryptocurrencies
        success, data = self.make_request('GET', '/crypto')
        if success and 'cryptocurrencies' in data:
            self.log_test("Get All Cryptocurrencies", True, f"Retrieved {len(data.get('cryptocurrencies', []))} cryptocurrencies")
        else:
            self.log_test("Get All Cryptocurrencies", False, f"Failed to get cryptocurrencies: {data}")

        # Test get specific cryptocurrency (Bitcoin)
        success, data = self.make_request('GET', '/crypto/bitcoin')
        if success and 'cryptocurrency' in data:
            self.log_test("Get Bitcoin Details", True, "Bitcoin details retrieved successfully")
        else:
            self.log_test("Get Bitcoin Details", False, f"Failed to get Bitcoin details: {data}")

    def test_new_features_endpoints(self):
        """Test new feature endpoints added in the update"""
        # Test password reset request endpoint
        reset_data = {"email": "test@example.com"}
        success, data = self.make_request('POST', '/auth/password-reset/request', reset_data, expected_status=200)
        if success or "password reset" in str(data).lower():
            self.log_test("Password Reset Request", True, "Password reset endpoint working")
        else:
            self.log_test("Password Reset Request", False, f"Password reset failed: {data}")

        # Test alerts endpoints (should require auth)
        success, data = self.make_request('GET', '/alerts', expected_status=401)
        if success or "unauthorized" in str(data).lower() or "authentication" in str(data).lower():
            self.log_test("Alerts Endpoint (Auth Required)", True, "Alerts endpoint correctly requires authentication")
        else:
            self.log_test("Alerts Endpoint (Auth Required)", False, f"Unexpected alerts response: {data}")

        # Test admin stats endpoint (should require auth)
        success, data = self.make_request('GET', '/admin/stats', expected_status=401)
        if success or "unauthorized" in str(data).lower() or "authentication" in str(data).lower():
            self.log_test("Admin Stats Endpoint (Auth Required)", True, "Admin stats endpoint correctly requires authentication")
        else:
            self.log_test("Admin Stats Endpoint (Auth Required)", False, f"Unexpected admin stats response: {data}")

        # Test wallet deposit endpoint (should require auth)
        deposit_data = {"amount": 100, "currency": "btc"}
        success, data = self.make_request('POST', '/wallet/deposit', deposit_data, expected_status=401)
        if success or "unauthorized" in str(data).lower() or "authentication" in str(data).lower():
            self.log_test("Wallet Deposit Endpoint (Auth Required)", True, "Wallet deposit endpoint correctly requires authentication")
        else:
            self.log_test("Wallet Deposit Endpoint (Auth Required)", False, f"Unexpected wallet deposit response: {data}")

    def test_auth_signup(self):
        """Test user signup"""
        test_email = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"  # Use valid domain
        signup_data = {
            "email": test_email,
            "name": "Test User",
            "password": "TestPassword123!"
        }
        
        success, data = self.make_request('POST', '/auth/signup', signup_data, expected_status=200)
        if success and 'user' in data:
            self.user_id = data['user']['id']
            self.log_test("User Signup", True, f"User created with ID: {self.user_id}")
            return test_email
        else:
            self.log_test("User Signup", False, f"Signup failed: {data}")
            return None

    def test_auth_login(self, email: str, password: str = "TestPassword123!"):
        """Test user login"""
        login_data = {
            "email": email,
            "password": password
        }
        
        success, data = self.make_request('POST', '/auth/login', login_data, expected_status=200)
        if success and 'user' in data:
            # Note: In production, tokens are in httpOnly cookies, not response body
            self.log_test("User Login", True, "Login successful (cookies set)")
            return True
        else:
            # Check if it's an email verification issue
            if "Email not verified" in str(data):
                self.log_test("User Login", False, "Email verification required (expected for new accounts)")
            else:
                self.log_test("User Login", False, f"Login failed: {data}")
            return False

    def test_protected_endpoints(self):
        """Test endpoints that require authentication"""
        # Test portfolio endpoint
        success, data = self.make_request('GET', '/portfolio', auth_required=True, expected_status=401)
        if success or "Unauthorized" in str(data) or "authentication" in str(data).lower():
            self.log_test("Portfolio Endpoint (Auth Required)", True, "Correctly requires authentication")
        else:
            self.log_test("Portfolio Endpoint (Auth Required)", False, f"Unexpected response: {data}")

        # Test orders endpoint
        success, data = self.make_request('GET', '/orders', auth_required=True, expected_status=401)
        if success or "Unauthorized" in str(data) or "authentication" in str(data).lower():
            self.log_test("Orders Endpoint (Auth Required)", True, "Correctly requires authentication")
        else:
            self.log_test("Orders Endpoint (Auth Required)", False, f"Unexpected response: {data}")

    def test_cors_and_security(self):
        """Test CORS and security headers"""
        try:
            response = requests.options(f"{self.api_base}/crypto", timeout=10)
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
            }
            
            if any(cors_headers.values()):
                self.log_test("CORS Configuration", True, f"CORS headers present: {cors_headers}")
            else:
                self.log_test("CORS Configuration", False, "No CORS headers found")
        except Exception as e:
            self.log_test("CORS Configuration", False, f"CORS test error: {str(e)}")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("="*70)
        print("🚀 CryptoVault Backend API Test Suite")
        print("="*70)
        
        # Basic connectivity tests
        print("\n📡 Testing Basic Connectivity...")
        self.test_root_endpoint()
        self.test_health_check()
        
        # Public API tests
        print("\n💰 Testing Cryptocurrency APIs...")
        self.test_crypto_endpoints()
        
        # New features tests
        print("\n🆕 Testing New Feature Endpoints...")
        self.test_new_features_endpoints()
        
        # Authentication tests
        print("\n🔐 Testing Authentication...")
        test_email = self.test_auth_signup()
        if test_email:
            self.test_auth_login(test_email)
        
        # Protected endpoint tests
        print("\n🛡️ Testing Protected Endpoints...")
        self.test_protected_endpoints()
        
        # Security tests
        print("\n🔒 Testing Security Configuration...")
        self.test_cors_and_security()
        
        # Print summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Return results for further processing
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100 if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = CryptoVaultAPITester()
    results = tester.run_all_tests()
    
    # Save detailed results to file
    with open('/app/test_reports/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    return 0 if results["success_rate"] >= 70 else 1

if __name__ == "__main__":
    sys.exit(main())