# conversion_engine.py
"""
PRODUCTION CREDIT CONVERSION ENGINE (POSTGRESQL)
Purpose: Converts daily temporary points into permanent wallet credits and rank.
Logic: Implements the 100:1 ratio and Tier-based Bonus Points from PDF Page 4.
Implementation: Secure Batch Processing.
"""

import logging
import psycopg2
from psycopg2 import extras
from security_vault import SecurityVault
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import SystemConfig

class ConversionEngine:
    def __init__(self, db):
        self.db = db
        # PDF Page 4: Bonus points awarded per 1 Credit earned
        self.TIER_BONUS_MATRIX = SystemConfig.TIER_BONUS_MATRIX
        # PDF Page 3: Conversion Ratio
        self.RATIO = SystemConfig.POINTS_TO_CREDIT_RATIO

    def midnight_batch_process(self, plate_id):
        """
        Executes the conversion refinery for a specific vehicle.
        In production, this is called by a scheduler at 00:00.
        """
        conn = self.db.get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                # 1. FETCH CURRENT DAILY POINTS & ACCOUNT STATE
                cursor.execute('''
                    SELECT a.points as daily_pts, d.current_tier, d.lifetime_credits, 
                           d.available_wallet, d.security_seal
                    FROM daily_accumulator a
                    JOIN drivers d ON d.plate_id = a.plate_id
                    WHERE a.plate_id = %s
                    FOR UPDATE OF a, d
                ''', (plate_id,))                
                state = cursor.fetchone()
                
                if not state or state['daily_pts'] <= 0:
                    return {"status": "skipped", "message": "No activity recorded for conversion."}

                # 2. SECURITY VERIFICATION: Ensure wallet wasn't hacked today
                if state['security_seal'] and SecurityVault.is_seal_broken(
                    plate_id, state['lifetime_credits'], state['available_wallet'], state['security_seal']
                ):
                    logging.critical(f"CONVERSION BLOCKED: Security Seal for {plate_id} is broken!")
                    return {"status": "security_lock", "message": "Account Integrity Failure"}

                # 3. PDF MATH: CONVERSION & TIER BONUS (Page 4)
                # Formula: (Base Points + (Base Credits * Tier Bonus)) / 100
                daily_pts = state['daily_pts']
                current_tier = state['current_tier']
                
                base_credits_earned = daily_pts / self.RATIO
                bonus_points = base_credits_earned * self.TIER_BONUS_MATRIX.get(current_tier, 0)
                
                total_new_credits = (daily_pts + bonus_points) / self.RATIO
                
                # 4. UPDATE PERMANENT WEALTH
                new_lifetime = round(state['lifetime_credits'] + total_new_credits, 4)
                new_wallet = round(state['available_wallet'] + total_new_credits, 4)
                
                # Check for Rank Promotion (Status Upgrade)
                new_tier = self._check_promotion_status(new_lifetime)
                
                # 5. GENERATE NEW SECURITY SEAL FOR UPDATED BALANCE
                new_seal = SecurityVault.create_seal(plate_id, new_life=new_lifetime, new_wallet=new_wallet)

                # 6. ATOMIC SAVE & RESET
                cursor.execute('''
                    UPDATE drivers SET 
                    lifetime_credits = %s, available_wallet = %s, 
                    current_tier = %s, security_seal = %s,
                    last_active = CURRENT_TIMESTAMP
                    WHERE plate_id = %s
                ''', (new_lifetime, new_wallet, new_tier, new_seal, plate_id))

                # Clear the accumulator for the next day
                cursor.execute("UPDATE daily_accumulator SET points = 0 WHERE plate_id = %s", (plate_id,))

                # Log to Permanent Audit Ledger
                cursor.execute('''
                    INSERT INTO audit_ledger (plate_id, tx_type, amount, unit, tier_at_time)
                    VALUES (%s, 'DAILY_CONVERSION', %s, 'CREDITS', %s)
                ''', (plate_id, total_new_credits, new_tier))

                conn.commit()
                logging.info(f"CONVERSION SUCCESS: {plate_id} deposited {total_new_credits} credits.")
                
                return {
                    "status": "success",
                    "deposited": round(total_new_credits, 2),
                    "tier": new_tier,
                    "new_balance": round(new_wallet, 2)
                }

        except Exception as e:
            conn.rollback()
            logging.error(f"CONVERSION_CRASH: {e}")
            return {"status": "error", "message": "Conversion process failed."}
        finally:
            conn.close()

    def _check_promotion_status(self, lifetime_xp):
        """Applies PDF Page 3 Thresholds."""
        t = SystemConfig.TIER_THRESHOLDS
        if lifetime_xp >= t["GOLD"]: return "Gold"
        if lifetime_xp >= t["SILVER"]: return "Silver"
        if lifetime_xp >= t["BRONZE"]: return "Bronze"
        return "Standard"