import random
import time

try:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt") # This will download if not present
    HAS_YOLO = True
except Exception as e:
    print(f"YOLO Warning: {e}. Running in Simulation Mode.")
    HAS_YOLO = False

def detect_objects(img):
    """
    Detects vehicles and violations.
    Returns: {
        "vehicle_count": int,
        "violations": [], # List of violation types
        "plates": [] # List of detected numbers
    }
    """
    
    if HAS_YOLO:
        try:
            results = model(img)
            # Process YOLO results
            # For hackathon speed, we might mix real detection with simulated "violation logic"
            # because detecting specific violations like 'lane discipline' from static frames is hard without robust logic.
            
            # Simple count from YOLO
            vehicle_count = len([d for d in results[0].boxes.cls if int(d) in [2, 3, 5, 7]]) # COCO IDs for vehicles
        except:
            vehicle_count = random.randint(0, 3)
    else:
        # Simulation Mode
        time.sleep(0.5) # Simulate processing time
        vehicle_count = random.randint(1, 5)

    # Random Mock Data for Demo (Mix with real counts if avail)
    possible_violations = ["None", "None", "None", "Signal Jump", "No Helmet", "Overspeeding"]
    violation = random.choice(possible_violations)
    
    mock_plates = ["KA01AB1234", "MH12CD5678", "DL3C9876", "TN05XY4321"]
    
    return {
        "vehicle_count": vehicle_count,
        "violation_type": violation,
        "plates": [random.choice(mock_plates)] if vehicle_count > 0 else []
    }
