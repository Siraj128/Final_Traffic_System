# intersection_feature/logic_processors/anomaly_processor.py
"""
PRODUCTION ANOMALY & FORENSIC SAFETY ENGINE (V4.0)
Purpose: Predictive safety monitoring, forensic event logging, and emergency alerting.
Source of Truth: 
    - PDF Page 6: Abnormal traffic conditions (Accidents, Gridlocks, Stoppages).
    - PDF Page 11: Event alert generation and monitoring layer.
Standard: Physics-validated forensic logging with JSONB telemetry snapshots.
"""

import sys
import os
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

# --- PRODUCTION ENVIRONMENT SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from models import TrackedObject
from intersection_db import IntersectionDatabase
from config.settings import SystemConfig

class AnomalyProcessor:
    def __init__(self, junction_id: str):
        self.junction_id = junction_id
        self.db = IntersectionDatabase()
        
        # INCIDENT DEBOUNCER: Ensures we don't flood the database with the same event
        # Format: { "entity_id_anomaly_type": last_logged_timestamp }
        self.incident_ledger = {}
        self.ALERT_COOLDOWN = 45 # 45 seconds between identical alerts

    def execute_safety_audit(self, active_tracks: Dict[str, TrackedObject]):
        """
        Performs a deep-scan safety audit on every frame.
        Analyzes physics, positioning, and cross-entity conflicts.
        """
        # 1. SCAN FOR GRIDLOCKS & BOX BLOCKAGES (PDF Page 1 & 6)
        self._audit_center_congestion(active_tracks)

        # 2. SCAN FOR ACCIDENTS & SUDDEN STOPPAGES (PDF Page 6)
        self._audit_kinetic_anomalies(active_tracks)

        # 3. SCAN FOR PEDESTRIAN CONFLICTS (PDF Page 6)
        self._audit_pedestrian_safety(active_tracks)

        # 4. SCAN FOR IMPROPER LANE USAGE (PDF Page 6)
        self._audit_lane_discipline(active_tracks)

    def _audit_center_congestion(self, tracks: Dict[str, TrackedObject]):
        """Identifies vehicles blocking the 'Dead Zone' for >10s (PDF Page 6)."""
        for vid, obj in tracks.items():
            if obj.is_stalled: # This boolean is set by the 10s timer in models.py
                self._dispatch_forensic_alert(
                    vid, obj, 
                    a_type="GRIDLOCK_DETECTED", 
                    severity="CRITICAL",
                    desc=f"Vehicle blocking intersection center for {obj.get_stall_duration()}s"
                )

    def _audit_kinetic_anomalies(self, tracks: Dict[str, TrackedObject]):
        """Detects sudden decelerations or hazards in transit roads (PDF Page 6)."""
        for vid, obj in tracks.items():
            # A. ACCIDENT DETECTION: Extreme De-acceleration (Sudden Stoppage)
            if obj.is_collision_risk():
                self._dispatch_forensic_alert(
                    vid, obj,
                    a_type="POTENTIAL_ACCIDENT",
                    severity="CRITICAL",
                    desc=f"Sudden stoppage detected. Deceleration: {round(obj.acceleration, 2)} m/s^2"
                )

            # B. ROAD HAZARD: Vehicle stopped in a moving transit lane
            if obj.current_zone == "TRANSIT" and obj.total_idling_time > 5.0:
                self._dispatch_forensic_alert(
                    vid, obj,
                    a_type="STATIONARY_HAZARD",
                    severity="HIGH",
                    desc="Vehicle stationary in high-speed transit lane."
                )

    def _audit_pedestrian_safety(self, tracks: Dict[str, TrackedObject]):
        """Detects Vehicle-to-Pedestrian conflict risks (PDF Page 6)."""
        pedestrians = [o for o in tracks.values() if o.obj_class == "Pedestrian"]
        vehicles_in_center = [o for o in tracks.values() if o.obj_class != "Pedestrian" and o.current_zone == "CENTER_BOX"]

        if pedestrians and vehicles_in_center:
            # Detect high-speed entry into a center containing pedestrians
            for v in vehicles_in_center:
                if v.speed_mps > 15.0: # Approx 50km/h
                    self._dispatch_forensic_alert(
                        v.camera_id, v,
                        a_type="PEDESTRIAN_CONFLICT_RISK",
                        severity="CRITICAL",
                        desc="High-speed vehicle entry while pedestrians are in center box."
                    )

    def _audit_lane_discipline(self, tracks: Dict[str, TrackedObject]):
        """Detects illegal maneuvers or wrong-way driving (PDF Page 6)."""
        for vid, obj in tracks.items():
            # Logic: If a vehicle exits into the same zone it entered (Illegal U-Turn)
            if obj.exit_zone and obj.exit_zone == obj.entry_zone:
                self._dispatch_forensic_alert(
                    vid, obj,
                    a_type="IMPROPER_LANE_USAGE",
                    severity="MEDIUM",
                    desc=f"Illegal turnaround detected from zone {obj.entry_zone}"
                )

    def _dispatch_forensic_alert(self, vid: str, obj: TrackedObject, a_type: str, severity: str, desc: str):
        """
        Collects physics data and saves an immutable forensic record to PostgreSQL.
        """
        alert_id = f"{vid}_{a_type}"
        now = time.time()

        # DEBOUNCING: Don't spam the DB if the accident/stall is still in progress
        if alert_id in self.incident_ledger:
            if now - self.incident_ledger[alert_id] < self.ALERT_COOLDOWN:
                return

        # 1. BUILD FORENSIC TELEMETRY (For Police Audit)
        telemetry = {
            "physics": {
                "velocity_mps": round(obj.speed_mps, 2),
                "accel_mss": round(obj.acceleration, 2),
                "bearing_deg": round(obj.bearing, 1)
            },
            "spatial": {
                "current_pos": obj.current_pos,
                "current_zone": obj.current_zone,
                "path_history": obj.path_history[-10:] # Last 10 points
            },
            "environmental": {
                "confidence": obj.confidence,
                "idling_sec": round(obj.total_idling_time, 2)
            }
        }

        # 2. PERSIST TO POSTGRESQL (ACID Transaction)
        self.db.log_safety_incident(
            self.junction_id,
            a_type,
            severity,
            desc,
            telemetry
        )

        # 3. UPDATE LEDGER
        self.incident_ledger[alert_id] = now
        logging.warning(f"!!! [CRITICAL {severity}] {desc} !!!")

    def cleanup_memory(self):
        """Standard production maintenance to clear old alert history."""
        now = time.time()
        self.incident_ledger = {k: v for k, v in self.incident_ledger.items() 
                                if (now - v) < self.ALERT_COOLDOWN}