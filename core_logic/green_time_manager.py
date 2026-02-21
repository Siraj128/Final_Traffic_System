import config

class GreenTimeManager:
    def __init__(self, cms_connector=None):
        """
        Args:
            cms_connector: Instance of CMSConnector to check for external commands.
        """
        # BASE CONFIGURATION (Standard Day)
        self.BASE_MIN_GREEN = 15
        self.BASE_MAX_GREEN = 45
        
        # ADAPTIVE LIMITS (Context Awareness)
        self.PEAK_THRESHOLD = 2.5   # If Sum(Priority) > 2.5, it's Peak Hour
        self.NIGHT_THRESHOLD = 0.5  # If Sum(Priority) < 0.5, it's Night Mode
        
        # Link to the Network
        self.cms_connector = cms_connector

    def _get_dynamic_limits(self, total_priority):
        """
        Determines G_min and G_max based on Total Traffic Load.
        Solves Case 8 (Peak) and Case 9 (Night).
        """
        # Case 8: Peak Hour (High Load)
        if total_priority > self.PEAK_THRESHOLD:
            return 20, 60 # Long cycles to clear queues
            
        # Case 9: Night Mode (Low Load)
        if total_priority < self.NIGHT_THRESHOLD:
            return 10, 20 # Fast switching, no waiting
            
        # Standard Mode
        return self.BASE_MIN_GREEN, self.BASE_MAX_GREEN

    def allocate_green_times(self, priority_scores):
        """
        Input: { 'North': 0.8, 'South': 0.2, ... }
        Output: { 'North': 42, 'South': 15, ... } (Seconds)
        """
        # 1. Calculate Total System Load
        # We sum only positive priorities (ignore -1.0 Blocked, 1000 Emergency)
        valid_scores = {k: v for k, v in priority_scores.items() if 0 < v < 100}
        total_priority = sum(valid_scores.values())
        
        # 2. Get Context-Aware Limits
        g_min, g_max = self._get_dynamic_limits(total_priority)
        
        green_times = {}
        
        # 3. Apply Formula for Each Lane
        for lane, p_i in priority_scores.items():
            
            # --- HANDLING CRITICAL OVERRIDES ---
            # NOTE: Emergency vehicle override removed (Part 9 Scope Exclusion)
            # Emergency vehicles are treated as standard traffic
                
            # Blocked / Gridlock (Priority 0 or -1) -> Red Light
            if p_i <= 0.0:
                green_times[lane] = 0
                continue
                
            # --- STANDARD CALCULATION ---
            if total_priority == 0:
                ratio = 0
            else:
                ratio = p_i / total_priority
                
            # Formula: G_i = G_min + (Ratio * Range)
            calc_time = g_min + (ratio * (g_max - g_min))
            
            # --- STEP 4: APPLY CMS THROTTLING (The "Gating" Logic) ---
            # [cite_start]This is the "Congestion Control" Feature [cite: 643-661]
            if self.cms_connector:
                override = self.cms_connector.get_active_override(lane)
                
                if override and override.get("action") == "REDUCE_GREEN":
                    reduction = override.get("value", 0)
                    original_time = calc_time
                    calc_time -= reduction
                    
                    # Log the intervention
                    if calc_time != original_time:
                         print(f"🛑 SMART-NET: Throttled {lane} by {reduction}s (CMS Command)")

            # Safety Clamp: Never go below 5 seconds (Drivers get confused)
            calc_time = max(calc_time, 5)
            
            # Round to nearest second
            green_times[lane] = int(calc_time)
            
        return green_times