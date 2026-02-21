import cv2
import json
import numpy as np
import os
import sys

# Try to import config, else use defaults
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import config
    GROUPS_WIDTH = config.GRID_GROUPS_WIDTH
except:
    GROUPS_WIDTH = 3 # Default to 3 lanes if config fails

# --- CONFIGURATION ---
VIDEO_SOURCE = os.path.join(os.path.dirname(__file__), "south.mp4") 
PHASE_NAME = "South" 
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', f"config_Phase_{PHASE_NAME}_Hybrid.json")

# --- GLOBAL STATE ---
drawing_mode = "grid" # Options: 'grid', 'priority', 'split', 'done'
points = []
current_frame = None
grid_rows = []
row_counter = 1
prev_row_bottom = None
priority_poly = []
split_line = []

def interpolate(p1, p2, div):
    return [ (int(p1[0] + (p2[0]-p1[0])*i/div), int(p1[1] + (p2[1]-p1[1])*i/div)) for i in range(int(div)+1) ]

def process_row_grid(corners):
    tl, tr, br, bl = corners
    row_data = []
    top_edge = interpolate(tl, tr, GROUPS_WIDTH)
    bot_edge = interpolate(bl, br, GROUPS_WIDTH)

    for g in range(GROUPS_WIDTH):
        group_data = []
        g_tl, g_tr = top_edge[g], top_edge[g+1]
        g_bl, g_br = bot_edge[g], bot_edge[g+1]
        sub_left = interpolate(g_tl, g_bl, 2)
        sub_right = interpolate(g_tr, g_br, 2)
        for i in range(2):
            sub_top = interpolate(sub_left[i], sub_right[i], 2)
            sub_bot = interpolate(sub_left[i+1], sub_right[i+1], 2)
            for j in range(2):
                c_tl, c_tr = sub_top[j], sub_top[j+1]
                c_bl, c_br = sub_bot[j], sub_bot[j+1]
                cell_poly = [[int(x), int(y)] for x, y in [c_tl, c_tr, c_br, c_bl]]
                group_data.append(cell_poly)
        row_data.append(group_data)
    return row_data

def mouse_callback(event, x, y, flags, param):
    global points, grid_rows, row_counter, prev_row_bottom, priority_poly, split_line, drawing_mode

    if event == cv2.EVENT_LBUTTONDOWN:
        # --- MODE 1: GRID ZONE (51-100m) ---
        if drawing_mode == "grid":
            points_needed = 4 if row_counter == 1 else 2
            if len(points) < points_needed:
                points.append((x, y))
                if len(points) == points_needed:
                    final_corners = []
                    if row_counter == 1:
                        final_corners = points
                        prev_row_bottom = (points[3], points[2]) 
                    else:
                        prev_bl, prev_br = prev_row_bottom
                        new_br, new_bl = points[0], points[1]
                        final_corners = [prev_bl, prev_br, new_br, new_bl]
                        prev_row_bottom = (new_bl, new_br)

                    cells = process_row_grid(final_corners)
                    grid_rows.append({"row_index": row_counter, "corners": final_corners, "grid_data": cells})
                    print(f"[OK] Grid Row {row_counter} Added.")
                    row_counter += 1
                    points = []

        # --- MODE 2: PRIORITY ZONE (0-50m) ---
        elif drawing_mode == "priority":
            points.append((x, y))

        # --- MODE 3: SPLIT LINE ---
        elif drawing_mode == "split":
            points.append((x, y))
            if len(points) == 2:
                split_line = points.copy()
                print("[OK] Split Line Set.")
                save_config()
                drawing_mode = "done"

    elif event == cv2.EVENT_RBUTTONDOWN:
        if drawing_mode == "priority" and len(points) > 2:
            priority_poly = points.copy()
            print("[OK] Priority Zone Polygon Saved.")
            points = []
            drawing_mode = "split"
            print("\n[STEP 3] Draw Split Line (Click Top then Bottom point of the lane divider).")

def save_config():
    data = {
        "phase_name": PHASE_NAME,
        "grid_rows_51_100m": [r['grid_data'] for r in grid_rows], 
        "priority_zone_0_50m": priority_poly,
        "split_line_0_50m": split_line
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"\n[SAVED] CONFIG SAVED: {OUTPUT_FILE}")
    print("Press 'q' to exit.")

def main():
    global current_frame, drawing_mode, points
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    ret, frame = cap.read()
    if not ret: print("Error reading video"); return
    cap.release()
    
    current_frame = frame.copy()
    cv2.namedWindow("Hybrid Setup")
    cv2.setMouseCallback("Hybrid Setup", mouse_callback)
    
    print(f"--- HYBRID SETUP: {PHASE_NAME} ---")
    print("👉 [STEP 1] Draw Grid Rows (Top Half Only). Press 'n' when done.")

    while True:
        display = current_frame.copy()

        # Visual Guide Line (Rough 50% mark)
        h, w = display.shape[:2]
        cv2.line(display, (0, h//2), (w, h//2), (0, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(display, "Approx 50m Line", (10, h//2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Draw Grid
        for row in grid_rows:
            pts = np.array(row['corners'], np.int32)
            cv2.polylines(display, [pts], True, (255, 0, 0), 2)
            for group in row['grid_data']:
                for cell in group:
                    c_pts = np.array(cell, np.int32)
                    cv2.polylines(display, [c_pts], True, (255, 100, 0), 1)

        # Draw Priority Poly
        if len(priority_poly) > 0:
            pts = np.array(priority_poly, np.int32)
            cv2.polylines(display, [pts], True, (0, 255, 0), 2)
            overlay = display.copy()
            cv2.fillPoly(overlay, [pts], (0, 255, 0))
            cv2.addWeighted(overlay, 0.2, display, 0.8, 0, display)
        elif drawing_mode == "priority" and len(points) > 0:
             pts = np.array(points, np.int32)
             cv2.polylines(display, [pts], False, (0, 255, 0), 1)

        # Draw Split Line
        if len(split_line) == 2:
            cv2.line(display, split_line[0], split_line[1], (0, 0, 255), 3)
        elif drawing_mode == "split" and len(points) > 0:
            for p in points: cv2.circle(display, p, 5, (0, 0, 255), -1)

        # Active Drawing
        if drawing_mode == "grid" and len(points) > 0:
            for p in points: cv2.circle(display, p, 4, (0, 255, 255), -1)
            if row_counter == 1 and len(points) > 1:
                 cv2.line(display, points[-2], points[-1], (0,255,0), 1)
            elif row_counter > 1 and len(points) == 1:
                 prev_br = prev_row_bottom[1]
                 cv2.line(display, prev_br, points[0], (0,255,0), 1)

        # Instructions
        status = f"MODE: {drawing_mode.upper()}"
        if drawing_mode == "grid": status += f" | Row {row_counter}"
        cv2.putText(display, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.imshow("Hybrid Setup", display)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('n') and drawing_mode == "grid":
            if len(grid_rows) > 0:
                print("✅ Grid Finished. Switching to Priority Zone.")
                drawing_mode = "priority"
                points = []
            else:
                print("⚠️ Draw at least 1 row first!")
        elif key == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()