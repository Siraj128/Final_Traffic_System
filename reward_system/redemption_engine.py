# redemption_engine.py
"""
PRODUCTION REDEMPTION & WALLET ENGINE (POSTGRESQL)
Purpose: Handles the 'Spending' of credits for real-world benefits.
Logic: Deducts from spendable wallet but PRESERVES lifetime rank.
Source of Truth: PDF Page 3 (Reward Catalog).
"""

import logging
import psycopg2
from psycopg2 import extras
from security_vault import SecurityVault
from exceptions import RegistrationError, DatabaseTransactionError
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import SystemConfig

class RedemptionEngine:
    def __init__(self, db):
        self.db = db
        # Loading catalog from central config
        self.CATALOG = SystemConfig.REWARD_CATALOG
        self.CREDIT_VALUE = SystemConfig.CREDIT_VALUE_INR

    def buy_reward(self, plate_id, reward_key):
        """
        Processes a digital purchase. 
        Enforces security seals and prevents double-spending via row-locking.
        """
        if reward_key not in self.CATALOG:
            return {"status": "error", "message": f"Item '{reward_key}' not found in catalog."}

        item = self.CATALOG[reward_key]
        # Calculate cost: (Cost in INR / 0.50) = Credits Needed
        credits_needed = round(item["cost_inr"] / self.CREDIT_VALUE, 2)

        conn = self.db.get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                
                # 1. FETCH & LOCK: 'FOR UPDATE' prevents other processes from touching this row
                cursor.execute('''
                    SELECT lifetime_credits, available_wallet, current_tier, security_seal 
                    FROM drivers 
                    WHERE plate_id = %s 
                    FOR UPDATE
                ''', (plate_id,))
                
                state = cursor.fetchone()
                if not state:
                    raise RegistrationError(f"Vehicle {plate_id} not found.")

                # 2. SECURITY VERIFICATION: Check seal before deducting funds
                if state['security_seal'] and SecurityVault.is_seal_broken(
                    plate_id, state['lifetime_credits'], state['available_wallet'], state['security_seal']
                ):
                    logging.critical(f"FRAUD ATTEMPT: Account {plate_id} integrity failure during redemption!")
                    return {"status": "security_lock", "message": "Transaction Blocked: Data Tampered."}

                # 3. BALANCE CHECK
                if state['available_wallet'] < credits_needed:
                    return {
                        "status": "denied",
                        "message": f"Insufficient Credits. Required: {credits_needed}, Available: {state['available_wallet']}"
                    }

                # 4. EXECUTION MATH
                # Wallet goes down, but Lifetime Status stays the same!
                new_wallet = round(state['available_wallet'] - credits_needed, 4)
                # Re-calculate the Security Seal for the new balance
                new_seal = SecurityVault.create_seal(plate_id, state['lifetime_credits'], new_wallet)

                # 5. ATOMIC SAVE
                cursor.execute('''
                    UPDATE drivers SET 
                    available_wallet = %s, 
                    security_seal = %s,
                    last_active = CURRENT_TIMESTAMP
                    WHERE plate_id = %s
                ''', (new_wallet, new_seal, plate_id))

                # Log to Permanent Audit Ledger
                cursor.execute('''
                    INSERT INTO audit_ledger (plate_id, tx_type, amount, unit, tier_at_time)
                    VALUES (%s, 'PURCHASE', %s, 'CREDITS', %s)
                ''', (plate_id, -credits_needed, state['current_tier']))

                conn.commit()
                logging.info(f"PURCHASE SUCCESS: {plate_id} bought {item['label']}.")

                return {
                    "status": "success",
                    "item": item["label"],
                    "deducted": credits_needed,
                    "new_balance": new_wallet,
                    "tier_preserved": state['current_tier']
                }

        except Exception as e:
            conn.rollback()
            logging.error(f"REDEMPTION_FAILURE: {e}")
            return {"status": "error", "message": "Relational transaction failed."}
        finally:
            conn.close()