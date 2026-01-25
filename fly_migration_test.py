#!/usr/bin/env python3
"""
Fly.io Migration Testing Suite
Tests specific endpoints and configurations for the Fly.io migration
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class FlyMigrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.api_base = f"{self.base_url}/api"
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🔗 Testing Fly.io migration at: {self.base_url}")

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED - {details}")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    def test_health_endpoint(self):
        """Test /health endpoint returns healthy status"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                database = data.get('database', 'unknown')
                if status == 'healthy':
                    self.log_test("Backend /health endpoint", True, 
                                f"Status: {status}, Database: {database}")
                else:
                    self.log_test("Backend /health endpoint", False, 
                                f"Status: {status}, Database: {database}")
            else:
                self.log_test("Backend /health endpoint", False, 
                            f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Backend /health endpoint", False, f"Error: {str(e)}")

    def test_api_health_endpoint(self):
        """Test /api/health endpoint works correctly"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                database = data.get('database', 'unknown')
                if status == 'healthy':
                    self.log_test("Backend /api/health endpoint", True, 
                                f"Status: {status}, Database: {database}")
                else:
                    self.log_test("Backend /api/health endpoint", False, 
                                f"Status: {status}, Database: {database}")
            else:
                self.log_test("Backend /api/health endpoint", False, 
                            f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Backend /api/health endpoint", False, f"Error: {str(e)}")

    def test_ping_endpoint(self):
        """Test /api/ping endpoint responds with pong"""
        try:
            response = requests.get(f"{self.api_base}/ping", timeout=10)
            if response.status_code == 200:
                data = response.json()
                message = data.get('message')
                if message == 'pong':
                    self.log_test("Backend /api/ping endpoint", True, 
                                f"Message: {message}, Status: {data.get('status')}")
                else:
                    self.log_test("Backend /api/ping endpoint", False, 
                                f"Expected 'pong', got: {message}")
            else:
                self.log_test("Backend /api/ping endpoint", False, 
                            f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Backend /api/ping endpoint", False, f"Error: {str(e)}")

    def test_crypto_endpoint(self):
        """Test /api/crypto endpoint returns cryptocurrency data"""
        try:
            response = requests.get(f"{self.api_base}/crypto", timeout=10)
            if response.status_code == 200:
                data = response.json()
                cryptocurrencies = data.get('cryptocurrencies', [])
                if cryptocurrencies and len(cryptocurrencies) > 0:
                    self.log_test("Backend /api/crypto endpoint", True, 
                                f"Retrieved {len(cryptocurrencies)} cryptocurrencies")
                else:
                    self.log_test("Backend /api/crypto endpoint", False, 
                                "No cryptocurrency data returned")
            else:
                self.log_test("Backend /api/crypto endpoint", False, 
                            f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Backend /api/crypto endpoint", False, f"Error: {str(e)}")

    def test_cors_headers(self):
        """Test CORS headers are correctly configured"""
        try:
            # Test with production origin
            headers = {
                'Origin': 'https://www.cryptovault.financial',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = requests.options(f"{self.api_base}/health", headers=headers, timeout=10)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            allowed_origin = cors_headers.get('Access-Control-Allow-Origin')
            credentials_allowed = cors_headers.get('Access-Control-Allow-Credentials')
            
            if allowed_origin and credentials_allowed == 'true':
                self.log_test("Backend CORS configuration", True, 
                            f"Origin: {allowed_origin}, Credentials: {credentials_allowed}")
            else:
                self.log_test("Backend CORS configuration", False, 
                            f"Origin: {allowed_origin}, Credentials: {credentials_allowed}")
                
        except Exception as e:
            self.log_test("Backend CORS configuration", False, f"Error: {str(e)}")

    def test_database_status_in_health(self):
        """Test health check includes database status"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                database_status = data.get('database')
                if database_status:
                    valid_statuses = ['connected', 'initializing', 'slow', 'error', 'unavailable']
                    if database_status in valid_statuses:
                        self.log_test("Database status in health check", True, 
                                    f"Database status: {database_status}")
                    else:
                        self.log_test("Database status in health check", False, 
                                    f"Unknown database status: {database_status}")
                else:
                    self.log_test("Database status in health check", False, 
                                "No database status in health response")
            else:
                self.log_test("Database status in health check", False, 
                            f"Health endpoint failed: {response.status_code}")
        except Exception as e:
            self.log_test("Database status in health check", False, f"Error: {str(e)}")

    def check_hardcoded_render_urls(self):
        """Verify no hardcoded Render URLs remain in critical config files"""
        files_to_check = [
            '/app/backend/.env',
            '/app/frontend/.env.production', 
            '/app/frontend/vercel.json',
            '/app/backend/fly.toml'
        ]
        
        render_urls_found = []
        
        for file_path in files_to_check:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if 'onrender.com' in content.lower():
                        # Find specific lines with render URLs
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if 'onrender.com' in line.lower():
                                render_urls_found.append(f"{file_path}:{i} - {line.strip()}")
            except FileNotFoundError:
                continue
            except Exception as e:
                print(f"Error checking {file_path}: {e}")
        
        if render_urls_found:
            self.log_test("No hardcoded Render URLs", False, 
                        f"Found Render URLs: {render_urls_found}")
        else:
            self.log_test("No hardcoded Render URLs", True, 
                        "No hardcoded Render URLs found in config files")

    def check_frontend_env_variables(self):
        """Verify frontend environment variables are correctly set for Fly.io"""
        try:
            # Check .env.production
            with open('/app/frontend/.env.production', 'r') as f:
                content = f.read()
                if 'cryptovault-api.fly.dev' in content:
                    self.log_test("Frontend env vars for Fly.io", True, 
                                "Frontend .env.production points to Fly.io")
                else:
                    self.log_test("Frontend env vars for Fly.io", False, 
                                "Frontend .env.production not configured for Fly.io")
            
            # Check vercel.json
            with open('/app/frontend/vercel.json', 'r') as f:
                content = f.read()
                if 'cryptovault-api.fly.dev' in content:
                    self.log_test("Vercel.json Fly.io config", True, 
                                "vercel.json rewrites point to Fly.io")
                else:
                    self.log_test("Vercel.json Fly.io config", False, 
                                "vercel.json not configured for Fly.io")
                    
        except Exception as e:
            self.log_test("Frontend environment variables", False, f"Error: {str(e)}")

    def validate_fly_config_files(self):
        """Validate Fly.io configuration files are valid"""
        # Check fly.toml
        try:
            with open('/app/backend/fly.toml', 'r') as f:
                content = f.read()
                required_sections = ['app =', '[build]', '[http_service]', 'internal_port = 8001']
                missing_sections = []
                
                for section in required_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                if not missing_sections:
                    self.log_test("fly.toml validation", True, 
                                "All required sections present in fly.toml")
                else:
                    self.log_test("fly.toml validation", False, 
                                f"Missing sections: {missing_sections}")
        except Exception as e:
            self.log_test("fly.toml validation", False, f"Error: {str(e)}")
        
        # Check Dockerfile.fly
        try:
            with open('/app/backend/Dockerfile.fly', 'r') as f:
                content = f.read()
                required_elements = ['FROM python:', 'WORKDIR', 'COPY requirements.txt', 'EXPOSE 8001']
                missing_elements = []
                
                for element in required_elements:
                    if element not in content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    self.log_test("Dockerfile.fly validation", True, 
                                "All required elements present in Dockerfile.fly")
                else:
                    self.log_test("Dockerfile.fly validation", False, 
                                f"Missing elements: {missing_elements}")
        except Exception as e:
            self.log_test("Dockerfile.fly validation", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all Fly.io migration tests"""
        print("🚀 Starting Fly.io Migration Tests")
        print("=" * 50)
        
        # Test backend endpoints
        self.test_health_endpoint()
        self.test_api_health_endpoint()
        self.test_ping_endpoint()
        self.test_crypto_endpoint()
        self.test_cors_headers()
        self.test_database_status_in_health()
        
        # Test configuration
        self.check_hardcoded_render_urls()
        self.check_frontend_env_variables()
        self.validate_fly_config_files()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 FLY.IO MIGRATION TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = FlyMigrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)