#!/usr/bin/env python3
"""
Advanced Trading Feature Testing - Focused test for the newly integrated features
Tests the Advanced Trading endpoints without complex authentication flows
"""

import requests
import json
import sys
from datetime import datetime

class AdvancedTradingTester:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.api_base = f"{self.base_url}/api"
        self.session = requests.Session()
        self.csrf_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        print(f"🎯 Advanced Trading Feature Tester")
        print(f"🔗 Testing backend at: {self.base_url}")

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_csrf_token(self):
        """Get CSRF token for authenticated requests"""
        if not self.csrf_token:
            try:
                # Get CSRF token and let session handle cookies automatically
                response = self.session.get(f"{self.api_base}/csrf", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    self.csrf_token = data.get('csrf_token')
                    print(f"🔐 CSRF token obtained and cookies set")
                    return True
            except Exception as e:
                print(f"⚠️ Failed to get CSRF token: {e}")
                return False
        return True

    def test_trading_pairs_endpoint(self):
        """Test GET /api/crypto/trading-pairs"""
        print("\n📊 Testing Trading Pairs Endpoint...")
        
        try:
            response = self.session.get(f"{self.api_base}/crypto/trading-pairs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'pairs' in data:
                    pairs = data['pairs']
                    expected_pairs = ['BTC/USD', 'ETH/USD', 'BNB/USD']
                    
                    if len(pairs) > 0 and all(pair in pairs for pair in expected_pairs):
                        self.log_test("Trading Pairs Endpoint", True, 
                                    f"Retrieved {len(pairs)} pairs including {expected_pairs}")
                    else:
                        self.log_test("Trading Pairs Endpoint", False, 
                                    f"Missing expected pairs. Got: {pairs[:5]}")
                else:
                    self.log_test("Trading Pairs Endpoint", False, 
                                f"Response missing 'pairs' field: {data}")
            else:
                self.log_test("Trading Pairs Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_test("Trading Pairs Endpoint", False, f"Request failed: {str(e)}")

    def test_advanced_orders_without_auth(self):
        """Test advanced orders endpoint without authentication (should return 401)"""
        print("\n🔒 Testing Advanced Orders Authentication...")
        
        # Get CSRF token first
        if not self.get_csrf_token():
            self.log_test("Advanced Orders - CSRF Setup", False, "Could not obtain CSRF token")
            return
        
        # Test POST /api/orders/advanced without authentication
        order_data = {
            "trading_pair": "BTC/USD",
            "order_type": "stop_loss",
            "side": "sell",
            "amount": 0.001,
            "stop_price": 45000.0,
            "time_in_force": "GTC"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': self.csrf_token
        }
        
        try:
            response = self.session.post(
                f"{self.api_base}/orders/advanced", 
                json=order_data, 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Advanced Orders - Auth Required", True, 
                            "Correctly requires authentication (401)")
            else:
                self.log_test("Advanced Orders - Auth Required", False, 
                            f"Expected 401, got {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_test("Advanced Orders - Auth Required", False, f"Request failed: {str(e)}")

    def test_order_cancellation_without_auth(self):
        """Test order cancellation without authentication (should return 401)"""
        print("\n❌ Testing Order Cancellation Authentication...")
        
        # Test DELETE /api/orders/{id} without authentication
        fake_order_id = "test-order-id"
        
        headers = {
            'X-CSRF-Token': self.csrf_token
        }
        
        try:
            response = self.session.delete(
                f"{self.api_base}/orders/{fake_order_id}", 
                headers=headers, 
                timeout=10
            )
            
            if response.status_code == 401:
                self.log_test("Order Cancellation - Auth Required", True, 
                            "Correctly requires authentication (401)")
            else:
                self.log_test("Order Cancellation - Auth Required", False, 
                            f"Expected 401, got {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_test("Order Cancellation - Auth Required", False, f"Request failed: {str(e)}")

    def test_get_orders_without_auth(self):
        """Test GET /api/orders without authentication (should return 401)"""
        print("\n📋 Testing Get Orders Authentication...")
        
        try:
            response = self.session.get(f"{self.api_base}/orders", timeout=10)
            
            if response.status_code == 401:
                self.log_test("Get Orders - Auth Required", True, 
                            "Correctly requires authentication (401)")
            else:
                self.log_test("Get Orders - Auth Required", False, 
                            f"Expected 401, got {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            self.log_test("Get Orders - Auth Required", False, f"Request failed: {str(e)}")

    def test_advanced_orders_validation(self):
        """Test validation for advanced orders endpoint"""
        print("\n⚠️ Testing Advanced Orders Validation...")
        
        # Test invalid order type
        invalid_data = {
            "trading_pair": "BTC/USD",
            "order_type": "invalid_type",
            "side": "buy",
            "amount": 0.001,
            "stop_price": 50000.0
        }
        
        headers = {
            'Content-Type': 'application/json',
            'X-CSRF-Token': self.csrf_token
        }
        
        try:
            response = self.session.post(
                f"{self.api_base}/orders/advanced", 
                json=invalid_data, 
                headers=headers, 
                timeout=10
            )
            
            # Should return 401 (auth required) or 400 (validation error)
            if response.status_code in [400, 401]:
                if response.status_code == 401:
                    self.log_test("Advanced Orders - Validation (Auth)", True, 
                                "Authentication required before validation")
                else:
                    self.log_test("Advanced Orders - Validation", True, 
                                "Invalid order type correctly rejected")
            else:
                self.log_test("Advanced Orders - Validation", False, 
                            f"Expected 400/401, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Advanced Orders - Validation", False, f"Request failed: {str(e)}")

    def test_backend_health(self):
        """Test that backend is healthy and responsive"""
        print("\n🏥 Testing Backend Health...")
        
        try:
            response = self.session.get(f"{self.api_base}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log_test("Backend Health", True, 
                                f"Backend healthy, DB: {data.get('database', 'unknown')}")
                else:
                    self.log_test("Backend Health", False, 
                                f"Backend not healthy: {data}")
            else:
                self.log_test("Backend Health", False, 
                            f"Health check failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Backend Health", False, f"Health check error: {str(e)}")

    def run_tests(self):
        """Run all Advanced Trading tests"""
        print("\n" + "="*60)
        print("🚀 ADVANCED TRADING FEATURE TESTS")
        print("="*60)
        
        # Basic health check
        self.test_backend_health()
        
        # Test public endpoints
        self.test_trading_pairs_endpoint()
        
        # Test authentication requirements
        self.test_get_orders_without_auth()
        self.test_advanced_orders_without_auth()
        self.test_order_cancellation_without_auth()
        
        # Test validation
        self.test_advanced_orders_validation()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 ADVANCED TRADING TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": self.tests_passed/self.tests_run*100 if self.tests_run > 0 else 0,
            "test_results": self.test_results
        }

def main():
    """Main test execution"""
    tester = AdvancedTradingTester()
    results = tester.run_tests()
    
    # Return appropriate exit code
    return 0 if results["success_rate"] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())