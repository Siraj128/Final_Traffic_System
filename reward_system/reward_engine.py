# reward_engine.py
"""
PRODUCTION REWARD & PENALTY DECISION ENGINE (POSTGRESQL)
Logic: Tier-based Multipliers, 3-Tier Capping, and Immediate Demotion.
Implementation: High-Concurrency Transaction Management.
"""

import logging
from datetime import date
import psycopg2
from psycopg2 import extras
from exceptions import RegistrationError, CapExceededError, DatabaseTransactionError
from cms_dispatcher import CMSDispatcher
from security_vault import SecurityVault
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import SystemConfig

class RewardEngine:
    def __init__(self, db):
        self.db = db
        self.dispatcher = CMSDispatcher()
        
        # Mapping Rules from Central Config (PDF Specs)
        self.REWARDS_MATRIX = SystemConfig.POINT_RULES
        self.PENALTY_MATRIX = SystemConfig.PENALTY_RULES
        self.VEHICLE_PROFILES = SystemConfig.VEHICLE_RULES

    def process_event(self, plate_id, action_key, intersection_id="PUNE_BASE_01"):
        """
        Primary entry point for traffic sensors. 
        Detects action type and routes to the appropriate production protocol.
        """
        try:
            if action_key in self.PENALTY_MATRIX:
                return self._execute_violation_protocol(plate_id, action_key, intersection_id)
            elif action_key in self.REWARDS_MATRIX:
                return self._execute_reward_protocol(plate_id, action_key)
            else:
                return {"status": "error", "message": f"Undefined Action Code: {action_key}"}

        except RegistrationError as e:
            return {"status": "blocked", "message": str(e)}
        except CapExceededError as e:
            return {"status": "capped", "message": str(e)}
        except Exception as e:
            logging.error(f"ENGINE_FAILURE: {e}")
            return {"status": "error", "message": "Transaction failed during engine processing."}

    def _execute_reward_protocol(self, plate, action):
        """Processes safe driving. Enforces Junction-Max, Daily-Max, and Junction-Count caps."""
        today = date.today()
        base_rule_points = self.REWARDS_MATRIX.get(action, 0)

        conn = self.db.get_connection()
        try:
            # Use RealDictCursor to access columns by name (e.g., res['v_type'])
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                
                # 1. FETCH CONTEXT: Join Driver, Rules, and Daily Stats in one atomic read
                cursor.execute('''
                    SELECT d.v_type, d.lifetime_credits, d.available_wallet, d.security_seal, d.current_tier,
                           a.points as daily_pts, a.junc_count
                    FROM drivers d
                    JOIN vehicle_rules r ON d.v_type = r.v_type
                    LEFT JOIN daily_accumulator a ON a.plate_id = d.plate_id AND a.log_date = %s
                    WHERE d.plate_id = %s
                ''', (today, plate))
                
                res = cursor.fetchone()
                if not res:
                    raise RegistrationError(f"Vehicle {plate} not found in relational vault.")

                # 2. SECURITY CHECK: Verify Digital Signature
                if res['security_seal'] and SecurityVault.is_seal_broken(plate, res['lifetime_credits'], res['available_wallet'], res['security_seal']):
                    return {"status": "security_lock", "message": "Account Integrity Compromised"}

                # 3. PDF CAP VALIDATION (Page 1)
                caps = self.VEHICLE_PROFILES.get(res['v_type'])
                curr_p = res['daily_pts'] or 0
                curr_j = res['junc_count'] or 0

                if curr_j >= caps['max_junc_day']:
                    raise CapExceededError(f"Daily limit of {caps['max_junc_day']} junctions reached.")
                if curr_p >= caps['daily_cap']:
                    raise CapExceededError(f"Daily point cap of {caps['daily_cap']} reached.")

                # 4. JUNCTION-LEVEL CAPPING
                # Math: Points added = the smaller of (Rule Points) or (Junction Max Limit)
                final_added = min(base_reward_points, caps['max_pts_junction'])

                # 5. ATOMIC UPDATE (UPSERT)
                cursor.execute('''
                    INSERT INTO daily_accumulator (plate_id, log_date, points, junc_count)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (plate_id, log_date) DO UPDATE SET
                    points = daily_accumulator.points + EXCLUDED.points,
                    junc_count = daily_accumulator.junc_count + 1
                ''', (plate, today, final_added, 1))
                
                # 6. LOG TO PERMANENT AUDIT LEDGER
                cursor.execute('''
                    INSERT INTO audit_ledger (plate_id, tx_type, amount, unit, tier_at_time)
                    VALUES (%s, 'REWARD_EARN', %s, 'POINTS', %s)
                ''', (plate, final_added, res['current_tier']))

                conn.commit()
                return {
                    "status": "success",
                    "added": final_added,
                    "total_today": curr_p + final_added,
                    "tier": res['current_tier']
                }
        except Exception as e:
            conn.rollback()
            raise DatabaseTransactionError(f"Reward commitment failed: {e}")
        finally:
            conn.close()

    def _execute_violation_protocol(self, plate, action, intersection):
        """Processes violations immediately. Triggers Demotion and Neighbor Sharing."""
        penalty_pts = self.PENALTY_MATRIX[action]
        penalty_credits = penalty_pts / SystemConfig.POINTS_TO_CREDIT_RATIO

        conn = self.db.get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                
                # 1. FETCH & VERIFY
                cursor.execute("SELECT lifetime_credits, available_wallet, security_seal FROM drivers WHERE plate_id=%s", (plate,))
                row = cursor.fetchone()
                
                if row['security_seal'] and SecurityVault.is_seal_broken(plate, row['lifetime_credits'], row['available_wallet'], row['security_seal']):
                    return {"status": "security_lock", "message": "Integrity Failure"}

                # 2. CALCULATE IMPACT
                new_life = round(row['lifetime_credits'] + penalty_credits, 4)
                new_wallet = round(row['available_wallet'] + penalty_credits, 4)
                
                # Tier Demotion Logic
                new_tier = self._calculate_current_tier(new_life)
                
                # New Security Seal
                new_seal = SecurityVault.create_seal(plate, new_life, new_wallet)

                # 3. UPDATE MASTER RECORDS
                cursor.execute('''
                    UPDATE drivers SET 
                    lifetime_credits = %s, available_wallet = %s, 
                    current_tier = %s, security_seal = %s,
                    last_active = CURRENT_TIMESTAMP
                    WHERE plate_id = %s
                ''', (new_life, new_wallet, new_tier, new_seal, plate))

                # 4. NEIGHBOR SHARING (PDF Page 11)
                cursor.execute('''
                    INSERT INTO watchlist (plate_id, violation_code, intersection_id, severity_score)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (plate_id) DO UPDATE SET
                    violation_code = EXCLUDED.violation_code,
                    timestamp = CURRENT_TIMESTAMP
                ''', (plate, action, intersection, abs(penalty_pts)))

                # 5. AUDIT LOGGING
                cursor.execute('''
                    INSERT INTO audit_ledger (plate_id, tx_type, amount, unit, tier_at_time)
                    VALUES (%s, 'PENALTY', %s, 'CREDITS', %s)
                ''', (plate, penalty_credits, new_tier))

                # 6. CMS JSON GENERATION
                cms_json = self.dispatcher.generate_violation_packet(plate, action, intersection)

                conn.commit()
                return {
                    "status": "violation_processed",
                    "penalty_credits": penalty_credits,
                    "new_tier": new_tier,
                    "cms_packet": cms_json
                }
        except Exception as e:
            conn.rollback()
            raise DatabaseTransactionError(f"Violation enforcement failed: {e}")
        finally:
            conn.close()

    def _calculate_current_tier(self, life_credits):
        """Thresholds from PDF Page 3."""
        t = SystemConfig.TIER_THRESHOLDS
        if life_credits >= t["GOLD"]: return "Gold"
        if life_credits >= t["SILVER"]: return "Silver"
        if life_credits >= t["BRONZE"]: return "Bronze"
        return "Standard"