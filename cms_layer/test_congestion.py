import requests
import json
import time

SERVER_URL = "http://localhost:8000"

def jam_university():
    print("🔥 Simulating GRIDLOCK at Pune University (PUNE_JW_02)...")
    payload = {
        "target_junction": "PUNE_JW_02",
        "saturation_value": 95.0
    }
    try:
        response = requests.post(f"{SERVER_URL}/inject_congestion", json=payload)
        if response.status_code == 200:
            print("✅ Success! Server Response:", response.json())
        else:
            print("❌ Failed:", response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

def clear_university():
    print("✅ Clearing Traffic at Pune University...")
    payload = {
        "target_junction": "PUNE_JW_02",
        "saturation_value": 10.0
    }
    try:
        response = requests.post(f"{SERVER_URL}/inject_congestion", json=payload)
        if response.status_code == 200:
            print("✅ Success! Server Response:", response.json())
        else:
            print("❌ Failed:", response.text)
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("1. Jam University (Test 1)")
    print("2. Clear University (Test 2)")
    choice = input("Select Test (1/2): ")
    
    if choice == "1":
        jam_university()
    elif choice == "2":
        clear_university()
    else:
        print("Invalid choice")
