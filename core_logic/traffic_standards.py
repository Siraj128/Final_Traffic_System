"""
Traffic Standards Module (Revised - Part 7 Spec)
Role: Single Source of Truth for Traffic Congestion States.
Ensures Hybrid (0-50m) and Grid (51-100m) speak the same language.

State Definitions (Part 7):
- SAFE: High Congestion / High Alert -> Play it safe, restrict lane openings
- LESS_CONGESTION: Moderate traffic -> Balanced, allow calculated risk
- MORE_LESSER_CONGESTION: Light traffic / Free flow -> Open all compatible lanes

NOTE: "SAFE" is counter-intuitive - it means "play it safe because traffic is heavy",
      NOT "the road is safe to drive on."
"""

# Saturation Thresholds (Part 7 Spec)
# Saturation = density % from zone_analyzer (0.0 to 1.0)
THRESHOLDS = {
    "SAFE": 0.50,                     # > 50% saturation -> SAFE (High Alert)
    "LESS_CONGESTION": 0.20,          # 20-50% saturation -> LESS_CONGESTION (Moderate)
    # < 20% saturation -> MORE_LESSER_CONGESTION (Free Flow)
}


def classify_state(saturation: float) -> str:
    """
    Universal classifier for Saturation/Density.
    
    Args:
        saturation: float between 0.0 and 1.0 representing lane occupancy
        
    Returns:
        str: "SAFE", "LESS_CONGESTION", or "MORE_LESSER_CONGESTION"
        
    Rules (Part 7):
        > 50%  -> SAFE (High congestion, be strict)
        20-50% -> LESS_CONGESTION (Moderate, calculated risks)
        < 20%  -> MORE_LESSER_CONGESTION (Light, open everything)
    """
    if saturation > THRESHOLDS["SAFE"]:
        return "SAFE"                         # High Alert - restrict lanes
    elif saturation > THRESHOLDS["LESS_CONGESTION"]:
        return "LESS_CONGESTION"              # Moderate - balanced
    else:
        return "MORE_LESSER_CONGESTION"       # Free flow - open all


# --- Legacy Alias (for backward compatibility) ---
def get_congestion_state(density: float) -> str:
    """Legacy wrapper. Use classify_state() for new code."""
    return classify_state(density)