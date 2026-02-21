"""
Plate Detector Module - Precision Mode
Uses a specific YOLO model to find the Plate ROI before OCR.
Eliminates reading stickers/logos on the vehicle body.
"""

from typing import Optional, Dict, Any
import numpy as np
import cv2
import os

# Project root: Traffic_System/
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

class PlateDetector:
    def __init__(self, model_path=None, conf_threshold=0.25):
        model_path = model_path or os.path.join(_PROJECT_ROOT, "models", "license_plate_detector.pt")
        self.module_name = "PLATE_DETECTOR"
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self._initialized = False

    def initialize(self) -> bool:
        if YOLO is None: return False
        try:
            print(f"   🛡️ Loading Dedicated Plate Model: {self.model_path}...")
            self.model = YOLO(self.model_path)
            self._initialized = True
            return True
        except Exception as e:
            print(f"   ❌ Plate Model Init Failed: {e}")
            return False

    def detect_plate(self, vehicle_image: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Input: Cropped Vehicle Image
        Output: Cropped Plate Image (or None)
        """
        if not self._initialized: return None
        
        # 1. Detect Plate Object
        results = self.model(vehicle_image, conf=self.conf_threshold, verbose=False)
        
        best_box = None
        max_conf = 0.0
        
        for r in results:
            for box in r.boxes:
                # Class 0 is usually 'license_plate' in this model
                conf = float(box.conf[0])
                if conf > max_conf:
                    max_conf = conf
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    best_box = (x1, y1, x2, y2)

        # 2. Crop & Preprocess
        if best_box:
            x1, y1, x2, y2 = best_box
            h, w = vehicle_image.shape[:2]
            
            # Safety Clamp
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            
            plate_crop = vehicle_image[y1:y2, x1:x2]
            
            # Enhancement for OCR
            gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
            # Contrast
            gray = cv2.equalizeHist(gray)
            # Denoise
            processed = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

            return {
                "bbox": [x1, y1, x2, y2], # Relative to vehicle image
                "plate_image": processed,
                "confidence": max_conf
            }
            
        return None