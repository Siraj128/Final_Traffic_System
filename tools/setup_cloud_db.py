import os
import sys
import psycopg2

# Add parent dir to path to import cloud_db_handler
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cms_layer.cloud_db_handler import get_db_connection

def setup_schema():
    print("🚀 Initializing Database Schema...")
    conn = get_db_connection()
    
    if not conn:
        print("❌ Could not connect to Database. Check .env credentials.")
        return
        
    try:
        cur = conn.cursor()
        
        # 1. Junction Status (Live State)
        print("Creating table: junction_status...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS junction_status (
                junction_id TEXT PRIMARY KEY,
                saturation_level FLOAT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_data TEXT
            );
        """)
        
        # 2. Violations (Evidence)
        print("Creating table: violations...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                id SERIAL PRIMARY KEY,
                plate TEXT,
                violation_type TEXT,
                junction_id TEXT,
                timestamp TIMESTAMP,
                evidence_url TEXT
            );
        """)
        
        # 3. Traffic History (Analytics)
        print("Creating table: traffic_history_log...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS traffic_history_log (
                id SERIAL PRIMARY KEY,
                junction_id TEXT,
                cycle_no INT,
                winner TEXT,
                green_time INT,
                timestamp TIMESTAMP,
                metrics TEXT
            );
        """)
        
        # 4. Active Interventions (Throttling)
        print("Creating table: active_interventions...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS active_interventions (
                source_id TEXT PRIMARY KEY,
                target_id TEXT,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 5. User Rewards (Ghost Data)
        print("Creating table: user_rewards...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_rewards (
                v1_plate TEXT PRIMARY KEY,
                v1_points INT DEFAULT 0,
                v2_plate TEXT,
                v2_points INT DEFAULT 0,
                user_id INT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        print("✅ Schema Created Successfully!")
        
    except Exception as e:
        print(f"❌ Schema Creation Failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_schema()
