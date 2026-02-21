"""
direction_finish_tracker.py  —  Phase 8
Camera 5 Finish-Line Directional Vehicle Counter

Counts outgoing vehicles by detecting when their centroid path crosses
one of 4 virtual finish lines at the ROI boundary edges:
  - Straight  -> top edge  (vehicles going straight through junction)
  - Left      -> left edge  (vehicles turning left)
  - Right     -> right edge (vehicles turning right)
  - Back      -> bottom edge (vehicles doing U-turns)

Usage:
    tracker = DirectionFinishTracker(roi_points)
    tracker.update(vehicle_id, (cx, cy))   # call each frame per vehicle
    counts = tracker.drain_counts()         # call once per heartbeat cycle
"""
from typing import Dict, Tuple


def _segments_cross(p1, p2, p3, p4) -> bool:
    """True if line segment p1-p2 crosses line segment p3-p4."""
    def _cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    d1 = _cross(p3, p4, p1)
    d2 = _cross(p3, p4, p2)
    d3 = _cross(p1, p2, p3)
    d4 = _cross(p1, p2, p4)

    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    return False


class DirectionFinishTracker:
    """
    Finish-line based directional counter for Camera 5 (Intersection Monitor).

    4 finish lines are derived from the bounding box of the intersection ROI:
        Top edge    -> "Straight"
        Left edge   -> "Left"
        Right edge  -> "Right"
        Bottom edge -> "Back"
    """

    def __init__(self, roi_points: list):
        self._finish_lines = self._build_finish_lines(roi_points)
        self._prev_positions: Dict[int, Tuple[int, int]] = {}
        self._counts: Dict[str, int] = {
            "Straight": 0, "Left": 0, "Right": 0, "Back": 0
        }

    def _build_finish_lines(self, roi_points: list) -> Dict[str, Tuple]:
        if not roi_points:
            return {}
        xs = [p[0] for p in roi_points]
        ys = [p[1] for p in roi_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        return {
            "Straight": ((min_x, min_y), (max_x, min_y)),
            "Left":     ((min_x, min_y), (min_x, max_y)),
            "Right":    ((max_x, min_y), (max_x, max_y)),
            "Back":     ((min_x, max_y), (max_x, max_y)),
        }

    def update(self, vehicle_id: int, centroid: Tuple[int, int]):
        """Call each frame for each detected vehicle."""
        if vehicle_id in self._prev_positions:
            prev = self._prev_positions[vehicle_id]
            for direction, (p3, p4) in self._finish_lines.items():
                if _segments_cross(prev, centroid, p3, p4):
                    self._counts[direction] += 1
                    break  # One crossing per frame per vehicle
        self._prev_positions[vehicle_id] = centroid

    def remove_vehicle(self, vehicle_id: int):
        """Call when a vehicle leaves the frame."""
        self._prev_positions.pop(vehicle_id, None)

    def drain_counts(self) -> Dict[str, int]:
        """
        Returns accumulated directional counts and resets them.
        Call ONCE per heartbeat cycle (~300ms).
        """
        result = dict(self._counts)
        self._counts = {k: 0 for k in self._counts}
        return result

    def get_finish_lines(self) -> Dict[str, Tuple]:
        return self._finish_lines
