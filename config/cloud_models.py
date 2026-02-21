"""
Cloud AI Model Configuration
"""
import os

# Project Root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class CloudModelConfig:
    # Model Paths (Relative to project root)
    HELMET_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "helmet_detector.pt")
    SEATBELT_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "seatbelt_detector.pt")
    PHONE_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "phone_detector.pt")
    PLATE_MODEL_PATH = os.path.join(_PROJECT_ROOT, "models", "license_plate_detector.pt")
    
    # Confidence Thresholds
    CONF_HELMET = 0.5
    CONF_SEATBELT = 0.4
    CONF_PHONE = 0.4
    CONF_PLATE = 0.25
    
    # Worker Settings
    POLL_INTERVAL = 2.0 # Seconds
    BATCH_SIZE = 1
