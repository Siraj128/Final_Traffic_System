"""
Safety Detectors Module (Cloud Layer)
Wraps YOLO models for specific safety violations.
Models: helmet.pt, seatbelt.pt, phone.pt
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Optional

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

# Project root assumption
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
import sys
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from config.cloud_models import CloudModelConfig

class BaseDetector:
    def __init__(self, model_path, conf_threshold=0.4):
        self.model_name = os.path.basename(model_path)
        self.conf_threshold = conf_threshold
        self.model = None
        self.model_path = model_path
        self._initialized = False

    def initialize(self):
        if YOLO is None:
            print(f"⚠️ [{self.model_name}] ultralytics not installed.")
            return False
        
        if not os.path.exists(self.model_path):
            print(f"⚠️ [{self.model_name}] Model weights not found at {self.model_path}")
            # In a real scenario, we might download them or fail.
            # For hackathon/demo, we proceed but detection will be skipped.
            return False

        try:
            print(f"☁️ [{self.model_name}] Loading Model...")
            self.model = YOLO(self.model_path)
            self._initialized = True
            return True
        except Exception as e:
            print(f"❌ [{self.model_name}] Init Failed: {e}")
            return False

    def predict(self, image: np.ndarray, target_class_id=0):
        if not self._initialized: return False
        
        results = self.model(image, conf=self.conf_threshold, verbose=False)
        for r in results:
            for box in r.boxes:
                if int(box.cls[0]) == target_class_id:
                    return True # Found object
        return False

class HelmetDetector(BaseDetector):
    def __init__(self):
        super().__init__(CloudModelConfig.HELMET_MODEL_PATH, conf_threshold=CloudModelConfig.CONF_HELMET)
    
    def check_helmet(self, rider_crop: np.ndarray) -> bool:
        """Returns TRUE if Helmet is detected."""
        return self.predict(rider_crop, target_class_id=0) # Assuming Class 0 = Helmet

class SeatbeltDetector(BaseDetector):
    def __init__(self):
        super().__init__(CloudModelConfig.SEATBELT_MODEL_PATH, conf_threshold=CloudModelConfig.CONF_SEATBELT)

    def check_seatbelt(self, driver_crop: np.ndarray) -> bool:
        """Returns TRUE if Seatbelt is detected."""
        return self.predict(driver_crop, target_class_id=0)

class PhoneDetector(BaseDetector):
    def __init__(self):
        super().__init__(CloudModelConfig.PHONE_MODEL_PATH, conf_threshold=CloudModelConfig.CONF_PHONE)

    def check_phone(self, driver_crop: np.ndarray) -> bool:
        """Returns TRUE if Phone usage is detected."""
        return self.predict(driver_crop, target_class_id=0)
