import sys
import os
import json
import random
import psycopg2
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from cms_layer.cloud_db_handler import get_db_connection

def seed_rto():
    print("[INFO] SEEDING RTO REGISTRY (Cloud)...")
    conn = get_db_connection()
    if not conn:
        print("[ERROR] DB Connection Failed")
        return

    try:
        cur = conn.cursor()
        
        # --- RESET SCHEMA (Dual-Vehicle Support) ---
        print("[INFO] Resetting Database Schema for V1/V2 Support...")
        cur.execute("DROP TABLE IF EXISTS rto_registry CASCADE;")
        cur.execute("DROP TABLE IF EXISTS user_rewards CASCADE;")
        
        # 1. Recreate RTO Registry
        cur.execute("""
            CREATE TABLE rto_registry (
                email TEXT PRIMARY KEY,
                owner_name TEXT,
                phone_number TEXT,
                driver_license_id TEXT,
                
                v1_plate TEXT UNIQUE,
                v1_type TEXT DEFAULT 'Car',
                
                v2_plate TEXT UNIQUE,
                v2_type TEXT DEFAULT 'Car',
                
                registered_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # 2. Recreate User Rewards
        cur.execute("""
            CREATE TABLE user_rewards (
                email TEXT PRIMARY KEY,
                user_id INTEGER, -- Link to App User ID
                owner_name TEXT,
                phone_number TEXT,
                driver_license_id TEXT,
                
                v1_plate TEXT,
                v1_points INTEGER DEFAULT 0,
                
                v2_plate TEXT,
                v2_points INTEGER DEFAULT 0,
                
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        print("[INFO] Schema Reset Complete.")

        # 3. Load Dummy JSON
        dummy_path = os.path.join(PROJECT_ROOT, 'config', 'dummy_profiles.json')
        if not os.path.exists(dummy_path):
            print(f"[ERROR] Config file not found: {dummy_path}")
            return
            
        with open(dummy_path, 'r') as f:
            profiles = json.load(f)
            
        print(f"[INFO] Loaded {len(profiles)} profiles from JSON.")
        
        inserted = 0
        for p in profiles:
            # 1. Generate Identity
            safe_name = p['owner'].replace(" ", ".").lower()
            fake_email = f"{safe_name}@citizen.in"
            fake_phone = f"+91-{random.randint(7000000000, 9999999999)}"
            fake_license = f"DL-{random.randint(10000,99999)}"
            
            # 2. Generate Vehicle 2 (Extension)
            # Standardize V1 Plate (Remove dashes/spaces)
            plate_1 = p['plate'].replace("-", "").replace(" ", "").upper()
            
            # Generate Valid V2 Plate: MH12[XX][1234]
            # Random 2 letters
            char1 = chr(random.randint(65, 90))
            char2 = chr(random.randint(65, 90))
            suffix = f"{char1}{char2}"
            # Random 4 digits
            digits = random.randint(1000, 9999)
            
            plate_2 = f"MH12{suffix}{digits}"
            
            cur.execute("""
                INSERT INTO rto_registry (email, owner_name, phone_number, driver_license_id, v1_plate, v1_type, v2_plate, v2_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO NOTHING
            """, (fake_email, p['owner'], fake_phone, fake_license, plate_1, "Car", plate_2, "Bike"))
            inserted += 1
            
        conn.commit()
        print(f"[SUCCESS] Successfully seeded {inserted} records into 'rto_registry' (Dual-Vehicle).")
        
    except Exception as e:
        print(f"[ERROR] Seeding Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_rto()
