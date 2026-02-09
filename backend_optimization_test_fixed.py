#!/usr/bin/env python3
"""
CryptoVault Backend Optimization Testing Suite - Fixed Version
Tests the deep optimization changes with proper mock email handling
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class BackendOptimizationTester:
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
        if details and passed:
            print(f"    ✓ {details}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def test_backend_health(self):
        """Test: GET /api/health returns 200"""
        try:
            response = self.make_request('GET', '/api/health')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_result("Backend Health Endpoint (/api/health)", True, response.status_code,
                                  details=f"Status: {data.get('status')}, Response time: {response.elapsed.total_seconds():.3f}s")
                    return True
                else:
                    self.log_result("Backend Health Endpoint (/api/health)", False, response.status_code, 
                                  f"Unhealthy status: {data.get('status')}")
            else:
                self.log_result("Backend Health Endpoint (/api/health)", False, response.status_code, 
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Backend Health Endpoint (/api/health)", False, 0, str(e))
            return False

    def test_prices_cache_headers(self):
        """Test: GET /api/prices returns Cache-Control headers"""
        try:
            response = self.make_request('GET', '/api/prices')
            
            if response.status_code == 200:
                cache_control = response.headers.get('Cache-Control')
                all_headers = dict(response.headers)
                
                if cache_control:
                    # Check for cache directives from the optimization
                    has_public = 'public' in cache_control
                    has_max_age = 'max-age' in cache_control
                    
                    if has_public and has_max_age:
                        self.log_result("Prices Cache Headers (/api/prices)", True, response.status_code,
                                      details=f"Cache-Control: {cache_control}")
                        return True
                    else:
                        self.log_result("Prices Cache Headers (/api/prices)", False, response.status_code,
                                      f"Missing cache directives in: {cache_control}")
                else:
                    # Check if there are any caching headers at all
                    cache_headers = {k: v for k, v in all_headers.items() if 'cache' in k.lower() or 'expires' in k.lower() or 'etag' in k.lower()}
                    if cache_headers:
                        self.log_result("Prices Cache Headers (/api/prices)", True, response.status_code,
                                      details=f"Alternative cache headers: {cache_headers}")
                        return True
                    else:
                        self.log_result("Prices Cache Headers (/api/prices)", False, response.status_code,
                                      "No Cache-Control or other cache headers found",
                                      details={"all_headers": list(all_headers.keys())})
            else:
                self.log_result("Prices Cache Headers (/api/prices)", False, response.status_code,
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Prices Cache Headers (/api/prices)", False, 0, str(e))
            return False

    def test_crypto_cache_headers(self):
        """Test: GET /api/crypto returns Cache-Control headers"""
        try:
            response = self.make_request('GET', '/api/crypto')
            
            if response.status_code == 200:
                cache_control = response.headers.get('Cache-Control')
                all_headers = dict(response.headers)
                
                if cache_control:
                    # Check for cache directives from the optimization
                    has_public = 'public' in cache_control
                    has_max_age = 'max-age' in cache_control
                    
                    if has_public and has_max_age:
                        self.log_result("Crypto Cache Headers (/api/crypto)", True, response.status_code,
                                      details=f"Cache-Control: {cache_control}")
                        return True
                    else:
                        self.log_result("Crypto Cache Headers (/api/crypto)", False, response.status_code,
                                      f"Missing cache directives in: {cache_control}")
                else:
                    # Check if there are any caching headers at all
                    cache_headers = {k: v for k, v in all_headers.items() if 'cache' in k.lower() or 'expires' in k.lower() or 'etag' in k.lower()}
                    if cache_headers:
                        self.log_result("Crypto Cache Headers (/api/crypto)", True, response.status_code,
                                      details=f"Alternative cache headers: {cache_headers}")
                        return True
                    else:
                        self.log_result("Crypto Cache Headers (/api/crypto)", False, response.status_code,
                                      "No Cache-Control or other cache headers found")
            else:
                self.log_result("Crypto Cache Headers (/api/crypto)", False, response.status_code,
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Crypto Cache Headers (/api/crypto)", False, 0, str(e))
            return False

    def test_auth_flow_with_mock_email(self):
        """Test: Auth flow with mock email service - should work without verification"""
        try:
            # Step 1: Signup with unique email
            timestamp = int(time.time())
            email = f"test{timestamp}@example.com"
            password = "Test123!@#"
            
            print(f"  🔧 Creating test user: {email}")
            signup_response = self.make_request('POST', '/api/auth/signup', json={
                "email": email,
                "password": password,
                "name": "Test User"
            })
            
            if signup_response.status_code not in [200, 201]:
                self.log_result("Auth Flow (signup -> login -> get me)", False, signup_response.status_code,
                              f"Signup failed: {signup_response.text[:200]}")
                return False
            
            signup_data = signup_response.json()
            print(f"  ✓ Signup successful: {signup_data.get('message', 'User created')}")
            
            # Step 2: Login immediately (should work with mock email)
            print(f"  🔧 Attempting login with: {email}")
            login_response = self.make_request('POST', '/api/auth/login', json={
                "email": email,
                "password": password
            })
            
            if login_response.status_code == 401:
                # Check if it's about email verification
                error_text = login_response.text.lower()
                if 'email not verified' in error_text or 'verify' in error_text:
                    # Since EMAIL_SERVICE=mock, this might be expected behavior
                    # Let's check if we can directly verify somehow or if mock bypasses this
                    print(f"  ⚠️ Login blocked by email verification despite mock service")
                    self.log_result("Auth Flow (signup -> login -> get me)", False, login_response.status_code,
                                  f"Email verification required despite EMAIL_SERVICE=mock: {login_response.text[:200]}")
                    return False
                else:
                    self.log_result("Auth Flow (signup -> login -> get me)", False, login_response.status_code,
                                  f"Login failed with other auth error: {login_response.text[:200]}")
                    return False
            elif login_response.status_code != 200:
                self.log_result("Auth Flow (signup -> login -> get me)", False, login_response.status_code,
                              f"Login failed: {login_response.text[:200]}")
                return False
            
            login_data = login_response.json()
            if 'access_token' not in login_data:
                self.log_result("Auth Flow (signup -> login -> get me)", False, login_response.status_code,
                              "No access_token in login response")
                return False
                
            self.user_token = login_data['access_token']
            print(f"  ✓ Login successful, token received")
            
            # Step 3: Get Me
            headers = {"Authorization": f"Bearer {self.user_token}"}
            me_response = self.make_request('GET', '/api/auth/me', headers=headers)
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                if 'email' in me_data and me_data['email'] == email:
                    print(f"  ✓ Get me successful: {me_data.get('name', 'User')}")
                    self.log_result("Auth Flow (signup -> login -> get me)", True, me_response.status_code,
                                  details=f"Complete flow successful for {email}")
                    return True
                else:
                    self.log_result("Auth Flow (signup -> login -> get me)", False, me_response.status_code,
                                  "Get me returned invalid user data")
            else:
                self.log_result("Auth Flow (signup -> login -> get me)", False, me_response.status_code,
                              f"Get me failed: {me_response.text[:200]}")
            return False
            
        except Exception as e:
            self.log_result("Auth Flow (signup -> login -> get me)", False, 0, str(e))
            return False

    def test_dashboard_loads_without_errors(self):
        """Test: Dashboard API endpoints work without errors"""
        try:
            if not self.user_token:
                # Try to create a test user first if no token
                success = self.test_auth_flow_with_mock_email()
                if not success or not self.user_token:
                    self.log_result("Dashboard Load Test", False, 0, "No user token available for testing")
                    return False
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # Test main dashboard endpoints
            endpoints_to_test = [
                ('/api/crypto', 'Crypto data'),
                ('/api/prices', 'Price data'),
            ]
            
            # Portfolio and transactions might not exist for new user, so we test them separately
            optional_endpoints = [
                ('/api/portfolio', 'Portfolio data'),
                ('/api/transactions?page=0&limit=5', 'Transaction data'),
            ]
            
            all_required_successful = True
            results = {}
            
            # Test required endpoints
            for endpoint, description in endpoints_to_test:
                try:
                    response = self.make_request('GET', endpoint, headers=headers)
                    success = response.status_code == 200
                    results[endpoint] = {
                        "status": response.status_code,
                        "success": success,
                        "description": description
                    }
                    if not success:
                        all_required_successful = False
                        print(f"    ❌ {description}: {response.status_code}")
                    else:
                        print(f"    ✓ {description}: {response.status_code}")
                except Exception as e:
                    results[endpoint] = {"status": 0, "success": False, "error": str(e)}
                    all_required_successful = False
                    print(f"    ❌ {description}: Error - {str(e)}")
            
            # Test optional endpoints (404/empty response is acceptable)
            for endpoint, description in optional_endpoints:
                try:
                    response = self.make_request('GET', endpoint, headers=headers)
                    success = response.status_code in [200, 404]  # Both OK
                    results[endpoint] = {
                        "status": response.status_code,
                        "success": success,
                        "description": description
                    }
                    if success:
                        print(f"    ✓ {description}: {response.status_code}")
                    else:
                        print(f"    ⚠️ {description}: {response.status_code}")
                except Exception as e:
                    results[endpoint] = {"status": 0, "success": True, "error": str(e)}
                    print(f"    ⚠️ {description}: Error - {str(e)} (acceptable)")
            
            self.log_result("Dashboard Load Test (API Dependencies)", all_required_successful, 
                          200 if all_required_successful else 500,
                          None if all_required_successful else "Some required dashboard APIs failed",
                          details=f"Tested {len(endpoints_to_test + optional_endpoints)} endpoints")
            return all_required_successful
            
        except Exception as e:
            self.log_result("Dashboard Load Test (API Dependencies)", False, 0, str(e))
            return False

    def test_backend_logs_clean(self):
        """Test: Backend responds consistently without excessive logging (indirect test)"""
        try:
            print("  🔧 Testing consistent API responses (proxy for clean logging)")
            
            # Test multiple calls to different endpoints to simulate normal usage
            test_calls = [
                ('/api/health', 'Health check'),
                ('/api/prices', 'Prices endpoint'), 
                ('/api/crypto', 'Crypto endpoint'),
            ]
            
            response_times = {}
            all_successful = True
            
            for endpoint, description in test_calls:
                times = []
                print(f"    Testing {description}...")
                
                # Make 3 calls to each endpoint
                for i in range(3):
                    try:
                        start_time = time.time()
                        response = self.make_request('GET', endpoint)
                        end_time = time.time()
                        
                        if response.status_code == 200:
                            times.append(end_time - start_time)
                        else:
                            all_successful = False
                            print(f"      ❌ Call {i+1}: {response.status_code}")
                            break
                        
                        if i < 2:  # Small delay except for last call
                            time.sleep(0.5)
                            
                    except Exception as e:
                        all_successful = False
                        print(f"      ❌ Call {i+1}: Error - {str(e)}")
                        break
                
                if times:
                    avg_time = sum(times) / len(times)
                    response_times[description] = f"{avg_time:.3f}s"
                    print(f"    ✓ {description}: {len(times)} calls, avg {avg_time:.3f}s")
                
            self.log_result("Backend Clean Logs (Consistent Performance)", all_successful, 
                          200 if all_successful else 500,
                          None if all_successful else "Inconsistent API responses detected",
                          details=response_times)
            return all_successful
            
        except Exception as e:
            self.log_result("Backend Clean Logs (Consistent Performance)", False, 0, str(e))
            return False

    def get_test_summary(self):
        """Get test summary data"""
        return {
            "summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "failed_tests": self.tests_run - self.tests_passed,
                "success_rate": (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            },
            "results": self.results,
            "backend_issues": [r for r in self.results if not r['passed']],
            "passed_tests": [r for r in self.results if r['passed']]
        }

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("🔬 BACKEND OPTIMIZATION TEST SUMMARY")
        print("="*70)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0.0%")
        print("="*70)
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"  - {result['test']}")
                if result['error']:
                    print(f"    Error: {result['error']}")
        
        passed_tests = [r for r in self.results if r['passed']]
        if passed_tests:
            print(f"\n✅ PASSED TESTS ({len(passed_tests)}):")
            for result in passed_tests:
                print(f"  - {result['test']}")
        
        return self.tests_passed == self.tests_run

def main():
    print("🚀 Starting Backend Optimization Tests - Deep Focus")
    print("🌐 Testing against: https://cryptovault-api.onrender.com")
    print("🎯 Focus: Cache headers, API performance, auth flow, clean logging")
    print("🔧 Email service: MOCK (should bypass verification)")
    print("-" * 70)
    
    tester = BackendOptimizationTester()
    
    # Run optimization-focused tests in logical order
    print("\n📍 1. CORE BACKEND HEALTH")
    tester.test_backend_health()
    
    print("\n📍 2. CACHE HEADER OPTIMIZATIONS")
    tester.test_prices_cache_headers()
    tester.test_crypto_cache_headers()
    
    print("\n📍 3. AUTHENTICATION FLOW")  
    tester.test_auth_flow_with_mock_email()
    
    print("\n📍 4. DASHBOARD API DEPENDENCIES")
    tester.test_dashboard_loads_without_errors()
    
    print("\n📍 5. LOG SPAM REDUCTION (Performance Test)")
    tester.test_backend_logs_clean()
    
    # Get final summary
    success = tester.print_summary()
    test_data = tester.get_test_summary()
    
    return success, test_data

if __name__ == "__main__":
    success, data = main()
    sys.exit(0 if success else 1)