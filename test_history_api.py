"""
Test script to verify the history API connection
"""
import requests
import json

BACKEND_URL = "https://workshop-ii-autorbi-webapp.onrender.com"

def test_health():
    """Test if backend is reachable"""
    print("Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"✓ Backend Status: {response.status_code}")
        print(f"  Response: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Backend Error: {e}")
        return False

def test_history_period():
    """Test the history period endpoint (without authentication)"""
    print("\nTesting history period endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/history/period?days=7")
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Success! Found {len(data)} activities")
            if data:
                print(f"  Sample activity: {json.dumps(data[0], indent=2)}")
        elif response.status_code == 401:
            print(f"  ⚠ Unauthorized - Authentication required")
            print(f"  This is expected if the endpoint requires authentication")
        else:
            print(f"  Response: {response.text}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def test_login():
    """Test login endpoint"""
    print("\nTesting login endpoint...")
    try:
        # Try to login with demo credentials (if they exist)
        # FastAPI expects form data in a specific format
        from requests.auth import HTTPBasicAuth
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            data={
                "username": "admin",
                "password": "admin123"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Login successful!")
            token = data.get("access_token")
            return token
        elif response.status_code == 401:
            print(f"  ⚠ Invalid credentials or user doesn't exist")
            print(f"  Note: You need to create a user first or use correct credentials")
        else:
            print(f"  Response: {response.text}")
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def test_authenticated_history(token):
    """Test history endpoint with authentication"""
    print("\nTesting authenticated history endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BACKEND_URL}/api/history/period?days=7",
            headers=headers
        )
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Success! Found {len(data)} activities")
            if data and len(data) > 0:
                print(f"  Latest activity:")
                print(f"    - Action: {data[0].get('action')}")
                print(f"    - Entity: {data[0].get('entity_type')}")
                print(f"    - Time: {data[0].get('created_at')}")
        else:
            print(f"  Response: {response.text}")
        return True
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("AutoRBI Backend History API Test")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Backend is not reachable. Please check the URL and network.")
        exit(1)
    
    # Test 2: Try history without auth
    test_history_period()
    
    # Test 3: Try to login
    token = test_login()
    
    # Test 4: If login successful, test authenticated history
    if token:
        test_authenticated_history(token)
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
