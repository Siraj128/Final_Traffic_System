import requests
import json
import random

BASE_URL = "http://localhost:5000/api"

def test_claim():
    # 1. Random Email to avoid "User already exists"
    # This ensures we are simulating a "New User" every time we run this test.
    email = f"claim_tester_{random.randint(1000,9999)}@test.com"
    
    payload = {
        "name": "Claim Tester",
        "email": email,
        "password": "password123",
        "mobile": "9999999999",
        "vehicle_number": "MH12-TEST-9999", # The Ghost Plate seeded earlier
        "vehicle_type": "Car"
    }
    
    print(f"[*] Sending Registration Request...")
    print(f"   Email: {email}")
    print(f"   Vehicle: MH12-TEST-9999 (Should have 500 Ghost Points)")
    
    try:
        # Call the Node.js Backend
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            user = data['user']
            
            print("\n[+] API Response: 200 OK")
            print(f"   User Created: {user['name']}")
            print(f"   Wallet Balance: {user['total_earned_points']} Points")
            
            # Logic Verification
            if int(user['total_earned_points']) == 500:
                print("\n[SUCCESS] VERIFICATION SUCCESSFUL!")
                print("   The logic correctly identified the Ghost Plate and transferred 500 points.")
            else:
                print(f"\n[FAIL] VERIFICATION FAILED: Expected 500 points, got {user['total_earned_points']}.")
                print("   (Did you run 'python tools/seed_ghost_reward.py' first?)")
        else:
            print(f"\n[-] API Failed: {response.status_code}")
            print(f"   Response: {response.text}")

    except Exception as e:
        print(f"\n[!] CONNECTION ERROR: {e}")
        print("   is the Backend Server running? (cd SafeDrive/backend_server && npm start)")

if __name__ == "__main__":
    test_claim()
