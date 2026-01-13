#!/usr/bin/env python3
"""
CryptoVault Financial Backend API Testing
Tests all backend endpoints for the institutional crypto custody platform
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class CryptoVaultAPITester:
    def __init__(self, base_url="https://cryptovault-header.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Dict[Any, Any] = None, headers: Dict[str, str] = None) -> tuple:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   Response: {response.text[:200]}...")
            else:
                print(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:300]}...")
                self.failed_tests.append({
                    'name': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'response': response.text[:300]
                })

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text

        except Exception as e:
            print(f"❌ FAILED - Error: {str(e)}")
            self.failed_tests.append({
                'name': name,
                'error': str(e)
            })
            return False, {}

    def test_health_endpoints(self):
        """Test health and basic endpoints"""
        print("\n" + "="*60)
        print("🏥 TESTING HEALTH & BASIC ENDPOINTS")
        print("="*60)
        
        # Test root endpoint
        self.run_test("Root Endpoint", "GET", "", 200)
        
        # Test health endpoint
        self.run_test("Health Check", "GET", "health", 200)

    def test_crypto_endpoints(self):
        """Test cryptocurrency data endpoints"""
        print("\n" + "="*60)
        print("💰 TESTING CRYPTOCURRENCY ENDPOINTS")
        print("="*60)
        
        # Test get all cryptocurrencies
        self.run_test("Get All Cryptocurrencies", "GET", "api/crypto", 200)
        
        # Test get specific cryptocurrency
        self.run_test("Get Bitcoin Details", "GET", "api/crypto/bitcoin", 200)
        
        # Test get price history
        self.run_test("Get Bitcoin Price History", "GET", "api/crypto/bitcoin/history?days=7", 200)
        
        # Test invalid cryptocurrency
        self.run_test("Get Invalid Crypto", "GET", "api/crypto/invalid-coin-xyz", 404)

    def test_auth_endpoints_basic(self):
        """Test authentication endpoints (basic tests without actual signup)"""
        print("\n" + "="*60)
        print("🔐 TESTING AUTHENTICATION ENDPOINTS")
        print("="*60)
        
        # Test login with invalid credentials (should fail)
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        self.run_test("Login Invalid Credentials", "POST", "api/auth/login", 401, login_data)
        
        # Test get current user without auth (should fail)
        self.run_test("Get Current User (No Auth)", "GET", "api/auth/me", 401)
        
        # Test refresh token without token (should fail)
        self.run_test("Refresh Token (No Token)", "POST", "api/auth/refresh", 401)

    def test_portfolio_endpoints_unauthorized(self):
        """Test portfolio endpoints without authentication (should fail)"""
        print("\n" + "="*60)
        print("📊 TESTING PORTFOLIO ENDPOINTS (UNAUTHORIZED)")
        print("="*60)
        
        # Test get portfolio without auth
        self.run_test("Get Portfolio (No Auth)", "GET", "api/portfolio", 401)
        
        # Test add holding without auth
        holding_data = {
            "symbol": "BTC",
            "name": "Bitcoin",
            "amount": 1.0
        }
        self.run_test("Add Holding (No Auth)", "POST", "api/portfolio/holding", 401, holding_data)

    def test_orders_endpoints_unauthorized(self):
        """Test order endpoints without authentication (should fail)"""
        print("\n" + "="*60)
        print("📋 TESTING ORDER ENDPOINTS (UNAUTHORIZED)")
        print("="*60)
        
        # Test get orders without auth
        self.run_test("Get Orders (No Auth)", "GET", "api/orders", 401)
        
        # Test create order without auth
        order_data = {
            "trading_pair": "BTC/USD",
            "order_type": "market",
            "side": "buy",
            "amount": 0.1,
            "price": 50000
        }
        self.run_test("Create Order (No Auth)", "POST", "api/orders", 401, order_data)

    def test_transactions_endpoints_unauthorized(self):
        """Test transaction endpoints without authentication (should fail)"""
        print("\n" + "="*60)
        print("💳 TESTING TRANSACTION ENDPOINTS (UNAUTHORIZED)")
        print("="*60)
        
        # Test get transactions without auth
        self.run_test("Get Transactions (No Auth)", "GET", "api/transactions", 401)
        
        # Test transaction stats without auth
        self.run_test("Get Transaction Stats (No Auth)", "GET", "api/transactions/stats/overview", 401)

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting CryptoVault Financial Backend API Tests")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all test suites
            self.test_health_endpoints()
            self.test_crypto_endpoints()
            self.test_auth_endpoints_basic()
            self.test_portfolio_endpoints_unauthorized()
            self.test_orders_endpoints_unauthorized()
            self.test_transactions_endpoints_unauthorized()
            
        except KeyboardInterrupt:
            print("\n⚠️ Tests interrupted by user")
        except Exception as e:
            print(f"\n💥 Unexpected error during testing: {str(e)}")
        
        # Print final results
        self.print_results()

    def print_results(self):
        """Print test results summary"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Total Tests: {self.tests_run}")
        print(f"🎯 Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print("\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"\n{i}. {test['name']}")
                if 'error' in test:
                    print(f"   Error: {test['error']}")
                else:
                    print(f"   Expected: {test['expected']}, Got: {test['actual']}")
                    print(f"   Response: {test['response']}")
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

def main():
    """Main function to run the tests"""
    tester = CryptoVaultAPITester()
    tester.run_all_tests()
    
    # Return exit code based on test results
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())