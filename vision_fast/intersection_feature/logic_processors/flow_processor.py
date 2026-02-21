# intersection_feature/logic_processors/flow_processor.py
"""
PRODUCTION TRAFFIC FLOW & WEIGHTED DEMAND ENGINE (V4.0 - GOLD STANDARD)
Purpose: High-fidelity trajectory analysis, weighted demand scoring, and safety auditing.
Source of Truth: 
    - PDF Page 3: Direction-Wise Counting & Traffic Demand Generation.
    - PDF Page 6: Pedestrian Detection & Movement Patterns.
    - PDF Page 12: Historical Analytics Support.
Standard: Vector-based logic, sub-millisecond state reporting, and transactional integrity.
"""

import sys
import os
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

# --- PRODUCTION ENVIRONMENT SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from models import TrackedObject
from intersection_db import IntersectionDatabase
from config.settings import SystemConfig

class TrafficFlowProcessor:
    def __init__(self, junction_id: str):
        self.junction_id = junction_id
        self.db = IntersectionDatabase()
        
        # ACTIVE STATE REGISTRY: Stores the Digital Twin objects
        self.active_tracks: Dict[str, TrackedObject] = {}
        
        # PERSISTENCE BUFFER: To handle 'ghost' detections and prevent double-counting
        self.exited_buffer = set()

        # REAL-TIME DEMAND MATRIX (PDF Page 3)
        # We calculate the 'Weighted Pressure' on each road.
        # This is what the Signal Controller reads to decide green times.
        self.live_pressure_matrix = {
            "NORTH": 0.0, "SOUTH": 0.0, "EAST": 0.0, "WEST": 0.0,
            "pedestrians_active": False,
            "total_unit_count": 0
        }

    def process_telemetry_stream(self, frame_data: List[Dict[str, Any]]):
        """
        The Master Processing Pipe. Processes raw telemetry into traffic intelligence.
        """
        current_frame_ids = set()
        
        # Reset frame-specific pressure to 0
        frame_pressure = {"NORTH": 0.0, "SOUTH": 0.0, "EAST": 0.0, "WEST": 0.0}
        peds_detected = 0

        # --- PHASE 1: TRACKING & VECTOR UPDATE ---
        for raw_obj in frame_data:
            oid = raw_obj['id']
            current_frame_ids.add(oid)
            
            # Map raw data to local variables
            pos = (raw_obj['x'], raw_obj['y'])
            speed = raw_obj['speed']
            o_class = raw_obj['class']
            confidence = raw_obj.get('confidence', 1.0)

            if oid in self.active_tracks:
                # Update existing physics and state machine (idling/zones/etc)
                self.active_tracks[oid].update_telemetry(pos, speed)
            else:
                # PDF Page 6: Register new object entry
                # Ignore if we just saw this object leave (prevents flicker counting)
                if oid not in self.exited_buffer:
                    self.active_tracks[oid] = TrackedObject(oid, o_class, pos)
                    logging.info(f"[FLOW] New {o_class} Identified: {oid} | Entry: {self.active_tracks[oid].entry_zone}")

            # --- PHASE 2: WEIGHTED DEMAND CALCULATION (PDF Page 3) ---
            # Instead of counting 1, 2, 3... we add the strategic weight of the class.
            # 1 Bus adds 5.0 pressure; 1 Car adds 2.0 pressure.
            obj = self.active_tracks[oid]
            if o_class == "Pedestrian":
                peds_detected += 1
            else:
                # Add to the pressure of the vehicle's CURRENT road
                current_zone = obj.current_zone
                if current_zone in frame_pressure:
                    frame_pressure[current_zone] += self._calculate_unit_weight(o_class)

        # --- PHASE 3: STATE BROADCAST (PostgreSQL Update) ---
        self.live_pressure_matrix.update(frame_pressure)
        self.live_pressure_matrix["pedestrians_active"] = peds_detected > 0
        self.live_pressure_matrix["total_unit_count"] = len(self.active_tracks)

        # Atomic push to the 'realtime_demand' table for external controllers
        self.db.update_live_demand(self.junction_id, self.live_pressure_matrix)

        # --- PHASE 4: COMPLETION & FORENSIC ARCHIVING ---
        # Detect objects that have left the scene (Lifecycle termination)
        previous_ids = set(self.active_tracks.keys())
        exited_ids = previous_ids - current_frame_ids

        for vid in exited_ids:
            self._archive_completed_trip(vid)
            
        # Manage buffer to prevent infinite memory growth
        if len(self.exited_buffer) > 100: self.exited_buffer.pop()

    def _calculate_unit_weight(self, vehicle_class: str) -> float:
        """
        Maps Strategic Values from PDF Page 1 & 3.
        Buses are weighted 5x more than motorbikes to prioritize mass transit.
        """
        # Production Logic: These are weights, not points. 
        # They represent 'Occupancy Load' on the asphalt.
        weights = {
            "Public Transport": 5.0, "Bus": 5.0,
            "Commercial": 3.0, "Truck": 3.0,
            "Car": 2.0, "Private Car": 2.0,
            "Two-Wheeler": 1.0,
        }
        return weights.get(vehicle_class, 1.5) # Default to 1.5 if unknown

    def _archive_completed_trip(self, vid: str):
        """
        Finalizing the Digital Twin. Logs the trajectory, idling time, 
        and turn classification to the permanent database.
        """
        vehicle = self.active_tracks[vid]
        
        # Only log if the trip was valid (Entry -> Center -> Exit)
        # This filters out 'noise' detections (Page 11)
        if vehicle.exit_zone and vehicle.has_entered_center:
            # 1. Classify the final movement (PDF Page 3: Straight, Left, Right)
            movement = vehicle.get_movement_classification()
            
            # 2. Persist to PostgreSQL (PDF Page 12 Historical Patterns)
            self.db.record_completed_trip(self.junction_id, vehicle)
            
            logging.info(f"[AUDIT] Lifecycle End: {vid} performed {movement}. "
                         f"Idling Total: {round(vehicle.total_idling_time, 1)}s")

        # 3. Clean Memory
        self.exited_buffer.add(vid)
        del self.active_tracks[vid]

    def get_signal_demand_packet(self) -> Dict:
        """
        Export function for the Signal Logic (Siraj).
        Returns a clean dictionary of road pressure.
        """
        return self.live_pressure_matrix