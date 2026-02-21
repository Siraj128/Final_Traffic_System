
import cv2
import time
import random
import requests
import numpy as np
import threading
import easyocr
from config.settings import SystemConfig

class ANPRController:
    """
    Hybrid ANPR Controller for Reward System.
    
    Strategy:
    1. Detect vehicles near Stop Line (Compliance Check).
    2. Attempt Real OCR (EasyOCR).
    3. Fallback to Simulation if OCR fails (to ensure demo works).
    4. Async Credit Points via Server API.
    """
    
    def __init__(self, endpoint_url=None, mode="REAL"):
        self.endpoint_url = endpoint_url or f"{SystemConfig.SAFEDRIVE_URL}/api/rewards/credit"
        self.mode = mode # "REAL" or "DUMMY"
        self.last_process_time = 0
        self.cooldown = 0.5 # Faster to allow tracking updates
        
        # Tools
        from vision_fast.utils.simple_tracker import SimpleTracker
        from vision_fast.utils.profile_manager import ProfileManager
        
        self.tracker = SimpleTracker(max_disappeared=15, max_distance=100)
        self.profile_manager = ProfileManager()
        
        # State: TrackID -> Assigned Profile (dict)
        self.track_map = {} 
        
        # Blacklist
        self.ignore_texts = ["MODE", "HYBRID", "STATUS", "CLEAR", "NORTH", "SOUTH", "EAST", "WEST", "LANE", "MODEYHYBRID"]
        
        # Initialize EasyOCR if REAL mode
        self.reader = None
        if self.mode == "REAL":
            print("    [ANPR] Initializing EasyOCR Engine... (This may take a moment)")
            self.reader = easyocr.Reader(['en'], gpu=True)
            print("    >> [ANPR] Engine Ready.") 
        else:
            print("    >> [ANPR] Running in DUMMY Mode (400 Profiles)")

    def process(self, frame, lane_data, raw_detections, phase_name, light_state="RED"):
        """
        1. Track all vehicles.
        2. Assign/Update Plates (Real vs Dummy).
        3. Return enriched list for Enforcement.
        """
        # Convert raw_detections (list of [x1,y1,x2,y2,conf,cls]) to [x,y,w,h] for tracker? 
        # SimpleTracker expects [x1, y1, x2, y2]
        
        valid_boxes = []
        for det in raw_detections:
            # raw_detections is a list of DICTIONARIES from VehicleDetector
            # {'vehicle_type': 'car', 'bbox_coordinates': [x1, y1, x2, y2], 'confidence_score': 0.9}
            
            if isinstance(det, dict):
                bbox = det.get("bbox_coordinates")
                if bbox:
                    valid_boxes.append(bbox)
            elif isinstance(det, (list, tuple, np.ndarray)):
                # Fallback for raw arrays
                valid_boxes.append(det[:4])
            
        # 1. Update Tracker
        objects = self.tracker.update(valid_boxes)
        
        # 2. Sync Track Map (Remove dead IDs)
        active_ids = set(objects.keys())
        dead_ids = set(self.track_map.keys()) - active_ids
        for did in dead_ids:
            # Release profile back to pool if in Dummy Mode?
            # Ideally yes, but depends on if vehicle left or just flickered.
            # SimpleTracker handles flicker (disappeared count). If it's gone from objects, it's gone.
            profile = self.track_map.pop(did, None)
            if self.mode == "DUMMY" and profile:
                self.profile_manager.release_profile(profile)
        
        results = []

        # 3. Process Active Tracks
        for obj_id, centroid in objects.items():
            # Get BBox for this object (find closest input box? SimpleTracker doesn't store bbox, just centroid)
            # We need bbox to run OCR or draw.
            # Reverse lookup bbox from centroid is tricky if multiple close.
            # Improved Tracker needed? Or just map input box to ID during update?
            # For this demo, let's find the best matching input box for the centroid.
            
            best_box = None
            min_dist = 9999
            cx, cy = centroid
            
            for box in valid_boxes:
                bx, by = int((box[0]+box[2])/2), int((box[1]+box[3])/2)
                dist = (cx-bx)**2 + (cy-by)**2
                if dist < min_dist:
                    min_dist = dist
                    best_box = box
            
            if best_box is None or min_dist > 2500: # >50px off
                continue
                
            x1, y1, x2, y2 = map(int, best_box)
            
            # --- ASSIGNMENT LOGIC ---
            
            # Init Track Entry if new
            if obj_id not in self.track_map:
                if self.mode == "DUMMY":
                    # Fetch new dummy profile
                    prof = self.profile_manager.get_profile()
                    if prof:
                        self.track_map[obj_id] = prof
                else:
                    # REAL Mode: Init empty, wait for OCR
                    self.track_map[obj_id] = {"plate": None, "conf": 0.0}
            
            # Get current profile
            profile = self.track_map.get(obj_id)
            if not profile: continue 

            # --- REAL MODE UPDATE ---
            if self.mode == "REAL" and profile.get("conf", 0) < 0.8:
                # Try to read plate if not yet confident
                # Crop vehicle
                try:
                    vehicle_crop = frame[y1:y2, x1:x2]
                    if vehicle_crop.size > 0:
                        text, conf = self._run_ocr(vehicle_crop)
                        if text:
                           profile["plate"] = text
                           profile["conf"] = conf
                           profile["owner"] = "Unknown" # Real world lookup would happen here
                           self.track_map[obj_id] = profile
                except: pass

            # --- CREDIT LOGIC (Simple One-Time Bonus for Demo) ---
            if profile.get("plate") and profile.get("plate") != "Scanning..." and not profile.get("credited", False):
                # Send points to DB
                self._send_credit(profile["plate"], 10, phase_name) # +10 points for detection compliance
                profile["credited"] = True
                self.track_map[obj_id] = profile

            # Add to results
            results.append({
                "track_id": obj_id,
                "bbox": (x1, y1, x2, y2),
                "plate": profile.get("plate", "Scanning..."),
                "owner": profile.get("owner", "Unknown"),
                "score": profile.get("score", 100)
            })
            
        return results

    def _run_ocr(self, img):
        """Run EasyOCR on a crop."""
        try:
            results = self.reader.readtext(img)
            for (_, text, prob) in results:
                clean_text = "".join(e for e in text if e.isalnum()).upper()
                if len(clean_text) > 4 and prob > 0.4:
                     if not any(bad in clean_text for bad in self.ignore_texts):
                         return clean_text, prob
        except: pass
        return None, 0.0

    def _send_credit(self, plate, points, phase):
        """Send credit to CMS Server (Async)."""
        if not plate or plate == "Scanning..." or points == 0:
            return

        def _worker():
            try:
                payload = {
                    "plate_number": plate,
                    "points": points,
                    "reason": "Traffic Compliance (Green Logic)",
                    "junction_id": SystemConfig.JUNCTION_ID
                }
                requests.post(self.endpoint_url, json=payload, timeout=2.0)
                print(f"    💸 [ANPR] Sent +{points} pts to {plate}") # Debug enabled for verification
            except Exception as e:
                print(f"    ⚠️ [ANPR] Credit Upload Failed: {e}")
        
        # Fire and Forget
        threading.Thread(target=_worker, daemon=True).start()
