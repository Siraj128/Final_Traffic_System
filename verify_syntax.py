import sys
import os
sys.path.append(os.getcwd())

print("Testing MainController Import...")
try:
    from main_controller import MainController
    print("[OK] MainController Imported")
except Exception as e:
    print(f"[FAIL] MainController Import Failed: {e}")

print("Testing DetectionController Import...")
try:
    from vision_fast.detection_controller import DetectionController
    print("[OK] DetectionController Imported")
except Exception as e:
    print(f"[FAIL] DetectionController Import Failed: {e}")
    import traceback
    traceback.print_exc()
