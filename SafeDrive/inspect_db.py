import sqlite3
import os

db_path = "Database/reward_app.db"

def inspect():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    tables = ["drivers", "leaderboard", "virtual_cards", "rewards", "violations", "transactions", "notifications", "redemption_catalog", "redemption_transactions", "driver_analytics", "system_config", "traffic_rules"]
    
    for table in tables:
        print(f"\n--- Schema for {table} ---")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            if not columns:
                print("Table does not exist.")
            else:
                for col in columns:
                    print(f"Column: {col[1]}, Type: {col[2]}")
        except Exception as e:
            print(f"Error inspecting {table}: {e}")

    conn.close()

if __name__ == "__main__":
    inspect()
