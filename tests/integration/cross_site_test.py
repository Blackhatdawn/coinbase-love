#!/usr/bin/env python3
"""
CryptoVault Cross-Site Cookie, WebSocket, and CORS Testing Suite
Tests specific requirements from the review request
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlparse

class CrossSiteAPITester:
    def __init__(self):
        self.base_url = "https://cryptovault-api.onrender.com"
        self.frontend_origin = "https://coinbase-love.vercel.app"
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Test results tracking
        self.tests_run = 0
        self.tests_passed = 0
        self.results = []
        
        # Authentication storage
        self.csrf_token = None
        self.access_token = None

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
        print()

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")

    def test_csrf_cookie_samesite_none_secure(self):
        """Test: GET /api/csrf should return Set-Cookie with SameSite=none; Secure"""
        try:
            response = self.make_request('GET', '/api/csrf')
            
            if response.status_code == 200:
                # Check Set-Cookie headers
                set_cookie_headers = response.headers.get_list('Set-Cookie') if hasattr(response.headers, 'get_list') else []
                if not set_cookie_headers:
                    # Fallback for requests library
                    set_cookie_headers = [response.headers.get('Set-Cookie', '')]
                
                csrf_cookie_found = False
                samesite_none = False
                secure_flag = False
                
                for cookie_header in set_cookie_headers:
                    if cookie_header and 'csrf_token=' in cookie_header.lower():
                        csrf_cookie_found = True
                        self.csrf_token = cookie_header.split('csrf_token=')[1].split(';')[0]
                        
                        # Check SameSite=None
                        if 'samesite=none' in cookie_header.lower():
                            samesite_none = True
                        
                        # Check Secure flag
                        if 'secure' in cookie_header.lower():
                            secure_flag = True
                        
                        break
                
                if csrf_cookie_found and samesite_none and secure_flag:
                    self.log_result(
                        "CSRF Cookie SameSite=none & Secure", 
                        True, 
                        response.status_code,
                        details={"cookie_header": set_cookie_headers[0] if set_cookie_headers else "None"}
                    )
                    return True
                else:
                    self.log_result(
                        "CSRF Cookie SameSite=none & Secure", 
                        False, 
                        response.status_code,
                        f"Missing flags - CSRF found: {csrf_cookie_found}, SameSite=none: {samesite_none}, Secure: {secure_flag}",
                        {"set_cookie_headers": set_cookie_headers}
                    )
            else:
                self.log_result(
                    "CSRF Cookie SameSite=none & Secure", 
                    False, 
                    response.status_code, 
                    response.text[:200]
                )
            return False
        except Exception as e:
            self.log_result("CSRF Cookie SameSite=none & Secure", False, 0, str(e))
            return False

    def test_auth_login_cookie_samesite_none_secure(self):
        """Test: POST /api/auth/login with testuser@example.com/Test123!@# should return Set-Cookie with SameSite=none; Secure"""
        try:
            # Get CSRF token first if we don't have one
            if not self.csrf_token:
                csrf_response = self.make_request('GET', '/api/csrf')
                if csrf_response.status_code == 200:
                    data = csrf_response.json()
                    self.csrf_token = data.get('csrf_token')
            
            headers = {}
            if self.csrf_token:
                headers['X-CSRF-Token'] = self.csrf_token
            
            response = self.make_request('POST', '/api/auth/login', 
                                       json={
                                           "email": "testuser@example.com",
                                           "password": "Test123!@#"
                                       },
                                       headers=headers)
            
            if response.status_code == 200:
                # Check for access_token in response body
                data = response.json()
                if 'access_token' in data:
                    self.access_token = data['access_token']
                
                # Check Set-Cookie headers for auth cookies
                set_cookie_headers = response.headers.get_list('Set-Cookie') if hasattr(response.headers, 'get_list') else []
                if not set_cookie_headers:
                    set_cookie_headers = [response.headers.get('Set-Cookie', '')]
                
                auth_cookie_found = False
                samesite_none = False
                secure_flag = False
                
                for cookie_header in set_cookie_headers:
                    if cookie_header and ('access_token=' in cookie_header.lower() or 'refresh_token=' in cookie_header.lower()):
                        auth_cookie_found = True
                        
                        # Check SameSite=None
                        if 'samesite=none' in cookie_header.lower():
                            samesite_none = True
                        
                        # Check Secure flag
                        if 'secure' in cookie_header.lower():
                            secure_flag = True
                        
                        break
                
                success = auth_cookie_found and samesite_none and secure_flag
                self.log_result(
                    "Auth Login Cookie SameSite=none & Secure", 
                    success, 
                    response.status_code,
                    None if success else f"Auth cookie found: {auth_cookie_found}, SameSite=none: {samesite_none}, Secure: {secure_flag}",
                    {"access_token_in_body": 'access_token' in data, "set_cookie_headers": set_cookie_headers}
                )
                return success
            else:
                self.log_result(
                    "Auth Login Cookie SameSite=none & Secure", 
                    False, 
                    response.status_code,
                    response.text[:200]
                )
            return False
        except Exception as e:
            self.log_result("Auth Login Cookie SameSite=none & Secure", False, 0, str(e))
            return False

    def test_cors_allow_credentials(self):
        """Test: OPTIONS /api/health with Origin: https://coinbase-love.vercel.app should return access-control-allow-credentials: true"""
        try:
            headers = {
                'Origin': self.frontend_origin,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'authorization,content-type'
            }
            
            response = self.make_request('OPTIONS', '/api/health', headers=headers)
            
            if response.status_code in [200, 204]:
                # Check CORS headers
                allow_credentials = response.headers.get('Access-Control-Allow-Credentials', '').lower()
                allow_origin = response.headers.get('Access-Control-Allow-Origin', '')
                
                credentials_allowed = allow_credentials == 'true'
                origin_allowed = allow_origin == self.frontend_origin or allow_origin == '*'
                
                success = credentials_allowed and origin_allowed
                self.log_result(
                    "CORS Allow Credentials", 
                    success, 
                    response.status_code,
                    None if success else f"Credentials: {allow_credentials}, Origin: {allow_origin}",
                    {
                        "access_control_allow_credentials": allow_credentials,
                        "access_control_allow_origin": allow_origin,
                        "all_cors_headers": {k: v for k, v in response.headers.items() if 'access-control' in k.lower()}
                    }
                )
                return success
            else:
                self.log_result(
                    "CORS Allow Credentials", 
                    False, 
                    response.status_code,
                    response.text[:200]
                )
            return False
        except Exception as e:
            self.log_result("CORS Allow Credentials", False, 0, str(e))
            return False

    def test_socketio_handshake_works(self):
        """Test: GET /socket.io/?EIO=4&transport=polling returns session ID"""
        try:
            response = self.make_request('GET', '/socket.io/?EIO=4&transport=polling')
            
            if response.status_code == 200:
                # Socket.IO response typically starts with protocol version and contains sid
                response_text = response.text
                if response_text and ('sid' in response_text.lower() or response_text.startswith(('0', '40', '42'))):
                    self.log_result(
                        "Socket.IO Handshake Works", 
                        True, 
                        response.status_code,
                        details={"response_preview": response_text[:100]}
                    )
                    return True
                else:
                    self.log_result(
                        "Socket.IO Handshake Works", 
                        False, 
                        response.status_code,
                        f"Unexpected response format: {response_text[:100]}"
                    )
            else:
                self.log_result(
                    "Socket.IO Handshake Works", 
                    False, 
                    response.status_code,
                    response.text[:200]
                )
            return False
        except Exception as e:
            self.log_result("Socket.IO Handshake Works", False, 0, str(e))
            return False

    def test_socketio_cors_vercel(self):
        """Test: GET /socket.io/?EIO=4&transport=polling with Origin: https://coinbase-love.vercel.app returns access-control-allow-origin header"""
        try:
            headers = {'Origin': self.frontend_origin}
            response = self.make_request('GET', '/socket.io/?EIO=4&transport=polling', headers=headers)
            
            if response.status_code == 200:
                allow_origin = response.headers.get('Access-Control-Allow-Origin', '')
                
                origin_allowed = allow_origin == self.frontend_origin or allow_origin == '*'
                
                if origin_allowed:
                    self.log_result(
                        "Socket.IO CORS Allows Vercel", 
                        True, 
                        response.status_code,
                        details={"access_control_allow_origin": allow_origin}
                    )
                    return True
                else:
                    self.log_result(
                        "Socket.IO CORS Allows Vercel", 
                        False, 
                        response.status_code,
                        f"Origin not allowed: {allow_origin}",
                        {"expected_origin": self.frontend_origin, "actual_origin": allow_origin}
                    )
            else:
                self.log_result(
                    "Socket.IO CORS Allows Vercel", 
                    False, 
                    response.status_code,
                    response.text[:200]
                )
            return False
        except Exception as e:
            self.log_result("Socket.IO CORS Allows Vercel", False, 0, str(e))
            return False

    def test_backend_health(self):
        """Test: GET /api/health returns status healthy"""
        try:
            response = self.make_request('GET', '/api/health')
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_result("Backend Health", True, response.status_code)
                    return True
                else:
                    self.log_result(
                        "Backend Health", 
                        False, 
                        response.status_code, 
                        f"Unhealthy status: {data.get('status')}"
                    )
            else:
                self.log_result("Backend Health", False, response.status_code, response.text[:200])
            return False
        except Exception as e:
            self.log_result("Backend Health", False, 0, str(e))
            return False

    def test_admin_login_not_blocked_by_csrf(self):
        """Test: POST /api/admin/login returns auth error (not CSRF error)"""
        try:
            response = self.make_request('POST', '/api/admin/login', 
                                       json={
                                           "email": "admin@cryptovault.financial",
                                           "password": "wrongpassword"
                                       })
            
            # We expect 401 (auth error), NOT 403 (CSRF error)
            if response.status_code == 401:
                self.log_result(
                    "Admin Login Not Blocked by CSRF", 
                    True, 
                    response.status_code,
                    "Returns auth error (401), not CSRF error (403)"
                )
                return True
            elif response.status_code == 403:
                # Check if it's a CSRF error
                error_text = response.text.lower()
                if 'csrf' in error_text:
                    self.log_result(
                        "Admin Login Not Blocked by CSRF", 
                        False, 
                        response.status_code,
                        "Still blocked by CSRF protection"
                    )
                else:
                    self.log_result(
                        "Admin Login Not Blocked by CSRF", 
                        True, 
                        response.status_code,
                        "Returns 403 but not CSRF related"
                    )
                    return True
            else:
                # Other status codes might be OK
                self.log_result(
                    "Admin Login Not Blocked by CSRF", 
                    True, 
                    response.status_code,
                    f"No CSRF blocking, returns {response.status_code}"
                )
                return True
            return False
        except Exception as e:
            self.log_result("Admin Login Not Blocked by CSRF", False, 0, str(e))
            return False

    def test_login_returns_access_token_in_body(self):
        """Test: Login returns access_token in response body"""
        try:
            # Use existing access token or get a new one
            if self.access_token:
                self.log_result(
                    "Login Returns Access Token in Body", 
                    True, 
                    200,
                    "Access token available from previous login test",
                    {"token_length": len(self.access_token)}
                )
                return True
            else:
                self.log_result(
                    "Login Returns Access Token in Body", 
                    False, 
                    0,
                    "No access token available - login may have failed"
                )
            return False
        except Exception as e:
            self.log_result("Login Returns Access Token in Body", False, 0, str(e))
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("🔬 CRYPTOVAULT CROSS-SITE COOKIE & CORS TEST SUMMARY")
        print("="*70)
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print("="*70)
        
        # Show failed tests
        failed_tests = [r for r in self.results if not r['passed']]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for result in failed_tests:
                print(f"  - {result['test']}: {result['error'] or 'See details above'}")
        else:
            print("\n🎉 ALL TESTS PASSED!")
        
        print(f"\n📋 Full results saved to /app/test_reports/cross_site_test_results.json")
        
        # Save results to file
        with open('/app/test_reports/cross_site_test_results.json', 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": self.tests_run,
                    "passed_tests": self.tests_passed,
                    "failed_tests": self.tests_run - self.tests_passed,
                    "success_rate": (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
                    "timestamp": datetime.utcnow().isoformat(),
                    "base_url": self.base_url,
                    "frontend_origin": self.frontend_origin
                },
                "results": self.results
            }, f, indent=2)
        
        return self.tests_passed == self.tests_run

def main():
    print("🚀 Starting CryptoVault Cross-Site Cookie, WebSocket & CORS Tests")
    print("🌐 Backend: https://cryptovault-api.onrender.com")
    print("🌐 Frontend: https://coinbase-love.vercel.app")
    print("-" * 70)
    
    tester = CrossSiteAPITester()
    
    # Run tests in the order specified in the review request
    tests_to_run = [
        # Required tests from review request
        tester.test_csrf_cookie_samesite_none_secure,
        tester.test_auth_login_cookie_samesite_none_secure,
        tester.test_cors_allow_credentials,
        tester.test_socketio_handshake_works,
        tester.test_socketio_cors_vercel,
        tester.test_backend_health,
        tester.test_admin_login_not_blocked_by_csrf,
        tester.test_login_returns_access_token_in_body,
    ]
    
    # Execute tests
    for test_func in tests_to_run:
        try:
            test_func()
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print(f"❌ Test execution error: {e}")
    
    # Print summary
    all_passed = tester.print_summary()
    
    # Return appropriate exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())