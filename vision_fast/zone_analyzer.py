"""
Zone Analyzer Module - Optimized for Hybrid Architecture
Role: Converts vehicle positions into Traffic Metrics (Density, Queue, Counts).
Features:
1. Area-Based Density (Bus > Car).
2. Separate Logic for Priority (0-50m) vs Grid (51-100m).
3. Queue Estimation (Distance from stop line).
"""

from typing import Dict, List, Any, Tuple
import numpy as np
import cv2

# Utils
try:
    from ..utils.logger import log_info, log_error
except ImportError:
    def log_info(msg, src): print(f"ℹ️ [{src}] {msg}")
    def log_error(msg, src): print(f"❌ [{src}] {msg}")

class ZoneAnalyzer:
    """
    Analyzes mapped vehicles to calculate traffic pressure metrics.
    """
    
    def __init__(self):
        self.module_name = "ZONE_ANALYZER"
        self._initialized = False
        
        # Calibration (Standard Vehicle Areas in pixels approx)
        # Assuming 720p/1080p, these should be tuned or dynamic based on ROI
        self.veh_weights = {
            'car': 1.0,
            'bus': 2.5,
            'truck': 2.5,
            'motorcycle': 0.3,
            'auto': 0.8,
            'unknown': 1.0
        }
        
        self.pixels_per_meter = 2.5 # Default, updated in init
        self.lane_areas = {} # Cache for polygon areas

    def initialize(self, zone_configs: Dict, pixels_per_meter: float = 2.5, stop_lines: Dict = None) -> bool:
        """
        Args:
            zone_configs: Not strictly needed if LaneMapper provides Polygons, 
                          but useful for caching areas.
            pixels_per_meter: For queue length calc.
            stop_lines: { "Phase_North": [y1, y2] } - definition of "front" of lane.
        """
        try:
            self.pixels_per_meter = pixels_per_meter
            self.stop_lines = stop_lines or {}
            self._initialized = True
            log_info("✅ Zone Analyzer Initialized.", self.module_name)
            return True
        except Exception as e:
            log_error(f"Init Failed: {e}", self.module_name)
            return False

    def analyze_zones(self, lane_groups: List[Dict[str, Any]], frame_obj: Any = None, mode: str = "HYBRID") -> Dict[str, Dict]:
        """
        Main Processing Function.
        Args:
            lane_groups: Output from LaneMapper.
            frame_obj: Numpy Frame OR Tuple shape.
            mode: 'HYBRID' (Split Zone) or 'GRID' (Full Occupancy).
        """
        if not self._initialized: return {}

        results = {}

        for group in lane_groups:
            lane_id = group['lane_id']
            vehicles = group['vehicles']
            
            # 1. Calculate Count & Weighted Count (PCU)
            count = len(vehicles)
            weighted_count = 0.0
            total_veh_area = 0.0
            
            # Queue tracking
            max_dist = 0.0
            
            # Determine Split Line (0-50m vs 51-100m)
            # Assuming camera view: Bottom is Near (0m), Top is Far (Horizon)
            # We split at 50% height for now (Calibrate later)
            frame_h = 360 # Default
            if frame_obj is not None:
                if hasattr(frame_obj, 'shape'): frame_h = frame_obj.shape[0]
                elif isinstance(frame_obj, tuple): frame_h = frame_obj[0]
            
            split_y = frame_h * 0.5 # Midpoint
            
            for veh in vehicles:
                # Get Centroid Y
                bbox = veh.get('bbox', [0,0,0,0])
                cy = (bbox[1] + bbox[3]) / 2
                
                
                
                weight = 1.0
                if mode == "GRID":
                    # GRID ZONE: Strict Occupancy / Cell Filling
                    weight = 1.0 
                else: 
                    # HYBRID ZONE
                    # Near (0-50m) -> Bottom of screen (y > split_y) -> Exact Type
                    # Far (51-100m) -> Top of screen (y < split_y) -> Occupancy Only
                    if cy > split_y:
                        # NEAR ZONE: Strict Classification
                        v_type = veh.get('class_name', 'unknown').lower()
                        weight = self.veh_weights.get(v_type, 1.0)
                    else:
                         # FAR ZONE: Occupancy
                         weight = 1.0
                
                weighted_count += weight
                
                # Area Calc (Approximation from bbox)
                w = max(0, bbox[2] - bbox[0])
                h = max(0, bbox[3] - bbox[1])
                total_veh_area += (w * h)

            # 2. Density Calculation
            # Hybrid Density: weighted_count / capacity
            # Capacity is higher for Grid/Far zones typically, but we normalize to Lane
            lane_capacity_pcu = 12.0
            density = min(1.0, weighted_count / lane_capacity_pcu)

            metrics = {
                "count": count,                          # Part 3 Contract: "count"
                "weighted_count": round(weighted_count, 2),  # Part 3 Contract: "weighted_count"
                "density": round(density, 3),            # Part 3 Contract: "density"
                "queue_length_meters": 0.0,              # Placeholder until StopLine logic is robust
                "is_active": count > 0
            }
            
            results[lane_id] = metrics

        return results