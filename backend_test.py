#!/usr/bin/env python3
"""
CryptoVault Backend API Testing Suite
Tests all authentication, wallet, alerts, and transaction endpoints
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class CryptoVaultAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.user_data = {}
        
        print(f"🚀 CryptoVault API Tester initialized")
        print(f"📍 Base URL: {base_url}")
        print("="*70)

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                    expected_status: int = 200) -> tuple[bool, Dict]:
        """Make HTTP request and validate response"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            if not success:
                print(f"   Status: {response.status_code} (expected {expected_status})")
                if response_data:
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
            
            return success, response_data
            
        except Exception as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test health endpoint"""
        success, data = self.make_request('GET', '/health')
        self.log_test("Health Check", success, 
                     "" if success else f"Health check failed: {data}")
        return success

    def test_api_health_check(self):
        """Test API health endpoint"""
        success, data = self.make_request('GET', '/api/health')
        self.log_test("API Health Check", success, 
                     "" if success else f"API health check failed: {data}")
        return success

    def test_signup(self):
        """Test user signup"""
        timestamp = datetime.now().strftime("%H%M%S")
        self.user_data = {
            "email": f"test_user_{timestamp}@example.com",
            "password": "TestPassword123!",
            "name": f"Test User {timestamp}"
        }
        
        success, data = self.make_request('POST', '/api/auth/signup', self.user_data)
        self.log_test("User Signup", success, 
                     "" if success else f"Signup failed: {data}")
        
        if success:
            self.user_data['user_id'] = data.get('user', {}).get('id')
            # Try to get verification token from response or database
            print(f"   User created, verification required: {data.get('verificationRequired', False)}")
        
        return success

    def test_verify_email(self):
        """Test email verification - try with a dummy token first"""
        # Since we can't get the actual verification token from email,
        # let's try to manually verify by updating the database or using a known pattern
        
        # First, let's try a simple verification token pattern
        dummy_token = "test_verification_token"
        verify_data = {"token": dummy_token}
        
        success, data = self.make_request('POST', '/api/auth/verify-email', verify_data, 400)  # Expect 400 for invalid token
        
        # This will fail, but let's log it and continue
        self.log_test("Email Verification (Expected Fail)", success, 
                     "Expected failure - no real verification token available")
        
        # For testing purposes, let's manually set email_verified=true in database
        # This is a workaround since we can't access the actual verification email
        return False  # Return False since we can't actually verify

    def test_login(self):
        """Test user login"""
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        success, data = self.make_request('POST', '/api/auth/login', login_data)
        self.log_test("User Login", success, 
                     "" if success else f"Login failed: {data}")
        
        if success:
            # Check if cookies are set (they should be in session automatically)
            print(f"   Cookies received: {len(self.session.cookies)} cookies")
            for cookie in self.session.cookies:
                print(f"   - {cookie.name}: {cookie.value[:20]}...")
        
        return success

    def test_get_current_user(self):
        """Test getting current user profile"""
        success, data = self.make_request('GET', '/api/auth/me')
        self.log_test("Get Current User", success, 
                     "" if success else f"Get user failed: {data}")
        return success

    def test_wallet_balance(self):
        """Test getting wallet balance"""
        success, data = self.make_request('GET', '/api/wallet/balance')
        self.log_test("Get Wallet Balance", success, 
                     "" if success else f"Get balance failed: {data}")
        
        if success:
            balance = data.get('wallet', {}).get('balances', {}).get('USD', 0)
            print(f"   Current USD balance: ${balance}")
        
        return success

    def test_create_alert(self):
        """Test creating a price alert"""
        alert_data = {
            "symbol": "BTC",
            "targetPrice": 50000.0,
            "condition": "above",
            "notifyPush": True,
            "notifyEmail": True
        }
        
        success, data = self.make_request('POST', '/api/alerts', alert_data, 200)
        self.log_test("Create Price Alert", success, 
                     "" if success else f"Create alert failed: {data}")
        
        if success:
            self.user_data['alert_id'] = data.get('alert', {}).get('id')
            print(f"   Alert ID: {self.user_data.get('alert_id')}")
        
        return success

    def test_get_alerts(self):
        """Test getting all alerts"""
        success, data = self.make_request('GET', '/api/alerts')
        self.log_test("Get All Alerts", success, 
                     "" if success else f"Get alerts failed: {data}")
        
        if success:
            alerts_count = len(data.get('alerts', []))
            print(f"   Found {alerts_count} alerts")
        
        return success

    def test_update_alert(self):
        """Test updating an alert"""
        if not self.user_data.get('alert_id'):
            self.log_test("Update Alert", False, "No alert ID available")
            return False
        
        update_data = {
            "targetPrice": 55000.0,
            "isActive": False
        }
        
        success, data = self.make_request('PATCH', f'/api/alerts/{self.user_data["alert_id"]}', update_data)
        self.log_test("Update Alert", success, 
                     "" if success else f"Update alert failed: {data}")
        return success

    def test_delete_alert(self):
        """Test deleting an alert"""
        if not self.user_data.get('alert_id'):
            self.log_test("Delete Alert", False, "No alert ID available")
            return False
        
        success, data = self.make_request('DELETE', f'/api/alerts/{self.user_data["alert_id"]}')
        self.log_test("Delete Alert", success, 
                     "" if success else f"Delete alert failed: {data}")
        return success

    def test_create_deposit(self):
        """Test creating a deposit"""
        deposit_data = {
            "amount": 100.0,
            "currency": "btc"
        }
        
        success, data = self.make_request('POST', '/api/wallet/deposit/create', deposit_data)
        self.log_test("Create Deposit", success, 
                     "" if success else f"Create deposit failed: {data}")
        
        if success:
            self.user_data['order_id'] = data.get('orderId')
            print(f"   Order ID: {self.user_data.get('order_id')}")
            print(f"   Mock mode: {data.get('mock', False)}")
        
        return success

    def test_get_deposit_status(self):
        """Test getting deposit status"""
        if not self.user_data.get('order_id'):
            self.log_test("Get Deposit Status", False, "No order ID available")
            return False
        
        success, data = self.make_request('GET', f'/api/wallet/deposit/{self.user_data["order_id"]}')
        self.log_test("Get Deposit Status", success, 
                     "" if success else f"Get deposit status failed: {data}")
        
        if success:
            status = data.get('deposit', {}).get('status')
            print(f"   Deposit status: {status}")
        
        return success

    def test_get_deposits_history(self):
        """Test getting deposits history"""
        success, data = self.make_request('GET', '/api/wallet/deposits')
        self.log_test("Get Deposits History", success, 
                     "" if success else f"Get deposits failed: {data}")
        
        if success:
            deposits_count = len(data.get('deposits', []))
            print(f"   Found {deposits_count} deposits")
        
        return success

    def test_get_transactions(self):
        """Test getting transactions"""
        success, data = self.make_request('GET', '/api/transactions')
        self.log_test("Get Transactions", success, 
                     "" if success else f"Get transactions failed: {data}")
        
        if success:
            transactions_count = len(data.get('transactions', []))
            print(f"   Found {transactions_count} transactions")
        
        return success

    def test_get_transaction_stats(self):
        """Test getting transaction statistics"""
        success, data = self.make_request('GET', '/api/transactions/summary/stats')
        self.log_test("Get Transaction Stats", success, 
                     "" if success else f"Get transaction stats failed: {data}")
        
        if success:
            total_deposits = data.get('totalDeposits', 0)
            print(f"   Total deposits: ${total_deposits}")
        
        return success

    def test_crypto_prices(self):
        """Test getting crypto prices"""
        success, data = self.make_request('GET', '/api/crypto')
        self.log_test("Get Crypto Prices", success, 
                     "" if success else f"Get crypto prices failed: {data}")
        
        if success:
            cryptos = data.get('cryptocurrencies', [])
            print(f"   Found {len(cryptos)} cryptocurrencies")
            if cryptos:
                btc = next((c for c in cryptos if c.get('symbol') == 'BTC'), None)
                if btc:
                    print(f"   BTC price: ${btc.get('price', 'N/A')}")
        
        return success

    def test_with_existing_user(self):
        """Test with a pre-existing verified user"""
        # Try common test credentials that might exist
        test_credentials = [
            {"email": "test@example.com", "password": "password123"},
            {"email": "admin@cryptovault.com", "password": "admin123"},
            {"email": "user@test.com", "password": "testpass123"}
        ]
        
        for creds in test_credentials:
            success, data = self.make_request('POST', '/api/auth/login', creds, expected_status=200)
            if success:
                self.user_data.update(creds)
                self.user_data['user_id'] = data.get('user', {}).get('id')
                self.log_test("Login with Existing User", True, f"Logged in as {creds['email']}")
                return True
        
        self.log_test("Login with Existing User", False, "No existing verified users found")
        return False

    def test_logout(self):
        """Test user logout"""
        success, data = self.make_request('POST', '/api/auth/logout')
        self.log_test("User Logout", success, 
                     "" if success else f"Logout failed: {data}")
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🧪 Starting CryptoVault API Tests")
        print("="*70)
        
        # Basic health checks
        self.test_health_check()
        self.test_api_health_check()
        
        # Try existing user first, then new signup
        authenticated = False
        
        # Try with existing verified user
        if self.test_with_existing_user():
            authenticated = True
        else:
            # Try new user signup and verification
            if self.test_signup():
                self.test_verify_email()  # This will fail but we'll log it
                # Try login anyway in case verification worked
                login_data = {
                    "email": self.user_data["email"],
                    "password": self.user_data["password"]
                }
                success, data = self.make_request('POST', '/api/auth/login', login_data)
                if success:
                    authenticated = True
                    self.log_test("User Login (After Signup)", True)
                else:
                    self.log_test("User Login (After Signup)", False, "Email verification required")
        
        if authenticated:
            # Authenticated endpoints
            self.test_get_current_user()
            self.test_wallet_balance()
            
            # Alerts CRUD
            if self.test_create_alert():
                self.test_get_alerts()
                self.test_update_alert()
                self.test_delete_alert()
            
            # Wallet operations
            if self.test_create_deposit():
                self.test_get_deposit_status()
            self.test_get_deposits_history()
            
            # Transactions
            self.test_get_transactions()
            self.test_get_transaction_stats()
            
            # Crypto data
            self.test_crypto_prices()
            
            # Logout
            self.test_logout()
        else:
            print("⚠️ Could not authenticate - skipping authenticated endpoint tests")
            # Still test public endpoints
            self.test_crypto_prices()
        
        # Print summary
        print("="*70)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("❌ Some tests failed!")
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['name']}: {result['details']}")
            return 1

def main():
    """Main test runner"""
    tester = CryptoVaultAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())