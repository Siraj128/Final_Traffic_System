import sys
import os
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from vision_fast.anpr_controller import ANPRController

def test_crash_fix():
    print(">> Testing ANPRController crash fix...")
    
    # Initialize in DUMMY mode to avoid EasyOCR loading overhead if possible
    # (Though logic runs same for valid_boxes extraction)
    anpr = ANPRController(mode="DUMMY")
    
    # Simulate the data structure that caused the crash
    # List of dictionaries as sent by VehicleDetector
    raw_detections = [
        {
            "vehicle_type": "car",
            "bbox_coordinates": [100, 100, 200, 200],
            "confidence_score": 0.9
        }
    ]
    
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    try:
        print(">> Processing frame with dict detections...")
        anpr.process(frame, {}, raw_detections, phase_name="Test")
        print(">> OK Success! No crash.")
    except TypeError as e:
        if "unhashable type: 'slice'" in str(e):
             print(f"xx Failed! Crashed with expected error: {e}")
        else:
             print(f"xx Failed! Crashed with TypeError: {e}")
    except Exception as e:
        print(f"xx Failed! Crashed with: {e}")

if __name__ == "__main__":
    test_crash_fix()
