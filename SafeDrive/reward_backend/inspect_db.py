import sqlite3
import os

db_path = r"d:\Antigravity\reward app\Database\reward_app.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM drivers")
        rows = cursor.fetchall()
        print(f"Total Drivers: {len(rows)}")
        for row in rows:
            print(row)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
