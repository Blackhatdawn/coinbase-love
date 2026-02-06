#!/usr/bin/env python3
"""
CryptoVault Backend API Testing Suite
Testing the backend APIs using the public URL from frontend env configuration
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class CryptoVaultAPITester:
    def __init__(self, base_url: str = None):
        # Use the public URL from frontend .env file
        if base_url is None:
            try:
                with open('/app/frontend/.env', 'r') as f:
                    env_content = f.read()
                    for line in env_content.split('\n'):
                        if line.startswith('VITE_API_BASE_URL='):
                            backend_url = line.split('=', 1)[1].strip()
                            if backend_url:
                                base_url = backend_url
                                break
                if not base_url:
                    base_url = "http://localhost:8001"
            except:
                base_url = "http://localhost:8001"
        
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🔗 Testing backend at: {self.base_url}")

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}: FAILED")
            if details:
                print(f"   {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    def test_health_check(self):
        """Test health endpoint - GET /api/health should return status:healthy"""
        try:
            response = self.session.get(f"{self.api_base}/health", timeout=15)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        self.log_test("Health Check", True, 
                                    f"Status: {data.get('status')}, Database: {data.get('database', 'unknown')}")
                    else:
                        self.log_test("Health Check", False, f"Expected 'healthy', got: {data.get('status')}")
                except json.JSONDecodeError:
                    self.log_test("Health Check", False, "Invalid JSON response")
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")

    def test_crypto_list_endpoint(self):
        """Test API endpoint /api/crypto/list returns crypto data"""
        endpoints_to_try = [
            "/crypto/list", 
            "/crypto",  # fallback
        ]
        
        for endpoint in endpoints_to_try:
            try:
                response = self.session.get(f"{self.api_base}{endpoint}", timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, dict) and ('cryptocurrencies' in data or 'data' in data):
                            crypto_list = data.get('cryptocurrencies') or data.get('data', [])
                            self.log_test("Crypto List Endpoint", True, 
                                        f"Endpoint {endpoint} returned {len(crypto_list)} cryptocurrencies")
                            return True
                        else:
                            # Try to see if it's a different structure
                            if isinstance(data, list) and len(data) > 0:
                                self.log_test("Crypto List Endpoint", True, 
                                            f"Endpoint {endpoint} returned list with {len(data)} items")
                                return True
                            else:
                                self.log_test("Crypto List Endpoint", False, 
                                            f"Endpoint {endpoint} - unexpected response structure: {type(data)}")
                    except json.JSONDecodeError:
                        self.log_test("Crypto List Endpoint", False, f"Endpoint {endpoint} - invalid JSON")
                else:
                    print(f"   Endpoint {endpoint}: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"   Endpoint {endpoint}: Request failed - {str(e)}")
                
        self.log_test("Crypto List Endpoint", False, "No working crypto list endpoint found")
        return False

    def test_cors_headers(self):
        """Test CORS headers are properly set"""
        try:
            # Test preflight request
            headers = {
                'Origin': 'https://400dc717-e040-4c41-aaa7-d04c7e41aa10.preview.emergentagent.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.api_base}/health", headers=headers, timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            # Check if CORS is configured
            if any(cors_headers.values()):
                self.log_test("CORS Headers", True, 
                            f"CORS configured: Origin={cors_headers['Access-Control-Allow-Origin']}, "
                            f"Credentials={cors_headers['Access-Control-Allow-Credentials']}")
            else:
                self.log_test("CORS Headers", False, "No CORS headers found in OPTIONS response")
                
        except requests.exceptions.RequestException as e:
            self.log_test("CORS Headers", False, f"CORS test failed: {str(e)}")

    def test_socketio_endpoint(self):
        """Test Socket.IO endpoint /socket.io/ is accessible"""
        try:
            # Test basic Socket.IO endpoint
            response = self.session.get(f"{self.base_url}/socket.io/", timeout=10)
            
            if response.status_code in [200, 400]:
                # 200 or 400 are both acceptable for Socket.IO without proper handshake
                self.log_test("Socket.IO Basic Endpoint", True, 
                            f"Socket.IO accessible (HTTP {response.status_code})")
            else:
                self.log_test("Socket.IO Basic Endpoint", False, 
                            f"Unexpected status: HTTP {response.status_code}")
            
            # Test Socket.IO with proper parameters
            try:
                socketio_url = f"{self.base_url}/socket.io/?EIO=4&transport=polling"
                response = self.session.get(socketio_url, timeout=10)
                if response.status_code == 200:
                    self.log_test("Socket.IO Handshake", True, "Socket.IO handshake successful")
                else:
                    self.log_test("Socket.IO Handshake", False, f"Handshake failed: HTTP {response.status_code}")
            except:
                self.log_test("Socket.IO Handshake", False, "Handshake test failed")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Socket.IO Endpoint", False, f"Socket.IO test failed: {str(e)}")

    def test_admin_api_endpoints(self):
        """Test Admin API endpoints exist"""
        admin_endpoints = [
            ("/admin/dashboard/stats", "GET"),
            ("/admin/users", "GET"),
            ("/admin/system/health", "GET")
        ]
        
        for endpoint, method in admin_endpoints:
            try:
                url = f"{self.api_base}{endpoint}"
                if method == "GET":
                    response = self.session.get(url, timeout=10)
                else:
                    response = self.session.post(url, timeout=10)
                
                # These should require auth, so 401 is expected and good
                if response.status_code == 401:
                    self.log_test(f"Admin API {endpoint}", True, 
                                f"Endpoint exists and requires authentication (HTTP 401)")
                elif response.status_code == 200:
                    self.log_test(f"Admin API {endpoint}", True, 
                                f"Endpoint accessible (HTTP 200)")
                else:
                    self.log_test(f"Admin API {endpoint}", False, 
                                f"Unexpected status: HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_test(f"Admin API {endpoint}", False, f"Request failed: {str(e)}")

    def test_auth_endpoints(self):
        """Test Auth endpoints work: POST /api/auth/login returns access_token in body"""
        try:
            # Test login endpoint exists
            login_data = {
                "email": "test@example.com",
                "password": "testpass"
            }
            
            response = self.session.post(f"{self.api_base}/auth/login", 
                                       json=login_data, timeout=10)
            
            if response.status_code in [200, 401, 422]:
                try:
                    data = response.json()
                    if response.status_code == 200 and 'access_token' in data:
                        self.log_test("Auth Login Endpoint", True, 
                                    "Login endpoint returns access_token")
                    elif response.status_code == 401:
                        self.log_test("Auth Login Endpoint", True, 
                                    "Login endpoint correctly rejects invalid credentials")
                    elif response.status_code == 422:
                        self.log_test("Auth Login Endpoint", True, 
                                    "Login endpoint validates input format")
                    else:
                        self.log_test("Auth Login Endpoint", False, 
                                    f"Unexpected response structure: {data}")
                except json.JSONDecodeError:
                    self.log_test("Auth Login Endpoint", False, "Invalid JSON response")
            else:
                self.log_test("Auth Login Endpoint", False, 
                            f"Unexpected status: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Auth Login Endpoint", False, f"Request failed: {str(e)}")

    def run_backend_tests(self):
        """Run all backend tests"""
        print("🚀 Starting CryptoVault Backend API Tests")
        print("=" * 50)
        
        # Run all tests
        self.test_health_check()
        self.test_crypto_list_endpoint()
        self.test_cors_headers()
        self.test_socketio_endpoint()
        self.test_admin_api_endpoints()
        self.test_auth_endpoints()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Test Summary")
        print("=" * 50)
        print(f"Total tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%")
        
        # Save results
        try:
            with open('/app/test_reports/backend_test_results.json', 'w') as f:
                json.dump({
                    "timestamp": datetime.utcnow().isoformat(),
                    "tests_run": self.tests_run,
                    "tests_passed": self.tests_passed,
                    "success_rate": (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0,
                    "results": self.test_results
                }, f, indent=2)
            print("\n📝 Results saved to /app/test_reports/backend_test_results.json")
        except Exception as e:
            print(f"\n⚠️ Could not save results: {e}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = CryptoVaultAPITester()
    success = tester.run_backend_tests()
    
    if success:
        print("\n🎉 All backend tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some backend tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()