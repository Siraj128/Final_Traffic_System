import os
import psycopg2
from dotenv import load_dotenv

# Load connection string from .env
load_dotenv()
DB_HOST = os.getenv("CLOUD_DB_HOST")
DB_NAME = "neondb" # Corrected from .env
DB_USER = os.getenv("CLOUD_DB_USER")
DB_PASS = os.getenv("CLOUD_DB_PASS")
DB_PORT = os.getenv("CLOUD_DB_PORT", "5432")

def seed_ghost_data():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            sslmode='require'
        )
        cursor = conn.cursor()

        # Updated to match App Regex: ^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$
        # Removed 'TEST' because it has 4 chars, regex expects 2.
        plate = "MH12AB9999"
        email = f"ghost_{plate}@temp.com"
        
        # 1. CLEANUP: Delete if exists
        cursor.execute("DELETE FROM user_rewards WHERE email = %s", (email,))
        print(f"[*] Cleanup: Deleted any existing row for {email}")

        # 2. Insert new Ghost Record with canonical plate
        cursor.execute("""
            INSERT INTO user_rewards (user_id, email, v1_plate, v1_points, v2_plate, v2_points)
            VALUES (NULL, %s, %s, 500, 'NONE', 0)
        """, (email, plate))
        print(f"[CREATED] Created Ghost Record: {plate} with 500 points.")

        conn.commit()
        cursor.close()
        conn.close()
        print("\n[SUCCESS] You can now Register in the App with 'MH12-TEST-9999' to claim these points.")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    seed_ghost_data()
