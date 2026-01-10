#!/usr/bin/env python3
"""
PHASE 1 BACKEND RE-TESTING - Authentication Fix Verification
Testing the bcrypt fix by switching from passlib to direct bcrypt library.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://wallet-hub-9.preview.emergentagent.com"

class AuthFixTester:
    def __init__(self):
        self.session = None
        self.timestamp = int(time.time())
        self.test_results = {
            "signup_fix": {"status": "pending", "details": ""},
            "rate_limiting": {"status": "pending", "details": ""},
            "login_unverified": {"status": "pending", "details": ""}
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(ssl=False)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_result(self, test_name: str, status: str, details: str):
        """Log test result"""
        self.test_results[test_name] = {"status": status, "details": details}
        print(f"[{status.upper()}] {test_name}: {details}")

    async def test_signup_fix(self):
        """Test authentication signup - CRITICAL (Was Broken)"""
        try:
            # Create test user with timestamp to ensure uniqueness
            test_email = f"test-fixed-{self.timestamp}@example.com"
            signup_data = {
                "email": test_email,
                "password": "TestPass123!",
                "name": "Test User Fixed"
            }
            
            print(f"🧪 Testing signup with email: {test_email}")
            
            async with self.session.post(f"{BACKEND_URL}/api/auth/signup", 
                                       json=signup_data) as response:
                
                print(f"📡 Response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"📄 Response data: {json.dumps(data, indent=2)}")
                    
                    # Check for expected response structure
                    if (data.get("verificationRequired") and 
                        "check your email" in data.get("message", "").lower()):
                        
                        self.log_result("signup_fix", "pass", 
                                      f"✅ Signup now works! Email: {test_email}, Verification required: {data.get('verificationRequired')}")
                        
                        # Store email for login test
                        self.test_email = test_email
                        return True
                    else:
                        self.log_result("signup_fix", "fail", 
                                      f"❌ Signup response missing required fields: {data}")
                        return False
                        
                elif response.status == 520:
                    # This was the previous error
                    data = await response.json()
                    self.log_result("signup_fix", "fail", 
                                  f"❌ Still getting 520 Internal Server Error (bcrypt issue not fixed): {data}")
                    return False
                    
                else:
                    data = await response.json()
                    self.log_result("signup_fix", "fail", 
                                  f"❌ Signup failed with status {response.status}: {data}")
                    return False
                    
        except Exception as e:
            self.log_result("signup_fix", "fail", f"❌ Signup exception: {str(e)}")
            return False

    async def test_rate_limiting(self):
        """Test rate limiting (Blocked Previously)"""
        try:
            print(f"🧪 Testing rate limiting with 6 rapid signup attempts...")
            
            rate_limit_hit = False
            success_count = 0
            
            for i in range(6):
                test_email = f"ratetest{i}-{self.timestamp}@cryptovault.test"
                signup_data = {
                    "email": test_email,
                    "password": "TestPass123!",
                    "name": f"Rate Test {i}"
                }
                
                print(f"📡 Attempt {i+1}/6: {test_email}")
                
                async with self.session.post(f"{BACKEND_URL}/api/auth/signup", 
                                           json=signup_data) as response:
                    
                    print(f"   Status: {response.status}")
                    
                    if response.status == 429:  # Too Many Requests
                        rate_limit_hit = True
                        self.log_result("rate_limiting", "pass", 
                                      f"✅ Rate limiting now works! Hit limit on attempt {i+1} (first {success_count} succeeded)")
                        return True
                        
                    elif response.status == 200:
                        success_count += 1
                        print(f"   ✅ Success #{success_count}")
                        
                    elif response.status == 520:
                        # If we still get 520 errors, signup is still broken
                        data = await response.json()
                        self.log_result("rate_limiting", "fail", 
                                      f"❌ Cannot test rate limiting - signup still broken (520 error): {data}")
                        return False
                        
                    else:
                        data = await response.json()
                        print(f"   ❌ Unexpected error: {response.status} - {data}")
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            if not rate_limit_hit:
                if success_count == 6:
                    self.log_result("rate_limiting", "fail", 
                                  f"❌ Rate limiting not working - all 6 attempts succeeded")
                else:
                    self.log_result("rate_limiting", "fail", 
                                  f"❌ Rate limiting test inconclusive - {success_count}/6 succeeded, no 429 error")
                return False
                    
        except Exception as e:
            self.log_result("rate_limiting", "fail", f"❌ Rate limiting test exception: {str(e)}")
            return False

    async def test_login_unverified(self):
        """Test login with new account (should fail with Invalid credentials)"""
        try:
            if not hasattr(self, 'test_email'):
                self.log_result("login_unverified", "skip", 
                              "⏭️ Skipped - no test email from signup test")
                return False
                
            print(f"🧪 Testing login with unverified account: {self.test_email}")
            
            login_data = {
                "email": self.test_email,
                "password": "TestPass123!"
            }
            
            async with self.session.post(f"{BACKEND_URL}/api/auth/login", 
                                       json=login_data) as response:
                
                print(f"📡 Response status: {response.status}")
                
                if response.status == 401:
                    data = await response.json()
                    print(f"📄 Response data: {json.dumps(data, indent=2)}")
                    
                    if "invalid credentials" in data.get("detail", "").lower():
                        self.log_result("login_unverified", "pass", 
                                      f"✅ Login correctly fails with 'Invalid credentials' for unverified account")
                        return True
                    else:
                        self.log_result("login_unverified", "pass", 
                                      f"✅ Login correctly rejected unverified account: {data.get('detail')}")
                        return True
                        
                elif response.status == 200:
                    self.log_result("login_unverified", "fail", 
                                  "❌ Login succeeded for unverified account (security issue)")
                    return False
                    
                else:
                    data = await response.json()
                    self.log_result("login_unverified", "fail", 
                                  f"❌ Unexpected login response {response.status}: {data}")
                    return False
                    
        except Exception as e:
            self.log_result("login_unverified", "fail", f"❌ Login test exception: {str(e)}")
            return False

    async def run_focused_tests(self):
        """Run focused authentication fix tests"""
        print("🚀 PHASE 1 BACKEND RE-TESTING - Authentication Fix Verification")
        print(f"📍 Backend URL: {BACKEND_URL}")
        print(f"🕐 Timestamp: {self.timestamp}")
        print("="*70)
        print("🎯 FOCUS: Testing bcrypt fix (passlib → direct bcrypt library)")
        print("="*70)
        
        # Test in priority order
        signup_success = await self.test_signup_fix()
        
        # Only test rate limiting if signup works
        if signup_success:
            await self.test_rate_limiting()
            await self.test_login_unverified()
        else:
            self.log_result("rate_limiting", "skip", 
                          "⏭️ Skipped - signup still broken")
            self.log_result("login_unverified", "skip", 
                          "⏭️ Skipped - signup still broken")
        
        print("="*70)
        print("📊 AUTHENTICATION FIX TEST RESULTS")
        print("="*70)
        
        all_passed = True
        for test_name, result in self.test_results.items():
            status = result["status"]
            if status == "pass":
                print(f"✅ {test_name}: {result['details']}")
            elif status == "fail":
                print(f"❌ {test_name}: {result['details']}")
                all_passed = False
            elif status == "skip":
                print(f"⏭️ {test_name}: {result['details']}")
            else:
                print(f"⚠️ {test_name}: {result['details']}")
        
        print("="*70)
        if all_passed and self.test_results["signup_fix"]["status"] == "pass":
            print("🎉 AUTHENTICATION FIX VERIFIED - All critical tests passing!")
        else:
            print("⚠️ AUTHENTICATION FIX INCOMPLETE - Issues remain")
        print("="*70)
        
        return self.test_results

async def main():
    """Main test runner for authentication fix verification"""
    async with AuthFixTester() as tester:
        results = await tester.run_focused_tests()
        return results

if __name__ == "__main__":
    asyncio.run(main())