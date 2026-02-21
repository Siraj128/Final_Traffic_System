import json
import random
import os

json_path = r'C:\Users\Siraj\Desktop\Traffic_System_Root - Copy\config\dummy_profiles_100.json'

vehicle_types = ['Car', 'Bike', 'Scooter', 'SUV', 'Truck']

def enrich_profiles():
    if not os.path.exists(json_path):
        print(f"Error: File not found at {json_path}")
        return

    with open(json_path, 'r') as f:
        profiles = json.load(f)

    print(f"Loaded {len(profiles)} profiles.")

    for p in profiles:
        # Randomly assign types if missing
        if 'v1_type' not in p:
            p['v1_type'] = random.choices(vehicle_types, weights=[50, 30, 15, 4, 1])[0]
        if 'v2_type' not in p:
            p['v2_type'] = random.choices(vehicle_types, weights=[50, 30, 15, 4, 1])[0]

    with open(json_path, 'w') as f:
        json.dump(profiles, f, indent=4)
    
    print(f"Successfully enriched {len(profiles)} profiles with vehicle types.")

if __name__ == "__main__":
    enrich_profiles()
