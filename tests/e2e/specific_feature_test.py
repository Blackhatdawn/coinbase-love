#!/usr/bin/env python3
"""
Test specific features mentioned in the review request
"""
import requests
import json

def test_specific_features():
    base_url = 'http://localhost:8001'
    
    print('🔍 Testing Specific Features from Review Request')
    print('='*60)
    
    results = []
    
    # 1. Socket.IO connection - GET /socket.io/?EIO=4&transport=polling should return sid
    print('1. Testing Socket.IO Connection...')
    try:
        response = requests.get(f'{base_url}/socket.io/?EIO=4&transport=polling', timeout=10)
        if response.status_code == 200 and 'sid' in response.text:
            print('✅ Socket.IO connection working - returns sid')
            print(f'   Response: {response.text[:100]}...')
            results.append(('Socket.IO Connection', True, 'Returns sid successfully'))
        else:
            print(f'❌ Socket.IO connection failed - Status: {response.status_code}')
            results.append(('Socket.IO Connection', False, f'Status: {response.status_code}'))
    except Exception as e:
        print(f'❌ Socket.IO connection error: {e}')
        results.append(('Socket.IO Connection', False, str(e)))
    
    # 2. Health check endpoint returns status healthy
    print('\n2. Testing Health Check Endpoint...')
    try:
        response = requests.get(f'{base_url}/health', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'healthy':
                print('✅ Health check returns healthy status')
                print(f'   Database: {data.get("database", "unknown")}')
                results.append(('Health Check', True, f'Status: healthy, DB: {data.get("database")}'))
            else:
                print(f'❌ Health check status not healthy: {data.get("status")}')
                results.append(('Health Check', False, f'Status: {data.get("status")}'))
        else:
            print(f'❌ Health check failed - Status: {response.status_code}')
            results.append(('Health Check', False, f'HTTP {response.status_code}'))
    except Exception as e:
        print(f'❌ Health check error: {e}')
        results.append(('Health Check', False, str(e)))
    
    # 3. Crypto prices endpoint returns data
    print('\n3. Testing Crypto Prices Endpoint...')
    try:
        response = requests.get(f'{base_url}/api/crypto', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'cryptocurrencies' in data and len(data['cryptocurrencies']) > 0:
                print(f'✅ Crypto prices endpoint working - {len(data["cryptocurrencies"])} cryptocurrencies')
                # Check if we have Bitcoin data
                btc_data = next((c for c in data['cryptocurrencies'] if c.get('symbol') == 'BTC'), None)
                if btc_data:
                    print(f'   BTC Price: ${btc_data.get("price", 0):,.2f}')
                results.append(('Crypto Prices', True, f'{len(data["cryptocurrencies"])} cryptocurrencies available'))
            else:
                print(f'❌ Crypto prices endpoint returned no data: {data}')
                results.append(('Crypto Prices', False, 'No cryptocurrency data'))
        else:
            print(f'❌ Crypto prices endpoint failed - Status: {response.status_code}')
            results.append(('Crypto Prices', False, f'HTTP {response.status_code}'))
    except Exception as e:
        print(f'❌ Crypto prices endpoint error: {e}')
        results.append(('Crypto Prices', False, str(e)))
    
    # 4. Auth flow testing
    print('\n4. Testing Auth Endpoints...')
    session = requests.Session()
    
    # Test signup
    try:
        signup_data = {
            'email': 'test_specific@example.com',
            'name': 'Test User',
            'password': 'TestPassword123!'
        }
        response = session.post(f'{base_url}/api/auth/signup', json=signup_data, timeout=10)
        if response.status_code == 200:
            print('✅ Auth signup endpoint working')
            results.append(('Auth Signup', True, 'User created successfully'))
            
            # Test login
            login_data = {
                'email': 'test_specific@example.com',
                'password': 'TestPassword123!'
            }
            response = session.post(f'{base_url}/api/auth/login', json=login_data, timeout=10)
            if response.status_code == 200:
                print('✅ Auth login endpoint working')
                results.append(('Auth Login', True, 'Login successful'))
                
                # Test profile (should work if cookies are set)
                response = session.get(f'{base_url}/api/auth/me', timeout=10)
                if response.status_code == 200:
                    print('✅ Auth profile endpoint working')
                    results.append(('Auth Profile', True, 'Profile retrieved'))
                else:
                    print(f'⚠️ Auth profile requires authentication: {response.status_code}')
                    results.append(('Auth Profile', False, 'Authentication issue'))
                    
            elif 'verify' in response.text.lower():
                print('✅ Auth login working (requires email verification)')
                results.append(('Auth Login', True, 'Requires email verification'))
            else:
                print(f'❌ Auth login failed - Status: {response.status_code}')
                results.append(('Auth Login', False, f'HTTP {response.status_code}'))
        else:
            print(f'❌ Auth signup failed - Status: {response.status_code}')
            results.append(('Auth Signup', False, f'HTTP {response.status_code}'))
            
    except Exception as e:
        print(f'❌ Auth endpoints error: {e}')
        results.append(('Auth Flow', False, str(e)))
    
    # 5. Test wallet balance (requires auth)
    print('\n5. Testing Wallet Balance...')
    try:
        response = session.get(f'{base_url}/api/wallet/balance', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print('✅ Wallet balance endpoint working')
            results.append(('Wallet Balance', True, 'Balance retrieved'))
        elif response.status_code == 401:
            print('✅ Wallet balance correctly requires authentication')
            results.append(('Wallet Balance Auth', True, 'Requires authentication'))
        else:
            print(f'❌ Wallet balance failed - Status: {response.status_code}')
            results.append(('Wallet Balance', False, f'HTTP {response.status_code}'))
    except Exception as e:
        print(f'❌ Wallet balance error: {e}')
        results.append(('Wallet Balance', False, str(e)))
    
    print('\n' + '='*60)
    print('📊 TEST RESULTS SUMMARY')
    print('='*60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, details in results:
        status = '✅ PASS' if success else '❌ FAIL'
        print(f'{status} {test_name}: {details}')
    
    print(f'\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)')
    
    return results

if __name__ == '__main__':
    test_specific_features()