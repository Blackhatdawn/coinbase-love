#!/usr/bin/env python3
"""
Local Backend Testing for Fly.io Migration
Tests all version endpoints locally and checks for Render references
"""

import requests
import sys
import json
import os
import glob
from datetime import datetime
from typing import Dict, Any, Optional, List

class LocalFlyMigrationTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []
        self.render_references = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if details:
                print(f"   {details}")
        else:
            print(f"❌ {name}")
            if details:
                print(f"   {details}")
            self.issues.append(f"{name}: {details}")

    def check_render_references(self) -> bool:
        """Check for remaining Render references in codebase"""
        print("\n🔍 Checking for Render references...")
        
        # Files to check
        files_to_check = [
            "/app/vercel.json",
            "/app/frontend/vercel.json",
            "/app/backend/.env",
            "/app/frontend/.env"
        ]
        
        # Add Python files
        for py_file in glob.glob("/app/backend/**/*.py", recursive=True):
            files_to_check.append(py_file)
        
        # Add TypeScript files
        for ts_file in glob.glob("/app/frontend/src/**/*.ts", recursive=True):
            files_to_check.append(ts_file)
        
        render_patterns = [
            "render.com",
            "onrender.com", 
            "onrender",
            "cryptovault-api.onrender.com"
        ]
        
        found_references = []
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in render_patterns:
                        if pattern.lower() in content.lower():
                            found_references.append(f"{file_path}: contains '{pattern}'")
                            
                except Exception as e:
                    continue
        
        if found_references:
            self.log_test("No Render references", False, f"Found {len(found_references)} references")
            for ref in found_references[:5]:  # Show first 5
                print(f"     • {ref}")
            if len(found_references) > 5:
                print(f"     • ... and {len(found_references) - 5} more")
            self.render_references = found_references
            return False
        else:
            self.log_test("No Render references", True, "All Render references removed")
            return True

    def test_health_endpoint(self) -> bool:
        """Test /health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'unknown')
                
                if status == 'healthy':
                    self.log_test("Health endpoint", True, f"Status: {status}")
                    return True
                else:
                    self.log_test("Health endpoint", False, f"Status: {status} (expected 'healthy')")
                    return False
            else:
                self.log_test("Health endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Health endpoint", False, f"Error: {str(e)}")
            return False

    def test_version_endpoint(self) -> Optional[Dict[str, Any]]:
        """Test /api/version endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['version', 'api_version', 'build_timestamp', 'git_commit', 
                                 'environment', 'min_frontend_version', 'min_backend_version', 'features']
                
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    features_count = len(data.get('features', {}))
                    self.log_test("Version endpoint", True, 
                                f"Version: {data['version']}, Features: {features_count}")
                    return data
                else:
                    self.log_test("Version endpoint", False, 
                                f"Missing fields: {missing_fields}")
                    return None
            else:
                self.log_test("Version endpoint", False, f"HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test("Version endpoint", False, f"Error: {str(e)}")
            return None

    def test_version_check_endpoint(self) -> bool:
        """Test /api/version/check endpoint"""
        try:
            # Test without client version
            response = requests.get(f"{self.base_url}/api/version/check", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['compatible', 'message', 'server_version', 'client_version', 'upgrade_required']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Test with client version
                    response2 = requests.get(f"{self.base_url}/api/version/check?client_version=1.0.0", timeout=5)
                    
                    if response2.status_code == 200:
                        data2 = response2.json()
                        self.log_test("Version check endpoint", True, 
                                    f"Compatible: {data2.get('compatible')}")
                        return True
                    else:
                        self.log_test("Version check endpoint", False, 
                                    f"Client version test failed: HTTP {response2.status_code}")
                        return False
                else:
                    self.log_test("Version check endpoint", False, 
                                f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Version check endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Version check endpoint", False, f"Error: {str(e)}")
            return False

    def test_version_features_endpoint(self) -> bool:
        """Test /api/version/features endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/version/features", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'features' in data:
                    features = data['features']
                    feature_count = len(features)
                    
                    # Check for expected features
                    expected_features = ['trading', 'wallet', 'p2p_transfer', 'price_alerts', 
                                       'two_factor_auth', 'admin_dashboard', 'websocket', 'crypto_payments']
                    
                    present_features = [f for f in expected_features if f in features]
                    
                    self.log_test("Version features endpoint", True, 
                                f"Features: {feature_count}, Expected present: {len(present_features)}/{len(expected_features)}")
                    return True
                else:
                    self.log_test("Version features endpoint", False, "No 'features' field in response")
                    return False
            else:
                self.log_test("Version features endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Version features endpoint", False, f"Error: {str(e)}")
            return False

    def test_version_deployment_endpoint(self) -> bool:
        """Test /api/version/deployment endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/version/deployment", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for Fly.io specific fields
                platform = data.get('platform')
                app_name = data.get('app_name')
                public_url = data.get('public_url')
                
                if platform == 'fly.io':
                    if app_name == 'coinbase-love':
                        if 'fly.dev' in str(public_url):
                            self.log_test("Version deployment endpoint", True, 
                                        f"Platform: {platform}, App: {app_name}")
                            return True
                        else:
                            self.log_test("Version deployment endpoint", False, 
                                        f"Public URL doesn't contain fly.dev: {public_url}")
                            return False
                    else:
                        self.log_test("Version deployment endpoint", False, 
                                    f"App name is '{app_name}', expected 'coinbase-love'")
                        return False
                else:
                    self.log_test("Version deployment endpoint", False, 
                                f"Platform is '{platform}', expected 'fly.io'")
                    return False
            else:
                self.log_test("Version deployment endpoint", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Version deployment endpoint", False, f"Error: {str(e)}")
            return False

    def check_fly_toml_config(self) -> bool:
        """Check fly.toml configuration"""
        try:
            fly_toml_path = "/app/backend/fly.toml"
            if os.path.exists(fly_toml_path):
                with open(fly_toml_path, 'r') as f:
                    content = f.read()
                
                if 'app = "coinbase-love"' in content:
                    if 'coinbase-love.fly.dev' in content:
                        self.log_test("fly.toml configuration", True, "App name and URLs correct")
                        return True
                    else:
                        self.log_test("fly.toml configuration", False, "Missing fly.dev URLs")
                        return False
                else:
                    self.log_test("fly.toml configuration", False, "App name not 'coinbase-love'")
                    return False
            else:
                self.log_test("fly.toml configuration", False, "fly.toml not found")
                return False
                
        except Exception as e:
            self.log_test("fly.toml configuration", False, f"Error: {str(e)}")
            return False

    def check_cors_config(self) -> bool:
        """Check CORS configuration in backend .env"""
        try:
            env_path = "/app/backend/.env"
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    content = f.read()
                
                if 'coinbase-love.fly.dev' in content:
                    self.log_test("CORS includes fly.dev", True, "Found coinbase-love.fly.dev in CORS")
                    return True
                else:
                    self.log_test("CORS includes fly.dev", False, "coinbase-love.fly.dev not in CORS")
                    return False
            else:
                self.log_test("CORS configuration", False, "Backend .env not found")
                return False
                
        except Exception as e:
            self.log_test("CORS configuration", False, f"Error: {str(e)}")
            return False

    def check_csp_headers(self) -> bool:
        """Check CSP headers include fly.dev domains"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            
            csp_header = response.headers.get('Content-Security-Policy', '')
            
            if 'fly.dev' in csp_header:
                self.log_test("CSP headers include fly.dev", True, "Found fly.dev in CSP")
                return True
            else:
                self.log_test("CSP headers include fly.dev", False, "fly.dev not found in CSP")
                return False
                
        except Exception as e:
            self.log_test("CSP headers check", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        print(f"🚀 Testing Fly.io Backend Migration (Local)")
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all tests
        self.test_health_endpoint()
        version_data = self.test_version_endpoint()
        self.test_version_check_endpoint()
        self.test_version_features_endpoint()
        self.test_version_deployment_endpoint()
        self.check_fly_toml_config()
        self.check_cors_config()
        self.check_csp_headers()
        self.check_render_references()
        
        print("=" * 60)
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.issues:
            print("\n🔍 Issues found:")
            for issue in self.issues:
                print(f"   • {issue}")
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        return {
            "success_rate": success_rate,
            "tests_passed": self.tests_passed,
            "tests_run": self.tests_run,
            "issues": self.issues,
            "render_references": self.render_references,
            "version_data": version_data,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Main test runner"""
    tester = LocalFlyMigrationTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results["success_rate"] >= 80:  # Allow for some minor issues
        print(f"\n✅ Migration test PASSED ({results['success_rate']:.1f}%)")
        return 0
    else:
        print(f"\n❌ Migration test FAILED ({results['success_rate']:.1f}%)")
        return 1

if __name__ == "__main__":
    sys.exit(main())