import cv2
import json
import os
import numpy as np
import sys

# Default video if none provided
DEFAULT_VIDEO = os.path.join("tools", "camera5.mp4")
OUTPUT_CONFIG = os.path.join("config", "intersection_roi.json")

points = []

def mouse_callback(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"📍 Point Added: {x}, {y}")

def main():
    global points
    
    video_path = DEFAULT_VIDEO
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        print("Please place 'camera5.mp4' in tools/ or provide path as argument.")
        return

    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Failed to read video frame.")
        return

    print("--- INSTRUCTIONS ---")
    print("1. Click 4 points to define the Center Box (Intersection Area).")
    print("2. Press 'r' to reset points.")
    print("3. Press 's' to save and exit.")
    print("4. Press 'q' to quit without saving.")
    print("--------------------")

    cv2.namedWindow("Setup ROI")
    cv2.setMouseCallback("Setup ROI", mouse_callback)

    while True:
        display = frame.copy()
        
        # Draw Polygon
        if len(points) > 0:
            pts = np.array(points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.polylines(display, [pts], True, (0, 0, 255), 2)
            for p in points:
                cv2.circle(display, p, 5, (0, 255, 0), -1)

        cv2.imshow("Setup ROI", display)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            if len(points) < 3:
                print("⚠️  Need at least 3 points!")
                continue
            
            data = {
                "roi": points,
                "threshold": 2 # Default gridlock threshold
            }
            
            with open(OUTPUT_CONFIG, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"✅ Saved ROI to {OUTPUT_CONFIG}")
            break
            
        elif key == ord('r'):
            points = []
            print("🔄 Reset points.")
            
        elif key == ord('q'):
            print("❌ Cancelled.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
