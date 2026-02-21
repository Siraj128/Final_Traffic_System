"""
verify_demo_mode.py

Automated Verification for Phase 18: Global Demo Mode.
Checks:
1. ProfileManager: Loads JSON, assigns, releases.
2. SimpleTracker: Assigns IDs, handles movement.
3. ANPRController: correctly assigns Dummy Plates in DUMMY mode.
"""

import sys
import os
import time
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from vision_fast.utils.profile_manager import ProfileManager
from vision_fast.utils.simple_tracker import SimpleTracker
from vision_fast.anpr_controller import ANPRController

def test_profile_manager():
    print("\n--- Testing ProfileManager ---")
    pm = ProfileManager()
    if len(pm.profiles) != 100:
        print(f"❌ Failed: Loaded {len(pm.profiles)} profiles (Expected 100)")
        return False
    
    p1 = pm.get_profile()
    print(f"Checkout 1: {p1['plate']} - {p1['owner']}")
    
    p2 = pm.get_profile()
    print(f"Checkout 2: {p2['plate']} - {p2['owner']}")
    
    if p1['plate'] == p2['plate']:
        print("XX Failed: Returned same profile twice!")
        return False
        
    pm.release_profile(p1)
    print("OK Released Profile 1")
    return True

def test_tracker():
    print("\n--- Testing SimpleTracker ---")
    tracker = SimpleTracker(max_disappeared=5)
    
    # Frame 1: Object at (100, 100)
    rects1 = [[90, 90, 110, 110]] 
    objects1 = tracker.update(rects1)
    id1 = list(objects1.keys())[0]
    print(f"Frame 1: Assigned ID {id1} to object at {objects1[id1]}")
    
    # Frame 2: Object moves to (105, 105)
    rects2 = [[95, 95, 115, 115]]
    objects2 = tracker.update(rects2)
    id2 = list(objects2.keys())[0]
    print(f"Frame 2: Assigned ID {id2} to object at {objects2[id2]}")
    
    if id1 != id2:
        print(f"XX Failed: ID changed from {id1} to {id2} (Should be same)")
        return False
        
    print("OK Tracker maintained ID across movement.")
    return True

def test_anpr_controller():
    print("\n--- Testing ANPRController (DUMMY MODE) ---")
    # Initialize in DUMMY mode
    anpr = ANPRController(mode="DUMMY")
    
    # Fake Frame (Black Image)
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    
    # Fake Detections: One car at [100, 100, 200, 200]
    # Format: [x1, y1, x2, y2, conf, cls]
    raw_detections = [[100, 100, 200, 200, 0.9, 2]] # Class 2 is usually car/vehicle
    
    # Process
    results = anpr.process(frame, {}, raw_detections, phase_name="TestPhase")
    
    if not results:
        print("XX Failed: No results returned.")
        return False
        
    res = results[0]
    print(f"Result: TrackID={res['track_id']}, Plate={res['plate']}, Owner={res['owner']}")
    
    if "MH12-DE" not in res['plate']:
        print(f"XX Failed: Plate {res['plate']} does not look like a Dummy Profile plate.")
        return False
        
    # Test Consistency (Frame 2)
    print("Processing Frame 2 (Same Car)...")
    results2 = anpr.process(frame, {}, raw_detections, phase_name="TestPhase")
    res2 = results2[0]
    
    if res['plate'] != res2['plate']:
        print(f"XX Failed: Plate changed from {res['plate']} to {res2['plate']}!")
        return False
        
    print("OK Persistent Dummy Plate assigned successfully.")
    return True

if __name__ == "__main__":
    print(">> Starting Global Demo Mode Verification...")
    
    if test_profile_manager() and test_tracker() and test_anpr_controller():
        print("\n>> ALL SYSTEMS GO! Global Demo Mode is verified.")
    else:
        print("\n>> VERIFICATION FAILED.")
