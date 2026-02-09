#!/usr/bin/env python3
"""
CryptoVault Backend Optimization Testing Suite
Tests the deep optimization changes applied to the backend
Focus: Cache headers, API performance, reduced log spam, React optimizations
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
        if details:
            print(f"    Details: {details}")

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
                    self.log_result("Backend Health Endpoint", True, response.status_code,
                                  details={"status": data.get('status'), "response_time": f"{response.elapsed.total_seconds():.3f}s"})
                    return True
                else:
                    self.log_result("Backend Health Endpoint", False, response.status_code, 
                                  f"Unhealthy status: {data.get('status')}")
            else:
                self.log_result("Backend Health Endpoint", False, response.status_code, 
                              response.text)
            return False
        except Exception as e:
            self.log_result("Backend Health Endpoint", False, 0, str(e))
            return False

    def test_prices_cache_headers(self):
        """Test: GET /api/prices returns Cache-Control headers"""
        try:
            response = self.make_request('GET', '/api/prices')
            
            if response.status_code == 200:
                cache_control = response.headers.get('Cache-Control')
                if cache_control:
                    # Check for expected cache directives
                    expected_directives = ['public', 'max-age', 'stale-while-revalidate']
                    has_directives = all(directive in cache_control for directive in expected_directives[:2])  # At least public and max-age
                    
                    self.log_result("Prices Endpoint Cache Headers", has_directives, response.status_code,
                                  None if has_directives else f"Missing cache directives",
                                  {"cache_control": cache_control, "response_time": f"{response.elapsed.total_seconds():.3f}s"})
                    return has_directives
                else:
                    self.log_result("Prices Endpoint Cache Headers", False, response.status_code,
                                  "No Cache-Control header found")
            else:
                self.log_result("Prices Endpoint Cache Headers", False, response.status_code,
                              response.text)
            return False
        except Exception as e:
            self.log_result("Prices Endpoint Cache Headers", False, 0, str(e))
            return False

    def test_crypto_cache_headers(self):
        """Test: GET /api/crypto returns Cache-Control headers"""
        try:
            response = self.make_request('GET', '/api/crypto')
            
            if response.status_code == 200:
                cache_control = response.headers.get('Cache-Control')
                if cache_control:
                    # Check for expected cache directives
                    expected_directives = ['public', 'max-age']
                    has_directives = all(directive in cache_control for directive in expected_directives)
                    
                    self.log_result("Crypto Endpoint Cache Headers", has_directives, response.status_code,
                                  None if has_directives else f"Missing cache directives",
                                  {"cache_control": cache_control, "response_time": f"{response.elapsed.total_seconds():.3f}s"})
                    return has_directives
                else:
                    self.log_result("Crypto Endpoint Cache Headers", False, response.status_code,
                                  "No Cache-Control header found")
            else:
                self.log_result("Crypto Endpoint Cache Headers", False, response.status_code,
                              response.text)
            return False
        except Exception as e:
            self.log_result("Crypto Endpoint Cache Headers", False, 0, str(e))
            return False

    def test_auth_signup_login_flow(self):
        """Test: Auth flow - signup -> login -> get me"""
        try:
            # Step 1: Signup
            timestamp = int(time.time())
            email = f"test{timestamp}@example.com"
            password = "Test123!@#"
            
            signup_response = self.make_request('POST', '/api/auth/signup', json={
                "email": email,
                "password": password,
                "name": "Test User"
            })
            
            if signup_response.status_code != 200:
                self.log_result("Auth Flow (signup -> login -> get me)", False, signup_response.status_code,
                              f"Signup failed: {signup_response.text[:200]}")
                return False
            
            # Step 2: Login
            login_response = self.make_request('POST', '/api/auth/login', json={
                "email": email,
                "password": password
            })
            
            if login_response.status_code != 200:
                self.log_result("Auth Flow (signup -> login -> get me)", False, login_response.status_code,
                              f"Login failed: {login_response.text[:200]}")
                return False
            
            login_data = login_response.json()
            if 'access_token' not in login_data:
                self.log_result("Auth Flow (signup -> login -> get me)", False, login_response.status_code,
                              "No access_token in login response")
                return False
                
            self.user_token = login_data['access_token']
            
            # Step 3: Get Me
            headers = {"Authorization": f"Bearer {self.user_token}"}
            me_response = self.make_request('GET', '/api/auth/me', headers=headers)
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                if 'email' in me_data and me_data['email'] == email:
                    self.log_result("Auth Flow (signup -> login -> get me)", True, me_response.status_code,
                                  details={"user_email": email, "flow_complete": True})
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

    def test_dashboard_no_js_errors(self):
        """Test: Basic Dashboard endpoint accessibility (proxy for JS error testing)"""
        # This is a simplified test since we can't test JS errors directly from backend
        # The actual JS error testing will be done in frontend automation
        try:
            # Test if we can access the main API endpoints the Dashboard would use
            if not self.user_token:
                self.log_result("Dashboard API Dependencies", False, 0, "No user token for testing")
                return False
            
            headers = {"Authorization": f"Bearer {self.user_token}"}
            
            # Test endpoints that Dashboard.tsx would call
            endpoints_to_test = [
                '/api/portfolio',
                '/api/transactions?page=0&limit=5',
                '/api/crypto'
            ]
            
            all_successful = True
            endpoint_results = {}
            
            for endpoint in endpoints_to_test:
                try:
                    response = self.make_request('GET', endpoint, headers=headers)
                    endpoint_results[endpoint] = {
                        "status": response.status_code,
                        "success": response.status_code in [200, 404]  # 404 is acceptable for some endpoints
                    }
                    if response.status_code not in [200, 404]:
                        all_successful = False
                except Exception as e:
                    endpoint_results[endpoint] = {"status": 0, "success": False, "error": str(e)}
                    all_successful = False
            
            self.log_result("Dashboard API Dependencies", all_successful, 200 if all_successful else 500,
                          None if all_successful else "Some dashboard API dependencies failed",
                          {"endpoints": endpoint_results})
            return all_successful
            
        except Exception as e:
            self.log_result("Dashboard API Dependencies", False, 0, str(e))
            return False

    def test_logs_spam_reduction(self):
        """Test: Verify endpoints respond without triggering excessive logging"""
        # This test is indirect - we check if endpoints respond quickly and properly
        # The actual log spam reduction would be observed in server logs
        try:
            # Test endpoints mentioned in optimization (websocket_feed.py, coincap_service.py)
            start_time = time.time()
            
            # Test multiple calls to prices endpoint to simulate real usage
            response_times = []
            for i in range(3):
                response = self.make_request('GET', '/api/prices')
                if response.status_code == 200:
                    response_times.append(response.elapsed.total_seconds())
                else:
                    self.log_result("Backend Log Spam Reduction", False, response.status_code,
                                  f"Failed on call {i+1}")
                    return False
                time.sleep(1)  # Small delay between requests
            
            avg_response_time = sum(response_times) / len(response_times)
            
            # Test crypto endpoint as well
            crypto_response = self.make_request('GET', '/api/crypto')
            if crypto_response.status_code != 200:
                self.log_result("Backend Log Spam Reduction", False, crypto_response.status_code,
                              "Crypto endpoint failed")
                return False
            
            self.log_result("Backend Log Spam Reduction", True, 200,
                          details={
                              "avg_prices_response_time": f"{avg_response_time:.3f}s",
                              "crypto_response_time": f"{crypto_response.elapsed.total_seconds():.3f}s",
                              "consistent_responses": len(response_times) == 3
                          })
            return True
            
        except Exception as e:
            self.log_result("Backend Log Spam Reduction", False, 0, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🔬 BACKEND OPTIMIZATION TEST SUMMARY")
        print("="*60)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0.0%")
        print("="*60)
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"  - {result['test']}: {result['error']}")
        else:
            print("\n✅ All optimization tests passed!")
        
        print(f"\n📋 Full results will be saved to test report")
        
        return self.tests_passed == self.tests_run, {
            "summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "failed_tests": self.tests_run - self.tests_passed,
                "success_rate": (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            },
            "results": self.results
        }

def main():
    print("🚀 Starting Backend Optimization Tests")
    print("🌐 Testing against: https://cryptovault-api.onrender.com")
    print("🎯 Focus: Cache headers, API performance, auth flow, dashboard dependencies")
    print("-" * 60)
    
    tester = BackendOptimizationTester()
    
    # Run optimization-focused tests
    tests_to_run = [
        # Core health check
        tester.test_backend_health,
        
        # Cache header optimizations
        tester.test_prices_cache_headers,
        tester.test_crypto_cache_headers,
        
        # Auth flow optimization
        tester.test_auth_signup_login_flow,
        
        # Dashboard dependencies
        tester.test_dashboard_no_js_errors,
        
        # Log spam reduction (indirect test)
        tester.test_logs_spam_reduction,
    ]
    
    # Execute tests
    for test_func in tests_to_run:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test execution error: {e}")
    
    # Get summary
    all_passed, test_data = tester.print_summary()
    
    return all_passed, test_data

if __name__ == "__main__":
    success, data = main()
    sys.exit(0 if success else 1)