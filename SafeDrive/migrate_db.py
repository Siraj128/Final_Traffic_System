import sqlite3
import os

db_path = "Database/reward_app.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Add missing columns to 'drivers'
    columns_to_add = [
        ("avatar", "TEXT"),
        ("tier", "TEXT DEFAULT 'Bronze'"),
        ("total_earned_credits", "INTEGER DEFAULT 0"),
        ("parking_quota", "INTEGER DEFAULT 0"),
        ("fuel_cashback", "INTEGER DEFAULT 0"),
        ("service_coupon_count", "INTEGER DEFAULT 0")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE drivers ADD COLUMN {col_name} {col_type}")
            print(f"Added '{col_name}' column to 'drivers' table.")
        except sqlite3.OperationalError:
            print(f"'{col_name}' column already exists in 'drivers' table.")

    # 2. Ensure traffic_rules table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS traffic_rules (
        rule_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        keywords TEXT,
        question TEXT,
        answer TEXT,
        fine_amount TEXT,
        impact TEXT
    )
    """)
    print("Ensured 'traffic_rules' table exists.")

    # 3. Ensure system_config table exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_config (
        config_id INTEGER PRIMARY KEY AUTOINCREMENT,
        fuel_cashback_rate FLOAT DEFAULT 0.05,
        parking_quota_base INTEGER DEFAULT 2,
        green_wave_min_tier TEXT DEFAULT 'Gold',
        violation_penalty_multiplier FLOAT DEFAULT 1.0,
        last_updated DATETIME
    )
    """)
    print("Ensured 'system_config' table exists.")
    
    # 4. Ensure driver_analytics table exists (just in case)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS driver_analytics (
        analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
        plate_number TEXT UNIQUE,
        driving_score FLOAT DEFAULT 100.0,
        risk_level TEXT DEFAULT 'SAFE',
        safe_streak_days INTEGER DEFAULT 0,
        total_rewards INTEGER DEFAULT 0,
        total_violations INTEGER DEFAULT 0,
        last_updated DATETIME,
        FOREIGN KEY(plate_number) REFERENCES drivers(plate_number)
    )
    """)
    print("Ensured 'driver_analytics' table exists.")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
