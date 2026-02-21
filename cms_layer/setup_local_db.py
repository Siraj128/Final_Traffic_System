import psycopg2
import os
from dotenv import load_dotenv

# Load env variables (force reload from file)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(_PROJECT_ROOT, '.env')
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT", "5432")

print(f"Connecting to {DB_NAME} at {DB_HOST} as {DB_USER}...")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT
    )
    cur = conn.cursor()
    
    print("Creating Tables...")

    # --- GROUP 1: CORE TRAFFIC LOGIC (From intersection_db.py & server.py) ---

    # 1. Junction Registry (Master List)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS junction_registry (
            junction_id TEXT PRIMARY KEY,
            location_name TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print(" - junction_registry: OK")

    # 2. Junction Status (Live State - server.py)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS junction_status (
            junction_id TEXT PRIMARY KEY,
            saturation_level FLOAT,
            raw_data JSONB,
            last_updated TIMESTAMP DEFAULT NOW()
        )
    """)
    print(" - junction_status: OK")

    # 3. Realtime Demand (Signal Pressure)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS realtime_demand (
            junction_id TEXT PRIMARY KEY REFERENCES junction_registry(junction_id),
            north_pressure FLOAT DEFAULT 0.0,
            south_pressure FLOAT DEFAULT 0.0,
            east_pressure FLOAT DEFAULT 0.0,
            west_pressure FLOAT DEFAULT 0.0,
            pedestrian_active BOOLEAN DEFAULT FALSE,
            last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print(" - realtime_demand: OK")

    # 4. Traffic Flow History (Vehicle Logs)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS traffic_flow_history (
            log_id SERIAL PRIMARY KEY,
            junction_id TEXT,
            vehicle_uuid UUID,
            vehicle_class TEXT,
            entry_zone TEXT,
            exit_zone TEXT,
            movement_type TEXT,
            idling_duration_sec FLOAT DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print(" - traffic_flow_history: OK")
    
    # 5. Traffic History Log (Aggregated Stats - server.py)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS traffic_history_log (
            id SERIAL PRIMARY KEY,
            junction_id TEXT NOT NULL,
            avg_saturation FLOAT DEFAULT 0.0,
            total_flow_count INTEGER DEFAULT 0,
            active_alerts TEXT DEFAULT 'Normal',
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)
    print(" - traffic_history_log: OK")

    # --- GROUP 2: REWARD SYSTEM (From database_controller.py) ---

    # 6. Vehicle Rules (Reference)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_rules (
            v_type TEXT PRIMARY KEY,
            max_pts_junction INTEGER NOT NULL,
            max_junc_day INTEGER NOT NULL,
            daily_cap INTEGER NOT NULL
        )
    """)
    print(" - vehicle_rules: OK")

    # 7. Drivers (Wallets)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            plate_id TEXT PRIMARY KEY,
            v_type TEXT NOT NULL, -- FK to vehicle_rules removed for independence
            lifetime_credits DOUBLE PRECISION DEFAULT 0.0,
            available_wallet DOUBLE PRECISION DEFAULT 0.0,
            current_tier TEXT DEFAULT 'Standard',
            security_seal TEXT, 
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print(" - drivers: OK")

    # 8. Daily Accumulator (Temp Points)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_accumulator (
            plate_id TEXT REFERENCES drivers(plate_id) ON DELETE CASCADE,
            log_date DATE NOT NULL,
            points INTEGER DEFAULT 0,
            junc_count INTEGER DEFAULT 0,
            PRIMARY KEY (plate_id, log_date)
        )
    """)
    print(" - daily_accumulator: OK")

    # 9. Audit Ledger (Transactions)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_ledger (
            tx_id SERIAL PRIMARY KEY,
            plate_id TEXT REFERENCES drivers(plate_id),
            tx_type TEXT NOT NULL, 
            amount DOUBLE PRECISION NOT NULL,
            unit TEXT NOT NULL, 
            tier_at_time TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print(" - audit_ledger: OK")

    # 10. Watchlist (Violators)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            plate_id TEXT PRIMARY KEY, -- REFERENCES drivers(plate_id) removed for flexibility
            violation_code TEXT NOT NULL,
            intersection_id TEXT NOT NULL,
            severity_score INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print(" - watchlist: OK")

    # --- GROUP 3: SAFETY & INTERVENTIONS ---

    # 11. Active Interventions (Throttling)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_interventions (
            source_id TEXT PRIMARY KEY,
            target_id TEXT,
            reason TEXT,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)
    print(" - active_interventions: OK")

    # 12. Safety Incidents (Forensic)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS safety_incidents (
            incident_id SERIAL PRIMARY KEY,
            junction_id TEXT, -- REFERENCES junction_registry(junction_id),
            anomaly_type TEXT NOT NULL, -- GRIDLOCK, ACCIDENT
            severity_level TEXT,
            incident_description TEXT,
            forensic_telemetry JSONB,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_resolved BOOLEAN DEFAULT FALSE
        )
    """)
    print(" - safety_incidents: OK")

    # 13. Traffic Violations (Evidence)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS traffic_violations (
            id SERIAL PRIMARY KEY,
            junction_id TEXT NOT NULL,
            plate_number TEXT DEFAULT 'PENDING',
            violation_type TEXT NOT NULL,
            violation_time TIMESTAMP DEFAULT NOW(),
            evidence_url TEXT,
            confidence FLOAT DEFAULT 0.0,
            penalty_applied BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            status TEXT DEFAULT 'PENDING',
            attributes JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            processed_at TIMESTAMP
        )
    """)
    print(" - traffic_violations: OK")

    # --- GROUP 4: MISSING TABLES (Inferred from generic traffic systems to match Screenshot) ---

    # 14. Directional Counts
    cur.execute("""
        CREATE TABLE IF NOT EXISTS directional_counts (
            id SERIAL PRIMARY KEY,
            junction_id TEXT,
            direction TEXT, -- North, South, East, West
            vehicle_count INTEGER DEFAULT 0,
            interval_start TIMESTAMP,
            interval_end TIMESTAMP
        )
    """)
    print(" - directional_counts: OK")

    # 15. Environmental Impact Daily
    cur.execute("""
        CREATE TABLE IF NOT EXISTS environmental_impact_daily (
            date DATE PRIMARY KEY,
            junction_id TEXT,
            co2_emitted_kg FLOAT DEFAULT 0.0,
            fuel_wasted_liters FLOAT DEFAULT 0.0,
            avg_idling_time_min FLOAT DEFAULT 0.0
        )
    """)
    print(" - environmental_impact_daily: OK")

    # 16. Intersections (Legacy/Alias for Junction Registry)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS intersections (
            intersection_id TEXT PRIMARY KEY,
            name TEXT,
            latitude FLOAT,
            longitude FLOAT,
            type TEXT
        )
    """)
    print(" - intersections: OK")

    # 17. Junction Anomalies (Legacy/Alias for Safety Incidents)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS junction_anomalies (
            id SERIAL PRIMARY KEY,
            junction_id TEXT,
            anomaly_type TEXT,
            details JSONB,
            detected_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print(" - junction_anomalies: OK")

    # 18. Safety Events (Legacy/Alias for Safety Incidents)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS safety_events (
            event_id SERIAL PRIMARY KEY,
            junction_id TEXT,
            event_type TEXT,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)
    print(" - safety_events: OK")

    # 19. Vehicle Trip Logs (Full Trip Tracking)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_trip_logs (
            trip_id SERIAL PRIMARY KEY,
            plate_id TEXT,
            start_junction TEXT,
            end_junction TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            distance_km FLOAT
        )
    """)
    print(" - vehicle_trip_logs: OK")

    conn.commit()
    print(" [OK] Database Setup Complete! All tables created.") 
    conn.close()

except Exception as e:
    print(f" [FAIL] Database Setup Failed: {e}")
