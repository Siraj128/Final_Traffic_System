"""
Detection Controller Module - Optimized Critical Path (Level 5.1)
Updates:
- Fixed LaneMapper initialization to support Native JSON parsing.
- Maintains strict Telemetry-only role.
"""

from typing import Dict, Any, List, Tuple
import time
import os
import json
import numpy as np
import traceback
import cv2

# --- 1. CORE DETECTION MODULES (FAST ONLY) ---
try:
    from .vehicle_detector import VehicleDetector
    from .lane_mapper import LaneMapper
    from .zone_analyzer import ZoneAnalyzer 
    from .anpr_controller import ANPRController # Phase 16: Reward System
    # --- UTILS ---
    from ..utils.logger import log_info, log_error
except ImportError:
    # Fallback for direct testing
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from vehicle_detector import VehicleDetector
    from lane_mapper import LaneMapper
    from zone_analyzer import ZoneAnalyzer
    from anpr_controller import ANPRController
    def log_info(msg, src): print(f"ℹ️ [{src}] {msg}")
    def log_error(msg, src): print(f"❌ [{src}] {msg}")

class DetectionController:
    """
    Lightweight Controller for Real-Time Traffic Signals.
    Running on: Single Laptop (Fast Path).
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.module_name = "DETECTION_CONTROLLER"
        self._initialized = False
        self.config = config or {}
        
        # --- A. Initialize ONLY Critical Sub-modules ---
        self.vehicle_detector = VehicleDetector() # Singleton Optimized
        self.lane_mapper = LaneMapper()
        self.vehicle_detector = VehicleDetector() # Singleton Optimized
        self.lane_mapper = LaneMapper()
        self.zone_analyzer = ZoneAnalyzer()
        self.anpr_controller = ANPRController() # Phase 16
        
        # Performance: Frame-Skip Logic
        self.detect_every_n = self.config.get("detect_every_n", 3) 
        self._frame_count = 0
        self._cached_detections = [] 

    def initialize(self) -> bool:
        """Initialize all fast components."""
        try:
            log_info("🚀 Initializing Detection Controller (Fast Path)...", self.module_name)
            
            # 1. Core Detection (Uses Shared Memory Model)
            if not self.vehicle_detector.initialize(): 
                log_error("Vehicle Detector Failed to Init", self.module_name)
                return False
            
            # 2. Lane Mapping Config (CRITICAL UPDATE)
            # The LaneMapper now parses the Grid/Hybrid JSON structure itself.
            # We pass the entire config dictionary.
            if not self.lane_mapper.initialize(self.config):
                log_error("Lane Mapper Failed to Init", self.module_name)
                return False
            
            # 3. Zone Analysis Config (Stop lines, ROI)
            # ZoneAnalyzer still needs specific params from the config
            zone_configs = self.config.get("zone_configs", {})
            ppm = self.config.get("pixels_per_meter", 2.5)
            stop_lines = self.config.get("stop_lines", {})
            
            if hasattr(self.zone_analyzer, 'initialize'):
                self.zone_analyzer.initialize(zone_configs, pixels_per_meter=ppm, stop_lines=stop_lines)
            
            # 4. Phase 16/18: ANPR & Reward System
            # Check for Dummy Mode Config
            anpr_mode = "DUMMY" if self.config.get("anpr_dummy_mode", False) else "REAL"
            self.anpr_controller = ANPRController(mode=anpr_mode)
            
            self._initialized = True
            log_info(f"✅ Detection Controller Ready. ANPR Mode: {anpr_mode}", self.module_name)
            return True
            
        except Exception as e:
            log_error(f"Controller Init Crashed: {e}", self.module_name)
            return False

    def process_frame(self, frame: np.ndarray, junction_data: Any = None, visualize: bool = False, detect_mode: str = "HYBRID", show_roi: bool = True, **kwargs) -> Dict[str, Any]:
        """
        Process a single frame for Traffic Signal Data ONLY.
        """
        if not self._initialized: 
            return {"status": "error", "error": "Not initialized"}
            
        timings = {}
        t_start = time.time()
        
        try:
            self._frame_count += 1
            
            # --- STEP 1: DETECT VEHICLES (Optimized) ---
            t0 = time.time()
            if self._frame_count % self.detect_every_n == 0:
                # Run Inference
                det_result = self.vehicle_detector.detect(frame, visualize=False)
                self._cached_detections = det_result.get("vehicle_detections", [])
            
            # Use specific/cached detections
            detections = self._cached_detections
            timings["detection"] = time.time() - t0
            
            t0 = time.time()
            # Assign 'lane_id' to each vehicle using the new optimized logic
            lane_groups = self.lane_mapper.assign_lanes(detections)
            timings["mapping"] = time.time() - t0
            
            # --- STEP 3: ANALYZE ZONES (Density/Counts) ---
            t0 = time.time()
            # This returns exactly what HybridCore needs:
            # { "North_Left": {count: 5, density: 0.2}, ... }
            zone_stats = self.zone_analyzer.analyze_zones(lane_groups, frame_obj=frame, mode=detect_mode)
            timings["analysis"] = time.time() - t0
            
            # --- STEP 4: HYBRID ANPR (Reward System) ---
            # Randomly checks for Good Behavior (Stopped at Red)
            # Now with Tracking & Dual Mode Support!
            anpr_results = self.anpr_controller.process(
                frame, 
                zone_stats,
                detections, # <--- Pass Raw Detections for Tracking
                phase_name=kwargs.get("phase_name", "Unknown"),
                light_state=kwargs.get("light_state", "RED")
            )

            # --- VISUALIZATION (Moved to End for Overlay) ---
            if visualize:
                # Use VehicleDetector's utility to draw on the frame in-place
                formatted_results = []
                for d in detections:
                    # VehicleDetector returns 'vehicle_type', 'confidence_score', 'bbox_coordinates'
                    lbl = d.get('vehicle_type', 'unknown')
                    if lbl == 'unknown': lbl = 'Vehicle' 
                    
                    formatted_results.append({
                        "vehicle_type": lbl,
                        "bbox_coordinates": d.get('bbox_coordinates', [0,0,0,0]),
                        "confidence_score": d.get('confidence_score', 0.0)
                    })

                self.vehicle_detector._draw_detections(frame, formatted_results)
                
                # VISUALIZE ROI (Lanes/Zones) -- CONDITIONALLY
                if show_roi:
                    self.lane_mapper.draw_lanes(frame, detect_mode=detect_mode)
                
                # OVERLAY MODE INFO - Top Right (System Mode)
                h_img, w_img = frame.shape[:2]
                cv2.putText(frame, f"MODE: {detect_mode}", (w_img - 350, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                
                # ANPR Mode Indicator - Bottom Right
                anpr_color = (0, 0, 255) if self.anpr_controller.mode == "DUMMY" else (0, 255, 0)
                cv2.putText(frame, f"ANPR: {self.anpr_controller.mode}", (w_img - 350, h_img - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, anpr_color, 2)
                
                # DRAW ANPR PLATES (Efficiently)
                if anpr_results:
                     for res in anpr_results:
                         # res: {track_id, bbox, plate, owner, ...}
                         x1, y1, x2, y2 = res['bbox']
                         plate = res.get('plate', '')
                         if plate and plate != "Scanning...":
                             # Draw Plate Text (White with Black Outline for visibility)
                             cv2.putText(frame, plate, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 4)
                             cv2.putText(frame, plate, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            timings["total"] = time.time() - t_start
            
            return {
                "status": "success",
                "timestamp": t_start,
                "lane_data": zone_stats, # <-- The Payload for Logic Core
                "raw_detections": detections, # <-- Raw bounding boxes for HybridCore
                "vehicle_count": len(detections),
                "intersection_status": "CLEAR",  # Part 3: From Camera 5 (CLEAR/BLOCKED)
                "metadata": {"timings": timings}
            }
            
        except Exception as e:
            log_error(f"Process Frame Failed: {e}", self.module_name)
            traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def shutdown(self):
        log_info("Shutting down Detection Controller...", self.module_name)
        pass