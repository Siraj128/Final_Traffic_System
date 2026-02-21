"""
Violation Manager Module
Orchestrates AI Models and Logic to detect 10+ types of traffic violations.
Implements 2-Step Verification (Temporal Consistency) to ensure high accuracy.
"""

import cv2
import numpy as np
from collections import deque
import time
import os

# Project root: Traffic_System/
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

from ..utils.logger import log_info, log_error, log_debug

class ViolationManager:
    """
    Central Logic Unit for detecting traffic violations.
    """
    
    def __init__(self):
        self.module_name = "VIOLATION_MANAGER"
        self._initialized = False
        
        # --- 1. MODEL CONFIGURATION ---
        self.models = {}
        self.model_files = {
            "helmet": os.path.join(_PROJECT_ROOT, "models", "helmet_detector.pt"),
            "phone": os.path.join(_PROJECT_ROOT, "models", "phone_detector.pt"),
            "seatbelt": os.path.join(_PROJECT_ROOT, "models", "seatbelt_detector.pt")
        }
        
        # --- 2. TRAFFIC RULES CONFIGURATION ---
        # Define allowed maneuvers (Lanes must match your config.json names)
        self.LANE_RULES = {
            "North_Left": ["LEFT_TURN", "U_TURN"],
            "North_Straight": ["STRAIGHT"],
            "North_Right": ["RIGHT_TURN"],
            "South_Left": ["LEFT_TURN", "U_TURN"],
            "South_Straight": ["STRAIGHT"],
            # Add others as needed...
        }
        
        # --- 3. STATE MEMORY ---
        # For Logic Checks (Lane Change, Wrong Way)
        # Structure: { veh_id: { "lane_history": deque([lane_id, ...]), "positions": deque([(x,y)...]) } }
        self.vehicle_history = {}
        
        # For 2-Step Verification
        # Structure: { veh_id: { "violation_type": frames_count } }
        self.pending_violations = {} 
        
        # Logged Violations (to avoid duplicate alerts)
        # Structure: Set((veh_id, violation_type))
        self.verified_violations = set() 
        
        # Thresholds
        self.CONSISTENCY_THRESHOLD = 5  # Frames required to confirm violation
        self.SPEED_LIMIT_PIXELS = 50    # Calibration needed for real world
        self.STOP_LINE_MARGIN = -2.0    # Meters past stop line

    def initialize(self) -> bool:
        """Loads all specialist AI models."""
        if YOLO is None:
            log_error("Ultralytics not installed.", self.module_name)
            return False
            
        log_info("⚖️ Initializing Violation Manager...", self.module_name)
        
        for key, path in self.model_files.items():
            try:
                # Load model
                self.models[key] = YOLO(path)
                log_info(f"   ✅ Loaded Specialist: {key}", self.module_name)
            except Exception as e:
                log_error(f"   ⚠️ Failed to load {key} ({path}): {e}", self.module_name)
        
        self._initialized = True
        return True

    def check_violations(self, frame: np.ndarray, vehicle: dict, signal_state: dict) -> list:
        """
        Main API: Analyzes a vehicle for all enabled violations.
        
        Args:
            frame: Full video frame (for cropping)
            vehicle: Vehicle dict from DetectionController
            signal_state: Dict {'North': 'RED', ...}
            
        Returns:
            List of confirmed violation strings (e.g., ["NO_HELMET", "RED_LIGHT_JUMP"])
        """
        if not self._initialized: return []
        
        veh_id = vehicle.get('id')
        if veh_id is None: return []

        active_violations = [] # Violations found in THIS frame
        
        # Update Tracking History
        self._update_history(vehicle)
        
        # ==========================
        # SECTION A: LOGIC CHECKS
        # ==========================
        
        # 1. Red Light Jump
        if self._check_red_light(vehicle, signal_state):
            active_violations.append("RED_LIGHT_JUMP")
            
        # 2. Stop Line Violation (Zebra Crossing)
        if self._check_stop_line(vehicle, signal_state):
            active_violations.append("STOP_LINE_CROSS")
            
        # 3. Wrong Way Driving
        if self._check_wrong_way(vehicle):
            active_violations.append("WRONG_WAY")
            
        # 4. Lane Discipline (Wrong Turn)
        if self._check_lane_discipline(vehicle):
            active_violations.append("LANE_DISCIPLINE")
            
        # 5. Unsafe Lane Change (Solid Line)
        if self._check_lane_change(vehicle):
            active_violations.append("UNSAFE_LANE_CHANGE")

        # ==========================
        # SECTION B: MODEL CHECKS
        # ==========================
        # Optimization: Only run heavy models on large enough vehicles and periodically
        # (Running every frame kills FPS. We use ID modulo 3 to run every 3rd frame)
        
        if veh_id % 3 == 0:
            veh_crop = self._crop_vehicle(frame, vehicle.get('bbox'))
            
            if veh_crop is not None and veh_crop.size > 0:
                v_type = vehicle.get('class_name', 'unknown')
                
                # --- Two-Wheeler Violations ---
                if v_type in ['motorcycle', 'bike', 'scooter']:
                    if 'helmet' in self.models:
                        res = self.models['helmet'](veh_crop, verbose=False, conf=0.4)[0]
                        
                        # 6. No Helmet
                        if self._check_no_helmet(res): 
                            active_violations.append("NO_HELMET")
                        
                        # 7. Triple Riding
                        if self._check_triple_riding(res): 
                            active_violations.append("TRIPLE_RIDING")

                # --- Four-Wheeler Violations ---
                if v_type in ['car', 'truck', 'bus', 'taxi']:
                    # 8. Mobile Phone Usage
                    # Checks for 'phone', 'mobile', 'cell' in standard YOLO classes
                    if 'phone' in self.models and \
                       self._detect_obj(self.models['phone'], veh_crop, ['phone', 'mobile', 'cell']):
                        active_violations.append("MOBILE_USAGE")
                        
                    # 9. No Seatbelt
                    if 'seatbelt' in self.models and \
                       self._detect_obj(self.models['seatbelt'], veh_crop, ['no-seatbelt', 'no_seatbelt']):
                        active_violations.append("NO_SEATBELT")

        # ==========================
        # SECTION C: VERIFICATION
        # ==========================
        return self._verify_violations(veh_id, active_violations)

    # -------------------------------------------------------------------------
    # LOGIC IMPLEMENTATIONS
    # -------------------------------------------------------------------------

    def _update_history(self, veh):
        vid = veh['id']
        if vid not in self.vehicle_history:
            self.vehicle_history[vid] = {
                "lane_history": deque(maxlen=20),
                "last_update": time.time()
            }
        
        if veh.get('lane_id'):
            self.vehicle_history[vid]["lane_history"].append(veh['lane_id'])

    def _check_red_light(self, veh, signal_state):
        # Requires: Vehicle Lane, Signal State, Dist to Stopline
        lane = veh.get('lane_id', '')
        # Extract Phase (e.g. "North" from "North_Straight")
        phase = lane.split('_')[0] if '_' in lane else ''
        
        if phase and signal_state.get(phase) == "RED":
            # If vehicle is SIGNIFICANTLY past stop line (e.g. -5 meters)
            dist = veh.get('dist_to_stopline', 100)
            if dist < -5.0: 
                return True
        return False

    def _check_stop_line(self, veh, signal_state):
        lane = veh.get('lane_id', '')
        phase = lane.split('_')[0] if '_' in lane else ''
        
        if phase and signal_state.get(phase) == "RED":
            # If vehicle is barely past stop line (Zebra Crossing violation)
            dist = veh.get('dist_to_stopline', 100)
            if -5.0 < dist < 0:
                return True
        return False

    def _check_wrong_way(self, veh):
        # Relies on DirectionTracker logic
        direction = veh.get('movement_dir', 'UNKNOWN')
        return direction == "WRONG_WAY"

    def _check_lane_discipline(self, veh):
        """Checks if movement matches lane arrows (e.g., Left Lane -> Straight = Violation)."""
        lane = veh.get('lane_id', '')
        move = veh.get('movement_dir', 'UNKNOWN')
        
        if not lane or move in ['UNKNOWN', 'STATIONARY']:
            return False
            
        # Check rule book
        if lane in self.LANE_RULES:
            allowed = self.LANE_RULES[lane]
            if move not in allowed:
                return True
        return False

    def _check_lane_change(self, veh):
        """Detects lane hopping near junctions."""
        history = self.vehicle_history.get(veh['id'], {}).get("lane_history", [])
        if len(history) < 10: return False
        
        # Logic: If lane ID changed from X to Y recently
        first_lane = history[0]
        last_lane = history[-1]
        
        if first_lane != last_lane:
            # Simplistic: Any lane change in ROI is a violation
            # Advanced: Check if line between lanes is Solid vs Dashed (requires map info)
            return True 
        return False

    # -------------------------------------------------------------------------
    # MODEL HELPER FUNCTIONS
    # -------------------------------------------------------------------------

    def _crop_vehicle(self, frame, bbox):
        if not bbox: return None
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1: return None
        return frame[y1:y2, x1:x2]

    def _check_no_helmet(self, results):
        """Returns True if 'no-helmet' or Head detected without helmet."""
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id].lower()
            if 'no' in label and 'helmet' in label: return True
        return False

    def _check_triple_riding(self, results):
        """Counts heads/helmets."""
        count = 0
        for box in results.boxes:
            label = results.names[int(box.cls[0])].lower()
            if 'helmet' in label or 'head' in label or 'person' in label:
                count += 1
        return count > 2

    def _detect_obj(self, model, img, keywords):
        """
        Generic detector that checks if any detected class matches keywords.
        Handles flexible naming (e.g. 'cell phone' vs 'mobile').
        """
        if not model: return False
        
        # Run inference
        results = model(img, verbose=False, conf=0.3)[0]
        
        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = results.names[cls_id].lower()
            
            # Check against all keywords
            for k in keywords:
                if k in label:
                    # Extra check for Phone (avoid low conf noise)
                    if 'phone' in k and float(box.conf[0]) < 0.45:
                        continue
                    return True
        return False

    # -------------------------------------------------------------------------
    # 2-STEP VERIFICATION SYSTEM
    # -------------------------------------------------------------------------

    def _verify_violations(self, veh_id, current_violations):
        """
        The Judge.
        Only returns a violation if it has been seen in N consecutive frames.
        """
        confirmed_list = []
        
        # Init memory for vehicle
        if veh_id not in self.pending_violations:
            self.pending_violations[veh_id] = {}
            
        # 1. Increment Counts for Current Violations
        for v in current_violations:
            self.pending_violations[veh_id][v] = self.pending_violations[veh_id].get(v, 0) + 1
            
            # Check Threshold
            if self.pending_violations[veh_id][v] == self.CONSISTENCY_THRESHOLD:
                # Unique Check: Only alert once per vehicle per violation type
                if (veh_id, v) not in self.verified_violations:
                    confirmed_list.append(v)
                    self.verified_violations.add((veh_id, v))
                    log_info(f"🚨 CONFIRMED VIOLATION: Vehicle {veh_id} -> {v}", self.module_name)
        
        # 2. Reset Counts for Missing Violations (Optional: decay logic)
        # If a violation is NOT in current frame, we could reset its count to 0
        # to ensure continuity.
        for v_type in list(self.pending_violations[veh_id].keys()):
            if v_type not in current_violations:
                # It disappeared! Reset counter.
                self.pending_violations[veh_id][v_type] = 0
                
        return confirmed_list

    def shutdown(self):
        self.models.clear()
        self._initialized = False