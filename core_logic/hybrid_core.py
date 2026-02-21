import json
import os
import sys
from shapely.geometry import Polygon, Point, box

# Import the existing Grid Core for the 51-100m section
# Ensure we can import from parent directory if running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core_logic.grid_core import GridCore

class HybridCore:
    def __init__(self, phase_name):
        """
        THE HYBRID ENGINE (0-100m) - INDIAN CONTEXT
        - Manages Zone A (51-100m) via GridCore.
        - Manages Zone B (0-50m) internally (Priority Logic).
        - Handles 0.5 Multiplier & Lane Splitting.
        """
        self.phase_name = phase_name
        self.grid_core = GridCore()
        
        # 1. VEHICLE WEIGHTS (Localized for India - Part 9 Spec)
        # Scale: Bus = 80 (Max), Bicycle = 25 (Min)
        # NOTE: Emergency vehicles treated as standard vehicles (Part 9 Scope Exclusion)
        self.VEHICLE_WEIGHTS = {
            "bus": 80,              # High Occupancy (BEST, PMPML, School Bus)
            "truck": 65,            # Heavy Commercial (Logistics)
            "tempo": 55,            # Light Commercial (Chota Hathi, Pickup)
            "car": 50,              # Private Vehicle (Sedan, SUV, Hatchback)
            "auto": 40,             # Auto Rickshaw (Para-transit)
            "motorcycle": 35,       # Two-Wheeler (Bike, Scooty)
            "bicycle": 25,          # Non-motorized
            "default": 50           # Default = Car weight
        }

        # 2. STATE MEMORY (For 0.5 Multiplier Logic)
        self.prev_state_data = {
            "congestion_level": "SAFE", 
            "opened_lanes": []          
        }
        
        # 3. LOAD HYBRID CONFIGURATION
        self.config = self._load_config(phase_name)
        
        # 4. PREPARE 0-50m POLYGON
        if self.config["priority_zone_0_50m"]:
            self.poly_0_50m = Polygon(self.config["priority_zone_0_50m"])
            # Pre-calculate Split Zones for 0-50m
            self.left_lane_poly, self.straight_lane_poly = self._split_zone(self.config["priority_zone_0_50m"])
        else:
            self.poly_0_50m = None
            self.left_lane_poly = None
            self.straight_lane_poly = None

    def _load_config(self, phase):
        """Loads config_Phase_X_Hybrid.json"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(base_path, "config", "Hybrid_Based_System", f"config_Phase_{phase}_Hybrid.json")
        
        if not os.path.exists(filename):
            print(f"⚠️ [HYBRID] Config {filename} not found! Using defaults.")
            return {"priority_zone_0_50m": [], "grid_rows_51_100m": []}
            
        with open(filename, 'r') as f:
            return json.load(f)

    def _split_zone(self, roi_coords):
        """Internal: Splits 0-50m Polygon into Left (35%) and Straight (65%)."""
        poly = Polygon(roi_coords)
        min_x, min_y, max_x, max_y = poly.bounds
        width = max_x - min_x
        
        # Define Split Boundary (35% from Left edge typical for Indian junctions)
        split_x = min_x + (width * 0.35) 
        
        left_lane_poly = box(min_x, min_y, split_x, max_y)
        straight_lane_poly = box(split_x, min_y, max_x, max_y)
        
        return left_lane_poly, straight_lane_poly

    def _get_vehicle_weight(self, class_id):
        """Internal: Returns weight based on localized class ID.
        NOTE: Emergency vehicles (ambulance, police, fire) are treated as standard
        vehicles per Part 9 Scope Exclusion - no special override logic."""
        label = str(class_id).lower()
        
        # Emergency vehicles treated as standard (no override - Part 9)
        if any(x in label for x in ["ambulance", "police", "fire"]): return self.VEHICLE_WEIGHTS["car"]
        if "bus" in label: return self.VEHICLE_WEIGHTS["bus"]
        if "truck" in label: return self.VEHICLE_WEIGHTS["truck"]
        if any(x in label for x in ["tempo", "pickup", "van", "minitruck"]): return self.VEHICLE_WEIGHTS["tempo"]
        if any(x in label for x in ["auto", "rickshaw", "tuk"]): return self.VEHICLE_WEIGHTS["auto"]
        if any(x in label for x in ["bike", "motorcycle", "scooty", "scooter"]): return self.VEHICLE_WEIGHTS["motorcycle"]
        if "bicycle" in label or "cyclist" in label: return self.VEHICLE_WEIGHTS["bicycle"]
        
        return self.VEHICLE_WEIGHTS["default"]

    def _parse_vehicle(self, v):
        """Helper to safely extract [x,y,w,h] and class_id from list OR dict."""
        if isinstance(v, dict):
            # Dict Format from DetectionController
            bbox = v.get("bbox_coordinates", [0,0,0,0])
            class_id = v.get("vehicle_type", "car")
            if "confidence_score" in v:
                conf = v["confidence_score"]
            else:
                conf = 0.5
        else:
            # List Format [x, y, w, h, class_id, conf]
            bbox = v[0:4]
            class_id = v[4] if len(v) > 4 else "car"
            conf = v[5] if len(v) > 5 else 0.5
            
        return bbox, class_id, conf

    def update_state(self, congestion_level, opened_lanes):
        """Updates the Context for the 0.5 Multiplier Logic."""
        self.prev_state_data["congestion_level"] = congestion_level
        self.prev_state_data["opened_lanes"] = opened_lanes

    def _calculate_0_50m_priority(self, vehicles):
        """Calculates weights for 0-50m zone and applies the 0.5 Multiplier."""
        raw_score_left = 0
        raw_score_straight = 0
        
        for v in vehicles:
            bbox, class_id, _ = self._parse_vehicle(v)
            weight = self._get_vehicle_weight(class_id)
            
            # Check Center Point
            center_x = bbox[0] + bbox[2]/2
            center_y = bbox[1] + bbox[3]/2
            veh_point = Point(center_x, center_y)
            
            # Sum Weights based on Sub-Lane
            if self.left_lane_poly and self.left_lane_poly.contains(veh_point):
                raw_score_left += weight
            elif self.straight_lane_poly and self.straight_lane_poly.contains(veh_point):
                raw_score_straight += weight

        # --- THE MULTIPLIER LOGIC ---
        left_lane_id = f"{self.phase_name}_Left" 
        was_open = left_lane_id in self.prev_state_data["opened_lanes"]
        
        state = self.prev_state_data["congestion_level"]
        apply_reduction = state in ["SAFE", "LESS_CONGESTION"]

        final_score_left = raw_score_left
        
        if was_open and apply_reduction:
            final_score_left = raw_score_left * 0.5
            print(f"   📉 [LOGIC] Applied 0.5x Multiplier to Left Lane (Old: {raw_score_left}, New: {final_score_left})")
            
        return raw_score_straight, final_score_left

    def process_hybrid_data(self, vehicles, congestion_state, prev_open_lanes):
        """MAIN API: Processes one frame of vehicle data."""
        # 1. Update Context
        self.update_state(congestion_state, prev_open_lanes)
        
        # 2. Split Vehicles into Zones
        vehs_0_50 = []
        vehs_51_100 = []
        
        if self.poly_0_50m:
            for v in vehicles:
                bbox, cid, _ = self._parse_vehicle(v)
                center = Point(bbox[0] + bbox[2]/2, bbox[1] + bbox[3]/2)
                if self.poly_0_50m.contains(center):
                    vehs_0_50.append(v)
                else:
                    vehs_51_100.append(v)
        else:
            vehs_51_100 = vehicles # Fallback

        # 3. Get Grid Grade (51-100m)
        self.grid_core.phases[self.phase_name] = self.config["grid_rows_51_100m"]
        
        grid_input = {self.phase_name: vehs_51_100}
        grid_status = self.grid_core.get_grid_system_status(grid_input)
        
        # Extract RAW VALUES
        phase_data = grid_status.get(self.phase_name, {"grade": "D", "val": 1.0})
        
        # 4. Get Priority Scores (0-50m)
        prio_straight, prio_left = self._calculate_0_50m_priority(vehs_0_50)
        
        # 5. Return Unified Packet
        return {
            "phase": self.phase_name,
            "grid_grade": phase_data["grade"],
            "grid_val": phase_data["val"],
            "priority_straight": prio_straight, 
            "priority_left": prio_left
        }

# --- TEST BLOCK (RUN ME!) ---
if __name__ == "__main__":
    print("\n🚦 --- TESTING HYBRID CORE (INDIAN CONTEXT) ---")
    
    # 1. Initialize
    core = HybridCore("North")
    
    # Check if config exists (Mocking polygons if missing for test)
    if not core.poly_0_50m:
        print("⚠️ Config not found. Creating MOCK 0-50m Zone for testing...")
        core.poly_0_50m = Polygon([[0, 200], [640, 200], [640, 480], [0, 480]])
        core.left_lane_poly, core.straight_lane_poly = core._split_zone([[0, 200], [640, 200], [640, 480], [0, 480]])

    # 2. Create Dummy Vehicles (Format: [x, y, w, h, class_id, conf])
    # Assume 640x480 resolution. 0-50m Zone is Y=200 to 480.
    
    dummy_vehs = [
        # --- 0-50m ZONE (Front) ---
        [50, 250, 40, 40, "auto", 0.9],       # Left Lane (Auto = 12)
        [50, 300, 40, 40, "auto", 0.9],       # Left Lane (Auto = 12)
        [400, 250, 50, 50, "car", 0.9],       # Straight Lane (Car = 15)
        [400, 350, 60, 60, "ambulance", 0.9], # Straight Lane (Ambulance = 300)

        # --- 51-100m ZONE (Back) ---
        [300, 50, 50, 50, "bus", 0.8],        # Grid Zone (Bus)
        [350, 50, 50, 50, "car", 0.8]         # Grid Zone (Car)
    ]
    
    # 3. Test Case A: Normal State (No Multiplier)
    print("\n🧪 TEST CASE A: State = MORE_LESSER_CONGESTION (Full Priority)")
    res_a = core.process_hybrid_data(dummy_vehs, "MORE_LESSER_CONGESTION", ["North_Left"])
    print(f"   ► Grid Grade: {res_a['grid_grade']} (Val: {res_a['grid_val']})")
    print(f"   ► Priority Straight: {res_a['priority_straight']} (Expected: 315 [300+15])")
    print(f"   ► Priority Left:     {res_a['priority_left']} (Expected: 24 [12+12])")

    # 4. Test Case B: Safe State (Multiplier Active)
    print("\n🧪 TEST CASE B: State = SAFE/lesser_congestion (0.5x Multiplier on Left)")
    # We claim 'North_Left' was just open, so it should be punished
    res_b = core.process_hybrid_data(dummy_vehs, "SAFE", ["North_Left"])
    print(f"   ► Priority Left:     {res_b['priority_left']} (Expected: 12.0 [24 * 0.5])")

    print("\n✅ Hybrid Core Test Complete.")