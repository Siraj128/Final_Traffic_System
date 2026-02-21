"""
Cloud Processor — The "Heavy" AI Worker (Phase 15)

This script should run on the Cloud Server (or a separate process).
It:
1. Connects to Neon DB.
2. Polls `violations_queue` (or `traffic_violations` with status 'PENDING').
3. Downloads the image (Simulated: reads from local/cloud path).
4. Runs Heavy AI (Helmet, Seatbelt, Phone, Plate).
5. Updates the record status.
"""

import time
import os
import sys
import json
import cv2
from datetime import datetime

# Path Hack
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from cms_layer.cloud_db_handler import db
from cloud_layer.models.safety_detectors import HelmetDetector, SeatbeltDetector, PhoneDetector
from vision_heavy.plate_detector import PlateDetector
from vision_heavy.ocr_reader import OCRReader
from config.cloud_models import CloudModelConfig

class CloudProcessor:
    def __init__(self):
        print("☁️ [CLOUD] Initializing AI Worker Node...")
        
        # Models
        self.helmet_model = HelmetDetector()
        self.seatbelt_model = SeatbeltDetector()
        # Models
        self.helmet_model = HelmetDetector()
        self.seatbelt_model = SeatbeltDetector()
        self.phone_model = PhoneDetector()
        self.plate_model = PlateDetector(
            model_path=CloudModelConfig.PLATE_MODEL_PATH,
            conf_threshold=CloudModelConfig.CONF_PLATE
        )
        self.ocr = OCRReader()
        
        self.running = True
        
    def start(self):
        # 1. Warmup Models
        self.helmet_model.initialize()
        self.seatbelt_model.initialize()
        self.phone_model.initialize()
        self.plate_model.initialize()
        
        print("\n☁️ [CLOUD] Worker Ready. Polling for jobs...\n")
        self._ensure_table_exists()
        self._poll_loop()

    def _ensure_table_exists(self):
        """Ensures the violations table exists to prevent crash on startup."""
        conn, source = db.get_best_connection()
        if not conn: return
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS traffic_violations (
                    id SERIAL PRIMARY KEY,
                    junction_id TEXT NOT NULL,
                    plate_number TEXT DEFAULT 'PENDING',
                    violation_type TEXT NOT NULL,
                    violation_time TIMESTAMP DEFAULT NOW(),
                    evidence_url TEXT,
                    confidence FLOAT DEFAULT 0.0,
                    penalty_applied BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    status TEXT DEFAULT 'PENDING',
                    attributes JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}',
                    processed_at TIMESTAMP
                )
            """)
            conn.commit()
            cur.close()
            conn.close()
            print("✅ [CLOUD] Database Schema Verified.")
        except Exception as e:
            print(f"⚠️ [CLOUD] Schema Verification Failed (Non-Fatal): {e}")

    def _poll_loop(self):
        conn, source = db.get_best_connection()
        if not conn:
            print("❌ [CLOUD] No DB Connection. Exiting.")
            return

        while self.running:
            try:
                # 1. Fetch Pending Job
                # Use a transaction to lock the row? For MVP, simple SELECT/UPDATE is fine.
                cur = conn.cursor()
                
                # Check for table existence first (idempotency)
                # In real prod, this schema should be migrated separately.
                
                cur.execute("""
                    SELECT id, evidence_url, violation_type, metadata 
                    FROM traffic_violations 
                    WHERE status = 'PENDING' 
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                """)
                
                row = cur.fetchone()
                
                if row:
                    job_id, img_path, v_type, meta_json = row
                    print(f"📥 [CLOUD] Processing Job #{job_id} ({v_type})")
                    
                    # 2. Process
                    result = self._process_image(img_path, v_type, meta_json)
                    
                    # 3. Update DB
                    attributes_json = json.dumps(result)
                    confirm_status = "CONFIRMED" if result.get("confirmed") else "REJECTED"
                    
                    cur.execute("""
                        UPDATE traffic_violations 
                        SET status = %s, attributes = %s, processed_at = NOW()
                        WHERE id = %s
                    """, (confirm_status, attributes_json, job_id))
                    
                    conn.commit()
                    print(f"✅ [CLOUD] Job #{job_id} Done -> {confirm_status}")
                else:
                    # No jobs
                    conn.commit() # Release any locks
                    print(".", end="", flush=True) # Visual Heartbeat
                    time.sleep(CloudModelConfig.POLL_INTERVAL) # Wait before next poll

            except Exception as e:
                print(f"⚠️ [CLOUD] Error in poll loop: {e}")
                if conn: conn.rollback()
                time.sleep(5.0)

    def _process_image(self, img_path, v_type, meta):
        """
        Runs the appropriate models based on violation type.
        """
        # For simulation, if img_path is remote URL, we'd request.get() it.
        # Here we assume shared FS or local path for MVP.
        if not os.path.exists(img_path):
            return {"error": "Image not found", "confirmed": False}
        
        img = cv2.imread(img_path)
        if img is None:
            return {"error": "Image load failed", "confirmed": False}
            
        attributes = {"confirmed": True} # Default confirm flow unless disproven
        
        # 1. Helmet Check (Two-Wheelers only)
        # We need vehicle class from Edge metadata ideally.
        # Assuming RLV/StopLine can be any vehicle.
        
        # 2. Seatbelt/Phone (Car drivers)
        if v_type in ["RLV", "SLV", "SPEED"]:
            # Run Safety checks as bonus
            has_seatbelt = self.seatbelt_model.check_seatbelt(img)
            using_phone = self.phone_model.check_phone(img)
            
            attributes["seatbelt_worn"] = has_seatbelt
            attributes["phone_used"] = using_phone
            
            if using_phone:
                attributes["secondary_violation"] = "Phone Usage"
                
        # 3. Plate Re-Verification (If Edge result was low confidence)
        # For now, let's just run it to populate data
        plate_data = self.plate_model.detect_plate(img)
        if plate_data:
            text = self.ocr.read_plate(plate_data)
            attributes["cloud_plate_text"] = text
        
        return attributes

if __name__ == "__main__":
    cpu = CloudProcessor()
    try:
        cpu.start()
    except KeyboardInterrupt:
        print("\n☁️ [CLOUD] Worker shutting down.")
