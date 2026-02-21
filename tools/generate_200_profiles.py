import json
import random

def generate_profiles(count=100):
    first_names = ["Aditya", "Priya", "Rahul", "Sneha", "Amit", "Neha", "Vikram", "Anjali", "Rohan", "Kavita", 
                   "Suresh", "Meera", "Arjun", "Pooja", "Manish", "Simran", "Rajesh", "Sunita", "Vikas", "Nisha",
                   "Aarav", "Ishani", "Vihaan", "Ananya", "Reyansh", "Myra", "Aryan", "Saanvi", "Kabir", "Kiara"]
    last_names = ["Sharma", "Patel", "Verma", "Gupta", "Singh", "Joshi", "Malhotra", "Deshmukh", "Mehta", "Reddy",
                  "Nair", "Iyer", "Kapoor", "Hegde", "Tiwari", "Kaur", "Kumar", "Rao", "Dubey", "Agarwal",
                  "Patil", "Desai", "Goel", "Bansal", "Chawla", "Saxena", "Khan", "Sheikh", "Bhatt", "Sen"]

    profiles = []
    for i in range(1, count + 1):
        first = random.choice(first_names)
        last = random.choice(last_names)
        owner = f"{first} {last}"
        
        # Unique Phone (10 digits starting with 9)
        phone = f"98765{i:05d}"
        email = f"{first.lower()}.{last.lower()}.{i}@safedrive.in"
        license_id = f"DL-{i+1000}"
        
        # Two vehicles per user (100 users -> 200 plates)
        # Using 4-digit suffix to reach 10 characters total (e.g., MH12DE1001)
        plate_1 = f"MH12-DE-{1000 + (i*2 - 1)}"
        plate_2 = f"MH12-DE-{1000 + (i*2)}"
        
        profiles.append({
            "owner": owner,
            "email": email,
            "phone": phone,
            "license": license_id,
            "v1_plate": plate_1,
            "v2_plate": plate_2,
            "score": random.randint(8, 10)
        })
        
    return profiles

if __name__ == "__main__":
    data = generate_profiles(100)
    import os
    target_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "dummy_profiles_100.json")
    with open(target_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Generated 100 users with 200 total plates at {target_path}")
