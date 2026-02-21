"""
background_service.py — Heavy Background Processing (Part 8, 11)

This module handles non-real-time tasks that run asynchronously:
1. ANPR (Automatic Number Plate Recognition) on violation frames
2. Violation detection and evidence packaging
3. Cloud database uploads (Siraj's DB — historical logs)
4. Reward system violation-to-wallet pipeline

Architecture:
    - Runs as a daemon thread, spawned by main_controller.py
    - Receives violation frames via a thread-safe queue
    - Does NOT interfere with the real-time signal cycle
    - Uploads are async and failure-tolerant (edge keeps working if cloud is down)
"""

import os
import sys
import time
import json
import threading
import traceback
from queue import Queue, Empty
from datetime import datetime
import cv2

from config.settings import SystemConfig
from cms_layer.cloud_db_handler import db  # Unified Connection Handlerme

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class BackgroundService:
    """
    Heavy-duty background processor.
    
    Receives jobs from the real-time pipeline and processes them
    without blocking the signal cycle.
    
    Job types:
        - "violation": Process a violation frame (ANPR → OCR → DB)
        - "cycle_log": Upload a cycle summary to cloud DB
        - "anomaly": Process and store anomaly detection data
    """
    
    def __init__(self):
        self._job_queue = Queue(maxsize=1000)
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._stats = {
            "violations_processed": 0,
            "cycles_uploaded": 0,
            "anomalies_logged": 0,
            "errors": 0
        }
        
        # Lazy-load heavy modules only when needed
        self._plate_detector = None
        self._ocr_reader = None
        self._plate_validator = None
        self._violation_manager = None
    
    def start(self):
        """Start the background worker thread."""
        self._worker_thread = threading.Thread(
            target=self._worker_loop, daemon=True, name="BackgroundWorker"
        )
        self._worker_thread.start()
        print("  🔧 [Background] Heavy processing service started")
    
    def stop(self):
        """Stop the background worker."""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        print(f"  🔧 [Background] Service stopped — Stats: {self._stats}")
    
    def submit_job(self, job_type, data):
        """
        Submit a job for background processing.
        
        Args:
            job_type: "violation", "cycle_log", "anomaly"
            data: dict with job-specific payload
        """
        try:
            self._job_queue.put_nowait({
                "type": job_type,
                "data": data,
                "submitted_at": time.time()
            })
        except Exception:
            self._stats["errors"] += 1
    
    # ─────────────────────────────────────────────────────────
    # WORKER LOOP
    # ─────────────────────────────────────────────────────────
    
    def _worker_loop(self):
        """Main worker loop — processes jobs from the queue."""
        while not self._stop_event.is_set():
            try:
                job = self._job_queue.get(timeout=1.0)
                job_type = job.get("type", "")
                
                if job_type == "violation":
                    self._process_violation(job["data"])
                elif job_type == "cycle_log":
                    self._upload_cycle_log(job["data"])
                elif job_type == "anomaly":
                    self._log_anomaly(job["data"])
                else:
                    print(f"  ⚠️ [Background] Unknown job type: {job_type}")
                    
            except Empty:
                continue
            except Exception as e:
                self._stats["errors"] += 1
                traceback.print_exc()
    
    # ─────────────────────────────────────────────────────────
    # JOB HANDLERS
    # ─────────────────────────────────────────────────────────
    
    def _process_violation(self, data):
        """
        Offloads violation to Cloud (Neon DB + Storage).
        The 'Cloud Processor' will pick this up later.
        """
        try:
            frame = data.get("frame")
            violation_type = data.get("violation_type", "UNKNOWN")
            timestamp = data.get("timestamp", time.time())
            
            if frame is None: return

            # 1. Save Snapshot to "Cloud Storage" (Simulated via shared folder)
            # In production, this would be S3.upload_file()
            storage_dir = os.path.join(PROJECT_ROOT, "cloud_storage", "active_violations")
            os.makedirs(storage_dir, exist_ok=True)
            
            filename = f"vio_{int(timestamp)}_{violation_type}.jpg"
            file_path = os.path.join(storage_dir, filename)
            cv2.imwrite(file_path, frame)
            
            # 2. Insert into DB with status='PENDING'
            self._store_violation_request({
                "evidence_path": file_path,
                "violation_type": violation_type,
                "timestamp": timestamp,
                "junction_id": data.get("junction_id", SystemConfig.JUNCTION_ID),
                "metadata": {
                    "bbox": data.get("vehicle_bbox", []),
                    "vehicle_class": "unknown" # Could pass from detection
                }
            })
            
            print(f"  ☁️ [Background] Uploaded Violation {violation_type} -> Cloud Queue")
            self._stats["violations_processed"] += 1
            
        except Exception as e:
            self._stats["errors"] += 1
            print(f"  ⚠️ [Background] Cloud Upload Failed: {e}")
    
    
    def _upload_cycle_log(self, data):
        """
        Upload cycle summary to Cloud DB (with Local Fallback).
        """
        try:
            conn, source = db.get_best_connection()
            if conn:
                cur = conn.cursor()
                sql = """
                    INSERT INTO traffic_history_log (junction_id, cycle_no, winner, green_time, timestamp, metrics)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                # Use current JUNCTION_ID if not present in data
                jid = data.get("junction_id", SystemConfig.JUNCTION_ID)
                metrics_json = json.dumps(data.get("scores", {}))
                
                cur.execute(sql, (
                    jid, 
                    data.get("cycle", 0),
                    data.get("winner", "UNKNOWN"),
                    data.get("green_time", 0),
                    datetime.now(),
                    metrics_json
                ))
                conn.commit()
                cur.close()
                conn.close()
                self._stats["cycles_uploaded"] += 1
                return

            # Fallback to JSON
            log_path = os.path.join(PROJECT_ROOT, "logs")
            os.makedirs(log_path, exist_ok=True)
            log_file = os.path.join(log_path, f"cycles_{datetime.now().strftime('%Y%m%d')}.jsonl")
            
            entry = {"timestamp": datetime.now().isoformat(), **data}
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
            
            self._stats["cycles_uploaded"] += 1
            
        except Exception as e:
            self._stats["errors"] += 1
            print(f"⚠️ [Background] Cycle Log Failed: {e}")
    
    def _log_anomaly(self, data):
        """
        Store anomaly detection data.
        
        Args:
            data: {
                "type": str (e.g., "GRIDLOCK", "ACCIDENT", "PEDESTRIAN_CONFLICT"),
                "severity": str,
                "telemetry": dict,
                "timestamp": float
            }
        """
        try:
            # Log to local file (cloud upload later)
            log_path = os.path.join(PROJECT_ROOT, "logs")
            os.makedirs(log_path, exist_ok=True)
            
            log_file = os.path.join(log_path, f"anomalies_{datetime.now().strftime('%Y%m%d')}.jsonl")
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                **data
            }
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
            
            self._stats["anomalies_logged"] += 1
            
        except Exception as e:
            self._stats["errors"] += 1
    
    # ─────────────────────────────────────────────────────────
    # HEAVY MODULE INITIALIZATION (Lazy)
    # ─────────────────────────────────────────────────────────
    
    def _init_heavy_modules(self):
        """Load ANPR modules only when first violation arrives."""
        try:
            from vision_heavy.plate_detector import PlateDetector
            from vision_heavy.ocr_reader import OCRReader
            from vision_heavy.plate_validator import PlateValidator
            
            self._plate_detector = PlateDetector()
            self._ocr_reader = OCRReader()
            self._plate_validator = PlateValidator()
            print("  🔧 [Background] Heavy ANPR modules loaded")
        except Exception as e:
            print(f"  ⚠️ [Background] Could not load ANPR modules: {e}")
    
    def _store_violation_request(self, record):
        """Stores pending violation request in DB."""
        try:
            conn, source = db.get_best_connection()
            if conn:
                cur = conn.cursor()
                sql = """
                    INSERT INTO traffic_violations 
                    (junction_id, violation_type, violation_time, evidence_url, status, metadata)
                    VALUES (%s, %s, %s, %s, 'PENDING', %s)
                """
                # Convert float timestamp to datetime if needed
                ts = record.get("timestamp")
                if isinstance(ts, float):
                    ts = datetime.fromtimestamp(ts)
                
                meta_json = json.dumps(record.get("metadata", {}))

                cur.execute(sql, (
                    record.get("junction_id"),
                    record.get("violation_type"),
                    ts,
                    record.get("evidence_path"),
                    meta_json
                ))
                conn.commit()
                cur.close()
                conn.close()
                return

            # Fallback (Offline Mode)
            log_path = os.path.join(PROJECT_ROOT, "logs")
            os.makedirs(log_path, exist_ok=True)
            log_file = os.path.join(log_path, f"pending_uploads_{datetime.now().strftime('%Y%m%d')}.jsonl")
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(record) + "\n")
                
        except Exception as e:
            print(f"⚠️ [Background] Violation Request Store Failed: {e}")


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == "__main__":
    print("🔧 Testing Background Service...")
    
    svc = BackgroundService()
    svc.start()
    
    # Submit test jobs
    svc.submit_job("cycle_log", {
        "cycle": 1,
        "winner": "North",
        "scores": {"North": 450, "South": 300, "East": 200, "West": 100},
        "green_time": 30,
        "state": "LESS_CONGESTION"
    })
    
    svc.submit_job("anomaly", {
        "type": "GRIDLOCK",
        "severity": "HIGH",
        "telemetry": {"density": 0.95, "stuck_count": 8}
    })
    
    time.sleep(3)
    svc.stop()
