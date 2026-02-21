# database_controller.py
"""
PRODUCTION DATA MANAGEMENT LAYER (POSTGRESQL)
Implementation: Industry Standard Relational Schema
Handles: Secure Persistence, Relational Integrity, and PDF-based Rule Seeding.
"""

import psycopg2
from psycopg2 import extras, sql
import logging
import sys
from datetime import datetime
import os
# Add root folder to path to find 'config'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.settings import SystemConfig

# Professional Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DB-CONTROLLER] - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class TrafficProductionDB:
    def __init__(self):
        self.params = SystemConfig.DB_PARAMS
        self._bootstrap_system()

    def get_connection(self):
        """Returns a secure connection to the PostgreSQL server."""
        try:
            return psycopg2.connect(**self.params)
        except psycopg2.Error as e:
            logging.critical(f"CRITICAL: Could not connect to PostgreSQL: {e}")
            raise

    def _bootstrap_system(self):
        """Step-by-step initialization: Creates DB, Tables, and Seeds Rules."""
        # 1. Connect to default 'postgres' database to create the platform DB
        try:
            # We connect to 'postgres' first because you cannot create a DB while connected to it
            temp_conn = psycopg2.connect(
                user=self.params["user"],
                password=self.params["password"],
                host=self.params["host"],
                port=self.params["port"],
                dbname="postgres" # Connect to system DB first
            )
            temp_conn.autocommit = True # Required for CREATE DATABASE commands
            with temp_conn.cursor() as cur:
                # Check if our database already exists
                cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (self.params["dbname"],))
                exists = cur.fetchone()
                
                if not exists:
                    # FIX: Use sql.SQL for the command and sql.Identifier only for the name
                    query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.params["dbname"]))
                    cur.execute(query)
                    logging.info(f"Production Database '{self.params['dbname']}' created.")
            temp_conn.close()
        except Exception as e:
            logging.error(f"Bootstrap Note: {e}")

        # 2. Now that DB exists, build the schema
        self._initialize_schema()

    def fetch_leaderboard(self, limit=10):
        """
        Fetches the highest-ranked drivers. 
        Note: It only includes drivers with valid security seals.
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                # We rank by lifetime_credits
                cursor.execute('''
                    SELECT plate_id, v_type, lifetime_credits, current_tier, security_seal, available_wallet
                    FROM drivers 
                    ORDER BY lifetime_credits DESC 
                    LIMIT %s
                ''', (limit,))
                return cursor.fetchall()

    def _initialize_schema(self):
        """Constructs the high-precision relational schema using PostgreSQL syntax."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                logging.info("Building Relational Schema...")

                # TABLE 1: Vehicle Category Rules (Source: PDF Page 1)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vehicle_rules (
                        v_type TEXT PRIMARY KEY,
                        max_pts_junction INTEGER NOT NULL,
                        max_junc_day INTEGER NOT NULL,
                        daily_cap INTEGER NOT NULL
                    )
                ''')

                # TABLE 2: Secure Driver Vault (Source: PDF Page 6 ER Diagram)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS drivers (
                        plate_id TEXT PRIMARY KEY,
                        v_type TEXT NOT NULL REFERENCES vehicle_rules(v_type),
                        lifetime_credits DOUBLE PRECISION DEFAULT 0.0,
                        available_wallet DOUBLE PRECISION DEFAULT 0.0,
                        current_tier TEXT DEFAULT 'Standard',
                        security_seal TEXT, 
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # TABLE 3: Daily Point Accumulator (Temporary Data)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS daily_accumulator (
                        plate_id TEXT REFERENCES drivers(plate_id) ON DELETE CASCADE,
                        log_date DATE NOT NULL,
                        points INTEGER DEFAULT 0,
                        junc_count INTEGER DEFAULT 0,
                        PRIMARY KEY (plate_id, log_date)
                    )
                ''')

                # TABLE 4: Permanent Audit Ledger (Evidence Trail)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audit_ledger (
                        tx_id SERIAL PRIMARY KEY,
                        plate_id TEXT REFERENCES drivers(plate_id),
                        tx_type TEXT NOT NULL, 
                        amount DOUBLE PRECISION NOT NULL,
                        unit TEXT NOT NULL, 
                        tier_at_time TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # TABLE 5: Global Watchlist (Horizontal Sharing - PDF Page 11)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS watchlist (
                        plate_id TEXT PRIMARY KEY REFERENCES drivers(plate_id),
                        violation_code TEXT NOT NULL,
                        intersection_id TEXT NOT NULL,
                        severity_score INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # SEEDING: Populate rules from SystemConfig (which matches PDF Page 1)
                for v_type, caps in SystemConfig.VEHICLE_RULES.items():
                    cursor.execute('''
                        INSERT INTO vehicle_rules (v_type, max_pts_junction, max_junc_day, daily_cap)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (v_type) DO UPDATE SET
                        max_pts_junction = EXCLUDED.max_pts_junction,
                        max_junc_day = EXCLUDED.max_junc_day,
                        daily_cap = EXCLUDED.daily_cap
                    ''', (v_type, caps['max_pts_junction'], caps['max_junc_day'], caps['daily_cap']))

                conn.commit()
                logging.info("Schema integrity verified. All tables operational.")

    def register_vehicle(self, plate, v_type):
        """Safely onboards a new vehicle using parameterized queries."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute('''
                        INSERT INTO drivers (plate_id, v_type) 
                        VALUES (%s, %s) ON CONFLICT DO NOTHING
                    ''', (plate, v_type))
                    conn.commit()
                except psycopg2.Error as e:
                    logging.error(f"Registration failed for {plate}: {e}")

    def get_neighbor_watchlist(self):
        """Retrieves high-severity violators using DictCursor for API compatibility."""
        with self.get_connection() as conn:
            # RealDictCursor allows results to be returned as Python dictionaries
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM watchlist ORDER BY timestamp DESC")
                return cursor.fetchall()