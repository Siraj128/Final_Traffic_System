import psycopg2
import os
from dotenv import load_dotenv

# Load env variables
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(_PROJECT_ROOT, '.env')
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "smart_net_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "Siraj.9892")

print(f"Checking tables in {DB_NAME}...")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()
    
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    rows = cur.fetchall()
    tables = [row[0] for row in rows]
    
    required = [
        "traffic_history_log", 
        "junction_status", 
        "active_interventions", 
        "traffic_violations",
        "junction_registry",
        "realtime_demand",
        "traffic_flow_history",
        "safety_incidents",
        "vehicle_rules",
        "drivers",
        "daily_accumulator",
        "audit_ledger",
        "watchlist",
        "directional_counts",
        "environmental_impact_daily",
        "intersections",
        "junction_anomalies",
        "safety_events",
        "vehicle_trip_logs"
    ]
    missing = [t for t in required if t not in tables]
    
    if not missing:
        print("[OK] All required tables found.")
        print(f"Tables: {', '.join(tables)}")
    else:
        print(f"[FAIL] Missing tables: {missing}")
        
    conn.close()

except Exception as e:
    print(f"[ERROR] {e}")
