import psycopg2
import os
import json
import time
from dotenv import load_dotenv

# Load env to get DB credentials (should be PUNE_JW_01's local DB)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(_PROJECT_ROOT, '.env')
load_dotenv(env_path)

def verify_nodes():
    host = os.getenv("DB_HOST", "localhost")
    name = os.getenv("DB_NAME", "smart_net_db")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS", "Siraj.9892")
    
    print(f"\n🔍 Checking Active Junctions in {name}...")
    
    try:
        conn = psycopg2.connect(host=host, database=name, user=user, password=password)
        cur = conn.cursor()
        
        # Query junction_status table
        cur.execute("SELECT junction_id, last_updated, saturation_level FROM junction_status ORDER BY junction_id")
        rows = cur.fetchall()
        
        if not rows:
            print("⚠️  No junctions found in database yet.")
        else:
            print(f"{'JUNCTION ID':<15} | {'LAST SEEN':<25} | {'SATURATION':<10}")
            print("-" * 55)
            for row in rows:
                jid, updated, sat = row
                status = "✅ ONLINE" if (time.time() - updated.timestamp() < 120) else "❌ OFFLINE"
                print(f"{jid:<15} | {str(updated):<25} | {sat:<10} {status}")
                
        conn.close()
    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    verify_nodes()
