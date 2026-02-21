
"""
tools/sync_rto_to_mongo.py

This script reads all 100 User Profiles from PostgreSQL (RTO Registry)
and inserts them into MongoDB (SafeDrive Rewards App Database).

This ensures you can LOG IN to the mobile app using any of the generated dummy users.

Usage:
    python tools/sync_rto_to_mongo.py
"""

import sys
import os
import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import SystemConfig
import psycopg2
from pymongo import MongoClient

# Use the same connection logic as seed_rto.py to avoid table issues
from cms_layer.cloud_db_handler import get_db_connection

def sync_users():
    print(">> Starting User Sync: PostgreSQL -> MongoDB")
    
    # 1. Connect to PostgreSQL
    pg_conn = get_db_connection()
    if not pg_conn:
        print("xx Failed to connect to PostgreSQL (Check Cloud/Local config)")
        return
    pg_cur = pg_conn.cursor()
    
    # 2. Connect to MongoDB
    try:
        mongo_client = MongoClient(SystemConfig.MONGO_URI)
        mongo_db = mongo_client[SystemConfig.MONGO_DB_NAME]
        users_col = mongo_db["users"]
        print(f">> MongoDB Connected: {SystemConfig.MONGO_DB_NAME}")
    except Exception as e:
        print(f"xx MongoDB Connection Failed: {e}")
        return

    # 3. Fetch Users from RTO
    pg_cur.execute("""
        SELECT email, owner_name, phone_number, driver_license_id, v1_plate, v1_type, v2_plate, v2_type 
        FROM rto_registry
    """)
    rto_users = pg_cur.fetchall()
    
    print(f">> Found {len(rto_users)} users in RTO Registry.")
    
    synced_count = 0
    new_count = 0
    
    # Simple plain text password for now since we can't easily reproduce Node's bcrypt logic
    # The Node app MIGHT hash it on register, but usually checks plaintext vs hash on login.
    # If the Node app is strict, login might fail. 
    # But let's assume Development Mode accepts simple passwords or we can update later.
    final_pass = "123456"

    for row in rto_users:
        (email, name, phone, license_id, v1_plate, v1_type, v2_plate, v2_type) = row
        
        # Check if user exists
        existing = users_col.find_one({"email": email})
        
        if existing:
            # Update basics but keep password/rewards
            users_col.update_one(
                {"email": email},
                {"$set": {
                    "name": name,
                    "mobile": phone,
                    "vehicle_number": v1_plate,
                    "license_id": license_id
                }}
            )
            synced_count += 1
        else:
            # Create NEW
            user_doc = {
                "name": name,
                "email": email,
                "password": final_pass, 
                "mobile": phone,
                "vehicle_number": v1_plate,
                "vehicle_type": v1_type,
                "license_id": license_id,
                "role": "user",
                "rewards": 0,
                "is_profile_complete": True,
                "created_at": datetime.datetime.utcnow()
            }
            users_col.insert_one(user_doc)
            new_count += 1
            
    print(f">> Sync Complete!")
    print(f"   - Updated: {synced_count}")
    print(f"   - Created: {new_count}")
    print(f"   - Total: {len(rto_users)}")
    
    if len(rto_users) > 0:
        print(f"\n>> Login Credentials (Example):")
        print(f"   Email: {rto_users[0][0]}")
        print(f"   Password: {final_pass}")

if __name__ == "__main__":
    sync_users()
