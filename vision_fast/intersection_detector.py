"""
intersection_detector.py  —  Phase 8 Upgrade
Camera 5 Intersection Monitor with Finish-Line Directional Tracking

- detect_status():         Returns BLOCKED / CLEAR (gridlock check)
- detect_full():           Returns status + accumulated directional counts
- drain_directional_counts(): Called once per heartbeat cycle to get counts
"""
import json
import os
import cv2
import numpy as np
from typing import Dict, Any, Tuple

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

try:
    from .vehicle_detector import VehicleDetector
except ImportError:
    import sys
    sys.path.append(os.path.join(_PROJECT_ROOT, "vision_fast"))
    from vehicle_detector import VehicleDetector

try:
    from core_logic.direction_finish_tracker import DirectionFinishTracker
except ImportError:
    sys.path.insert(0, _PROJECT_ROOT)
    from core_logic.direction_finish_tracker import DirectionFinishTracker


class IntersectionDetector:
    def __init__(self, config_path=None):
        self.module_name = "INTERSECTION_DETECTOR"
        self._config_path = config_path or os.path.join(_PROJECT_ROOT, "config", "intersection_roi.json")
        self.roi_points = []
        self.gridlock_threshold = 5
        self._initialized = False

        # Reuse the singleton detector
        self.detector = VehicleDetector()

        # Phase 8: Finish-line directional tracker (init after ROI is loaded)
        self._finish_tracker: DirectionFinishTracker = None

        # Simple nearest-centroid vehicle ID tracking
        self._tracked_ids: Dict[int, Tuple[int, int]] = {}  # id -> last centroid
        self._next_id: int = 0

    def initialize(self) -> bool:
        """Load ROI config and set up finish-line tracker."""
        try:
            if not os.path.exists(self._config_path):
                print(f"⚠️ [{self.module_name}] ROI Config not found: {self._config_path}")
                return False

            with open(self._config_path, 'r') as f:
                data = json.load(f)
                roi_raw = data.get("roi", [])
                self.roi_points = np.array(roi_raw, dtype=np.int32)
                self.gridlock_threshold = data.get("threshold", 6)

            if not self.detector.initialize():
                return False

            # Phase 8: Build finish-line tracker from ROI points
            self._finish_tracker = DirectionFinishTracker(roi_raw)

            self._initialized = True
            print(f"✅ [{self.module_name}] Ready. Threshold: {self.gridlock_threshold}. "
                  f"Finish lines: {list(self._finish_tracker.get_finish_lines().keys())}")
            return True
        except Exception as e:
            print(f"❌ [{self.module_name}] Init Failed: {e}")
            return False

    # ------------------------------------------------------------------ #
    # INTERNAL: assign / update vehicle IDs by nearest centroid           #
    # ------------------------------------------------------------------ #
    def _assign_id(self, cx: int, cy: int) -> int:
        best_id, best_d = None, float("inf")
        for vid, (px, py) in self._tracked_ids.items():
            d = (cx - px) ** 2 + (cy - py) ** 2
            if d < best_d:
                best_d, best_id = d, vid
        if best_id is None or best_d > 80 ** 2:  # 80px threshold
            vid = self._next_id
            self._next_id += 1
        else:
            vid = best_id
        self._tracked_ids[vid] = (cx, cy)
        return vid

    # ------------------------------------------------------------------ #
    # PUBLIC API                                                           #
    # ------------------------------------------------------------------ #
    def detect_status(self, frame: np.ndarray) -> str:
        """
        Returns 'BLOCKED' if vehicles in ROI > threshold, else 'CLEAR'.
        Also updates the finish-line tracker with detected centroids.
        """
        if not self._initialized:
            return "CLEAR"

        res = self.detector.detect(frame)
        detections = res.get("vehicle_detections", [])
        if not detections:
            return "CLEAR"

        count_in_roi = 0
        current_ids = set()

        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            if cv2.pointPolygonTest(self.roi_points, (float(cx), float(cy)), False) >= 0:
                count_in_roi += 1
                if self._finish_tracker:
                    vid = self._assign_id(cx, cy)
                    self._finish_tracker.update(vid, (cx, cy))
                    current_ids.add(vid)

        # Clean up vehicles no longer visible
        gone = set(self._tracked_ids.keys()) - current_ids
        for vid in gone:
            if self._finish_tracker:
                self._finish_tracker.remove_vehicle(vid)
            del self._tracked_ids[vid]

        if count_in_roi > self.gridlock_threshold:
            print(f"🔥 [{self.module_name}] GRIDLOCK! Count: {count_in_roi}")
            return "BLOCKED"
        return "CLEAR"

    def detect_full(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Returns both the intersection status and current directional counts.
        Use this instead of detect_status() when you need both.
        """
        status = self.detect_status(frame)
        return {
            "status": status,
            "directional_counts": self.drain_directional_counts()
        }

    def drain_directional_counts(self) -> Dict[str, int]:
        """
        Called once per heartbeat cycle. Returns and resets directional counts.
        Safe to call even before initialize() — returns empty dict.
        """
        if self._finish_tracker:
            return self._finish_tracker.drain_counts()
        return {"Straight": 0, "Left": 0, "Right": 0, "Back": 0}
