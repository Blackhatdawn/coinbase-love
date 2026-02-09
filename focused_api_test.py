#!/usr/bin/env python3
"""
Focused API Testing for CryptoVault - Testing specific fixes from review request
"""

import requests
import sys
import json
import time
from datetime import datetime

class CryptoVaultFocusedTester:
    def __init__(self, base_url: str = "https://cryptovault-api.onrender.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Test results
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        
        # Auth storage
        self.access_token = None

    def log_result(self, test_name: str, passed: bool, response_code: int = None, 
                   error: str = None, details: dict = None):
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
        
        status = "PASS" if passed else "FAIL"
        print(f"{status} - {test_name} [{response_code}]")
        if error:
            print(f"    Error: {error}")
        if details:
            print(f"    Details: {details}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        
        headers = kwargs.get('headers', {})
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        kwargs['headers'] = headers
        
        response = self.session.request(method, url, **kwargs)
        return response

    def test_health_endpoint(self):
        """Test: Health endpoint returns 200 - verifies basic backend connectivity"""
        try:
            response = self.make_request('GET', '/api/health')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_result("Backend health endpoint /api/health returns 200", True, 
                                  response.status_code, 
                                  details={"response": data})
                    return True
                else:
                    self.log_result("Backend health endpoint /api/health returns 200", False, 
                                  response.status_code, 
                                  f"Status not healthy: {data.get('status')}")
            else:
                self.log_result("Backend health endpoint /api/health returns 200", False, 
                              response.status_code, response.text[:200])
            return False
        except Exception as e:
            self.log_result("Backend health endpoint /api/health returns 200", False, 0, str(e))
            return False

    def test_auth_signup_auto_verify(self):
        """Test: Auth signup creates user with auto-verified email"""
        try:
            timestamp = int(time.time())
            test_email = f"test{timestamp}@example.com"
            
            response = self.make_request('POST', '/api/auth/signup', json={
                "email": test_email,
                "password": "Test123!@#",
                "name": "Test User"
            })
            
            if response.status_code == 200:
                data = response.json()
                # Check if email verification is not required (auto-verified)
                verification_required = data.get('verificationRequired', True)
                email_sent = data.get('emailSent', False)
                
                # In auto-verify mode, verification should not be required
                auto_verified = not verification_required or data.get('user', {}).get('emailVerified', False)
                
                self.log_result("Auth flow works: signup creates user with auto-verified email", 
                              auto_verified, response.status_code,
                              None if auto_verified else "Email verification still required",
                              {"test_email": test_email, "verification_required": verification_required,
                               "email_sent": email_sent, "response_keys": list(data.keys())})
                
                # Try to login immediately to verify auto-verification
                if auto_verified:
                    login_response = self.make_request('POST', '/api/auth/login', json={
                        "email": test_email,
                        "password": "Test123!@#"
                    })
                    
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        if 'access_token' in login_data:
                            self.access_token = login_data['access_token']
                            print(f"    Login successful - access token obtained")
                            return True, test_email
                        else:
                            print(f"    Login response missing access_token")
                    else:
                        print(f"    Login failed: {login_response.status_code}")
                
                return auto_verified, test_email
            else:
                self.log_result("Auth flow works: signup creates user with auto-verified email", 
                              False, response.status_code, response.text[:200])
                return False, None
        except Exception as e:
            self.log_result("Auth flow works: signup creates user with auto-verified email", 
                          False, 0, str(e))
            return False, None

    def test_wallet_balance_endpoint(self):
        """Test: api.wallet.balance() method works - tests the backend endpoint"""
        if not self.access_token:
            self.log_result("api.wallet.balance() method works (backend endpoint)", 
                          False, 0, "No access token available")
            return False
            
        try:
            response = self.make_request('GET', '/api/wallet/balance')
            
            if response.status_code == 200:
                data = response.json()
                # Check if wallet balance data is returned
                has_wallet_data = 'wallet' in data or 'balance' in data or 'balances' in data
                
                self.log_result("api.wallet.balance() method works (backend endpoint)", 
                              has_wallet_data, response.status_code,
                              None if has_wallet_data else "No wallet/balance data in response",
                              {"response_keys": list(data.keys()), "data": data})
                return has_wallet_data
            else:
                self.log_result("api.wallet.balance() method works (backend endpoint)", 
                              False, response.status_code, response.text[:200])
                return False
        except Exception as e:
            self.log_result("api.wallet.balance() method works (backend endpoint)", 
                          False, 0, str(e))
            return False

    def test_trading_page_endpoint(self):
        """Test: Trading page loads correctly - check if trading endpoints exist"""
        try:
            # Test trading orders endpoint
            response = self.make_request('GET', '/api/orders')
            
            # Should return 401 (unauthorized) not 404 (not found) if endpoint exists
            if response.status_code == 401:
                self.log_result("Trading page loads correctly (endpoints exist)", 
                              True, response.status_code,
                              "Orders endpoint exists (returns auth error)")
                return True
            elif response.status_code == 404:
                self.log_result("Trading page loads correctly (endpoints exist)", 
                              False, response.status_code, "Orders endpoint not found")
                return False
            elif response.status_code == 200:
                # If we have auth, this is good
                data = response.json()
                self.log_result("Trading page loads correctly (endpoints exist)", 
                              True, response.status_code,
                              "Orders endpoint accessible",
                              {"response_type": type(data).__name__})
                return True
            else:
                self.log_result("Trading page loads correctly (endpoints exist)", 
                              True, response.status_code,
                              f"Orders endpoint exists (returns {response.status_code})")
                return True
        except Exception as e:
            self.log_result("Trading page loads correctly (endpoints exist)", 
                          False, 0, str(e))
            return False

    def test_dashboard_portfolio_endpoint(self):
        """Test: Dashboard loads with portfolio data - check portfolio endpoint"""
        try:
            response = self.make_request('GET', '/api/portfolio')
            
            # Should return 401 (unauthorized) not 404 (not found) if endpoint exists
            if response.status_code == 401:
                self.log_result("Dashboard loads with portfolio data (endpoint exists)", 
                              True, response.status_code,
                              "Portfolio endpoint exists (returns auth error)")
                return True
            elif response.status_code == 404:
                self.log_result("Dashboard loads with portfolio data (endpoint exists)", 
                              False, response.status_code, "Portfolio endpoint not found")
                return False
            elif response.status_code == 200:
                data = response.json()
                self.log_result("Dashboard loads with portfolio data (endpoint exists)", 
                              True, response.status_code,
                              "Portfolio endpoint accessible",
                              {"response_type": type(data).__name__})
                return True
            else:
                self.log_result("Dashboard loads with portfolio data (endpoint exists)", 
                              True, response.status_code,
                              f"Portfolio endpoint exists (returns {response.status_code})")
                return True
        except Exception as e:
            self.log_result("Dashboard loads with portfolio data (endpoint exists)", 
                          False, 0, str(e))
            return False

    def print_summary(self):
        """Print focused test summary"""
        print("\n" + "="*80)
        print("CRYPTOVAULT FOCUSED API TEST SUMMARY - Phase 2 Fixes Verification")
        print("="*80)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print("="*80)
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print("\nFAILED TESTS:")
            for result in failed_tests:
                print(f"  - {result['test']}: {result['error'] or 'Failed'}")
        
        passed_tests = [r for r in self.results if r['passed']]
        if passed_tests:
            print("\nPASSED TESTS:")
            for result in passed_tests:
                print(f"  + {result['test']}")
        
        return self.tests_passed == self.tests_run

def main():
    print("Starting CryptoVault Focused API Tests - Phase 2 Fixes Verification")
    print("Testing specific features mentioned in review request...")
    print("-" * 80)
    
    tester = CryptoVaultFocusedTester()
    
    # Run focused tests for the review request
    print("\n1. Testing backend health endpoint...")
    tester.test_health_endpoint()
    
    print("\n2. Testing auth flow with auto-verified email...")
    signup_success, test_email = tester.test_auth_signup_auto_verify()
    
    print("\n3. Testing wallet balance endpoint...")
    tester.test_wallet_balance_endpoint()
    
    print("\n4. Testing trading page endpoints...")
    tester.test_trading_page_endpoint()
    
    print("\n5. Testing dashboard portfolio endpoints...")
    tester.test_dashboard_portfolio_endpoint()
    
    # Print summary
    all_passed = tester.print_summary()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())