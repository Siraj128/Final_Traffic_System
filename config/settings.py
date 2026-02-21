# config/settings.py
"""
GLOBAL PRODUCTION CONFIGURATION
Single Source of Truth for the entire Pune Traffic Safety Platform.
Combines: Reward System Rules & Intersection Perception Geometry.

Credentials loaded from .env file (Part 12: Database Migration Plan).
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

class SystemConfig:
    # ==========================================================
    # --- 1. GLOBAL DATABASE & SECURITY (Loaded from .env) ---
    # ==========================================================
    DB_PARAMS = {
        "dbname": os.getenv("DB_NAME", "traffic_reward_pro"),
        "user":   os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASS", "aynan@2023"),
        "host":   os.getenv("DB_HOST", "127.0.0.1"),
        "port":   os.getenv("DB_PORT", "5432")
    }
    
    # Secret key for HMAC Security Seals (from .env)
    SYSTEM_SECRET = os.getenv("SYSTEM_SECRET", "PUNE_CITY_AYNAN_SECURE_777_PRO")
    
    # Network Identity
    JUNCTION_ID = os.getenv("JUNCTION_ID", "PUNE_JW_01")
    
    # CMS / Central Brain URL (Python FastAPI on port 8000)
    CMS_SERVER_URL = os.getenv("CMS_SERVER_URL", "http://localhost:8000")

    # SafeDrive Rewards Backend (Node.js on port 5000)
    SAFEDRIVE_URL = os.getenv("SAFEDRIVE_URL", "http://localhost:5000")

    # CARLA Bridge Server (for simulation demo)
    CARLA_BRIDGE_URL = os.getenv("CARLA_BRIDGE_URL", "http://localhost:8100")

    # Mobile App Database (PostgreSQL)
    APP_DB_PARAMS = {
        "dbname": "safedrive_apps",
        "user":   "safedrive_user",
        "password": "safedrive",
        "host":   "127.0.0.1",
        "port":   "5432"
    }

    # ==========================================================
    # --- 2. REWARD SYSTEM CONFIGURATION (From PDF Pages 1-4, 9) ---
    # ==========================================================
    
    # Economic Logic
    POINTS_TO_CREDIT_RATIO = 100  # 100 Points = 1 Credit
    CREDIT_VALUE_INR = 0.5        # 1 Credit = 0.50 RS

    # Vehicle Caps (PDF Page 1)
    VEHICLE_RULES = {
        "Two-Wheeler":      {"max_pts_junction": 12, "max_junc_day": 8, "daily_cap": 96},
        "Private Car":       {"max_pts_junction": 15, "max_junc_day": 8, "daily_cap": 120},
        "Taxi":              {"max_pts_junction": 18, "max_junc_day": 6, "daily_cap": 180},
        "Auto-Rickshaw":     {"max_pts_junction": 15, "max_junc_day": 6, "daily_cap": 150},
        "Commercial":        {"max_pts_junction": 22, "max_junc_day": 6, "daily_cap": 132},
        "Public Transport":  {"max_pts_junction": 28, "max_junc_day": 6, "daily_cap": 168}
    }

    # Reward Matrix (PDF Pages 2 & 3)
    POINT_RULES = {
        # Priority 1: Safety
        "RED_STOP": 5, "NO_SIGNAL_JUMP": 5, "STOP_LINE_RESPECT": 4, "PEDESTRIAN_YIELD": 4,
        # Priority 2: Flow
        "SMOOTH_PASS": 3, "NO_SUDDEN_BRAKE": 3, "NO_SUDDEN_ACCEL": 3, 
        "LANE_DISCIPLINE": 2, "NO_BLOCK_INTERSECTION": 4,
        # Priority 3: Efficiency
        "SIGNAL_TIMING": 2, "CLEAR_ON_TIME": 2, "NO_HONKING": 1, "PEAK_HOUR_COMPLY": 3
    }

    # Penalty Matrix (PDF Page 9)
    PENALTY_RULES = {
        "RLV": -100,      # Red Light Violation
        "SLV": -40,       # Stop Line Violation
        "WLV": -30,       # Wrong Lane Violation
        "BI": -40,        # Blocking Intersection
        "IT": -50,        # Illegal Turn
        "SPEED": -60      # Speeding
    }

    # Tier Thresholds (PDF Page 3)
    TIER_THRESHOLDS = {
        "GOLD": 2000,
        "SILVER": 1000,
        "BRONZE": 500
    }
    
    # Bonus Matrix (PDF Page 4)
    TIER_BONUS_MATRIX = {
        "Gold": 20,
        "Silver": 10,
        "Bronze": 5,
        "Standard": 0
    }

    # Redemption Catalog (PDF Page 3)
    REWARD_CATALOG = {
        "FASTAG_100": {"cost_inr": 100, "label": "₹100 FASTag Credit"},
        "TOLL_PASS":  {"cost_inr": 50,  "label": "Free Single Toll Pass"},
        "PARKING_WAI": {"cost_inr": 20,  "label": "Municipal Parking Waiver"},
        "INS_DISC":    {"cost_inr": 500, "label": "5% Insurance Discount"}
    }

    # ==========================================================
    # --- 3. INTERSECTION FEATURE CONFIGURATION (From PDF Pages 6 & 11) ---
    # ==========================================================
    
    # Anomaly Thresholds
    STUCK_TIMER_LIMIT = 10.0 # Seconds before gridlock alert
    STATIONARY_SPEED_THRESHOLD = 0.5 # Speed considered "Stopped"

    # Movement Logic (Entry Zone + Exit Zone = Movement)
    MOVEMENT_TYPES = {
        ("NORTH", "SOUTH"): "STRAIGHT",
        ("NORTH", "WEST"):  "RIGHT_TURN",
        ("NORTH", "EAST"):  "LEFT_TURN",
        
        ("SOUTH", "NORTH"): "STRAIGHT",
        ("SOUTH", "EAST"):  "RIGHT_TURN",
        ("SOUTH", "WEST"):  "LEFT_TURN",
        
        ("EAST", "WEST"):   "STRAIGHT",
        ("EAST", "SOUTH"):  "LEFT_TURN",
        ("EAST", "NORTH"):  "RIGHT_TURN",
        
        ("WEST", "EAST"):   "STRAIGHT",
        ("WEST", "NORTH"):  "LEFT_TURN",
        ("WEST", "SOUTH"):  "RIGHT_TURN"
    }
    
    # Junction Topology (Digital Map)
    JUNCTION_GEOMETRY = {
        # The "Dead Zone" (Middle Box)
        "CENTER_BOX": {"x_min": 300, "x_max": 500, "y_min": 300, "y_max": 500},
        
        # Entry Zones (Where we start tracking for direction)
        "ENTRY_ZONES": {
            "NORTH": {"y_max": 150},
            "SOUTH": {"y_min": 650},
            "EAST":  {"x_min": 650},
            "WEST":  {"x_max": 150}
        }
    }