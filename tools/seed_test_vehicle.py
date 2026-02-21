
import psycopg2
import bcrypt
import os

# DB Config
DB_PARAMS = {
    "dbname": "safedrive_apps",
    "user": "safedrive_user",
    "password": "safedrive",
    "host": "localhost",
    "port": "5432"
}

def seed_data():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        email = "testuser3@example.com"
        password = "password123"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 1. Insert User
        print(f"Creating User: {email} ...")
        # Check if exists
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        res = cur.fetchone()
        
        if res:
            user_id = res[0]
            print(f"  Result: User already exists (ID: {user_id})")
        else:
            cur.execute("""
                INSERT INTO users (name, email, password, mobile, wallet_balance)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, ("Test User 3", email, hashed, "9999999999", 500.0))
            user_id = cur.fetchone()[0]
            print(f"  Result: Created User ID: {user_id}")
            
        # 2. Insert Vehicle
        plate = "MH12TEST03"
        print(f"Adding Vehicle: {plate} ...")
        
        cur.execute("SELECT id FROM vehicles WHERE plate_number = %s", (plate,))
        if cur.fetchone():
             print(f"  Result: Vehicle already exists.")
        else:
            cur.execute("""
                INSERT INTO vehicles (user_id, plate_number, vehicle_type, is_primary)
                VALUES (%s, %s, %s, %s)
            """, (user_id, plate, "Car", True))
            print(f"  Result: Vehicle Added.")
            
        conn.commit()
        cur.close()
        conn.close()
        print("\nSUCCESS! Login with:")
        print(f"Email: {email}")
        print(f"Pass:  {password}")
        
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    seed_data()
