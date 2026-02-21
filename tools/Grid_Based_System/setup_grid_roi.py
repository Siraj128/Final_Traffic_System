# Fix path to import config from parent directory
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))    
import cv2
import json
import numpy as np
import config

# Global State
points = []
phase_rows = []
row_counter = 1
prev_row_bottom = None
current_frame = None

def click_event(event, x, y, flags, params):
    global points, current_frame, row_counter, prev_row_bottom

    # --- FIX: HARD STOP AT 10 ROWS ---
    if row_counter > 10:
        print("⛔ MAX LIMIT REACHED (10 Rows). Press 'S' to Save.")
        return

    # Row 1 needs 4 points. Subsequent rows need 2.
    points_needed = 4 if row_counter == 1 else 2

    if event == cv2.EVENT_LBUTTONDOWN and len(points) < points_needed:
        points.append((x, y))
        
        # Visual: Red Circle
        cv2.circle(current_frame, (x, y), 5, (0, 0, 255), -1)
        
        # Visual: Connect Lines Logic
        if row_counter == 1:
            if len(points) > 1:
                cv2.line(current_frame, points[-2], points[-1], (0, 255, 0), 2)
            if len(points) == 4: # Close Box
                cv2.line(current_frame, points[-1], points[0], (0, 255, 0), 2)
        else:
            prev_bl, prev_br = prev_row_bottom
            if len(points) == 1: # Connect New BR to Old BR
                cv2.line(current_frame, prev_br, points[0], (0, 255, 0), 2)
            if len(points) == 2: # Connect New BL to New BR & Old BL
                cv2.line(current_frame, points[0], points[1], (0, 255, 0), 2)
                cv2.line(current_frame, points[1], prev_bl, (0, 255, 0), 2)

        cv2.imshow('Phase ROI Setup', current_frame)

def interpolate(p1, p2, div):
    return [ (p1[0] + (p2[0]-p1[0])*i/div, p1[1] + (p2[1]-p1[1])*i/div) for i in range(int(div)+1) ]

def process_row_grid(corners):
    """Calculates the 3 Groups -> 4 Cells structure for a single row"""
    tl, tr, br, bl = corners
    row_data = []

    # 1. Divide Width (3 Groups)
    top_edge = interpolate(tl, tr, config.GRID_GROUPS_WIDTH)
    bot_edge = interpolate(bl, br, config.GRID_GROUPS_WIDTH)

    for g in range(config.GRID_GROUPS_WIDTH):
        group_data = []
        g_tl, g_tr = top_edge[g], top_edge[g+1]
        g_bl, g_br = bot_edge[g], bot_edge[g+1]

        # 2. Divide Group into 4 Sub-Cells (2x2)
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

def main(video_path, phase_id):
    global current_frame, points, row_counter, prev_row_bottom, phase_rows
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Cannot open {video_path}")
        return

    print(f"--- SETUP FOR PHASE: {phase_id} ---")
    print(f"Video: {video_path}")
    print("1. Pause (SPACE). 2. Draw 10 Rows (Click/N). 3. Save (S).")

    paused = False

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret: cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
            current_frame = frame.copy()
            
            # Draw Confirmed Rows
            for row in phase_rows:
                pts = np.array(row['corners'], np.int32)
                cv2.polylines(current_frame, [pts], True, (255, 0, 0), 2)
        
        # Overlay Status Text
        status_text = f"PHASE: {phase_id} | ROW: {row_counter}/10"
        if row_counter > 10:
            status_text = "DONE! Press 'S' to SAVE."
            
        cv2.putText(current_frame, status_text, (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow('Phase ROI Setup', current_frame)
        cv2.setMouseCallback('Phase ROI Setup', click_event)
        
        key = cv2.waitKey(30) & 0xFF
        
        if key == ord(' '): paused = not paused
        
        elif key == ord('n'): # NEXT ROW
            if row_counter > 10:
                print("Already finished 10 rows. Press 'S' to save.")
                continue

            points_needed = 4 if row_counter == 1 else 2
            
            if len(points) == points_needed:
                final_corners = []
                if row_counter == 1:
                    final_corners = points
                    prev_row_bottom = (points[3], points[2]) # BL, BR
                else:
                    prev_bl, prev_br = prev_row_bottom
                    new_br, new_bl = points[0], points[1]
                    final_corners = [prev_bl, prev_br, new_br, new_bl]
                    prev_row_bottom = (new_bl, new_br)

                # Generate Grid Data
                grid_cells = process_row_grid(final_corners)
                
                phase_rows.append({
                    "row_index": row_counter,
                    "corners": final_corners,
                    "grid_data": grid_cells
                })
                
                print(f"✅ Row {row_counter} Captured.")
                row_counter += 1
                points = []

                if row_counter > 10:
                    print("🎉 All 10 Rows Captured! Press 'S' to Save.")
            else:
                print(f"❌ Need {points_needed} points.")

        elif key == ord('s'): # SAVE
            if row_counter > 10:
                output_data = {
                    "phase_id": phase_id,
                    "video_source": video_path,
                    "rows": [r['grid_data'] for r in phase_rows]
                }
                
                filename = f"config_{phase_id}.json"
                with open(filename, 'w') as f:
                    json.dump(output_data, f, indent=4)
                
                print(f"✅ Configuration saved to {filename}")
                break
            else:
                print(f"❌ Incomplete! You are only on Row {row_counter}/10")

        elif key == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Usage: python setup_phase_roi.py <video_file> <phase_name>
    # Example: python setup_phase_roi.py north_feed.mp4 Phase_North
    if len(sys.argv) < 3:
        print("Usage: python tools/setup_phase_roi.py <video_path> <phase_id>")
        # Default for testing if run directly without args
        # main("north.mp4", "Phase1_North") 
    else:
        main(sys.argv[1], sys.argv[2])


