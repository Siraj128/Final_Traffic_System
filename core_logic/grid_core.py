import os
import sys
import json
from shapely.geometry import Polygon, box
import config

# Ensure we can import config from root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class GridCore:
    def __init__(self):
        self.phases = {}
        self.lane_status = {}  # Stores Events: 'NORMAL', 'ACCIDENT', 'STALLED', 'EMERGENCY'
        
        # Load all 4 phase configurations
        for phase in config.LANES:
            self.lane_status[phase] = "NORMAL"
            
            filename = f"config_Phase_{phase}.json"
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    data = json.load(f)
                    raw_rows = data['rows']
                    
                    # --- AUTO-CORRECTION: ENSURE ROW 0 IS FURTHEST (100m) ---
                    if len(raw_rows) > 1:
                        # Compare Y of First Row vs Last Row
                        y_row_0 = raw_rows[0][0][0][0][1] # [Group0][Cell0][Point0][y]
                        y_last = raw_rows[-1][0][0][0][1]
                        
                        # If Row 0 is "Lower" (Higher Y) than Last Row, reverse it
                        if y_row_0 > y_last:
                            raw_rows.reverse()
                            
                    self.phases[phase] = raw_rows
            else:
                # print(f"⚠️ Warning: {filename} not found. Run tools/setup_phase_roi.py first.")
                self.phases[phase] = []

    # --- 1. THE NERVOUS SYSTEM (Event Handler) ---
    def set_lane_event(self, lane, event_type):
        """
        External modules call this to report anomalies.
        event_type: 'NORMAL', 'ACCIDENT', 'STALLED', 'GRIDLOCK', 'EMERGENCY', 'BLIND'
        """
        if lane in self.lane_status:
            self.lane_status[lane] = event_type

    # --- 2. HELPER FUNCTIONS ---
    def _percent_to_value(self, percent):
        """Converts Occupancy % to Priority Value (1.0 - 5.0)"""
        if percent >= 80: return 5.0 # S
        elif percent >= 60: return 4.0 # A
        elif percent >= 40: return 3.0 # B
        elif percent >= 20: return 2.0 # C
        else: return 1.0 # D

    def _value_to_grade(self, value):
        """Converts Final Numeric Score to Letter Grade"""
        if value >= 4.5: return 'S'
        elif value >= 4.0: return 'A'
        elif value >= 3.0: return 'B'
        elif value >= 2.0: return 'C'
        else: return 'D'

    def _calculate_cell_fill(self, cell_poly_coords, vehicles):
        """Calculates % overlap between a cell polygon and vehicle boxes"""
        cell_poly = Polygon(cell_poly_coords)
        if cell_poly.area == 0: return 0.0
        
        occupied_area = 0.0
        for v in vehicles:
            # Vehicle format: [x, y, w, h] OR dict
            if isinstance(v, dict):
                bbox = v.get("bbox_coordinates", [0,0,0,0])
                px, py, pw, ph = bbox
            else:
                px, py, pw, ph = v[:4]
            
            veh_box = box(px, py, px+pw, py+ph)
            
            if cell_poly.intersects(veh_box):
                intersection = cell_poly.intersection(veh_box)
                occupied_area += intersection.area
        
        percent = (occupied_area / cell_poly.area) * 100
        return min(percent, 100.0)

    # --- 3. UNIVERSAL CALCULATOR (The Core Logic) ---
    def _calculate_segment_metrics(self, lane, vehicles, start_row, end_row):
        """
        Returns raw metrics (Average Density %, Average Grade Value) for a specific slice.
        Used by both Grid (0-10) and Priority (0-5) systems.
        """
        if lane not in self.phases: return 0.0, 1.0

        raw_rows = self.phases[lane]
        # Safety Clip
        end_row = min(end_row, len(raw_rows))
        
        target_rows = raw_rows[start_row:end_row]
        if not target_rows: return 0.0, 1.0

        total_grade_value = 0
        total_fill_percent = 0
        cell_count = 0

        for row in target_rows:
            for group in row:
                for cell_poly in group:
                    fill = self._calculate_cell_fill(cell_poly, vehicles)
                    
                    # Accumulate Raw Data
                    total_fill_percent += fill
                    total_grade_value += self._percent_to_value(fill)
                    cell_count += 1
        
        if cell_count == 0: return 0.0, 1.0
        
        # Averages
        avg_density = (total_fill_percent / cell_count) / 100.0 # Normalized 0.0 to 1.0
        avg_grade_val = total_grade_value / cell_count # 1.0 to 5.0
        
        return avg_density, avg_grade_val

    # --- 4. PUBLIC API (The Dual Endpoints) ---

    def get_grid_system_status(self, all_vehicles):
        """
        For GRID SYSTEM (0-100m).
        UPDATED: Now returns a dictionary with both Grade and Raw Value.
        Format: { "North": { "grade": "A", "val": 4.2 }, ... }
        """
        results = {}
        for lane in config.LANES:
            status = self.lane_status.get(lane, "NORMAL")
            
            # Default values
            grade_char = "D"
            grade_val = 1.0

            # 1. Event Handling (Overrides)
            if status == "ACCIDENT":
                grade_char, grade_val = "BLOCK", 0.0
            elif status == "GRIDLOCK":
                grade_char, grade_val = "GRIDLOCK", 5.0
            # NOTE: Emergency vehicle override removed (Part 9 Scope Exclusion)
            # Emergency vehicles are treated as standard traffic
            elif status == "BLIND":
                grade_char, grade_val = "C", 2.0 # Safe default for Blind Camera
            else:
                # 2. Normal Calculation
                # HybridCore injects specific rows (51-100m) before calling this,
                # so 0-10 covers whatever rows are currently loaded in self.phases
                _, grade_val = self._calculate_segment_metrics(lane, all_vehicles.get(lane, []), 0, 10)
                
                if status == "STALLED":
                    # Stalled cars exist, force higher awareness
                    grade_val = max(grade_val, 3.0) 
                    grade_char = f"STALLED ({self._value_to_grade(grade_val)})"
                else:
                    grade_char = self._value_to_grade(grade_val)

            # 3. Return Structured Data
            results[lane] = {
                "grade": grade_char,
                "val": round(grade_val, 2) # Raw float for Hybrid Formula
            }
        return results

    def get_priority_system_data(self, all_vehicles):
        """
        Legacy/Alternative endpoint.
        Returns Raw Data for Formula: Pi = alpha*C + beta*D...
        """
        data = {}
        for lane in config.LANES:
            # Calculate for Rows 0-5
            density, grade_val = self._calculate_segment_metrics(lane, all_vehicles.get(lane, []), 0, 5)
            
            data[lane] = {
                "D_i": density,       # Density (0.0 - 1.0)
                "C_i": grade_val,     # Congestion Severity (1.0 - 5.0)
                "Event": self.lane_status.get(lane, "NORMAL")
            }
        return data

# --- Quick Test Block ---
if __name__ == "__main__":
    core = GridCore()
    dummy_data = { "North": [[100, 100, 50, 50]], "South": [], "East": [], "West": [] }
    
    # Test 1: Grid Status (New Format)
    print(f"Grid Status: {core.get_grid_system_status(dummy_data)}")