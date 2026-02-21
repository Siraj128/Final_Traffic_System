import sqlite3
import os
from datetime import datetime

db_path = "Database/reward_app.db"

def migrate():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;") # Disable for reorganization

    try:
        # 0. Check if drivers already has driver_id
        cursor.execute("PRAGMA table_info(drivers)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'driver_id' not in columns:
            # Fallback for very old setup if driver_id doesn't exist
            print("Adding driver_id to drivers table...")
            # This is complex in SQLite, skipping for now assuming driver_id exists per models.py
            pass

        # 1. Create Vehicles table
        print("Creating 'vehicles' table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER,
            plate_number TEXT UNIQUE,
            vehicle_type TEXT,
            brand TEXT,
            model TEXT,
            color TEXT,
            fastag_id TEXT,
            is_primary BOOLEAN DEFAULT 0,
            compliance_score FLOAT DEFAULT 100.0,
            safe_streak_days INTEGER DEFAULT 0,
            created_at DATETIME,
            FOREIGN KEY(driver_id) REFERENCES drivers(driver_id)
        )
        """)

        # 2. Migrate Driver data to Vehicles
        print("Migrating driver vehicle data to 'vehicles' table...")
        cursor.execute("PRAGMA table_info(drivers)")
        drivers_cols = [col[1] for col in cursor.fetchall()]
        
        if 'plate_number' in drivers_cols:
            # Check if we already migrated
            cursor.execute("SELECT count(*) FROM vehicles")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                INSERT INTO vehicles (driver_id, plate_number, vehicle_type, is_primary, compliance_score, created_at)
                SELECT driver_id, plate_number, vehicle_type, 1, compliance_score, ? FROM drivers
                """, (datetime.utcnow(),))
                print("Successfully migrated vehicles.")
            else:
                print("Vehicles table already has data, skipping initial migration.")
        else:
            print("No 'plate_number' in drivers table, skipping vehicle migration.")

        # 3. Create map of plate_number to vehicle_id for updating other tables
        cursor.execute("SELECT plate_number, vehicle_id, driver_id FROM vehicles")
        mapping = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        # 4. Reorganize related tables to use vehicle_id and driver_id
        tables_to_fix = [
            ('virtual_cards', ['card_id', 'driver_id', 'card_number', 'expiry_date', 'cvv', 'card_balance', 'is_frozen']),
            ('rewards', ['reward_id', 'driver_id', 'vehicle_id', 'reward_type', 'reward_points', 'junction_id', 'timestamp']),
            ('violations', ['violation_id', 'driver_id', 'vehicle_id', 'violation_type', 'penalty_points', 'junction_id', 'timestamp']),
            ('transactions', ['transaction_id', 'driver_id', 'transaction_type', 'amount', 'balance_after', 'description', 'timestamp']),
            ('notifications', ['notification_id', 'driver_id', 'title', 'message', 'limit_type', 'is_read', 'timestamp']),
            ('leaderboard', ['leaderboard_id', 'driver_id', 'rank_score', 'rank_position', 'last_updated']),
            ('redemption_transactions', ['transaction_id', 'driver_id', 'reward_id', 'points_spent', 'status', 'coupon_code', 'timestamp']),
            ('driver_analytics', ['analytics_id', 'vehicle_id', 'driving_score', 'risk_level', 'safe_streak_days', 'total_rewards', 'total_violations', 'last_updated'])
        ]

        for table_name, new_cols in tables_to_fix:
            print(f"Refactoring table '{table_name}'...")
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"Table '{table_name}' does not exist, skipping.")
                continue

            # Get old data
            cursor.execute(f"SELECT * FROM {table_name}")
            old_rows = cursor.fetchall()
            
            # Get old columns to map correctly
            cursor.execute(f"PRAGMA table_info({table_name})")
            old_cols = [col[1] for col in cursor.fetchall()]

            # Skip if already refactored (if new_cols match current cols)
            if set(new_cols) == set(old_cols):
                print(f"Table '{table_name}' already follows new schema, skipping.")
                continue
            
            # Create NEW table
            cursor.execute(f"ALTER TABLE {table_name} RENAME TO {table_name}_old")
            
            col_defs = []
            for col in new_cols:
                if col == 'plate_number': continue # Should be gone
                
                ctype = "TEXT"
                if any(x in col for x in ['id', 'points', 'amount', 'spent', 'balance', 'days', 'rewards', 'violations', 'position']):
                    ctype = "INTEGER"
                if any(x in col for x in ['score']):
                    ctype = "FLOAT"
                if any(x in col for x in ['is_frozen', 'is_read', 'is_primary']):
                    ctype = "BOOLEAN"
                if any(x in col for x in ['timestamp', 'last_updated', 'created_at']):
                    ctype = "DATETIME"
                
                col_defs.append(f"{col} {ctype}")

            cursor.execute(f"CREATE TABLE {table_name} ({', '.join(col_defs)}, PRIMARY KEY({new_cols[0]}))")
            
            # Insert data while mapping plate_number
            for row in old_rows:
                row_dict = dict(zip(old_cols, row))
                new_row_vals = []
                # Use plate_number if it exists in old_cols
                plate = row_dict.get('plate_number')
                v_id, d_id = mapping.get(plate, (None, None))
                
                # If d_id is None, try to get it from existing driver_id in row if it was there
                if d_id is None and 'driver_id' in row_dict:
                    d_id = row_dict['driver_id']
                
                valid_row = True
                for col in new_cols:
                    if col == 'vehicle_id':
                        new_row_vals.append(v_id)
                    elif col == 'driver_id':
                        new_row_vals.append(d_id)
                    else:
                        new_row_vals.append(row_dict.get(col))
                
                if valid_row:
                    placeholders = ", ".join(["?"] * len(new_row_vals))
                    cursor.execute(f"INSERT INTO {table_name} ({', '.join(new_cols)}) VALUES ({placeholders})", new_row_vals)
            
            cursor.execute(f"DROP TABLE {table_name}_old")

        # 5. Clean up Drivers table (remove plate_number, vehicle_type, compliance_score as they moved to vehicles)
        print("Cleaning up 'drivers' table...")
        cursor.execute("PRAGMA table_info(drivers)")
        current_drivers_cols = [col[1] for col in cursor.fetchall()]
        
        required_driver_cols = ['driver_id', 'owner_name', 'mobile', 'email', 'password_hash', 'wallet_points', 'avatar', 'tier', 'total_earned_credits', 'parking_quota', 'fuel_cashback', 'service_coupon_count']
        
        if 'plate_number' in current_drivers_cols:
            cursor.execute("SELECT * FROM drivers")
            drivers_rows = cursor.fetchall()
            
            col_defs = []
            for col in required_driver_cols:
                ctype = "TEXT"
                if any(x in col for x in ['id', 'points', 'credits', 'quota', 'cashback', 'count']):
                    ctype = "INTEGER"
                col_defs.append(f"{col} {ctype}")
            
            cursor.execute("ALTER TABLE drivers RENAME TO drivers_old")
            cursor.execute(f"CREATE TABLE drivers ({', '.join(col_defs)}, PRIMARY KEY(driver_id))")
            
            for row in drivers_rows:
                row_dict = dict(zip(current_drivers_cols, row))
                new_vals = [row_dict.get(col) for col in required_driver_cols]
                placeholders = ", ".join(["?"] * len(new_vals))
                cursor.execute(f"INSERT INTO drivers ({', '.join(required_driver_cols)}) VALUES ({placeholders})", new_vals)
                
            cursor.execute("DROP TABLE drivers_old")
        else:
            print("Drivers table already cleaned up, skipping.")

        conn.commit()
        print("Migration to Multi-Vehicle system completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.close()

if __name__ == "__main__":
    migrate()
