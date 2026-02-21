# reward_api.py
"""
OFFICIAL REWARD PLATFORM API GATEWAY (POSTGRESQL)
Implementation: High-Concurrency Service Layer
"""

import logging
from database_controller import TrafficProductionDB
from reward_engine import RewardEngine
from conversion_engine import ConversionEngine
from redemption_engine import RedemptionEngine
from psycopg2 import extras
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import SystemConfig

class RewardSystemAPI:
    def __init__(self):
        self.db = TrafficProductionDB()
        self.reward_engine = RewardEngine(self.db)
        self.conversion_engine = ConversionEngine(self.db)
        self.redemption_engine = RedemptionEngine(self.db)
        logging.info("Traffic Safety Reward Platform API - Online (Postgres Secure)")

    # --- FOR SIRAJ: SENSOR INTERFACE ---
    
    def record_traffic_event(self, plate_id, action_key, intersection_id="PUNE_BASE"):
        """Records a daytime point event or immediate violation."""
        return self.reward_engine.process_event(plate_id, action_key, intersection_id)

    def get_watchlist(self):
        """Returns the neighbor observation list for signal logic."""
        return self.db.get_neighbor_watchlist()

    # --- FOR SAQLAIN: USER APP INTERFACE ---

    def get_driver_profile(self, plate_id):
        """Returns the complete wallet and rank status for the mobile app."""
        conn = self.db.get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                # 1. Fetch permanent data (Wallet/Tier)
                cursor.execute('''
                    SELECT plate_id, v_type, lifetime_credits, available_wallet, current_tier 
                    FROM drivers WHERE plate_id = %s
                ''', (plate_id,))
                res = cursor.fetchone()
                
                if not res:
                    return {"status": "error", "message": "Driver not found"}

                # 2. Fetch today's points (Pending conversion)
                cursor.execute('''
                    SELECT points FROM daily_accumulator 
                    WHERE plate_id = %s AND log_date = CURRENT_DATE
                ''', (plate_id,))
                acc_res = cursor.fetchone()
                daily_points = acc_res['points'] if acc_res else 0

                return {
                    "plate": res['plate_id'],
                    "vehicle": res['v_type'],
                    "rank": res['current_tier'],
                    "wallet_credits": round(res['available_wallet'], 2),
                    "wallet_inr": round(res['available_wallet'] * SystemConfig.CREDIT_VALUE_INR, 2),
                    "lifetime_xp": round(res['lifetime_credits'], 2),
                    "points_earned_today": daily_points
                }
        finally:
            conn.close()

    def request_redemption(self, plate_id, reward_key):
        """Calls the redemption engine to spend credits."""
        return self.redemption_engine.buy_reward(plate_id, reward_key)

    # --- FOR THE SYSTEM: MIDNIGHT PROCESSING ---

    def run_midnight_batch(self, plate_id):
        """Triggers the Refinery logic (Points -> Credits)."""
        return self.conversion_engine.midnight_batch_process(plate_id)

    def register_user(self, plate, vehicle_type):
        """Onboards a new vehicle category."""
        self.db.register_vehicle(plate, vehicle_type)
        return {"status": "success", "message": f"Vehicle {plate} registered."}