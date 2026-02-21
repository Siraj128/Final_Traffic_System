# config.py

# --- Physical Constants ---
LANES = ["North", "South", "East", "West"]
GRID_ROWS_TOTAL = 10      # We draw 10 rows of 10m each
GRID_GROUPS_WIDTH = 3     # 3 Groups across width
GRID_SUBCELLS = 4         # 4 Cells per group (2x2)

# --- Grading Thresholds (Occupancy % -> Value) ---
#
CELL_GRADE_MAP = {
    80: 5.0, # S
    60: 4.0, # A
    40: 3.0, # B
    20: 2.0, # C
    0:  1.0  # D
}

# --- Final Grade Thresholds (Value -> Letter) ---
FINAL_GRADE_THRESHOLDS = [
    (5.0, 'S'),
    (4.0, 'A'),
    (3.0, 'B'),
    (2.0, 'C'),
    (1.0, 'D')
]

# --- Signal Timing Constants (Part 6: Temporal Logic) ---
GREEN_MIN = 15            # Minimum green time (seconds)
GREEN_MAX = 90            # Maximum green time (seconds)
YELLOW_DURATION = 15      # Fixed yellow phase duration (seconds)
FREEZE_OFFSET = 3         # Seconds before green ends: snapshot state
DEADLINE_OFFSET = 10      # Seconds remaining in yellow: calculation must be done
# Processing Window = YELLOW_DURATION - DEADLINE_OFFSET = 5 seconds