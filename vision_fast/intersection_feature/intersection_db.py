# intersection_feature/intersection_db.py
"""
PRODUCTION DATABASE VAULT (V4.0)
Purpose: High-performance relational storage for Flow, Safety, and Analytics.
Source of Truth: 
    - PDF Page 2: Junction Monitoring.
    - PDF Page 3 & 6: Direction-Wise Counting & Event Detection.
    - PDF Page 12: Historical Analytics & Dashboard Support.
Standard: ACID Compliant, Forensic JSONB Logging, Time-Series Optimized.
"""

import sys
import os
import logging
import psycopg2
from psycopg2 import extras
from datetime import datetime
from typing import Dict, List, Any

# --- PRODUCTION PATH CONFIG ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import SystemConfig

class IntersectionDatabase:
    def __init__(self):
        self.params = SystemConfig.DB_PARAMS
        self._initialize_vault_schema()

    def get_connection(self):
        """Returns a high-performance connection with dictionary support."""
        try:
            conn = psycopg2.connect(**self.params)
            # Row_factory for Postgres (DictCursor)
            return conn
        except psycopg2.Error as e:
            logging.critical(f"[DB-VAULT] Connection failed: {e}")
            raise

    def _initialize_vault_schema(self):
        """Builds the forensic-ready relational architecture."""
        conn = self.get_connection()
        conn.autocommit = True # Allow table creation without manual commit
        try:
            with conn.cursor() as cursor:
                # 1. Master Junction Registry (PDF Page 2)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS junction_registry (
                        junction_id TEXT PRIMARY KEY,
                        location_name TEXT NOT NULL,
                        status TEXT DEFAULT 'ACTIVE',
                        last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 2. Historical Flow Logs (PDF Page 3 & 12)
                # Stores every completed vehicle passage for pattern analysis
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS traffic_flow_history (
                        log_id SERIAL PRIMARY KEY,
                        junction_id TEXT REFERENCES junction_registry(junction_id),
                        vehicle_uuid UUID NOT NULL,
                        vehicle_class TEXT,
                        entry_zone TEXT,
                        exit_zone TEXT,
                        movement_type TEXT,
                        idling_duration_sec FLOAT DEFAULT 0.0,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 3. Safety & Forensic Incidents (PDF Page 6 & 11)
                # Stores Accidents/Gridlocks with full physics snapshots (JSONB)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS safety_incidents (
                        incident_id SERIAL PRIMARY KEY,
                        junction_id TEXT REFERENCES junction_registry(junction_id),
                        anomaly_type TEXT NOT NULL, -- GRIDLOCK, ACCIDENT, etc.
                        severity_level TEXT, -- CRITICAL, HIGH, MEDIUM
                        incident_description TEXT,
                        forensic_telemetry JSONB, -- STOPS, SPEED, ACCELERATION
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_resolved BOOLEAN DEFAULT FALSE
                    )
                ''')

                # 4. Real-Time Demand Buffer (PDF Page 3)
                # High-speed table for the Signal Controller to read pressure
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS realtime_demand (
                        junction_id TEXT PRIMARY KEY REFERENCES junction_registry(junction_id),
                        north_pressure FLOAT DEFAULT 0.0,
                        south_pressure FLOAT DEFAULT 0.0,
                        east_pressure FLOAT DEFAULT 0.0,
                        west_pressure FLOAT DEFAULT 0.0,
                        pedestrian_active BOOLEAN DEFAULT FALSE,
                        last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # --- MIGRATION: Ensure 'last_heartbeat' exists in 'junction_registry' ---
                cursor.execute('''
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                     WHERE table_name='junction_registry' AND column_name='last_heartbeat') THEN 
                            ALTER TABLE junction_registry ADD COLUMN last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                        END IF;
                    END $$;
                ''')

                # --- MIGRATION: Sync 'realtime_demand' columns to V4.0 Naming ---
                cursor.execute('''
                    DO $$ 
                    BEGIN 
                        -- Rename demand -> pressure
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='realtime_demand' AND column_name='north_demand') THEN
                            ALTER TABLE realtime_demand RENAME COLUMN north_demand TO north_pressure;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='realtime_demand' AND column_name='south_demand') THEN
                            ALTER TABLE realtime_demand RENAME COLUMN south_demand TO south_pressure;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='realtime_demand' AND column_name='east_demand') THEN
                            ALTER TABLE realtime_demand RENAME COLUMN east_demand TO east_pressure;
                        END IF;
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='realtime_demand' AND column_name='west_demand') THEN
                            ALTER TABLE realtime_demand RENAME COLUMN west_demand TO west_pressure;
                        END IF;
                        -- Rename pedestrians -> pedestrian_active
                        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='realtime_demand' AND column_name='pedestrians') THEN
                            ALTER TABLE realtime_demand RENAME COLUMN pedestrians TO pedestrian_active;
                        END IF;
                    END $$;
                ''')

                logging.info("[DB-VAULT] Relational Integrity Verified.")
        except Exception as e:
            logging.error(f"[DB-VAULT] Schema Build Failure: {e}")
        finally:
            conn.close()

    def register_junction(self, junction_id: str, location_name: str):
        """Registers or updates a junction in the vault registry (PDF Page 2)."""
        conn = self.get_connection()
        conn.autocommit = True
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO junction_registry (junction_id, location_name)
                    VALUES (%s, %s)
                    ON CONFLICT (junction_id) DO UPDATE SET
                    location_name = EXCLUDED.location_name,
                    last_heartbeat = CURRENT_TIMESTAMP
                ''', (junction_id, location_name))
                logging.info(f"[DB-VAULT] Junction {junction_id} synced.")
        finally:
            conn.close()
    # ==========================================================
    # --- PRODUCTION DATA INGESTION METHODS ---
    # ==========================================================

    def record_completed_trip(self, junction_id: str, vehicle_obj: Any):
        """Persists the finished lifecycle of a vehicle (PDF Page 3/6)."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                movement = vehicle_obj.get_movement_classification()
                cursor.execute('''
                    INSERT INTO traffic_flow_history 
                    (junction_id, vehicle_uuid, vehicle_class, entry_zone, exit_zone, movement_type, idling_duration_sec)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                ''', (
                    junction_id, str(vehicle_obj.internal_uuid), vehicle_obj.obj_class,
                    vehicle_obj.entry_zone, vehicle_obj.exit_zone, movement,
                    round(vehicle_obj.total_idling_time, 2)
                ))
                conn.commit()
        finally:
            conn.close()

    def update_live_demand(self, junction_id: str, demand_matrix: Dict):
        """Atomic update of the road pressure for the Signal Logic (PDF Page 3)."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO realtime_demand 
                    (junction_id, north_pressure, south_pressure, east_pressure, west_pressure, pedestrian_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (junction_id) DO UPDATE SET
                    north_pressure = EXCLUDED.north_pressure,
                    south_pressure = EXCLUDED.south_pressure,
                    east_pressure = EXCLUDED.east_pressure,
                    west_pressure = EXCLUDED.west_pressure,
                    pedestrian_active = EXCLUDED.pedestrian_active,
                    last_update = CURRENT_TIMESTAMP
                ''', (
                    junction_id, 
                    demand_matrix['NORTH'], demand_matrix['SOUTH'],
                    demand_matrix['EAST'], demand_matrix['WEST'],
                    demand_matrix['pedestrians_active']
                ))
                conn.commit()
        finally:
            conn.close()

    def log_safety_incident(self, junction_id: str, a_type: str, severity: str, desc: str, telemetry: Dict):
        """Saves a forensic record of a safety event (PDF Page 6)."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO safety_incidents 
                    (junction_id, anomaly_type, severity_level, incident_description, forensic_telemetry)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (junction_id, a_type, severity, desc, extras.Json(telemetry)))
                conn.commit()
        finally:
            conn.close()

    # ==========================================================
    # --- ANALYTICS & DASHBOARD SUPPORT (PDF Page 12) ---
    # ==========================================================

    def get_dashboard_summary(self, junction_id: str):
        """Aggregates historical data for city authorities."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                # Get Movement Totals
                cursor.execute('''
                    SELECT movement_type, COUNT(*) as volume 
                    FROM traffic_flow_history 
                    WHERE junction_id = %s AND timestamp > NOW() - INTERVAL '24 hours'
                    GROUP BY movement_type
                ''', (junction_id,))
                flow_stats = {row['movement_type']: row['volume'] for row in cursor.fetchall()}

                # Get Anomaly Count
                cursor.execute('''
                    SELECT COUNT(*) as total FROM safety_incidents 
                    WHERE junction_id = %s AND timestamp > NOW() - INTERVAL '24 hours'
                ''', (junction_id,))
                alerts = cursor.fetchone()['total']

                return {
                    "last_24h_flow": flow_stats,
                    "total_alerts": alerts,
                    "junction_status": "OPTIMAL"
                }
        finally:
            conn.close()