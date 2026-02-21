"""
Vehicle Detector Module - Dual Engine (Ensemble)
Optimized for Single Laptop / Multi-Stream Architecture
Features:
1. Singleton Pattern: Loads AI models ONCE in shared memory for all 5 cameras.
2. Dual Engine: RT-DETR (High Accuracy) + Indian YOLO (Local Classes).
3. Resolution Optimization: Forces 640p inference for speed.
"""

from typing import Dict, Any, List
import numpy as np
import cv2
import os
import threading
import torch

# Project root resolution (Assuming file is in Traffic_System_Root/vision_fast/)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

try:
    from ultralytics import RTDETR, YOLO
except ImportError:
    print("❌ Ultralytics not installed.")
    RTDETR = None
    YOLO = None

class VehicleDetector:
    # --- SINGLETON SHARED MEMORY ---
    _SHARED_RTDETR = None
    _SHARED_YOLO = None
    _RTDETR_PATH = None
    _YOLO_PATH = None
    _INIT_LOCK = threading.Lock()

    def __init__(self, 
                 transformer_path=None, 
                 indian_path=None, 
                 conf_threshold=0.3):
        """
        Dual Engine Detector with Singleton Memory Management.
        """
        self.module_name = "VEHICLE_DETECTOR"
        self.conf_threshold = conf_threshold
        self._initialized = False
        
        # Paths (resolve to absolute using project root)
        # Default assumes models are in Traffic_System_Root/models/
        default_rtdetr = os.path.join(_PROJECT_ROOT, "models", "rtdetr-l.pt")
        default_indian = os.path.join(_PROJECT_ROOT, "models", "indian_traffic.pt")
        
        self.path_transformer = transformer_path or default_rtdetr
        self.path_indian = indian_path or default_indian
        
        # Instance references to shared models
        self.model_acc = None   # RT-DETR
        self.model_local = None # Indian YOLO
        
        # Standard Classes (RT-DETR COCO mapping)
        self.coco_map = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck', 1: 'bicycle'}
        self.coco_targets = [1, 2, 3, 5, 7] 

    def initialize(self) -> bool:
        if RTDETR is None or YOLO is None: return False
        
        # Thread-Safe Initialization
        with VehicleDetector._INIT_LOCK:
            # 1. Load RT-DETR (If not already loaded)
            if VehicleDetector._SHARED_RTDETR is None:
                print(f"🔄 [SYSTEM] Loading Shared RT-DETR: {self.path_transformer}...")
                try:
                    model = RTDETR(self.path_transformer)
                    # Warmup / Fuse to prevent runtime errors
                    print("   🔥 Fusing RT-DETR (Thread-Safe)...")
                    if hasattr(model, 'fuse'): model.fuse()
                    VehicleDetector._SHARED_RTDETR = model
                    VehicleDetector._RTDETR_PATH = self.path_transformer
                    print("   ✅ RT-DETR Loaded & Fused.")
                except Exception as e:
                    print(f"   ❌ Failed to load RT-DETR: {e}")
                    return False
            else:
                 print("   ⚡ Using existing Shared RT-DETR.")
    
            # 2. Load Indian YOLO (If not already loaded)
            if VehicleDetector._SHARED_YOLO is None:
                print(f"🔄 [SYSTEM] Loading Shared Indian-YOLO: {self.path_indian}...")
                try:
                    model = YOLO(self.path_indian)
                    print("   🔥 Fusing Indian-YOLO (Thread-Safe)...")
                    if hasattr(model, 'fuse'): model.fuse()
                    VehicleDetector._SHARED_YOLO = model
                    VehicleDetector._YOLO_PATH = self.path_indian
                    print("   ✅ Indian-YOLO Loaded & Fused.")
                except Exception as e:
                    print(f"   ❌ Failed to load Indian-YOLO: {e}")
                    return False
            else:
                 print("   ⚡ Using existing Shared Indian-YOLO.")
    
            # 3. Assign Shared Models to this Instance
            self.model_acc = VehicleDetector._SHARED_RTDETR
            self.model_local = VehicleDetector._SHARED_YOLO
        
        # Identify Indian Classes automatically from the shared model
        if hasattr(self.model_local, 'names'):
            self.indian_names = self.model_local.names
        else:
            self.indian_names = {} # Fallback

        self._initialized = True
        return True

    def detect(self, frame: np.ndarray, visualize: bool = False) -> Dict[str, Any]:
        if not self._initialized: return {"vehicle_count": 0, "vehicle_detections": []}

        # --- STEP 1: RUN BOTH MODELS (Optimized) ---
        # Force imgsz=640 for speed on the Edge
        
        # A. Run RT-DETR
        res_acc = self.model_acc(frame, conf=self.conf_threshold, verbose=False, classes=self.coco_targets, imgsz=640)[0]
        
        # B. Run Indian YOLO
        res_loc = self.model_local(frame, conf=self.conf_threshold, verbose=False, imgsz=640)[0]

        # --- STEP 2: PARSE DETECTIONS ---
        all_detections = []

        # Parse RT-DETR
        for box in res_acc.boxes:
            confidence = float(box.conf[0])
            if confidence < self.conf_threshold: continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            label = self.coco_map.get(cls_id, 'unknown')
            
            all_detections.append({
                "bbox": [x1, y1, x2, y2],
                "label": label,
                "conf": confidence,
                "priority": 1 # Lower priority
            })

        # Parse Indian YOLO
        for box in res_loc.boxes:
            confidence = float(box.conf[0])
            if confidence < self.conf_threshold: continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            if cls_id in self.indian_names:
                raw_label = self.indian_names[cls_id]
                label = self._normalize_indian_name(raw_label)
                
                all_detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "label": label,
                    "conf": confidence,
                    "priority": 2 # Higher priority
                })

        # --- STEP 3: SMART MERGE (NMS) ---
        final_detections = self._merge_detections(all_detections)

        # --- STEP 4: FORMAT OUTPUT ---
        formatted_results = []
        for d in final_detections:
            x1, y1, x2, y2 = d['bbox']
            cx, cy = (x1+x2)//2, (y1+y2)//2
            formatted_results.append({
                "vehicle_type": d['label'],
                "bbox_coordinates": [x1, y1, x2, y2],
                "confidence_score": round(d['conf'], 2),
                "centroid": (cx, cy),
                # internal keys for downstream logic
                "bbox": [x1, y1, x2, y2],
                "class_name": d['label']
            })

        if visualize:
            self._draw_detections(frame, formatted_results)

        return {"vehicle_count": len(formatted_results), "vehicle_detections": formatted_results}

    def _merge_detections(self, detections, iou_thresh=0.6):
        """
        Prioritizes Indian classes over generic ones using IOU.
        """
        if not detections: return []
        
        # Sort by Priority (High to Low), then Confidence
        detections.sort(key=lambda x: (x['priority'], x['conf']), reverse=True)
        
        keep = []
        while detections:
            best = detections.pop(0)
            keep.append(best)
            
            remaining = []
            for other in detections:
                iou = self._calculate_iou(best['bbox'], other['bbox'])
                if iou < iou_thresh:
                    remaining.append(other)
            detections = remaining
            
        return keep

    def _calculate_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        if interArea == 0: return 0

        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea)
        return iou

    def _normalize_indian_name(self, name):
        n = name.lower()
        if 'auto' in n or 'rickshaw' in n: return 'auto'
        if 'tempo' in n or 'lcv' in n: return 'tempo'
        if 'bike' in n or 'scooty' in n: return 'motorcycle'
        return n

    def _draw_detections(self, frame, detections):
        for det in detections:
            x1, y1, x2, y2 = det['bbox_coordinates']
            label = f"{det['vehicle_type']} {det['confidence_score']}"
            color = (0, 255, 255) if det['vehicle_type'] in ['auto', 'tempo'] else (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)