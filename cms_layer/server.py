from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import os
import json
import asyncio
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from config.settings import SystemConfig

# 1. SECURITY & CONFIG
load_dotenv()
API_KEY = os.getenv("GOOGLE_MAPS_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
JUNCTION_ID = os.getenv("JUNCTION_ID", "PUNE_JW_01")

# 2. INTER-CITY LINKS (Federated Network Stubs)
# If these nodes jam, we would ideally talk to external IPs.
EXTERNAL_LINKS = {
    "PUNE_JW_27": "http://10.0.0.5:8000" # Example Link to PCMC Smart City CMS
}

app = FastAPI(title="Smart-Net CMS: Federated Intelligence Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE CONNECTION (Unified) ---
from .cloud_db_handler import get_db_connection

# --- BACKGROUND TASK: HISTORY LOGGER (Gap 4 Solution) ---
async def log_history_task():
    """
    Runs in background to snapshot traffic state every 60s for Analytics.
    """
    while True:
        await asyncio.sleep(60) # Wait 1 minute
        conn = get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                # Aggregate data from live status
                cur.execute("SELECT junction_id, saturation_level FROM junction_status")
                rows = cur.fetchall()
                
                for row in rows:
                    jid, sat = row
                    alert_status = "Normal"
                    if sat > 80: alert_status = "Congested"
                    if sat > 95: alert_status = "Gridlock"
                    
                    # Insert into History Log
                    cur.execute("""
                        INSERT INTO traffic_history_log (junction_id, avg_saturation, total_flow_count, active_alerts)
                        VALUES (%s, %s, %s, %s)
                    """, (jid, sat, 0, alert_status)) # 0 flow count placeholder for now
                
                conn.commit()
                print("📝 [HISTORY] Traffic Snapshot saved to Database.")
            except Exception as e:
                print(f"History Log Error: {e}")
            finally:
                conn.close()

@app.on_event("startup")
async def startup_event():
    print(f"[SERVER] Starting CMS Federated Node: {JUNCTION_ID}")
    if JUNCTION_ID not in TOPOLOGY_NODES:
        print(f"⚠️  [SERVER] Warning: ID '{JUNCTION_ID}' not found in Topology!")
    
    # Start the history logger when server starts
    asyncio.create_task(log_history_task())

    # --- DB SCHEMA INIT ---
    conn = get_db_connection()
    if conn:
        try:
            print("[SERVER] Verifying Database Schema...")
            cur = conn.cursor()
            
            # 1. Traffic History Log
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
            # Migration for missing columns
            try:
                cur.execute("ALTER TABLE traffic_history_log ADD COLUMN IF NOT EXISTS avg_saturation FLOAT DEFAULT 0.0")
                cur.execute("ALTER TABLE traffic_history_log ADD COLUMN IF NOT EXISTS total_flow_count INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE traffic_history_log ADD COLUMN IF NOT EXISTS active_alerts TEXT DEFAULT 'Normal'")
            except Exception: pass

            # 2. Junction Status
            cur.execute("""
                CREATE TABLE IF NOT EXISTS junction_status (
                    junction_id TEXT PRIMARY KEY,
                    saturation_level FLOAT,
                    raw_data JSONB,
                    last_updated TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # 3. Active Interventions
            cur.execute("""
                CREATE TABLE IF NOT EXISTS active_interventions (
                    source_id TEXT PRIMARY KEY,
                    target_id TEXT,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)

            # 4. Traffic Violations (Moved from Endpoint to Startup)
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
            
            # 5. Users (Cloud Auth Sync)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    full_name TEXT, -- Legacy Compatibility
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    mobile TEXT UNIQUE,
                    avatar_url TEXT,
                    total_earned_points INTEGER DEFAULT 0,
                    wallet_balance DECIMAL(10,2) DEFAULT 0.00,
                    role TEXT DEFAULT 'user',
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # Ensure columns exist and names are correct if table was already created
            # This is "Siraj's Migration" to ensure the move from local -> cloud works.
            try:
                # Legacy column handling is now done via ADD COLUMN IF NOT EXISTS below
                
                # 2. Add all production columns
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT DEFAULT 'TEMP_HASH'")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile TEXT UNIQUE")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_earned_points INTEGER DEFAULT 0")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS wallet_balance DECIMAL(10,2) DEFAULT 0.00")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user'")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT")
                cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP")
            except Exception as e:
                print(f"⚠️  Users Migration Warning: {e}")
                conn.rollback() # Clear the aborted transaction state

            # 6. Vehicles (Cloud Auth Sync)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    plate_number TEXT UNIQUE NOT NULL,
                    vehicle_type TEXT DEFAULT 'Car',
                    is_primary BOOLEAN DEFAULT FALSE,
                    rto_slot INTEGER DEFAULT 1, -- 1 for v1, 2 for v2
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            try:
                cur.execute("ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS rto_slot INTEGER DEFAULT 1")
            except Exception as e:
                print(f"⚠️  Vehicles Migration Warning: {e}")
                conn.rollback() # Clear the aborted transaction state

            # 7. Transactions (Cloud Auth Sync)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(user_id),
                    type TEXT NOT NULL, -- e.g., 'EARNED', 'REDEEMED'
                    amount INTEGER DEFAULT 0,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # 7. RTO REGISTRY (Identity Source)
            # Refactored for Phone-based Identity (User: Siraj)
            # FORCE RECREATION to ensure phone_number is the PRIMARY KEY
            cur.execute("DROP TABLE IF EXISTS rto_registry CASCADE")
            cur.execute("""
                CREATE TABLE rto_registry (
                    phone_number TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    owner_name TEXT,
                    driver_license_id TEXT,
                    
                    v1_plate TEXT UNIQUE,
                    v1_type TEXT DEFAULT 'Car',
                    
                    v2_plate TEXT UNIQUE,
                    v2_type TEXT DEFAULT 'Car',
                    
                    registered_at TIMESTAMP DEFAULT NOW()
                )
            """)

            # 8. User Rewards (App View)
            # FORCE RECREATION to ensure phone_number is the PRIMARY KEY
            cur.execute("DROP TABLE IF EXISTS user_rewards CASCADE")
            cur.execute("""
                CREATE TABLE user_rewards (
                    phone_number TEXT PRIMARY KEY,
                    user_id SERIAL,
                    email TEXT,
                    owner_name TEXT,
                    driver_license_id TEXT,
                    
                    v1_plate TEXT,
                    v1_points INTEGER DEFAULT 0,
                    v1_type TEXT DEFAULT 'Car',
                    
                    v2_plate TEXT,
                    v2_points INTEGER DEFAULT 0,
                    v2_type TEXT DEFAULT 'Car',
                    
                    total_points INTEGER DEFAULT 0, -- Combined Score (V1 + V2)
                    
                    vehicle_type TEXT DEFAULT 'Car', -- Legacy Compatibility
                    last_updated TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)

            try:
                cur.execute("ALTER TABLE user_rewards ADD COLUMN IF NOT EXISTS total_points INTEGER DEFAULT 0")
            except Exception as e:
                print(f"⚠️  User Rewards Migration Warning: {e}")
                conn.rollback()

            # --- SEED RTO DATA (From dummy_profiles_100.json) ---
            try:
                dummy_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'dummy_profiles_100.json')
                if os.path.exists(dummy_json_path):
                    with open(dummy_json_path, 'r') as f:
                        profiles = json.load(f)
                    
                    print(f"[SERVER] Seeding RTO Registry with {len(profiles)} users (200 vehicles)...")
                    
                    for p in profiles:
                        # 1. RTO Registry Only (Rewards table should stay empty until detection)
                        cur.execute("""
                            INSERT INTO rto_registry (phone_number, email, owner_name, driver_license_id, v1_plate, v1_type, v2_plate, v2_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (phone_number) DO UPDATE SET 
                            v1_plate = EXCLUDED.v1_plate, 
                            v1_type = EXCLUDED.v1_type,
                            v2_plate = EXCLUDED.v2_plate,
                            v2_type = EXCLUDED.v2_type;
                        """, (p['phone'], p['email'], p['owner'], p['license'], p['v1_plate'], p.get('v1_type', 'Car'), p['v2_plate'], p.get('v2_type', 'Car')))
                        
                    conn.commit()
                    print("✅ [SERVER] RTO Registry Synced (100 Users, 200 Plates).")
            except Exception as e:
                print(f"⚠️ [SERVER] Failed to seed RTO data: {e}")
                conn.rollback()

            conn.commit()
            print("✅ [SERVER] Schema Verified (RTO Registry + Enhanced Rewards).")
        except Exception as e:
            print(f"xx [SERVER] Schema Init Error: {e}")
            conn.rollback()
        finally:
            conn.close()

# --- 2. THE DEFINITIVE PUNE TOPOLOGY ---
TOPOLOGY_NODES = {
    # --- WEST CORRIDOR (Aundh -> University) ---
    "PUNE_JW_01": { "name": "Bremen Chowk (Aundh)", "lat": 18.5529, "lng": 73.8066 },
    "PUNE_JW_02": { "name": "Pune University Circle", "lat": 18.5362, "lng": 73.8306 },
    "PUNE_JW_03": { "name": "E-Square Junction", "lat": 18.5320, "lng": 73.8340 },
    "PUNE_JW_04": { "name": "Sancheti Hospital Chowk", "lat": 18.5284, "lng": 73.8490 },
    "PUNE_JW_05": { "name": "Simla Office Chowk", "lat": 18.5260, "lng": 73.8500 },

    # --- CORE LOOP (Deccan / FC / JM) ---
    "PUNE_JW_06": { "name": "Deccan Gymkhana Bus Stand", "lat": 18.5158, "lng": 73.8418 },
    "PUNE_JW_07": { "name": "Goodluck Chowk", "lat": 18.5167, "lng": 73.8405 },
    "PUNE_JW_08": { "name": "Fergusson College Gate", "lat": 18.5185, "lng": 73.8427 },
    "PUNE_JW_09": { "name": "Dnyaneshwar Paduka Chowk", "lat": 18.5222, "lng": 73.8415 },
    "PUNE_JW_10": { "name": "Jhansi Rani Chowk (Balgandharva)", "lat": 18.5200, "lng": 73.8460 },

    # --- KOTHRUD CORRIDOR (Karve Road) ---
    "PUNE_JW_11": { "name": "Chandani Chowk", "lat": 18.5080, "lng": 73.7920 },
    "PUNE_JW_12": { "name": "Paud Phata", "lat": 18.5110, "lng": 73.8180 },
    "PUNE_JW_13": { "name": "Nal Stop", "lat": 18.5085, "lng": 73.8240 },

    # --- SOUTH CORRIDOR (Satara Road / Swargate) ---
    "PUNE_JW_15": { "name": "Katraj Snake Park", "lat": 18.4575, "lng": 73.8580 },
    "PUNE_JW_16": { "name": "Padmavati Chowk", "lat": 18.4800, "lng": 73.8590 },
    "PUNE_JW_17": { "name": "Swargate Jedhe Chowk", "lat": 18.5005, "lng": 73.8585 },
    "PUNE_JW_18": { "name": "Sarasbaug Junction", "lat": 18.5040, "lng": 73.8530 },

    # --- EAST CORRIDOR (Station / Camp) ---
    "PUNE_JW_19": { "name": "Pune RTO Chowk", "lat": 18.5290, "lng": 73.8560 },
    "PUNE_JW_20": { "name": "Pune Railway Station", "lat": 18.5289, "lng": 73.8744 },
    "PUNE_JW_21": { "name": "Jehangir Hospital Chowk", "lat": 18.5300, "lng": 73.8760 },
    "PUNE_JW_22": { "name": "Blue Diamond Chowk", "lat": 18.5380, "lng": 73.8850 },
    "PUNE_JW_23": { "name": "Yerwada Gunjan Chowk", "lat": 18.5450, "lng": 73.8860 },

    # --- NORTH CORRIDOR (Nagar Road) ---
    "PUNE_JW_24": { "name": "Viman Nagar Chowk", "lat": 18.5650, "lng": 73.9130 },
    "PUNE_JW_25": { "name": "Hyatt Regency Junction", "lat": 18.5600, "lng": 73.9100 },
    "PUNE_JW_26": { "name": "Shastrinagar Chowk", "lat": 18.5520, "lng": 73.8950 },

    # --- PCMC LINK (Old Highway) ---
    "PUNE_JW_27": { "name": "Nashik Phata", "lat": 18.6038, "lng": 73.8208 },
    "PUNE_JW_28": { "name": "Kasarwadi", "lat": 18.5866, "lng": 73.8205 },
    "PUNE_JW_29": { "name": "Dapodi", "lat": 18.5724, "lng": 73.8266 },

    # --- HADAPSAR CORRIDOR (Solapur Road) ---
    "PUNE_JW_30": { "name": "Magarpatta City Main Gate", "lat": 18.5144, "lng": 73.9257 },
    "PUNE_JW_31": { "name": "Hadapsar Gadital", "lat": 18.5036, "lng": 73.9272 },
    "PUNE_JW_32": { "name": "Fatima Nagar", "lat": 18.5065, "lng": 73.8990 },

    # --- KHARADI EXTENSION ---
    "PUNE_JW_33": { "name": "Kharadi Bypass", "lat": 18.5510, "lng": 73.9350 },
    "PUNE_JW_34": { "name": "Phoenix Market City", "lat": 18.5620, "lng": 73.9170 },

    # --- CAMP AREA ---
    "PUNE_JW_35": { "name": "Pulgate", "lat": 18.5060, "lng": 73.8790 },
    "PUNE_JW_36": { "name": "Golibar Maidan", "lat": 18.5020, "lng": 73.8720 }
}

# --- 3. DIRECTIONAL CONNECTION LOGIC ---
# Format: { DOWNSTREAM_NODE: { "INCOMING_LANE_NAME": "UPSTREAM_NODE_ID" } }
NETWORK_CONNECTIONS = {
    # University Flow (North-West)
    "PUNE_JW_02": {"North": "PUNE_JW_01"}, 
    "PUNE_JW_03": {"North": "PUNE_JW_02"}, 
    "PUNE_JW_04": {"North": "PUNE_JW_03"}, 
    "PUNE_JW_05": {"North": "PUNE_JW_04"}, 

    # FC/JM Loop (Central)
    "PUNE_JW_08": {"South": "PUNE_JW_07"}, 
    "PUNE_JW_09": {"South": "PUNE_JW_08"}, 
    "PUNE_JW_10": {"West":  "PUNE_JW_06"}, 
    
    # Karve Road (West)
    "PUNE_JW_12": {"West": "PUNE_JW_11"}, 
    "PUNE_JW_13": {"West": "PUNE_JW_12"}, 
    "PUNE_JW_06": {"West": "PUNE_JW_13"}, 

    # Swargate Flow (South)
    "PUNE_JW_16": {"South": "PUNE_JW_15"}, 
    "PUNE_JW_17": {"South": "PUNE_JW_16"}, 
    "PUNE_JW_36": {"South": "PUNE_JW_17"}, 
    "PUNE_JW_35": {"West":  "PUNE_JW_36"}, 

    # Station Flow (East)
    "PUNE_JW_19": {"West": "PUNE_JW_05"}, 
    "PUNE_JW_20": {"West": "PUNE_JW_19"}, 
    "PUNE_JW_21": {"West": "PUNE_JW_20"}, 

    # Nagar Road (North-East)
    "PUNE_JW_25": {"East": "PUNE_JW_24"}, 
    "PUNE_JW_26": {"East": "PUNE_JW_25"},
    "PUNE_JW_23": {"East": "PUNE_JW_26"}, 

    # PCMC (North)
    "PUNE_JW_28": {"North": "PUNE_JW_27"}, 
    "PUNE_JW_29": {"North": "PUNE_JW_28"}, 
    "PUNE_JW_01": {"North": "PUNE_JW_29"}, 

    # Hadapsar (East)
    "PUNE_JW_32": {"East": "PUNE_JW_31"}, 
    "PUNE_JW_35": {"East": "PUNE_JW_32"}, 

    # Kharadi
    "PUNE_JW_34": {"East": "PUNE_JW_33"}, 
    "PUNE_JW_24": {"East": "PUNE_JW_34"}  
}

pending_commands = {}       # {upstream_id: [cmd_dict, ...]}  — Phase 7 multi-lane
latest_score_cache = {}     # {junction_id: enriched_heartbeat}  — fast dashboard source


# --- MongoDB Connection (For Mobile App Sync) ---
# --- APP DB Connection (For Mobile App Sync) ---
# We connect on-demand to avoid holding a connection if not needed constantly
# or use a global if frequency is high. Here, on-demand is fine for rewards.

def sync_to_app_db(phone, points, plate):
    """
    Syncs the reward credit to the Mobile App's PostgreSQL DB (safedrive_apps).
    Keyed by phone_number for identity consistency.
    """
    try:
        # Connect to App DB
        import psycopg2
        conn = psycopg2.connect(**SystemConfig.APP_DB_PARAMS)
        cur = conn.cursor()
        
        # 1. Update User Points and Wallet
        # 100 Points = 0.50 INR (From SystemConfig)
        wallet_inc = points * (SystemConfig.CREDIT_VALUE_INR / SystemConfig.POINTS_TO_CREDIT_RATIO)
        
        cur.execute("""
            UPDATE users 
            SET total_earned_points = total_earned_points + %s,
                wallet_balance = wallet_balance + %s
            WHERE phone_number = %s
            RETURNING user_id
        """, (points, wallet_inc, phone))
        
        row = cur.fetchone()
        
        if row:
            user_id = row[0]
             # 2. Log Transaction
            cur.execute("""
                INSERT INTO transactions (user_id, type, amount, description)
                VALUES (%s, 'EARNED', %s, %s)
            """, (user_id, points, f"Reward for Good Driving ({plate})"))
             
            conn.commit()
            print(f"  ✅ [APP_DB] Synced +{points} pts to {email}")
        else:
            print(f"  ⚠️ [APP_DB] User {email} not found in App DB.")
             
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  ❌ [APP_DB] Sync Failed: {e}")

# --- Pydantic Models ---
class LaneData(BaseModel):
    saturation_level: float
    current_green_time: int
    event: str = "NORMAL"
    score_details: Optional[dict] = None
    directional_counts: Optional[dict] = None  # {"Straight": 5, "Left": 2, "Right": 3}

class Heartbeat(BaseModel):
    junction_id: str
    timestamp: float
    lanes: Dict[str, LaneData]

class GhostInjection(BaseModel):
    target_junction: str
    saturation_value: float

# --- API ENDPOINTS ---

@app.get("/")
def home():
    conn = get_db_connection()
    status = "Connected" if conn else "Disconnected"
    if conn: conn.close()
    return {"status": "Online", "db": status, "nodes": len(TOPOLOGY_NODES)}

@app.get("/topology")
def get_topology():
    return {"nodes": TOPOLOGY_NODES, "connections": NETWORK_CONNECTIONS}

@app.get("/commands/{node_id}")
def get_commands(node_id: str):
    """
    Phase 7: Edge node polls for pending commands.
    Returns a list of command dicts (multi-lane throttle support).
    Clears the queue after delivery (one-shot commands).
    """
    cmds = pending_commands.pop(node_id, [])
    # Normalise: always return a list even if legacy single-dict was stored
    if isinstance(cmds, dict):
        cmds = [cmds]
    return cmds


@app.get("/live_status")
def get_live_status():
    conn = get_db_connection()
    if not conn: return {}
    cur = conn.cursor(cursor_factory=RealDictCursor)
    state = {}
    try:
        cur.execute("SELECT junction_id, raw_data FROM junction_status")
        rows = cur.fetchall()
        for row in rows:
            state[row['junction_id']] = row['raw_data']
    finally:
        cur.close()
        conn.close()
    return state

@app.post("/heartbeat")
@app.post("/api/heartbeat")
async def receive_heartbeat(data: Heartbeat, background_tasks: BackgroundTasks):
    """
    RECEIVE Heartbeat from Edge Node (Turbo: 300ms pulses).
    1. Compute per-phase saturation & update in-memory cache immediately.
    2. Offload heavy DB persistence + congestion logic to background task.
    """
    # 1. Compute per-phase saturation & junction average
    phase_saturations = {}
    for lane_name, lane_stats in data.lanes.items():
        phase_saturations[lane_name] = round(lane_stats.saturation_level, 1)

    junction_avg_sat = (
        round(sum(phase_saturations.values()) / len(phase_saturations), 1)
        if phase_saturations else 0.0
    )

    # 2. Update in-memory cache (ultra-fast dashboard source)
    cache_entry = data.dict()
    cache_entry["phase_saturations"] = phase_saturations
    cache_entry["junction_saturation"] = junction_avg_sat
    latest_score_cache[data.junction_id] = cache_entry

    # 3. Offload DB + congestion logic to background
    background_tasks.add_task(persist_heartbeat_to_db, data, phase_saturations, junction_avg_sat)

    return {"status": "ACK", "server_says_throttled": False}


async def persist_heartbeat_to_db(data: Heartbeat, phase_saturations: dict, junction_avg_sat: float):
    """
    Background task: DB persistence + multi-phase congestion logic.
    Runs AFTER the fast ACK is already returned to the edge node.
    """
    conn = get_db_connection()
    if not conn:
        return
    cur = conn.cursor()
    try:
        # 1. UPSERT junction status with per-phase saturation
        enriched = data.dict()
        enriched["phase_saturations"] = phase_saturations
        enriched["junction_saturation"] = junction_avg_sat
        json_data = json.dumps(enriched)

        cur.execute("""
            INSERT INTO junction_status (junction_id, saturation_level, raw_data)
            VALUES (%s, %s, %s)
            ON CONFLICT (junction_id)
            DO UPDATE SET saturation_level = EXCLUDED.saturation_level,
                          raw_data = EXCLUDED.raw_data,
                          last_updated = CURRENT_TIMESTAMP;
        """, (data.junction_id, junction_avg_sat, json_data))
        conn.commit()

        # 2. CONGESTION CHECK (per-phase, multi-throttle)
        any_congested = any(s > 80 for s in phase_saturations.values())
        if any_congested:
            if data.junction_id in EXTERNAL_LINKS:
                print(f"[FEDERATED] Alert -> {EXTERNAL_LINKS[data.junction_id]}")
            else:
                _trigger_advanced_throttling(data.junction_id, phase_saturations, cur)
                conn.commit()

        # 3. RECOVERY CHECK
        cur.execute("SELECT source_id FROM active_interventions WHERE target_id = %s", (data.junction_id,))
        active_sources = cur.fetchall()
        if active_sources and junction_avg_sat < 50:
            for row in active_sources:
                print(f"[RECOVERY] {data.junction_id} clear -> releasing {row[0]}")
                _trigger_recovery(row[0], cur)
            conn.commit()

        # 4. PERSIST DIRECTIONAL COUNTS (if provided by edge node)
        for lane_name, lane_stats in data.lanes.items():
            if lane_stats.directional_counts:
                try:
                    cur.execute("""
                        INSERT INTO directional_counts
                            (junction_id, phase, counts_json, recorded_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (
                        data.junction_id,
                        lane_name,
                        json.dumps(lane_stats.directional_counts)
                    ))
                except Exception:
                    pass  # Table may not exist yet - non-fatal
        conn.commit()

    except Exception as e:
        print(f"[HB_BG_ERROR] {e}")
    finally:
        cur.close()
        conn.close()

@app.post("/inject_congestion")
def inject_ghost_congestion(data: GhostInjection):
    conn = get_db_connection()
    if not conn: return {"status": "DB_ERROR"}
    cur = conn.cursor()

    try:
        event_type = "GHOST_JAM" if data.saturation_value > 80 else "NORMAL"
        fake_data = {
            "junction_id": data.target_junction,
            "timestamp": 0,
            "lanes": {"North": {"saturation_level": data.saturation_value, "current_green_time": 0, "event": event_type}}
        }

        sql = """
        INSERT INTO junction_status (junction_id, saturation_level, raw_data)
        VALUES (%s, %s, %s)
        ON CONFLICT (junction_id) 
        DO UPDATE SET saturation_level = EXCLUDED.saturation_level, raw_data = EXCLUDED.raw_data;
        """
        cur.execute(sql, (data.target_junction, data.saturation_value, json.dumps(fake_data)))
        conn.commit()
        
        if data.saturation_value > 50:
            # Ghost Attack: build synthetic phase_saturations dict
            ghost_saturations = {
                "North": data.saturation_value,
                "South": round(data.saturation_value * 0.6, 1),
                "East":  round(data.saturation_value * 0.5, 1),
                "West":  round(data.saturation_value * 0.4, 1),
            }
            _trigger_advanced_throttling(data.target_junction, ghost_saturations, cur)
            conn.commit()
        elif data.saturation_value <= 50:
            cur.execute("SELECT source_id FROM active_interventions WHERE target_id = %s", (data.target_junction,))
            active_sources = cur.fetchall()
            if active_sources:
                for row in active_sources:
                    _trigger_recovery(row[0], cur)
                conn.commit()
    finally:
        cur.close()
        conn.close()
    return {"status": "GHOST_ACK"}

@app.get("/commands/{junction_id}")
def get_commands(junction_id: str):
    if junction_id in pending_commands:
        return pending_commands.pop(junction_id)
    return {"command_type": "NO_OP"}

# --- VIOLATION REPORTING (Phase 5: CMS + Enforcement) ---

class ViolationReport(BaseModel):
    junction_id: str
    plate_number: str
    violation_type: str     # "RLV", "SLV", "WLV", "BI", "IT", "SPEED"
    timestamp: float
    evidence_url: Optional[str] = None
    confidence: float = 0.0

class RewardCredit(BaseModel):
    plate_number: str
    points: int
    reason: str
    junction_id: str

@app.post("/violations/report")
async def report_violation(report: ViolationReport):
    """
    Receives violation reports from edge devices.
    Stores in database and optionally triggers reward wallet deduction.
    """
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor()
            # Ensure violations table exists (Handled at Startup now)
            # Schema Migration for existing tables (Hackathon safe)
            try:
                cur.execute("ALTER TABLE traffic_violations ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'PENDING'")
                cur.execute("ALTER TABLE traffic_violations ADD COLUMN IF NOT EXISTS attributes JSONB DEFAULT '{}'")
                cur.execute("ALTER TABLE traffic_violations ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'")
                cur.execute("ALTER TABLE traffic_violations ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP")
                conn.commit()
            except Exception:
                conn.rollback() # Ignore if already exists or error
            
            cur.execute("""
                INSERT INTO traffic_violations 
                (junction_id, plate_number, violation_type, evidence_url, confidence)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                report.junction_id,
                report.plate_number,
                report.violation_type,
                report.evidence_url,
                report.confidence
            ))
            
            violation_id = cur.fetchone()[0]
            conn.commit()
            
            junction_name = TOPOLOGY_NODES.get(report.junction_id, {}).get('name', report.junction_id)
            print(f"🚨 VIOLATION #{violation_id}: {report.violation_type} by {report.plate_number} at {junction_name}")
            
            return {
                "status": "recorded",
                "violation_id": violation_id,
                "junction": junction_name
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()
    
    return {"status": "db_unavailable"}

@app.get("/violations/{junction_id}")
async def get_violations(junction_id: str, limit: int = 50):
    """Get recent violations for a junction."""
    conn = get_db_connection()
    if conn:
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("""
                SELECT * FROM traffic_violations 
                WHERE junction_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (junction_id, limit))
            return {"violations": cur.fetchall()}
        except Exception as e:
            return {"violations": [], "error": str(e)}
        finally:
            conn.close()
    return {"violations": []}


def _trigger_advanced_throttling(congested_node_id, phase_saturations, cur):
    """
    Smart-Net 2.0 (Phase 7): Multi-phase throttling.
    Sends THROTTLE_ADJUST for every congested phase (>80%) up to 3 upstreams.
    Throttle severity is proportional to each phase's individual saturation.
    """
    connections = NETWORK_CONNECTIONS.get(congested_node_id, {})
    target_name = TOPOLOGY_NODES.get(congested_node_id, {}).get('name', congested_node_id)
    throttled_count = 0

    for phase_name, sat in phase_saturations.items():
        if sat <= 80 or throttled_count >= 3:
            continue  # Only throttle congested phases; max 3 at once

        upstream_id = connections.get(phase_name)
        if not upstream_id:
            continue  # No upstream feeder defined for this phase

        # Severity-based throttle value
        if sat > 95:
            throttle_value = 25
            print(f"[GRIDLOCK] Phase {phase_name} @ {sat}% -> HEAVY throttle ({throttle_value}s) to {upstream_id}")
        elif sat > 80:
            throttle_value = 15
            print(f"[CONGESTION] Phase {phase_name} @ {sat}% -> HIGH throttle ({throttle_value}s) to {upstream_id}")
        else:
            throttle_value = 10

        # Persist intervention
        cur.execute("""
            INSERT INTO active_interventions (source_id, target_id, reason)
            VALUES (%s, %s, %s)
            ON CONFLICT (source_id) DO NOTHING
        """, (upstream_id, congested_node_id, f"Phase {phase_name} Congestion ({sat}%)"))

        # Queue command as list to support multi-lane response
        if upstream_id not in pending_commands:
            pending_commands[upstream_id] = []
        # Avoid duplicate commands for same phase
        existing_phases = [cmd.get("target_lane") for cmd in pending_commands[upstream_id]]
        if phase_name not in existing_phases:
            pending_commands[upstream_id].append({
                "command_type": "THROTTLE_ADJUST",
                "target_lane": phase_name,
                "action": "REDUCE_GREEN",
                "value": throttle_value,
                "reason": f"Congestion at {target_name} phase {phase_name} ({sat}%)"
            })
        throttled_count += 1


def _trigger_recovery(source_id, cur):
    cur.execute("DELETE FROM active_interventions WHERE source_id = %s", (source_id,))
    pending_commands[source_id] = [
        {
            "command_type": "RESTORE_NORMAL",
            "target_lane": phase,
            "reason": "Traffic Cleared"
        }
        for phase in ["North", "South", "East", "West"]
    ]
    print(f"[RESTORE] {source_id}")

# =============================================================================
# 6. REWARD SYSTEM ENDPOINTS (Phase 16)
# =============================================================================

@app.post("/rewards/credit")
def credit_points(data: RewardCredit):
    """
    Internal Endpoint: Traffic Processor sends 'Good Behavior' events here.
    Supports Dual-Vehicle User Profiles (V1/V2).
    """
    conn = get_db_connection()
    if not conn: return {"status": "DB_ERROR"}
    cur = conn.cursor()
    
    try:
        plate = data.plate_number
        points = data.points
        
        # 1. Lookup in RTO Registry (Identity Source)
        # Normalize input plate for search
        p_val = plate.replace("-", "").replace(" ", "").upper()
        cur.execute("""
            SELECT email, owner_name, phone_number, driver_license_id, v1_plate, v1_type, v2_plate, v2_type
            FROM rto_registry 
            WHERE REPLACE(REPLACE(v1_plate, '-', ''), ' ', '') = %s 
               OR REPLACE(REPLACE(v2_plate, '-', ''), ' ', '') = %s
        """, (p_val, p_val))
        
        rto_user = cur.fetchone()
        
        if rto_user:
            # 2. Registered Vehicle Found!
            (email, owner, phone, license_id, v1_plate, v1_type, v2_plate, v2_type) = rto_user
            
            # Upsert into User Rewards (Keyed by Phone)
            cur.execute("""
                INSERT INTO user_rewards 
                (phone_number, email, owner_name, driver_license_id, v1_plate, v1_points, v2_plate, v2_points)
                VALUES (%s, %s, %s, %s, %s, 0, %s, 0)
                ON CONFLICT (phone_number) DO UPDATE SET 
                email = EXCLUDED.email,
                owner_name = EXCLUDED.owner_name,
                driver_license_id = EXCLUDED.driver_license_id,
                v1_plate = EXCLUDED.v1_plate, 
                v2_plate = EXCLUDED.v2_plate;
            """, (phone, email, owner, license_id, v1_plate, v2_plate))
            
            # Determine which slot to credit (Normalize for safe comparison)
            p_norm = plate.replace("-", "").replace(" ", "").upper()
            v1_norm = (v1_plate or "").replace("-", "").replace(" ", "").upper()
            
            if p_norm == v1_norm:
                cur.execute("UPDATE user_rewards SET v1_points = v1_points + %s, last_updated = NOW(), updated_at = NOW() WHERE phone_number = %s", (points, phone))
            else:
                cur.execute("UPDATE user_rewards SET v2_points = v2_points + %s, last_updated = NOW(), updated_at = NOW() WHERE phone_number = %s", (points, phone))
                
            conn.commit()
            try:
                sync_to_app_db(phone, points, plate)
            except Exception as e:
                print(f"  ⚠️ [SYNC] Failed to sync with Mobile App: {e}")
            
            print(f"  🏆 [REWARD] +{points} pts to {phone} ({plate})")
            return {"status": "CREDITED", "user": phone}
            
        else:
            # 3. Ghost Data: Store points for unregistered plate
            # Use ghost_PHONE logic for consistency if we want, or stay with plate.
            # User said "unique key should be phone number", for ghost data we still only have plate.
            ghost_id = f"ghost_{plate}" 
            print(f"  👻 [GHOST] {plate} not in RTO. Creating/Updating Ghost Profile...")
            
            cur.execute("""
                INSERT INTO user_rewards 
                (phone_number, owner_name, v1_plate, v1_points, last_updated, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (phone_number) 
                DO UPDATE SET v1_points = user_rewards.v1_points + %s, last_updated = NOW(), updated_at = NOW()
            """, (ghost_id, "Ghost Owner", plate, points, points))
            
            conn.commit()
            return {"status": "GHOST_RECORDED", "phone_number": ghost_id}
        
    except Exception as e:
        print(f"❌ [REWARD] Credit Failed: {e}")
        conn.rollback()
        return {"status": "ERROR", "detail": str(e)}
    finally:
        cur.close()
        conn.close()

@app.get("/rewards/profile/{phone}")
def get_user_profile(phone: str):
    """
    App Endpoint: Fetch user profile and ensure rewards are synced.
    Keyed by phone_number.
    """
    conn = get_db_connection()
    if not conn: return {"status": "DB_ERROR"}
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT * FROM user_rewards WHERE phone_number = %s", (phone,))
        user_data = cur.fetchone()
        
        if user_data:
            return {
                "status": "SUCCESS",
                "user": {
                    "phone": phone,
                    "name": user_data['owner_name'],
                    "email": user_data['email'],
                    "license": user_data['driver_license_id']
                },
                "vehicles": [
                    {"plate": user_data['v1_plate'], "points": user_data['v1_points'], "slot": "V1"},
                    {"plate": user_data['v2_plate'], "points": user_data['v2_points'], "slot": "V2"}
                ]
            }
        
        # Fallback: Check RTO directly
        cur.execute("SELECT * FROM rto_registry WHERE phone_number = %s", (phone,))
        rto_data = cur.fetchone()
        
        if rto_data:
             return {
                "status": "SUCCESS_NO_POINTS",
                "user": {
                    "phone": phone,
                    "name": rto_data['owner_name'],
                    "email": rto_data['email'],
                    "license": rto_data['driver_license_id']
                },
                "vehicles": [
                    {"plate": rto_data['v1_plate'], "points": 0, "slot": "V1"},
                    {"plate": rto_data['v2_plate'], "points": 0, "slot": "V2"}
                ]
            }
            
        return {"status": "NOT_FOUND"}
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)