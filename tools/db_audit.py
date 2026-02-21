import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load .env
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

def check_db(name, host, dbname, user, password, port, sslmode=None):
    print(f"\n[ CHECKING {name} DATABASE... ]")
    print(f"   Host: {host}")
    print(f"   DB Name: {dbname}")
    
    try:
        conn = psycopg2.connect(
            host=host,
            database=dbname,
            user=user,
            password=password,
            port=port,
            sslmode=sslmode,
            connect_timeout=10
        )
        print("   [OK] Connection Successful!")
        
        cur = conn.cursor()
        
        # Check Tables
        tables = ["traffic_violations", "user_rewards", "users", "junction_status", "traffic_history_log", "rto_registry"]
        print(f"   [AUDIT] Table Rows:")
        
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"      - {table}: {count} rows")
                
                # Detailed Column Check for user_rewards (Dual-Vehicle)
                if table == "user_rewards":
                    cur.execute("SELECT * FROM user_rewards LIMIT 0")
                    col_names = [desc[0] for desc in cur.description]
                    required = ["email", "v1_plate", "v2_plate", "v1_points", "v2_points"]
                    missing = [c for c in required if c not in col_names]
                    
                    if not missing:
                         print(f"        -> [SCHEMA OK] Dual-Vehicle Columns Verified (V1/V2).")
                    else:
                         print(f"        -> [SCHEMA FAIL] Missing columns: {missing}")
                         
            except psycopg2.errors.UndefinedTable:
                print(f"      - {table}: [MISSING]")
                conn.rollback() 
            except Exception as e:
                print(f"      - {table}: [ERROR] ({e})")
                conn.rollback()

        conn.close()
        return True
    except Exception as e:
        print(f"   [FAIL] Connection Failed: {e}")
        return False

def audit_all():
    print("="*60)
    print("HTMS DATABASE ARCHITECTURE AUDIT")
    print("="*60)
    
    # 1. LOCAL
    check_db(
        "LOCAL (PostgreSQL)", 
        os.getenv("DB_HOST"),
        os.getenv("DB_NAME"),
        os.getenv("DB_USER"),
        os.getenv("DB_PASS"),
        os.getenv("DB_PORT")
    )

    # 2. CLOUD
    check_db(
        "CLOUD (Neon)", 
        os.getenv("CLOUD_DB_HOST"),
        os.getenv("CLOUD_DB_NAME"),
        os.getenv("CLOUD_DB_USER"),
        os.getenv("CLOUD_DB_PASS"),
        os.getenv("CLOUD_DB_PORT"),
        sslmode="require"
    )

if __name__ == "__main__":
    audit_all()
