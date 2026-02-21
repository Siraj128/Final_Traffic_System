"""
Lane Mapper Module - Optimized for Edge (Level 5)
Features:
1. Zero-Dependency Geometry (No Shapely) - Uses OpenCV C++ backend.
2. Native JSON Support - Parses 'Grid' and 'Hybrid' config files directly.
3. Sub-Lane Logic - Uses Vector Math to split Priority Zones (Left vs Straight).
"""

from typing import Dict, List, Tuple, Any, Optional, Union
import cv2
import numpy as np
import traceback

# Utils
try:
    from ..utils.logger import log_info, log_error
except ImportError:
    def log_info(msg, src): print(f"ℹ️ [{src}] {msg}")
    def log_error(msg, src): print(f"❌ [{src}] {msg}")

class LaneMapper:
    """
    High-Performance Geometry Engine.
    Maps points to Polygons (Lanes/Zones) using cv2.pointPolygonTest.
    """
    
    def __init__(self, resolution: Tuple[int, int] = (1280, 720)):
        self.module_name = "LANE_MAPPER"
        self.resolution = resolution
        
        # Structure: { "Phase_Name": { "type": "hybrid/grid", "polys": [...], "split_line": ... } }
        self.phase_maps = {} 
        self._initialized = False

    def initialize(self, configs: Union[Dict, List[Dict]]) -> bool:
        """
        Loads lane configurations from parsed JSON files.
        Supports both 'Grid' and 'Hybrid' JSON formats.
        
        Args:
            configs: A single config dict OR a list of config dicts (one per phase).
        """
        try:
            log_info("🔄 Initializing Lane Mapper with Native JSON support...", self.module_name)
            self.phase_maps = {}
            
            # Normalize to list
            if isinstance(configs, dict): configs = [configs]
            
            for cfg in configs:
                # 1. Identify Phase & Type
                phase_id = cfg.get("phase_name") or cfg.get("phase_id", "Unknown")
                
                # Container for this phase
                phase_data = {
                    "priority_poly": None,    # The 0-50m Zone (Contour)
                    "split_line": None,       # The dividing line [[x1,y1], [x2,y2]]
                    "grid_cells": []          # List of (ID, Contour)
                }

                # --- PARSE HYBRID SYSTEM (0-50m) ---
                if "priority_zone_0_50m" in cfg:
                    raw_points = cfg["priority_zone_0_50m"]
                    if raw_points:
                        phase_data["priority_poly"] = np.array(raw_points, dtype=np.int32)
                
                if "split_line_0_50m" in cfg:
                    phase_data["split_line"] = cfg["split_line_0_50m"]

                # --- PARSE GRID SYSTEM (51-100m) ---
                # Key can be 'rows' (Grid JSON) or 'grid_rows_51_100m' (Hybrid JSON)
                grid_rows = cfg.get("rows") or cfg.get("grid_rows_51_100m")
                
                if grid_rows:
                    # Iterate nested structure: Rows -> Cells -> Points
                    for r_idx, row in enumerate(grid_rows):
                        for c_idx, cell_points in enumerate(row):
                            # Handle various nesting levels in JSON
                            # We expect cell_points to be a list of [x,y]
                            try:
                                # Recursively find the list of points if deeply nested
                                poly_pts = self._extract_points(cell_points)
                                if len(poly_pts) >= 3:
                                    cell_id = f"{phase_id}_Grid_R{r_idx}_C{c_idx}"
                                    contour = np.array(poly_pts, dtype=np.int32)
                                    phase_data["grid_cells"].append((cell_id, contour))
                            except Exception:
                                continue

                self.phase_maps[phase_id] = phase_data
                log_info(f"   ✅ Loaded Phase: {phase_id} (Priority: {'Yes' if phase_data['priority_poly'] is not None else 'No'}, Grid Cells: {len(phase_data['grid_cells'])})", self.module_name)

            self._initialized = True
            return True
            
        except Exception as e:
            log_error(f"LaneMapper Init Failed: {e}", self.module_name)
            traceback.print_exc()
            return False

    def assign_lanes(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Maps vehicles to lanes.
        Priority: 
        1. Check Priority Zone (0-50m). If inside, apply Split Logic (Left/Straight).
        2. If not, check Grid Cells (51-100m).
        """
        if not self._initialized: return []

        # Prepare Result Container
        # We group by "lane_id" (e.g., "East_Left", "East_Straight", "East_Grid_R0_C1")
        lane_groups = {} 

        for det in detections:
            # 1. Get Centroid
            if "centroid" in det:
                cx, cy = det["centroid"]
            else:
                bbox = det.get("bbox_coordinates", det.get("bbox", [0,0,0,0]))
                cx = (bbox[0] + bbox[2]) // 2
                cy = (bbox[1] + bbox[3]) // 2
                det["centroid"] = (cx, cy)

            matched_lane_id = None
            point = (float(cx), float(cy))

            # 2. Iterate Phases
            for phase_id, p_data in self.phase_maps.items():
                
                # A. CHECK PRIORITY ZONE (0-50m) - FASTEST
                if p_data["priority_poly"] is not None:
                    # pointPolygonTest: >0 Inside, =0 On Edge, <0 Outside
                    if cv2.pointPolygonTest(p_data["priority_poly"], point, False) >= 0:
                        
                        # Apply Split Logic (Left vs Straight)
                        if p_data["split_line"]:
                            side = self._check_side(point, p_data["split_line"])
                            # Convention: You might need to invert this based on your specific camera angle
                            # For now: Side A = Left, Side B = Straight
                            if side > 0:
                                matched_lane_id = f"{phase_id}_Left"
                            else:
                                matched_lane_id = f"{phase_id}_Straight"
                        else:
                            matched_lane_id = f"{phase_id}_Priority"
                        
                        break # Found match, stop searching

                # B. CHECK GRID ZONES (51-100m)
                # Only check if not found in priority (assuming strict z-ordering)
                if matched_lane_id is None:
                    for cell_id, contour in p_data["grid_cells"]:
                        if cv2.pointPolygonTest(contour, point, False) >= 0:
                            matched_lane_id = cell_id
                            # We could break here, or keep checking if overlaps exist
                            # Breaking for speed
                            break
                
                if matched_lane_id: break

            # 3. Assign
            if matched_lane_id:
                det["lane_id"] = matched_lane_id
                if matched_lane_id not in lane_groups: lane_groups[matched_lane_id] = []
                lane_groups[matched_lane_id].append(det)
            else:
                det["lane_id"] = None

        # 4. Format Output
        results = []
        for lid, vehicles in lane_groups.items():
            results.append({
                "lane_id": lid,
                "vehicle_count": len(vehicles),
                "vehicles": vehicles
            })
            
        return results

    def _check_side(self, point, line_coords):
        """
        Uses Cross Product to determine which side of the line a point is on.
        Line: A -> B. Point: P.
        Cross = (Bx - Ax)*(Py - Ay) - (By - Ay)*(Px - Ax)
        """
        try:
            A = line_coords[0]
            B = line_coords[1]
            P = point
            
            # Vector AB
            AB_x = B[0] - A[0]
            AB_y = B[1] - A[1]
            
            # Vector AP
            AP_x = P[0] - A[0]
            AP_y = P[1] - A[1]
            
            # Cross Product 2D
            cross = (AB_x * AP_y) - (AB_y * AP_x)
            return cross
        except:
            return 0

    def _extract_points(self, data):
        """Helper to flatten nested lists into a simple point list."""
        # This handles the deep nesting in the Grid JSON: [[[[x,y],...]]]
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], (int, float)):
                return [data] # It's a single point [x,y]
            
            points = []
            for item in data:
                points.extend(self._extract_points(item))
            return points
        return []

    def draw_lanes(self, frame: np.ndarray, lane_results: List[Dict[str, Any]] = None, detect_mode: str = "HYBRID") -> None:
        """
        Visualizes the Polygons + Split Lines.
        """
        if not self._initialized: 
            return

        for phase_id, p_data in self.phase_maps.items():
            # 1. Draw Grid Cells (Blue) - Always Draw 
            for cell_id, contour in p_data["grid_cells"]:
                cv2.polylines(frame, [contour], True, (255, 100, 0), 1)
            
            # 2. Draw Priority Zone (Yellow) - ONLY IN HYBRID MODE
            if detect_mode == "HYBRID" and p_data["priority_poly"] is not None:
                cv2.polylines(frame, [p_data["priority_poly"]], True, (0, 255, 255), 2)
                
                # 3. Draw Split Line (Red)
                if p_data["split_line"]:
                    try:
                        pt1 = (int(p_data["split_line"][0][0]), int(p_data["split_line"][0][1]))
                        pt2 = (int(p_data["split_line"][1][0]), int(p_data["split_line"][1][1]))
                        cv2.line(frame, pt1, pt2, (0, 0, 255), 2)
                        
                        # Label
                        mid = ((pt1[0]+pt2[0])//2, (pt1[1]+pt2[1])//2)
                        cv2.putText(frame, "SPLIT", mid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)
                    except (IndexError, TypeError, ValueError):
                        pass

            # 4. Draw Counts if provided
            if lane_results:
                for grp in lane_results:
                    lid = grp.get('lane_id')
                    count = grp.get('vehicle_count', 0)
                    
                    # Only draw if it belongs to this phase
                    if lid and str(lid).startswith(str(phase_id)):
                        font_scale = 0.6
                        if p_data["priority_poly"] is not None:
                            # Get bounding rect of the priority zone
                            x, y, w, h = cv2.boundingRect(p_data["priority_poly"])
                            label = f"{lid}: {count}"
                            
                            color = (0, 255, 255) if "Left" in str(lid) else (0, 255, 0)
                            # Offset Y based on lane type
                            text_y = y - 10 if "Left" in str(lid) else y - 30
                            cv2.putText(frame, label, (x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)
                        else:
                            # Fallback for Grid logic
                            for cell_id, contour in p_data["grid_cells"]:
                                if cell_id == lid:
                                    x, y, w, h = cv2.boundingRect(contour)
                                    cv2.putText(frame, str(count), (x, y+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                                    break
        return