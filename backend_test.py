#!/usr/bin/env python3
"""
Auth Flow Testing Suite for CryptoVault
Tests signup, login, logout, and session persistence flows
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class AuthFlowTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        
        # Test user data
        self.test_email = f"newuser{int(time.time())}@test.com"
        self.test_password = "TestPass123!"
        self.test_name = "Test User Auth"
        
        print(f"🧪 Test credentials: {self.test_email} / {self.test_password}")

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
        print(f"{status} - {test_name}")
        if response_code:
            print(f"    Status: {response_code}")
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

    def test_signup_flow(self):
        """Test: POST /api/auth/signup creates new account and auto-logs in"""
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password,
                "name": self.test_name
            }
            
            response = self.make_request('POST', '/api/auth/signup', json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['user', 'message']
                has_required = all(field in data for field in required_fields)
                
                if has_required:
                    # Check if auto-login happened (access_token in response for mocked email)
                    auto_login = 'access_token' in data
                    verification_required = data.get('verificationRequired', True)
                    
                    # Check cookies for auth tokens
                    cookies = response.cookies
                    has_auth_cookies = 'access_token' in cookies and 'refresh_token' in cookies
                    
                    self.log_result("Signup Flow", True, response.status_code,
                                  details={
                                      "auto_login": auto_login,
                                      "verification_required": verification_required,
                                      "has_auth_cookies": has_auth_cookies,
                                      "user_id": data.get('user', {}).get('id'),
                                      "message": data.get('message')
                                  })
                    return True, auto_login, has_auth_cookies
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Signup Flow", False, response.status_code,
                                  f"Missing required fields: {missing}")
            else:
                self.log_result("Signup Flow", False, response.status_code,
                              response.text[:200])
            return False, False, False
        except Exception as e:
            self.log_result("Signup Flow", False, 0, str(e))
            return False, False, False

    def test_login_flow(self):
        """Test: POST /api/auth/login returns tokens and sets cookies"""
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = self.make_request('POST', '/api/auth/login', json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check response structure
                required_fields = ['user', 'access_token']
                has_required = all(field in data for field in required_fields)
                
                if has_required:
                    # Check cookies for auth tokens
                    cookies = response.cookies
                    has_auth_cookies = 'access_token' in cookies and 'refresh_token' in cookies
                    
                    self.log_result("Login Flow", True, response.status_code,
                                  details={
                                      "has_access_token_in_body": True,
                                      "has_auth_cookies": has_auth_cookies,
                                      "user_id": data.get('user', {}).get('id'),
                                      "token_length": len(data.get('access_token', ''))
                                  })
                    return True, data.get('access_token'), has_auth_cookies
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_result("Login Flow", False, response.status_code,
                                  f"Missing required fields: {missing}")
            else:
                self.log_result("Login Flow", False, response.status_code,
                              response.text[:200])
            return False, None, False
        except Exception as e:
            self.log_result("Login Flow", False, 0, str(e))
            return False, None, False

    def test_authenticated_request(self, access_token: str):
        """Test: GET /api/auth/me with valid token returns user profile"""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self.make_request('GET', '/api/auth/me', headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'user' in data:
                    user = data['user']
                    expected_fields = ['id', 'email', 'name']
                    has_fields = all(field in user for field in expected_fields)
                    
                    self.log_result("Authenticated Request (/me)", has_fields, response.status_code,
                                  None if has_fields else f"Missing user fields",
                                  details={
                                      "email_matches": user.get('email') == self.test_email,
                                      "name_matches": user.get('name') == self.test_name
                                  })
                    return has_fields
                else:
                    self.log_result("Authenticated Request (/me)", False, response.status_code,
                                  "No user in response")
            else:
                self.log_result("Authenticated Request (/me)", False, response.status_code,
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Authenticated Request (/me)", False, 0, str(e))
            return False

    def test_session_with_cookies(self):
        """Test: GET /api/auth/me using only cookies (no Authorization header)"""
        try:
            # Don't send Authorization header - rely only on cookies from previous requests
            response = self.make_request('GET', '/api/auth/me')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'user' in data:
                    user = data['user']
                    self.log_result("Session Persistence (cookies only)", True, response.status_code,
                                  details={
                                      "email": user.get('email'),
                                      "cookies_working": True
                                  })
                    return True
                else:
                    self.log_result("Session Persistence (cookies only)", False, response.status_code,
                                  "No user in response")
            else:
                self.log_result("Session Persistence (cookies only)", False, response.status_code,
                              f"Expected 200, got {response.status_code}. Cookies may not be working.")
            return False
        except Exception as e:
            self.log_result("Session Persistence (cookies only)", False, 0, str(e))
            return False

    def test_logout_flow(self):
        """Test: POST /api/auth/logout clears session"""
        try:
            response = self.make_request('POST', '/api/auth/logout')
            
            if response.status_code == 200:
                data = response.json()
                
                if 'message' in data:
                    # Check that cookies are cleared
                    cookies_cleared = True
                    for cookie in response.cookies:
                        if cookie.name in ['access_token', 'refresh_token']:
                            # Cookie should be expired or empty
                            if cookie.value and cookie.expires and cookie.expires > time.time():
                                cookies_cleared = False
                                break
                    
                    self.log_result("Logout Flow", True, response.status_code,
                                  details={
                                      "message": data.get('message'),
                                      "cookies_cleared": cookies_cleared
                                  })
                    return True
                else:
                    self.log_result("Logout Flow", False, response.status_code,
                                  "No message in logout response")
            else:
                self.log_result("Logout Flow", False, response.status_code,
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Logout Flow", False, 0, str(e))
            return False

    def test_session_after_logout(self):
        """Test: GET /api/auth/me after logout should fail"""
        try:
            response = self.make_request('GET', '/api/auth/me')
            
            # Should get 401 after logout
            if response.status_code == 401:
                self.log_result("Session Invalidated After Logout", True, response.status_code,
                              "Correctly returns 401 after logout")
                return True
            else:
                self.log_result("Session Invalidated After Logout", False, response.status_code,
                              f"Expected 401 after logout, got {response.status_code}")
            return False
        except Exception as e:
            self.log_result("Session Invalidated After Logout", False, 0, str(e))
            return False

    def test_login_with_existing_account(self):
        """Test: Login with the account created during signup"""
        try:
            payload = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = self.make_request('POST', '/api/auth/login', json=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'user' in data and 'access_token' in data:
                    self.log_result("Login with Existing Account", True, response.status_code,
                                  details={
                                      "user_email": data['user'].get('email'),
                                      "login_successful": True
                                  })
                    return True
                else:
                    self.log_result("Login with Existing Account", False, response.status_code,
                                  "Missing user or access_token in response")
            else:
                self.log_result("Login with Existing Account", False, response.status_code,
                              response.text[:200])
            return False
        except Exception as e:
            self.log_result("Login with Existing Account", False, 0, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("🔬 AUTH FLOW TEST SUMMARY")
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
        
        return self.tests_passed == self.tests_run

def main():
    print("🚀 Starting CryptoVault Auth Flow Tests")
    print("🌐 Testing against: http://localhost:8001 (development environment)")
    print("-" * 60)
    
    tester = AuthFlowTester()
    
    # Test signup flow
    signup_success, auto_login, has_cookies = tester.test_signup_flow()
    
    if signup_success:
        if auto_login and has_cookies:
            # Test authenticated request after signup auto-login
            tester.test_session_with_cookies()
            
            # Test logout
            tester.test_logout_flow()
            
            # Verify session is cleared
            tester.test_session_after_logout()
        
        # Test manual login (whether or not auto-login happened)
        login_success, access_token, login_cookies = tester.test_login_flow()
        
        if login_success and access_token:
            # Test authenticated request with token
            tester.test_authenticated_request(access_token)
            
            if login_cookies:
                # Test session persistence with cookies
                tester.test_session_with_cookies()
        
        # Test logout again if we logged in
        if login_success:
            tester.test_logout_flow()
            tester.test_session_after_logout()
        
        # Test login with existing account
        tester.test_login_with_existing_account()
    
    # Print summary
    all_passed = tester.print_summary()
    
    # Return appropriate exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())