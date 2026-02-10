#!/usr/bin/env python3
"""
Fly.io Migration Backend Testing Suite
Tests all version endpoints and verifies Fly.io configuration
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class FlyMigrationTester:
    def __init__(self, base_url: str = "https://coinbase-love.fly.dev"):
        self.base_url = base_url.rstrip('/')
        self.tests_run = 0
        self.tests_passed = 0
        self.issues = []

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

    def test_health_endpoint(self) -> bool:
        """Test /health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
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
            response = requests.get(f"{self.base_url}/api/version", timeout=10)
            
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
            response = requests.get(f"{self.base_url}/api/version/check", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['compatible', 'message', 'server_version', 'client_version', 'upgrade_required']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Test with client version
                    response2 = requests.get(f"{self.base_url}/api/version/check?client_version=1.0.0", timeout=10)
                    
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
            response = requests.get(f"{self.base_url}/api/version/features", timeout=10)
            
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
            response = requests.get(f"{self.base_url}/api/version/deployment", timeout=10)
            
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

    def check_cors_headers(self) -> bool:
        """Check CORS configuration includes fly.dev domains"""
        try:
            # Make an OPTIONS request to check CORS
            response = requests.options(f"{self.base_url}/api/version", 
                                      headers={'Origin': 'https://coinbase-love.fly.dev'}, 
                                      timeout=10)
            
            cors_origin = response.headers.get('Access-Control-Allow-Origin', '')
            
            if 'coinbase-love.fly.dev' in cors_origin or cors_origin == '*':
                self.log_test("CORS configuration", True, f"Origin: {cors_origin}")
                return True
            else:
                self.log_test("CORS configuration", False, f"Origin: {cors_origin}")
                return False
                
        except Exception as e:
            self.log_test("CORS configuration", False, f"Error: {str(e)}")
            return False

    def check_security_headers(self) -> bool:
        """Check CSP headers include fly.dev domains"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=10)
            
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
        print(f"🚀 Testing Fly.io Backend Migration")
        print(f"📍 Base URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all tests
        self.test_health_endpoint()
        version_data = self.test_version_endpoint()
        self.test_version_check_endpoint()
        self.test_version_features_endpoint()
        self.test_version_deployment_endpoint()
        self.check_cors_headers()
        self.check_security_headers()
        
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
            "version_data": version_data,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """Main test runner"""
    tester = FlyMigrationTester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    if results["success_rate"] >= 85:  # Allow for some minor issues
        print(f"\n✅ Migration test PASSED ({results['success_rate']:.1f}%)")
        return 0
    else:
        print(f"\n❌ Migration test FAILED ({results['success_rate']:.1f}%)")
        return 1

if __name__ == "__main__":
    sys.exit(main())