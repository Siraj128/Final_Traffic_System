import json
import os
import config
from collections import deque
from core_logic.hybrid_core import HybridCore
from core_logic.traffic_standards import classify_state

class DecisionMaker:
    def __init__(self):
        """
        THE BRAIN (Decision Maker)
        - Manages 4 Hybrid Cores (N, S, E, W).
        - Determines Global Congestion State (Safe / Lesser / More Lesser).
        - Calculates Composite Scores & Adaptive Green Times.
        """
        # 1. CONFIGURATION
        self.G_MIN = 15  # Minimum Green Time (seconds)
        self.G_MAX = 90  # Maximum Green Time (seconds)
        self.GRID_SCALAR = 100 # Multiplier to scale Grid Value (1.0-5.0) to Priority Scale (100-500)
        
        # 2. STATE MEMORY
        # "SAFE" = High Congestion (Strict Logic, 0.5 multiplier active)
        # "LESS_CONGESTION" = Medium (0.5 multiplier active)
        # "MORE_LESSER_CONGESTION" = Low (No multiplier, free flow)
        self.current_state = "SAFE" 
        self.prev_open_lanes = [] # Tracks which lanes were open in last cycle

        # 3. INITIALIZE HYBRID CORES (Per Phase)
        print("   🧠 [INIT] Initializing Hybrid Cores...")
        self.hybrid_cores = {
            "North": HybridCore("North"),
            "South": HybridCore("South"),
            "East":  HybridCore("East"),
            "West":  HybridCore("West")
        }

        # 4. HISTORY (For CMS Gridlock Detection)
        self.cycle_history = {
            "North": deque(maxlen=4), "South": deque(maxlen=4),
            "East": deque(maxlen=4),  "West": deque(maxlen=4)
        }

        # 5. LAST DETAILS (shared with background heartbeat loop for real saturation)
        self.last_details = {}

        # 6. LANE COMBINATIONS (Conflict Matrix - Part 9)
        self._load_lane_combinations()

    def _load_lane_combinations(self):
        """Loads the lane conflict matrix from config/lane_combinations.json."""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        combo_path = os.path.join(base_path, "config", "lane_combinations.json")
        
        if os.path.exists(combo_path):
            with open(combo_path, 'r') as f:
                self.lane_combinations = json.load(f)
            print("   🧠 [INIT] Lane Combinations loaded.")
        else:
            print("   ⚠️ [INIT] lane_combinations.json not found! Using default (winner only).")
            self.lane_combinations = {}

    def _determine_next_state(self, avg_saturation):
        """
        Decides the Global State for the NEXT cycle based on average saturation.
        Uses traffic_standards.classify_state() for consistent thresholds.
        
        Args:
            avg_saturation: float 0.0-1.0 representing average lane density
        """
        return classify_state(avg_saturation)

    def _get_allowed_lanes(self, winner_phase, state):
        """
        Looks up the lane conflict matrix to determine which lanes can
        safely open alongside the winner phase.
        
        Args:
            winner_phase: str ("North", "South", "East", "West")
            state: str ("SAFE", "LESS_CONGESTION", "MORE_LESSER_CONGESTION")
        Returns:
            list of allowed lane names
        """
        if not self.lane_combinations:
            # Fallback: only winner's lanes
            return [f"{winner_phase}_All"]
        
        phase_combos = self.lane_combinations.get(winner_phase, {})
        return phase_combos.get(state, [f"{winner_phase}_All"])

    def decide_signals(self, vehicle_data):
        """
        MAIN API: Called by main.py
        Args:
            vehicle_data: Dict { "North": [vehicle_list], "South": ... }
        Returns:
            { "priority_scores": ..., "allocated_times": ..., "system_state": ... }
        """
        raw_scores = {}
        meta_data = {}
        total_p = 0
        
        # --- STEP 1: GATHER SCORES FROM HYBRID CORES ---
        for phase_name, core in self.hybrid_cores.items():
            vehs = vehicle_data.get(phase_name, [])
            
            # CALL HYBRID CORE
            # Pass current state so it knows whether to apply 0.5 multiplier
            data = core.process_hybrid_data(vehs, self.current_state, self.prev_open_lanes)
            
            # --- STEP 2: COMPOSITE FORMULA ---
            # Composite = (Grid_Val * 100) + P_Straight + P_Left
            grid_score = data['grid_val'] * self.GRID_SCALAR
            p_straight = data['priority_straight']
            p_left = data['priority_left'] # Already adjusted by HybridCore logic
            
            composite_score = grid_score + p_straight + p_left
            
            # Store Results
            raw_scores[phase_name] = int(composite_score)
            total_p += composite_score
            
            # Save Metadata for GUI/Debugging
            meta_data[phase_name] = {
                "Grid_Raw": data['grid_val'],
                "Grid_Score": int(grid_score),
                "P_Str": p_straight,
                "P_Left": p_left,
                "Final": int(composite_score)
            }

        # --- STEP 3: ADAPTIVE GREEN TIME CALCULATION ---
        # Formula: Gi = Gmin + (Pi / Total_P) * (Gmax - Gmin)
        green_times = {}
        if total_p == 0:
            # Fallback for empty road
            for p in self.hybrid_cores: green_times[p] = self.G_MIN
        else:
            for phase, p_score in raw_scores.items():
                ratio = p_score / total_p
                variable_time = ratio * (self.G_MAX - self.G_MIN)
                final_time = self.G_MIN + variable_time
                green_times[phase] = int(final_time)

        # --- STEP 4: UPDATE STATE FOR NEXT CYCLE ---
        # Calculate average saturation across all phases for state classification
        # Saturation is derived from grid values: grid_val is 1.0-5.0, map to 0.0-1.0
        avg_saturation = 0.0
        if meta_data:
            grid_vals = [d['Grid_Raw'] for d in meta_data.values()]
            # Map grid_val (1.0-5.0) to saturation (0.0-1.0)
            avg_saturation = sum((v - 1.0) / 4.0 for v in grid_vals) / len(grid_vals)
        
        self.current_state = self._determine_next_state(avg_saturation)
        
        # Determine winner and allowed lanes from conflict matrix
        winner_phase = max(raw_scores, key=raw_scores.get)
        allowed_lanes = self._get_allowed_lanes(winner_phase, self.current_state)
        self.prev_open_lanes = allowed_lanes

        # Store for background heartbeat loop (real per-phase saturation)
        self.last_details = meta_data

        # Update History for CMS
        self.update_history(green_times)

        return {
            "priority_scores": raw_scores,
            "allocated_times": green_times,
            "system_state": self.current_state,
            "details": meta_data
        }

    # --- CMS SUPPORT METHODS ---
    def update_history(self, green_times):
        """Updates cyclic memory for Gridlock Detection."""
        for lane, time_val in green_times.items():
            self.cycle_history[lane].append(time_val)

    def calculate_network_saturation(self, lane_name, lane_data_unused):
        """
        CMS Helper: Returns saturation 0-100% based on Decision History.
        """
        history = list(self.cycle_history.get(lane_name, []))
        if not history: return 0.0
        
        avg_time = sum(history) / len(history)
        saturation = ((avg_time - self.G_MIN) / (self.G_MAX - self.G_MIN)) * 100
        return min(max(saturation, 0.0), 100.0)

# --- TEST BLOCK ---
if __name__ == "__main__":
    print("\n🧠 --- TESTING DECISION MAKER (HYBRID INTEGRATION) ---")
    dm = DecisionMaker()
    
    # Mock Vehicle Data
    dummy_data = {
        "North": [[50, 250, 40, 40, "auto", 0.9], [400, 350, 60, 60, "bus", 0.9]], # 1 Auto + 1 Bus
        "South": [[50, 250, 40, 40, "car", 0.9]], # 1 Car
        "East": [],
        "West": []
    }
    
    print(f"\n1. Processing Frame (State: {dm.current_state})...")
    result = dm.decide_signals(dummy_data)
    
    print("\n📊 SCORES:")
    for phase, score in result['priority_scores'].items():
        print(f"   - {phase}: {score}")
        
    print("\n⏱️ ALLOCATED TIMES:")
    for phase, time in result['allocated_times'].items():
        print(f"   - {phase}: {time}s")
        
    print(f"\n🔄 NEXT STATE: {result['system_state']}")