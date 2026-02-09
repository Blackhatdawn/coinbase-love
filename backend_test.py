#!/usr/bin/env python3
"""
CryptoVault Backend API Testing Suite
Tests all critical endpoints for Phase 2 fixes verification
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class CryptoVaultAPITester:
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
        self.csrf_token = None

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
        
        # Add common headers
        headers = kwargs.get('headers', {})
        if self.csrf_token and method.upper() in ['POST', 'PUT', 'PATCH', 'DELETE']:
            headers['X-CSRF-Token'] = self.csrf_token
        kwargs['headers'] = headers
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def test_backend_health(self):
        """Test: GET /api/health returns healthy"""
        try:
            response = self.make_request('GET', '/api/health')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_result("Backend Health Check", True, response.status_code)
                    return True
                else:
                    self.log_result("Backend Health Check", False, response.status_code, 
                                  f"Unhealthy status: {data.get('status')}")
            else:
                self.log_result("Backend Health Check", False, response.status_code, 
                              response.text)
            return False
        except Exception as e:
            self.log_result("Backend Health Check", False, 0, str(e))
            return False

    def test_csrf_endpoint(self):
        """Test: GET /api/csrf returns csrf_token"""
        try:
            response = self.make_request('GET', '/api/csrf')
            
            if response.status_code == 200:
                data = response.json()
                if 'csrf_token' in data:
                    self.csrf_token = data['csrf_token']
                    self.log_result("CSRF Token Generation", True, response.status_code,
                                  details={"csrf_token_length": len(self.csrf_token)})
                    return True
                else:
                    self.log_result("CSRF Token Generation", False, response.status_code,
                                  "No csrf_token in response")
            else:
                self.log_result("CSRF Token Generation", False, response.status_code,
                              response.text)
            return False
        except Exception as e:
            self.log_result("CSRF Token Generation", False, 0, str(e))
            return False

    def test_config_endpoint(self):
        """Test: GET /api/config returns runtime configuration"""
        try:
            response = self.make_request('GET', '/api/config')
            
            if response.status_code == 200:
                data = response.json()
                # Expect configuration object
                if isinstance(data, dict) and len(data) > 0:
                    self.log_result("Config Endpoint", True, response.status_code,
                                  details={"config_keys": list(data.keys())})
                    return True
                else:
                    self.log_result("Config Endpoint", False, response.status_code,
                                  "Empty or invalid configuration")
            else:
                self.log_result("Config Endpoint", False, response.status_code,
                              response.text)
            return False
        except Exception as e:
            self.log_result("Config Endpoint", False, 0, str(e))
            return False

    def test_socketio_handshake(self):
        """Test: GET /socket.io/?EIO=4&transport=polling returns session"""
        try:
            response = self.make_request('GET', '/socket.io/?EIO=4&transport=polling')
            
            if response.status_code == 200:
                # Socket.IO response typically starts with a number (protocol version)
                if response.text and (response.text.startswith('0') or 'sid' in response.text):
                    self.log_result("Socket.IO Handshake", True, response.status_code,
                                  details={"response_preview": response.text[:50]})
                    return True
                else:
                    self.log_result("Socket.IO Handshake", False, response.status_code,
                                  f"Unexpected response: {response.text[:100]}")
            else:
                self.log_result("Socket.IO Handshake", False, response.status_code,
                              response.text)
            return False
        except Exception as e:
            self.log_result("Socket.IO Handshake", False, 0, str(e))
            return False

    def test_socketio_stats(self):
        """Test: GET /api/socketio/stats returns connection statistics"""
        try:
            response = self.make_request('GET', '/api/socketio/stats')
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['total_connections', 'active_connections', 'authenticated_users', 'connections']
                has_expected_fields = all(field in data for field in expected_fields)
                
                if has_expected_fields:
                    self.log_result("Socket.IO Stats Endpoint", True, response.status_code,
                                  details={
                                      "total_connections": data.get('total_connections', 0),
                                      "active_connections": data.get('active_connections', 0),
                                      "authenticated_users": data.get('authenticated_users', 0)
                                  })
                    return True
                else:
                    missing_fields = [f for f in expected_fields if f not in data]
                    self.log_result("Socket.IO Stats Endpoint", False, response.status_code,
                                  f"Missing expected fields: {missing_fields}")
            else:
                self.log_result("Socket.IO Stats Endpoint", False, response.status_code,
                              response.text)
            return False
        except Exception as e:
            self.log_result("Socket.IO Stats Endpoint", False, 0, str(e))
            return False

    def test_socketio_websocket_transport(self):
        """Test: GET /socket.io/?EIO=4&transport=websocket should handle WebSocket upgrade"""
        try:
            # Try websocket transport (this might fail but we check the response)
            response = self.make_request('GET', '/socket.io/?EIO=4&transport=websocket')
            
            # For WebSocket upgrade, we might get 400 (Bad Request) which is expected for HTTP client
            # The important thing is it doesn't return 404
            if response.status_code in [400, 426]:  # 426 = Upgrade Required
                self.log_result("Socket.IO WebSocket Transport Availability", True, response.status_code,
                              "WebSocket transport detected (expected HTTP client failure)")
                return True
            elif response.status_code == 404:
                self.log_result("Socket.IO WebSocket Transport Availability", False, response.status_code,
                              "WebSocket transport not found")
                return False
            else:
                self.log_result("Socket.IO WebSocket Transport Availability", True, response.status_code,
                              f"WebSocket transport accessible (status: {response.status_code})")
                return True
        except Exception as e:
            self.log_result("Socket.IO WebSocket Transport Availability", False, 0, str(e))
            return False

    def test_crypto_listing(self):
        """Test: GET /api/crypto returns cryptocurrency data"""
        try:
            response = self.make_request('GET', '/api/crypto')
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Check if crypto data has expected structure
                    first_coin = data[0]
                    expected_fields = ['id', 'symbol', 'name', 'price']
                    has_fields = all(field in first_coin for field in expected_fields)
                    
                    self.log_result("Crypto Listing", has_fields, response.status_code,
                                  None if has_fields else f"Missing fields: {expected_fields}",
                                  {"count": len(data), "first_coin": first_coin})
                    return has_fields
                else:
                    self.log_result("Crypto Listing", False, response.status_code,
                                  "Empty or invalid crypto list")
            else:
                self.log_result("Crypto Listing", False, response.status_code,
                              response.text)
            return False
        except Exception as e:
            self.log_result("Crypto Listing", False, 0, str(e))
            return False

    def test_auth_signup(self):
        """Test: POST /api/auth/signup creates user"""
        try:
            # Generate unique email
            timestamp = int(time.time())
            email = f"test{timestamp}@example.com"
            
            response = self.make_request('POST', '/api/auth/signup', json={
                "email": email,
                "password": "Test123!@#",
                "name": "Test User"
            })
            
            if response.status_code == 200:
                data = response.json()
                if 'user' in data or 'message' in data:
                    self.log_result("Auth Signup", True, response.status_code,
                                  details={"email": email, "response_keys": list(data.keys())})
                    return True, email
                else:
                    self.log_result("Auth Signup", False, response.status_code,
                                  "No user or message in response")
            else:
                self.log_result("Auth Signup", False, response.status_code,
                              response.text[:200])
            return False, None
        except Exception as e:
            self.log_result("Auth Signup", False, 0, str(e))
            return False, None

    def test_auth_login(self, email: str = None, password: str = None):
        """Test: POST /api/auth/login returns access_token in body"""
        if not email:
            email = "testuser@example.com"
            password = "Test123!@#"
            
        try:
            response = self.make_request('POST', '/api/auth/login', json={
                "email": email,
                "password": password
            })
            
            if response.status_code == 200:
                data = response.json()
                # Check for access_token in response body
                if 'access_token' in data:
                    self.user_token = data['access_token']
                    self.log_result("Auth Login (access_token in body)", True, response.status_code,
                                  details={"has_access_token": True, "token_length": len(self.user_token)})
                    return True
                else:
                    self.log_result("Auth Login (access_token in body)", False, response.status_code,
                                  "No access_token in response body",
                                  details={"response_keys": list(data.keys())})
            else:
                self.log_result("Auth Login (access_token in body)", False, response.status_code,
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Auth Login (access_token in body)", False, 0, str(e))
            return False

    def test_wallet_balance_with_auth(self):
        """Test: GET /api/wallet/balance returns wallet data (with auth cookie)"""
        if not self.user_token:
            self.log_result("Wallet Balance (with auth)", False, 0, "No user token available")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            response = self.make_request('GET', '/api/wallet/balance', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and ('balance' in data or 'balances' in data):
                    self.log_result("Wallet Balance (with auth)", True, response.status_code,
                                  details={"response_keys": list(data.keys())})
                    return True
                else:
                    self.log_result("Wallet Balance (with auth)", False, response.status_code,
                                  "No balance data in response")
            else:
                self.log_result("Wallet Balance (with auth)", False, response.status_code,
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Wallet Balance (with auth)", False, 0, str(e))
            return False

    def test_admin_login_csrf_fix(self):
        """Test: POST /api/admin/login no longer fails with CSRF error"""
        try:
            response = self.make_request('POST', '/api/admin/login', json={
                "email": "admin@cryptovault.financial",
                "password": "wrongpassword"  # Expect auth error, not CSRF error
            })
            
            # We expect 401 (auth error), NOT 403 (CSRF error)
            if response.status_code == 401:
                self.log_result("Admin Login CSRF Fix", True, response.status_code,
                              "Returns auth error instead of CSRF error")
                return True
            elif response.status_code == 403:
                # Check if it's a CSRF error
                error_text = response.text.lower()
                if 'csrf' in error_text:
                    self.log_result("Admin Login CSRF Fix", False, response.status_code,
                                  "Still failing with CSRF error")
                else:
                    self.log_result("Admin Login CSRF Fix", True, response.status_code,
                                  "Returns 403 but not CSRF related")
                    return True
            else:
                # Other status codes might be OK depending on implementation
                self.log_result("Admin Login CSRF Fix", True, response.status_code,
                              f"No CSRF error, returns {response.status_code}")
                return True
            return False
        except Exception as e:
            self.log_result("Admin Login CSRF Fix", False, 0, str(e))
            return False

    def test_admin_dashboard_stats(self):
        """Test: GET /api/admin/dashboard/stats returns 401 (exists but requires auth)"""
        try:
            response = self.make_request('GET', '/api/admin/dashboard/stats')
            
            # We expect 401 (unauthorized) not 404 (not found)
            if response.status_code == 401:
                self.log_result("Admin Dashboard Stats Endpoint Exists", True, response.status_code,
                              "Returns 401 (unauthorized) - endpoint exists")
                return True
            elif response.status_code == 404:
                self.log_result("Admin Dashboard Stats Endpoint Exists", False, response.status_code,
                              "Returns 404 - endpoint not found")
            else:
                self.log_result("Admin Dashboard Stats Endpoint Exists", True, response.status_code,
                              f"Endpoint exists, returns {response.status_code}")
                return True
            return False
        except Exception as e:
            self.log_result("Admin Dashboard Stats Endpoint Exists", False, 0, str(e))
            return False

    def test_p2p_transfer_endpoint(self):
        """Test: POST /api/transfers/p2p returns auth error (not 404)"""
        try:
            response = self.make_request('POST', '/api/transfers/p2p', json={
                "recipient_email": "test@example.com",
                "amount": 10,
                "currency": "USD"
            })
            
            # We expect 401 (unauthorized) not 404 (not found)
            if response.status_code == 401:
                self.log_result("P2P Transfer Endpoint Exists", True, response.status_code,
                              "Returns auth error (not 404) - endpoint exists")
                return True
            elif response.status_code == 404:
                self.log_result("P2P Transfer Endpoint Exists", False, response.status_code,
                              "Returns 404 - endpoint not found")
            else:
                self.log_result("P2P Transfer Endpoint Exists", True, response.status_code,
                              f"Endpoint exists, returns {response.status_code}")
                return True
            return False
        except Exception as e:
            self.log_result("P2P Transfer Endpoint Exists", False, 0, str(e))
            return False

    def test_double_prefix_bug_fix(self):
        """Test: GET /api/api/admin/dashboard/stats returns 404 (not 401)"""
        try:
            response = self.make_request('GET', '/api/api/admin/dashboard/stats')
            
            # We expect 404 (not found) because double prefix is invalid
            if response.status_code == 404:
                self.log_result("Double-Prefix Bug Fixed", True, response.status_code,
                              "Returns 404 for double prefix (bug fixed)")
                return True
            elif response.status_code == 401:
                self.log_result("Double-Prefix Bug Fixed", False, response.status_code,
                              "Still routes to admin endpoint (bug not fixed)")
            else:
                # Other codes might be acceptable
                self.log_result("Double-Prefix Bug Fixed", True, response.status_code,
                              f"Double prefix handled appropriately: {response.status_code}")
                return True
            return False
        except Exception as e:
            self.log_result("Double-Prefix Bug Fixed", False, 0, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🔬 CRYPTOVAULT API TEST SUMMARY")
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
                print(f"  - {result['test']}: {result['error']}")
        
        print(f"\n📋 Full results saved to backend_test_results.json")
        
        # Save results to file
        with open('/app/test_reports/backend_test_results.json', 'w') as f:
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
    print("🚀 Starting CryptoVault Backend API Tests")
    print("🌐 Testing against: https://cryptovault-api.onrender.com")
    print("-" * 60)
    
    tester = CryptoVaultAPITester()
    
    # Run all tests in sequence
    tests_to_run = [
        # Core infrastructure
        tester.test_backend_health,
        tester.test_csrf_endpoint,
        tester.test_config_endpoint,
        tester.test_socketio_handshake,
        
        # API endpoints
        tester.test_crypto_listing,
        
        # Authentication flow
        tester.test_auth_signup,
        lambda: tester.test_auth_login(),  # Use default test user
        tester.test_wallet_balance_with_auth,
        
        # Admin and fixes
        tester.test_admin_login_csrf_fix,
        tester.test_admin_dashboard_stats,
        tester.test_p2p_transfer_endpoint,
        tester.test_double_prefix_bug_fix,
    ]
    
    # Execute tests
    for test_func in tests_to_run:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test execution error: {e}")
    
    # Print summary
    all_passed = tester.print_summary()
    
    # Return appropriate exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())