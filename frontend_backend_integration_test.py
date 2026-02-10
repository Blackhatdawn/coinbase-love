#!/usr/bin/env python3
"""
Frontend-Backend Integration Test Suite

Tests all critical integration points between Vercel frontend and Render backend:
- URL normalization (no trailing slashes)
- CORS configuration
- Cookie-based authentication
- Socket.IO connectivity
- CSRF protection
"""

import asyncio
import aiohttp
import socketio
import json
import sys
from typing import Dict, Any, Optional
from urllib.parse import urljoin, urlparse

class IntegrationTester:
    def __init__(self, frontend_url: str, backend_url: str):
        self.frontend_url = frontend_url.rstrip('/')
        self.backend_url = backend_url.rstrip('/')
        self.session = None
        self.socket_client = None
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.socket_client:
            self.socket_client.disconnect()

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        self.test_results[test_name] = {"passed": passed, "message": message}

    async def test_url_normalization(self):
        """Test that backend URLs are properly normalized (no trailing slashes)"""
        print("\n🔧 Testing URL Normalization...")
        
        try:
            # Test backend config endpoint
            config_url = urljoin(self.backend_url + '/', '/api/config')
            async with self.session.get(config_url) as response:
                if response.status == 200:
                    config = await response.json()
                    
                    # Check that URLs don't have trailing slashes (except root)
                    api_url = config.get('apiBaseUrl', '')
                    app_url = config.get('appUrl', '')
                    ws_url = config.get('wsBaseUrl', '')
                    
                    issues = []
                    if api_url and api_url != '/' and api_url.endswith('/'):
                        issues.append(f"apiBaseUrl has trailing slash: {api_url}")
                    if app_url and app_url != '/' and app_url.endswith('/'):
                        issues.append(f"appUrl has trailing slash: {app_url}")
                    if ws_url and ws_url != '/' and ws_url.endswith('/'):
                        issues.append(f"wsBaseUrl has trailing slash: {ws_url}")
                    
                    if issues:
                        self.log_test("URL Normalization", False, "; ".join(issues))
                    else:
                        self.log_test("URL Normalization", True, "All URLs properly normalized")
                else:
                    self.log_test("URL Normalization", False, f"Config endpoint failed: {response.status}")
                    
        except Exception as e:
            self.log_test("URL Normalization", False, f"Exception: {str(e)}")

    async def test_cors_configuration(self):
        """Test CORS headers and preflight requests"""
        print("\n🌐 Testing CORS Configuration...")
        
        try:
            # Test preflight request
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization,X-CSRF-Token'
            }
            
            async with self.session.options(
                urljoin(self.backend_url + '/', '/api/auth/login'),
                headers=headers
            ) as response:
                
                cors_headers = {
                    'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                    'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
                }
                
                # Check if frontend origin is allowed
                allowed_origin = cors_headers['Access-Control-Allow-Origin']
                if allowed_origin in (self.frontend_url, '*'):
                    self.log_test("CORS Origin", True, f"Frontend origin allowed: {allowed_origin}")
                else:
                    self.log_test("CORS Origin", False, f"Frontend origin not allowed: {allowed_origin}")
                
                # Check credentials support
                allow_credentials = cors_headers['Access-Control-Allow-Credentials']
                if allow_credentials == 'true':
                    self.log_test("CORS Credentials", True, "Credentials supported")
                else:
                    self.log_test("CORS Credentials", False, "Credentials not supported")
                
                # Check required headers
                required_headers = ['Content-Type', 'X-CSRF-Token']
                allowed_headers = cors_headers['Access-Control-Allow-Headers'] or ''
                
                missing_headers = [h for h in required_headers if h.lower() not in allowed_headers.lower()]
                if not missing_headers:
                    self.log_test("CORS Headers", True, "Required headers allowed")
                else:
                    self.log_test("CORS Headers", False, f"Missing headers: {missing_headers}")
                    
        except Exception as e:
            self.log_test("CORS Configuration", False, f"Exception: {str(e)}")

    async def test_cookie_authentication(self):
        """Test cookie-based authentication flow"""
        print("\n🍪 Testing Cookie Authentication...")
        
        try:
            login_data = {
                "email": "test@example.com",
                "password": "testpassword123"
            }
            
            # Test login with credentials
            async with self.session.post(
                urljoin(self.backend_url + '/', '/api/auth/login'),
                json=login_data,
                headers={'Origin': self.frontend_url}
            ) as response:
                
                if response.status == 200:
                    # Check for cookies
                    cookies = response.cookies
                    has_access_token = 'access_token' in cookies
                    has_refresh_token = 'refresh_token' in cookies
                    
                    if has_access_token and has_refresh_token:
                        self.log_test("Login Cookies", True, "Access and refresh tokens set")
                    else:
                        self.log_test("Login Cookies", False, "Missing tokens in response")
                    
                    # Test cookie attributes
                    for cookie in cookies:
                        if cookie.key in ['access_token', 'refresh_token']:
                            # Check SameSite attribute
                            same_site = cookie.get('samesite')
                            secure = cookie.get('secure', False)
                            httponly = cookie.get('httponly', False)
                            
                            if same_site and same_site.lower() in ['none', 'lax']:
                                self.log_test(f"Cookie {cookie.key} SameSite", True, f"SameSite={same_site}")
                            else:
                                self.log_test(f"Cookie {cookie.key} SameSite", False, f"Invalid SameSite: {same_site}")
                            
                            if httponly:
                                self.log_test(f"Cookie {cookie.key} HttpOnly", True, "HttpOnly enabled")
                            else:
                                self.log_test(f"Cookie {cookie.key} HttpOnly", False, "HttpOnly disabled")
                            
                            if secure:
                                self.log_test(f"Cookie {cookie.key} Secure", True, "Secure enabled")
                            else:
                                self.log_test(f"Cookie {cookie.key} Secure", False, "Secure disabled")
                else:
                    self.log_test("Cookie Authentication", False, f"Login failed: {response.status}")
                    
        except Exception as e:
            self.log_test("Cookie Authentication", False, f"Exception: {str(e)}")

    async def test_csrf_protection(self):
        """Test CSRF token endpoint and protection"""
        print("\n🛡️ Testing CSRF Protection...")
        
        try:
            # Test CSRF token endpoint
            async with self.session.get(
                urljoin(self.backend_url + '/', '/csrf'),
                headers={'Origin': self.frontend_url}
            ) as response:
                
                if response.status == 200:
                    # Check for CSRF cookie
                    csrf_cookie = response.cookies.get('csrf_token')
                    if csrf_cookie:
                        self.log_test("CSRF Token", True, "CSRF token cookie set")
                    else:
                        self.log_test("CSRF Token", False, "CSRF token cookie missing")
                    
                    # Check that cookie is HttpOnly
                    if csrf_cookie and csrf_cookie.get('httponly'):
                        self.log_test("CSRF HttpOnly", True, "CSRF token is HttpOnly")
                    else:
                        self.log_test("CSRF HttpOnly", False, "CSRF token not HttpOnly")
                else:
                    self.log_test("CSRF Protection", False, f"CSRF endpoint failed: {response.status}")
                    
        except Exception as e:
            self.log_test("CSRF Protection", False, f"Exception: {str(e)}")

    async def test_socketio_connectivity(self):
        """Test Socket.IO connection with credentials"""
        print("\n🔌 Testing Socket.IO Connectivity...")
        
        try:
            # Create Socket.IO client with credentials
            self.socket_client = socketio.AsyncClient(
                ssl_verify=False,
                cookiejar=self.session.cookie_jar
            )
            
            connected = False
            connection_error = None
            
            @self.socket_client.event
            def connect():
                nonlocal connected
                connected = True
                print("    Socket.IO connected successfully")
            
            @self.socket_client.event
            def connect_error(data):
                nonlocal connection_error
                connection_error = str(data)
                print(f"    Socket.IO connection error: {data}")
            
            # Connect to Socket.IO server
            socket_url = self.backend_url.replace('https://', 'wss://').replace('http://', 'ws://')
            await self.socket_client.connect(socket_url)
            
            # Wait a moment for connection
            await asyncio.sleep(2)
            
            if connected:
                self.log_test("Socket.IO Connection", True, "Connected successfully")
                
                # Test authentication
                try:
                    await self.socket_client.emit('authenticate', {'user_id': 'test', 'token': 'test'})
                    self.log_test("Socket.IO Auth", True, "Authentication event sent")
                except Exception as e:
                    self.log_test("Socket.IO Auth", False, f"Auth failed: {str(e)}")
            else:
                self.log_test("Socket.IO Connection", False, f"Failed to connect: {connection_error}")
                
        except Exception as e:
            self.log_test("Socket.IO Connectivity", False, f"Exception: {str(e)}")

    async def test_api_endpoints(self):
        """Test basic API endpoints with proper headers"""
        print("\n📡 Testing API Endpoints...")
        
        endpoints = [
            ('/health', 'Health Check'),
            ('/ping', 'Ping'),
            ('/api/config', 'Config'),
        ]
        
        for endpoint, name in endpoints:
            try:
                async with self.session.get(
                    urljoin(self.backend_url + '/', endpoint),
                    headers={'Origin': self.frontend_url}
                ) as response:
                    if response.status == 200:
                        self.log_test(f"API {name}", True, f"Status: {response.status}")
                    else:
                        self.log_test(f"API {name}", False, f"Status: {response.status}")
            except Exception as e:
                self.log_test(f"API {name}", False, f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all integration tests"""
        print(f"🧪 Running Integration Tests")
        print(f"   Frontend: {self.frontend_url}")
        print(f"   Backend:  {self.backend_url}")
        print("=" * 60)
        
        await self.test_url_normalization()
        await self.test_cors_configuration()
        await self.test_cookie_authentication()
        await self.test_csrf_protection()
        await self.test_socketio_connectivity()
        await self.test_api_endpoints()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result['passed'])
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅" if result['passed'] else "❌"
            print(f"{status} {test_name}")
            if result['message']:
                print(f"    {result['message']}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Frontend-backend integration is working correctly.")
            return True
        else:
            print("⚠️ Some tests failed. Please review the issues above.")
            return False


async def main():
    """Main test runner"""
    # Configuration - update these URLs for your deployment
    FRONTEND_URL = "https://coinbase-love.vercel.app"
    BACKEND_URL = "https://cryptovault-api.onrender.com"
    
    if len(sys.argv) > 1:
        FRONTEND_URL = sys.argv[1]
    if len(sys.argv) > 2:
        BACKEND_URL = sys.argv[2]
    
    async with IntegrationTester(FRONTEND_URL, BACKEND_URL) as tester:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
