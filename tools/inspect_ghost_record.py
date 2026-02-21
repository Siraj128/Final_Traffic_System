import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv("CLOUD_DB_HOST")
DB_NAME = "neondb"
DB_USER = os.getenv("CLOUD_DB_USER")
DB_PASS = os.getenv("CLOUD_DB_PASS")
DB_PORT = os.getenv("CLOUD_DB_PORT", "5432")

def inspect_ghost():
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
        
        print(f"[*] Connecting to {DB_NAME} on {DB_HOST}...")

        # Query by email
        cursor.execute("SELECT * FROM user_rewards WHERE email LIKE 'ghost_%'")
        rows = cursor.fetchall()
        
        print(f"[*] Found {len(rows)} Ghost Records:")
        for row in rows:
            print(f"   ROW: {row}")

        # Query by plate
        cursor.execute("SELECT * FROM user_rewards WHERE v1_plate = 'MH12-TEST-9999'")
        rows_plate = cursor.fetchall()
        print(f"[*] Found {len(rows_plate)} records by Plate 'MH12-TEST-9999':")
        for row in rows_plate:
            print(f"   ROW: {row}")

        conn.close()

    except Exception as e:
        print(f"[!] Error: {e}")

if __name__ == "__main__":
    inspect_ghost()
