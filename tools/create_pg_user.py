
"""
tools/create_pg_user.py

Creates a new user 'safedrive_user' with password 'safedrive'
and grants permissions on 'safedrive_apps' database.
"""
import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import SystemConfig

# Admin config (postgres/aynan@2023)
DB_CONFIG = SystemConfig.DB_PARAMS

NEW_USER = "safedrive_user"
NEW_PASS = "safedrive"
TARGET_DB = "safedrive_apps"

def create_user():
    print(">> Connecting as Admin (postgres)...")
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname='{NEW_USER}'")
        if not cur.fetchone():
            print(f">> Creating user '{NEW_USER}' with password '{NEW_PASS}'...")
            cur.execute(f"CREATE USER {NEW_USER} WITH PASSWORD '{NEW_PASS}'")
        else:
            print(f">> User '{NEW_USER}' already exists. Updating password...")
            cur.execute(f"ALTER USER {NEW_USER} WITH PASSWORD '{NEW_PASS}'")
            
        # Grant Connect
        print(f">> Granting CONNECT on database '{TARGET_DB}'...")
        cur.execute(f"GRANT CONNECT ON DATABASE {TARGET_DB} TO {NEW_USER}")
        
        # Grant Schema Usage (Need to connect to target DB for this usually, but let's try owner change or superuser)
        # Easiest way: make user owner of database? Or grant all.
        print(f">> Making '{NEW_USER}' owner of '{TARGET_DB}'...")
        cur.execute(f"ALTER DATABASE {TARGET_DB} OWNER TO {NEW_USER}")
        
        cur.close()
        conn.close()
        print(">> User Created and Permissions Granted.")
        return True
        
    except Exception as e:
        print(f"xx Failed: {e}")
        return False

if __name__ == "__main__":
    create_user()
