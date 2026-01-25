#!/usr/bin/env python3
"""
CryptoVault Fly.io Migration Testing Suite
Tests all Fly.io specific endpoints and configuration
"""

import requests
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class FlyIoMigrationTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🚀 Testing Fly.io migration at: {self.base_url}")

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

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200, base_url: str = None) -> tuple[bool, Dict]:
        """Make HTTP request and validate response"""
        if base_url:
            url = f"{base_url}/{endpoint.lstrip('/')}"
        else:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        headers = {'Content-Type': 'application/json'}

        try:
            if method.upper() == 'GET':
                response = self.session.get(url, headers=headers, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=10)
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

    def test_basic_health_endpoints(self):
        """Test basic health endpoints"""
        print("\n🏥 Testing Basic Health Endpoints...")
        
        # Test /health endpoint
        success, data = self.make_request('GET', 'health')
        if success and data.get('status') == 'healthy':
            self.log_test("Backend /health endpoint", True, f"Status: {data.get('status')}")
        else:
            self.log_test("Backend /health endpoint", False, f"Response: {data}")

        # Test /api/health endpoint
        success, data = self.make_request('GET', 'api/health')
        if success and data.get('status') == 'healthy':
            self.log_test("Backend /api/health endpoint", True, f"Status: {data.get('status')}")
        else:
            self.log_test("Backend /api/health endpoint", False, f"Response: {data}")

        # Test /api/ping endpoint
        success, data = self.make_request('GET', 'api/ping')
        if success and data.get('message') == 'pong':
            self.log_test("Backend /api/ping endpoint", True, f"Message: {data.get('message')}")
        else:
            self.log_test("Backend /api/ping endpoint", False, f"Response: {data}")

    def test_fly_status_endpoints(self):
        """Test new Fly.io status endpoints"""
        print("\n🛩️ Testing Fly.io Status Endpoints...")
        
        # Test /api/fly/status endpoint
        success, data = self.make_request('GET', 'api/fly/status')
        if success and 'deployment' in data and 'platform' in data.get('deployment', {}):
            platform = data['deployment'].get('platform')
            region = data['deployment'].get('region', 'unknown')
            self.log_test("Fly.io status endpoint", True, f"Platform: {platform}, Region: {region}")
        else:
            self.log_test("Fly.io status endpoint", False, f"Response: {data}")

        # Test /api/fly/region endpoint
        success, data = self.make_request('GET', 'api/fly/region')
        if success and 'region' in data:
            region = data.get('region')
            machine_id = data.get('machine_id', 'unknown')
            self.log_test("Fly.io region endpoint", True, f"Region: {region}, Machine: {machine_id}")
        else:
            self.log_test("Fly.io region endpoint", False, f"Response: {data}")

        # Test /api/fly/instances endpoint
        success, data = self.make_request('GET', 'api/fly/instances')
        if success and 'instance' in data:
            instance = data.get('instance', {})
            machine_id = instance.get('machine_id', 'unknown')
            region = instance.get('region', 'unknown')
            self.log_test("Fly.io instances endpoint", True, f"Machine: {machine_id}, Region: {region}")
        else:
            self.log_test("Fly.io instances endpoint", False, f"Response: {data}")

        # Test /api/fly/health/fly endpoint
        success, data = self.make_request('GET', 'api/fly/health/fly')
        if success and data.get('status') == 'healthy':
            region = data.get('region', 'unknown')
            machine_id = data.get('machine_id', 'unknown')
            self.log_test("Fly.io health endpoint", True, f"Status: healthy, Region: {region}, Machine: {machine_id}")
        else:
            self.log_test("Fly.io health endpoint", False, f"Response: {data}")

    def test_fly_configuration_files(self):
        """Test Fly.io configuration files"""
        print("\n📋 Testing Fly.io Configuration Files...")
        
        # Test fly.toml exists and has auto-scaling config
        try:
            with open('/app/backend/fly.toml', 'r') as f:
                fly_config = f.read()
                
            # Check for auto-scaling configuration
            if 'min = 1' in fly_config and 'max = 3' in fly_config:
                self.log_test("fly.toml auto-scaling config", True, "min=1 and max=3 found")
            else:
                self.log_test("fly.toml auto-scaling config", False, "Auto-scaling config not found or incorrect")
                
            # Check for app name
            if 'app = "cryptovault-api"' in fly_config:
                self.log_test("fly.toml app name", True, "App name: cryptovault-api")
            else:
                self.log_test("fly.toml app name", False, "App name not found or incorrect")
                
        except FileNotFoundError:
            self.log_test("fly.toml exists", False, "fly.toml file not found")
        except Exception as e:
            self.log_test("fly.toml validation", False, f"Error reading fly.toml: {str(e)}")

        # Test Dockerfile.fly exists and is valid
        try:
            with open('/app/backend/Dockerfile.fly', 'r') as f:
                dockerfile_content = f.read()
                
            # Check for multi-stage build
            if 'FROM python:3.11-slim AS builder' in dockerfile_content:
                self.log_test("Dockerfile.fly multi-stage build", True, "Multi-stage build found")
            else:
                self.log_test("Dockerfile.fly multi-stage build", False, "Multi-stage build not found")
                
            # Check for health check
            if 'HEALTHCHECK' in dockerfile_content:
                self.log_test("Dockerfile.fly health check", True, "Health check found")
            else:
                self.log_test("Dockerfile.fly health check", False, "Health check not found")
                
        except FileNotFoundError:
            self.log_test("Dockerfile.fly exists", False, "Dockerfile.fly file not found")
        except Exception as e:
            self.log_test("Dockerfile.fly validation", False, f"Error reading Dockerfile.fly: {str(e)}")

    def test_vercel_configuration(self):
        """Test vercel.json points to fly.dev URL not render.com"""
        print("\n🔧 Testing Vercel Configuration...")
        
        try:
            with open('/app/frontend/vercel.json', 'r') as f:
                vercel_config = json.load(f)
                
            # Check rewrites for fly.dev URLs
            rewrites = vercel_config.get('rewrites', [])
            fly_urls = []
            render_urls = []
            
            for rewrite in rewrites:
                destination = rewrite.get('destination', '')
                if 'fly.dev' in destination:
                    fly_urls.append(destination)
                elif 'render.com' in destination:
                    render_urls.append(destination)
            
            if fly_urls and not render_urls:
                self.log_test("vercel.json points to fly.dev", True, f"Found {len(fly_urls)} fly.dev URLs, 0 render.com URLs")
            elif render_urls:
                self.log_test("vercel.json points to fly.dev", False, f"Still contains render.com URLs: {render_urls}")
            else:
                self.log_test("vercel.json points to fly.dev", False, "No fly.dev URLs found in rewrites")
                
        except FileNotFoundError:
            self.log_test("vercel.json exists", False, "vercel.json file not found")
        except Exception as e:
            self.log_test("vercel.json validation", False, f"Error reading vercel.json: {str(e)}")

    def test_deployment_scripts(self):
        """Test deployment scripts exist and are executable"""
        print("\n📜 Testing Deployment Scripts...")
        
        import os
        
        scripts = [
            '/app/backend/deploy-fly.sh',
            '/app/backend/verify-fly-deployment.sh'
        ]
        
        for script_path in scripts:
            script_name = os.path.basename(script_path)
            
            if os.path.exists(script_path):
                # Check if executable
                if os.access(script_path, os.X_OK):
                    self.log_test(f"{script_name} executable", True, "Script exists and is executable")
                else:
                    self.log_test(f"{script_name} executable", False, "Script exists but is not executable")
                    
                # Check script content
                try:
                    with open(script_path, 'r') as f:
                        content = f.read()
                        
                    if 'flyctl' in content and 'cryptovault-api' in content:
                        self.log_test(f"{script_name} content", True, "Script contains flyctl and app name")
                    else:
                        self.log_test(f"{script_name} content", False, "Script missing flyctl or app name")
                        
                except Exception as e:
                    self.log_test(f"{script_name} content", False, f"Error reading script: {str(e)}")
            else:
                self.log_test(f"{script_name} exists", False, "Script file not found")

    def run_all_tests(self):
        """Run all Fly.io migration tests"""
        print("🚀 CryptoVault Fly.io Migration Test Suite")
        print("=" * 50)
        
        self.test_basic_health_endpoints()
        self.test_fly_status_endpoints()
        self.test_fly_configuration_files()
        self.test_vercel_configuration()
        self.test_deployment_scripts()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        return self.test_results

def main():
    # Use the backend URL from environment or default to localhost
    import os
    backend_url = os.environ.get('PUBLIC_API_URL', 'http://localhost:8001')
    
    tester = FlyIoMigrationTester(backend_url)
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if tester.tests_passed == tester.tests_run:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {tester.tests_run - tester.tests_passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())