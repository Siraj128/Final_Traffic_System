import os
import psycopg2
from dotenv import load_dotenv

# Load env from backend_server/.env
env_path = os.path.join(os.path.dirname(__file__), '..', 'SafeDrive', 'backend_server', '.env')
load_dotenv(env_path)

def inspect_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'Siraj.9892'),
            database=os.getenv('DB_NAME', 'safedrive_apps')
        )
        cur = conn.cursor()

        print("\n--- 1. LATEST USERS ---")
        cur.execute("SELECT user_id, name, email, wallet_balance, total_earned_points FROM users ORDER BY created_at DESC LIMIT 5;")
        users = cur.fetchall()
        for u in users:
            print(f"User: {u[1]} ({u[2]}) | ID: {u[0]} | Wallet: {u[3]} | Points: {u[4]}")

        print("\n--- 2. VEHICLES FOR LATEST USER ---")
        if users:
            latest_uid = users[0][0]
            cur.execute("SELECT * FROM vehicles WHERE user_id = %s", (latest_uid,))
            vehs = cur.fetchall()
            if vehs:
                for v in vehs:
                    print(f"Vehicle: {v[2]} | ID: {v[0]} | Type: {v[3]}")
            else:
                print("No vehicles found for this user.")
        
        print("\n--- 3. CHECK FOR MH12AB9999 ---")
        cur.execute("SELECT * FROM vehicles WHERE plate_number LIKE '%MH12AB9999%'")
        ghost_veh = cur.fetchall()
        if ghost_veh:
             for v in ghost_veh:
                print(f"Found Ghost Plate: {v[2]} | Link User ID: {v[1]}")
        else:
            print("Ghost Plate 'MH12AB9999' NOT FOUND in vehicles table.")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_db()
