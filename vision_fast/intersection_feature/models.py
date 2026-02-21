# intersection_feature/models.py
"""
ULTIMATE PRODUCTION DATA MODELS (V4.0)
Level: Mission-Critical Intelligent Transport System (ITS)
Purpose: High-fidelity Digital Twin tracking with Physics-Validation.
Source of Truth: 13-Page Intersection PDF (Pages 3, 5, 6, 11).
"""

import time
import math
import uuid
from typing import List, Tuple, Dict, Optional
from config.settings import SystemConfig

class TrackedObject:
    """
    A Production-Grade entity model that manages its own lifecycle, 
    physics, and behavioral anomalies.
    """
    def __init__(self, tracking_id: str, obj_class: str, initial_pos: Tuple[int, int], env_state: str = "CLEAR"):
        # 1. IDENTITY & AUDIT (Industry Standard)
        self.internal_uuid = uuid.uuid4()      # Unique identifier for the Centralized Server
        self.camera_id = tracking_id           # ID assigned by the local camera module
        self.obj_class = obj_class             # PDF Page 6: Car, Bus, Two-Wheeler, Pedestrian
        self.env_context = env_state           # PDF Page 5: Rain, Fog, Low Light
        self.confidence = 1.0                  # Default confidence

        # 2. PHYSICS & TRAJECTORY (PDF Page 6: Accident/Slowdown detection)
        self.current_pos = initial_pos
        self.previous_pos = initial_pos
        self.vx = 0.0                          # Velocity X (pixels/sec)
        self.vy = 0.0                          # Velocity Y
        self.speed_mps = 0.0                   # Speed in Meters per Second (scaled)
        self.acceleration = 0.0                # For 'Sudden Stoppage' detection
        self.bearing = 0.0                     # Direction in degrees
        self.path_history: List[Tuple[int, int, float]] = [] # (x, y, timestamp)
        
        # 3. INTERSECTION STATE MACHINE (PDF Page 3: Direction-wise tracking)
        self.entry_zone = self._map_coordinates_to_zone(initial_pos)
        self.current_zone = self.entry_zone
        self.exit_zone = None
        self.has_entered_center = False
        
        # 4. ENVIRONMENTAL & ECONOMIC (PDF Page 4)
        self.total_idling_time = 0.0
        self.idling_start_ts: Optional[float] = None

        # 5. ANOMALY & SAFETY LOGIC (PDF Page 6: Vehicles stopping in middle)
        self.is_stalled = False
        self.stall_start_ts: Optional[float] = None
        self.last_seen_ts = time.time()
        self.is_active = True # False when object leaves junction

    def update_telemetry(self, new_pos: Tuple[int, int], raw_speed: float, confidence: float = 1.0):
        """
        Processes new frame data. Calculates physics and checks for safety threats.
        """
        now = time.time()
        dt = now - self.last_seen_ts
        if dt <= 0: dt = 0.033 # Default to 30fps if dt is invalid

        # A. UPDATE PHYSICS VECTORS (Vector Math)
        dx = new_pos[0] - self.current_pos[0]
        dy = new_pos[1] - self.current_pos[1]
        
        self.vx = dx / dt
        self.vy = dy / dt
        self.bearing = math.degrees(math.atan2(dy, dx))
        
        # Acceleration = (New Speed - Old Speed) / Time
        self.acceleration = (raw_speed - self.speed_mps) / dt
        self.previous_pos = self.current_pos
        self.current_pos = new_pos
        self.speed_mps = raw_speed
        self.confidence = confidence
        self.last_seen_ts = now
        
        # Log history for trajectory prediction
        self.path_history.append((new_pos[0], new_pos[1], now))
        if len(self.path_history) > 30: self.path_history.pop(0)

        # B. UPDATE STATE MACHINE (Zone Logic)
        new_zone = self._map_coordinates_to_zone(new_pos)
        if new_zone == "CENTER_BOX":
            self.has_entered_center = True
        
        # Detect Exit: Object was in Center, now in a Road Zone
        if self.has_entered_center and new_zone != "CENTER_BOX" and new_zone != "TRANSIT":
            self.exit_zone = new_zone

        self.current_zone = new_zone

        # C. BEHAVIORAL AUDIT: IDLING & STALLS (PDF Page 4 & 6)
        self._audit_behavioral_state(now)

    def _audit_behavioral_state(self, current_ts: float):
        """Monitor for idling (fuel waste) and stalls (gridlock)."""
        is_stationary = self.speed_mps < SystemConfig.STATIONARY_SPEED_THRESHOLD
        
        # 1. Idling (PDF Page 4)
        if is_stationary:
            if self.idling_start_ts is None:
                self.idling_start_ts = current_ts
            else:
                self.total_idling_time = current_ts - self.idling_start_ts
        else:
            self.idling_start_ts = None

        # 2. Gridlock Stalls (PDF Page 6)
        if self.current_zone == "CENTER_BOX" and is_stationary:
            if self.stall_start_ts is None:
                self.stall_start_ts = current_ts
            elif (current_ts - self.stall_start_ts) >= SystemConfig.STUCK_TIMER_LIMIT:
                self.is_stalled = True
        else:
            self.stall_start_ts = None
            self.is_stalled = False

    def get_stall_duration(self) -> float:
        """Helper for the Anomaly Processor description."""
        if self.stall_start_ts:
            return round(time.time() - self.stall_start_ts, 1)
        return 0.0

    def is_collision_risk(self) -> bool:
        """
        Detects 'Sudden Stoppage' (PDF Page 6).
        Production Logic: High deceleration without a traffic signal cause.
        """
        # Threshold: Braking harder than 15 m/s^2 is likely a collision
        return self.acceleration < -15.0

    def get_movement_classification(self) -> str:
        """
        Classifies turn type based on Entry/Exit zones (PDF Page 3).
        """
        if not self.entry_zone or not self.exit_zone:
            return "INCOMPLETE_PASSAGE"
        
        route = (self.entry_zone, self.exit_zone)
        return SystemConfig.MOVEMENT_TYPES.get(route, "UNDEFINED_MOVEMENT")

    def _map_coordinates_to_zone(self, pos: Tuple[int, int]) -> str:
        """
        Translates raw pixels to meaningful zones from the PDF.
        Supports dynamic intersection sizes via config.
        """
        x, y = pos
        geo = SystemConfig.JUNCTION_GEOMETRY
        
        # 1. Check Center Box (The core of the intersection)
        c = geo["CENTER_BOX"]
        if (c['x_min'] <= x <= c['x_max'] and c['y_min'] <= y <= c['y_max']):
            return "CENTER_BOX"

        # 2. Check Directional Entry Zones (Trigger lines - PDF Page 3)
        ez = geo["ENTRY_ZONES"]
        if y < ez["NORTH"].get("y_max", -1): return "NORTH"
        if y > ez["SOUTH"].get("y_min", 9999): return "SOUTH"
        if x > ez["EAST"].get("x_min", 9999):  return "EAST"
        if x < ez["WEST"].get("x_max", -1):  return "WEST"

        return "TRANSIT"

    def serialize_for_transmission(self) -> Dict:
        """
        Formats the object for JSON transmission to the CMS (PDF Page 7).
        """
        return {
            "uuid": str(self.internal_uuid),
            "class": self.obj_class,
            "speed": round(self.speed_mps, 2),
            "accel": round(self.acceleration, 2),
            "path": self.entry_zone + " -> " + (self.exit_zone or "TRANSIT"),
            "is_anomaly": self.is_stalled or self.is_collision_risk()
        }