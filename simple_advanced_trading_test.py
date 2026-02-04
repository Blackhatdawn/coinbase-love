#!/usr/bin/env python3
"""
Advanced Trading Feature Testing - Simplified approach
Focus on testing endpoint availability and basic functionality
"""

import requests
import json
import sys
from datetime import datetime

class SimpleAdvancedTradingTester:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.api_base = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🎯 Simple Advanced Trading Feature Tester")
        print(f"🔗 Testing backend at: {self.base_url}")

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

    def test_trading_pairs_endpoint(self):
        """Test GET /api/crypto/trading-pairs - Core feature"""
        print("\n📊 Testing Trading Pairs Endpoint...")
        
        try:
            response = requests.get(f"{self.api_base}/crypto/trading-pairs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data and isinstance(data['pairs'], list):
                    pairs = data['pairs']
                    expected_pairs = ['BTC/USD', 'ETH/USD', 'BNB/USD', 'XRP/USD', 'ADA/USD']
                    found_pairs = [p for p in expected_pairs if p in pairs]
                    
                    if len(pairs) >= 10 and len(found_pairs) >= 3:
                        self.log_test("Trading Pairs Endpoint", True, 
                                    f"Retrieved {len(pairs)} pairs, found {len(found_pairs)} expected pairs: {found_pairs}")
                    else:
                        self.log_test("Trading Pairs Endpoint", False, 
                                    f"Insufficient pairs. Got {len(pairs)} pairs, expected pairs found: {found_pairs}")
                else:
                    self.log_test("Trading Pairs Endpoint", False, 
                                f"Invalid response structure: {data}")
            else:
                self.log_test("Trading Pairs Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Trading Pairs Endpoint", False, f"Request failed: {str(e)}")

    def test_orders_endpoint_structure(self):
        """Test that orders endpoints exist and return proper auth errors"""
        print("\n📋 Testing Orders Endpoint Structure...")
        
        # Test GET /api/orders
        try:
            response = requests.get(f"{self.api_base}/orders", timeout=10)
            
            if response.status_code == 401:
                try:
                    data = response.json()
                    if 'error' in data and data['error'].get('code') in ['UNAUTHORIZED', 'AUTHENTICATION_REQUIRED']:
                        self.log_test("GET /api/orders - Auth Check", True, 
                                    "Correctly requires authentication")
                    else:
                        self.log_test("GET /api/orders - Auth Check", False, 
                                    f"Unexpected error structure: {data}")
                except:
                    self.log_test("GET /api/orders - Auth Check", True, 
                                "Returns 401 (auth required)")
            else:
                self.log_test("GET /api/orders - Auth Check", False, 
                            f"Expected 401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("GET /api/orders - Auth Check", False, f"Request failed: {str(e)}")

    def test_advanced_orders_endpoint_structure(self):
        """Test that advanced orders endpoint exists"""
        print("\n🎯 Testing Advanced Orders Endpoint Structure...")
        
        # Test POST /api/orders/advanced (should require auth/CSRF)
        try:
            response = requests.post(f"{self.api_base}/orders/advanced", 
                                   json={"test": "data"}, timeout=10)
            
            # Should return 401 (auth) or 403 (CSRF) - both indicate endpoint exists
            if response.status_code in [401, 403]:
                try:
                    data = response.json()
                    error_code = data.get('error', {}).get('code', '')
                    
                    if error_code in ['UNAUTHORIZED', 'CSRF_TOKEN_MISSING', 'CSRF_TOKEN_INVALID']:
                        self.log_test("POST /api/orders/advanced - Endpoint Exists", True, 
                                    f"Endpoint exists, requires auth/CSRF (code: {error_code})")
                    else:
                        self.log_test("POST /api/orders/advanced - Endpoint Exists", True, 
                                    f"Endpoint exists, security check active")
                except:
                    self.log_test("POST /api/orders/advanced - Endpoint Exists", True, 
                                f"Endpoint exists, returns {response.status_code}")
            else:
                self.log_test("POST /api/orders/advanced - Endpoint Exists", False, 
                            f"Unexpected status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("POST /api/orders/advanced - Endpoint Exists", False, f"Request failed: {str(e)}")

    def test_order_cancellation_endpoint_structure(self):
        """Test that order cancellation endpoint exists"""
        print("\n❌ Testing Order Cancellation Endpoint Structure...")
        
        # Test DELETE /api/orders/{id}
        test_id = "test-order-id"
        try:
            response = requests.delete(f"{self.api_base}/orders/{test_id}", timeout=10)
            
            # Should return 401 (auth) or 403 (CSRF) - both indicate endpoint exists
            if response.status_code in [401, 403]:
                try:
                    data = response.json()
                    error_code = data.get('error', {}).get('code', '')
                    
                    if error_code in ['UNAUTHORIZED', 'CSRF_TOKEN_MISSING', 'CSRF_TOKEN_INVALID']:
                        self.log_test("DELETE /api/orders/{id} - Endpoint Exists", True, 
                                    f"Endpoint exists, requires auth/CSRF (code: {error_code})")
                    else:
                        self.log_test("DELETE /api/orders/{id} - Endpoint Exists", True, 
                                    f"Endpoint exists, security check active")
                except:
                    self.log_test("DELETE /api/orders/{id} - Endpoint Exists", True, 
                                f"Endpoint exists, returns {response.status_code}")
            else:
                self.log_test("DELETE /api/orders/{id} - Endpoint Exists", False, 
                            f"Unexpected status {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("DELETE /api/orders/{id} - Endpoint Exists", False, f"Request failed: {str(e)}")

    def test_backend_health_and_routing(self):
        """Test backend health and API routing"""
        print("\n🏥 Testing Backend Health and Routing...")
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.api_base}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    db_status = data.get('database', 'unknown')
                    self.log_test("Backend Health Check", True, 
                                f"Backend healthy, Database: {db_status}")
                else:
                    self.log_test("Backend Health Check", False, 
                                f"Backend not healthy: {data}")
            else:
                self.log_test("Backend Health Check", False, 
                            f"Health check failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Backend Health Check", False, f"Health check error: {str(e)}")

        # Test API routing
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'CryptoVault' in data.get('message', ''):
                    self.log_test("API Routing Check", True, 
                                "Root endpoint accessible and returns CryptoVault info")
                else:
                    self.log_test("API Routing Check", False, 
                                f"Unexpected root response: {data}")
            else:
                self.log_test("API Routing Check", False, 
                            f"Root endpoint failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("API Routing Check", False, f"Routing check error: {str(e)}")

    def test_crypto_endpoints_integration(self):
        """Test crypto endpoints that support trading pairs"""
        print("\n💰 Testing Crypto Endpoints Integration...")
        
        # Test general crypto endpoint
        try:
            response = requests.get(f"{self.api_base}/crypto", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'cryptocurrencies' in data:
                    cryptos = data['cryptocurrencies']
                    if len(cryptos) > 0:
                        # Check if we have BTC and ETH data
                        btc_found = any(c.get('symbol') == 'BTC' for c in cryptos)
                        eth_found = any(c.get('symbol') == 'ETH' for c in cryptos)
                        
                        if btc_found and eth_found:
                            self.log_test("Crypto Data Integration", True, 
                                        f"Retrieved {len(cryptos)} cryptocurrencies including BTC and ETH")
                        else:
                            self.log_test("Crypto Data Integration", False, 
                                        f"Missing BTC or ETH in {len(cryptos)} cryptocurrencies")
                    else:
                        self.log_test("Crypto Data Integration", False, 
                                    "No cryptocurrency data returned")
                else:
                    self.log_test("Crypto Data Integration", False, 
                                f"Invalid crypto response: {data}")
            else:
                self.log_test("Crypto Data Integration", False, 
                            f"Crypto endpoint failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Crypto Data Integration", False, f"Crypto test error: {str(e)}")

    def run_tests(self):
        """Run all simplified Advanced Trading tests"""
        print("\n" + "="*70)
        print("🚀 ADVANCED TRADING FEATURE TESTS (SIMPLIFIED)")
        print("="*70)
        
        # Core functionality tests
        self.test_backend_health_and_routing()
        self.test_crypto_endpoints_integration()
        self.test_trading_pairs_endpoint()
        
        # Endpoint structure tests
        self.test_orders_endpoint_structure()
        self.test_advanced_orders_endpoint_structure()
        self.test_order_cancellation_endpoint_structure()
        
        # Print summary
        print("\n" + "="*70)
        print("📊 ADVANCED TRADING TEST SUMMARY")
        print("="*70)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Detailed results
        print(f"\n📋 Test Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {result['test']}")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100 if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = SimpleAdvancedTradingTester()
    results = tester.run_tests()
    
    # Return appropriate exit code
    return 0 if results["success_rate"] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())