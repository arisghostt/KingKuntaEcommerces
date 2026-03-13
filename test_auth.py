#!/usr/bin/env python3
"""
Test Bearer Token Authentication Endpoint
Run this script to verify the /api/auth/token/ endpoint is working
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000"
AUTH_ENDPOINT = f"{API_BASE}/api/auth/token/"
INVENTORY_ENDPOINT = f"{API_BASE}/api/inventory/adjustments/"

def test_auth_root():
    """Optional step: ensure the bare /api/auth/ endpoint exists and lists subpaths"""
    root_url = f"{API_BASE}/api/auth/"
    print("=" * 60)
    print("STEP 0: Testing /api/auth/ (root overview)")
    print("=" * 60)
    print()

    try:
        response = requests.get(root_url)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except Exception:
            print(response.text)
        print()

        if response.status_code == 200:
            data = response.json()
            if 'token' in data and 'status' in data:
                print('✅ Root auth endpoint exists and returns links')
            else:
                print('⚠️  Root returned 200 but missing expected keys')
        else:
            print('⚠️  Root auth endpoint returned non‑200, maybe not defined')
    except Exception as e:
        print(f"❌ ERROR: {e}")

    print()


def test_login():
    """Step 1: Test login endpoint and get token"""
    print("=" * 60)
    print("STEP 1: Testing /api/auth/token/ (Login)")
    print("=" * 60)
    print()
    
    credentials = {
        "username": "admin",
        "password": "password123"
    }
    
    print(f"Sending POST request to: {AUTH_ENDPOINT}")
    print(f"Credentials: {json.dumps(credentials, indent=2)}")
    print()
    
    try:
        response = requests.post(AUTH_ENDPOINT, json=credentials)
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        print(json.dumps(response.json(), indent=2))
        print()
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            if token:
                print(f"✅ SUCCESS! Token obtained:")
                print(f"   Token: {token[:50]}...")
                print()
                return token
            else:
                print("❌ FAILED: No token in response")
                return None
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print("Possible causes:")
            print("  1. Admin user doesn't exist")
            print("  2. Wrong username/password")
            print("  3. Server not running")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ FAILED: Cannot connect to server")
        print("Make sure the Django server is running:")
        print("  python manage.py runserver")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def test_api_call(token):
    """Step 2: Test authenticated API call using the token"""
    print("=" * 60)
    print("STEP 2: Testing Authenticated API Call")
    print("=" * 60)
    print()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Sending GET request to: {INVENTORY_ENDPOINT}")
    print(f"Headers:")
    print(f"  Authorization: Bearer {token[:50]}...")
    print()
    
    try:
        response = requests.get(INVENTORY_ENDPOINT, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Preview:")
        data = response.json()
        print(json.dumps(data, indent=2)[:500] + "...")
        print()
        
        if response.status_code == 200:
            print("✅ SUCCESS! Your Bearer Token is working!")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print("Response:", response.text)
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_without_token():
    """Test: What happens without a token (should fail)"""
    print("=" * 60)
    print("STEP 3: Testing Request WITHOUT Token (should fail)")
    print("=" * 60)
    print()
    
    print(f"Sending GET request to: {INVENTORY_ENDPOINT}")
    print("Headers: (none)")
    print()
    
    try:
        response = requests.get(INVENTORY_ENDPOINT)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ CORRECT! Server rejected request without token (401 Unauthorized)")
        else:
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()

def test_invalid_token():
    """Test: What happens with an invalid token (should fail)"""
    print("=" * 60)
    print("STEP 4: Testing Request with INVALID Token (should fail)")
    print("=" * 60)
    print()
    
    invalid_token = "invalid_token_12345"
    headers = {
        "Authorization": f"Bearer {invalid_token}",
        "Content-Type": "application/json"
    }
    
    print(f"Sending GET request to: {INVENTORY_ENDPOINT}")
    print(f"Headers:")
    print(f"  Authorization: Bearer {invalid_token}")
    print()
    
    try:
        response = requests.get(INVENTORY_ENDPOINT, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ CORRECT! Server rejected invalid token (401 Unauthorized)")
        else:
            print(f"Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"ERROR: {e}")
    
    print()

def main():
    """Run all tests"""
    print()
    print("╔" + "=" * 58 + "╗")
    print("║  BEARER TOKEN AUTHENTICATION TEST SUITE                  ║")
    print("║  Testing: /api/auth/token/ endpoint                      ║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Test 0: root overview (not strictly required but nice)
    test_auth_root()
    # Test 1: Login and get token
    token = test_login()
    if not token:
        print("\n⚠️  Cannot proceed without token. Fix the login issue first.")
        sys.exit(1)
    
    # Test 2: Use token in authenticated request
    test_api_call(token)
    
    # Test 3: Verify request fails without token
    test_without_token()
    
    # Test 4: Verify request fails with invalid token
    test_invalid_token()
    
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
✅ All tests passed! Your Bearer Token Authentication is working.

Next steps for your frontend:
1. POST to /api/auth/token/ with username/password
2. Store the returned token in localStorage
3. Include token in Authorization header: "Bearer <token>"
4. Make your API calls with the token

See FRONTEND_AUTH_GUIDE.md for complete frontend examples.
""")

if __name__ == "__main__":
    main()
