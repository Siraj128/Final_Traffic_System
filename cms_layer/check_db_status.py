import psycopg2
import os
import sys
from dotenv import load_dotenv

# Load env
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(_PROJECT_ROOT, '.env')
load_dotenv(env_path)

def check_local():
    print("\n[LOCAL DATABASE STATUS]")
    host = os.getenv("DB_HOST")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    port = os.getenv("DB_PORT")
    
    print(f"Config: {user}@{host}:{port}/{name}")
    try:
        conn = psycopg2.connect(host=host, database=name, user=user, password=os.getenv("DB_PASS"), port=port)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f" [OK] Connection: SUCCESS")
        print(f" [INFO] Tables Found: {count}")
        return True
    except Exception as e:
        print(f" [FAIL] Connection: FAILED ({e})")
        return False

def check_cloud():
    print("\n[CLOUD DATABASE STATUS]")
    host = os.getenv("CLOUD_DB_HOST")
    name = os.getenv("CLOUD_DB_NAME")
    user = os.getenv("CLOUD_DB_USER")
    
    if not host:
        print(" [WARN] Config: Not set in .env")
        return False
        
    print(f"Config: {user}@{host}/{name}")
    try:
        conn = psycopg2.connect(
            host=host, 
            database=name, 
            user=user, 
            password=os.getenv("CLOUD_DB_PASS"), 
            port=os.getenv("CLOUD_DB_PORT"),
            sslmode="require"
        )
        conn.close()
        print(f" [OK] Connection: SUCCESS")
        return True
    except Exception as e:
        print(f" [FAIL] Connection: FAILED ({e})")
        return False

if __name__ == "__main__":
    print(f"Time: {os.getenv('datetime', '')}")
    l = check_local()
    c = check_cloud()
    print("\n[SUMMARY]")
    print(f"Local DB: {'ONLINE' if l else 'OFFLINE'}")
    print(f"Cloud DB: {'ONLINE' if c else 'OFFLINE'}")
