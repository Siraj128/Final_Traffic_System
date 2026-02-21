# intersection_feature/detection_dummy.py
"""
ULTIMATE PRODUCTION PERCEPTION SIMULATOR (V3.0)
Purpose: Generates high-fidelity synthetic traffic data for system validation.
Source of Truth: 
    - PDF Page 5: Environmental Pre-processing (Rain/Fog/Low Light).
    - PDF Page 6: Object Classification (Cars, Buses, Pedestrians).
    - PDF Page 11: Detection Confidence & Metadata Output.
Standard: Deterministic Physics with Stochastic Anomaly Injection.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import config module
sys.path.append(str(Path(__file__).parent.parent))

import random
import time
import math
from typing import List, Dict, Any
from config.settings import SystemConfig

class DetectionDummy:
    def __init__(self):
        # 1. SIMULATION STATE
        self.active_objects = {} # Tracking current objects in view
        self.next_id = 1000
        self.frame_id = 0
        
        # 2. ENVIRONMENTAL ENGINE (PDF Page 5)
        # Simulation cycles through these to test system resilience
        self.env_states = ["CLEAR", "HEAVY_RAIN", "DENSE_FOG", "LOW_LIGHT"]
        self.current_env = "CLEAR"
        
        # 3. OBJECT CLASSES (PDF Page 6)
        self.classes = ["Car", "Bus", "Two-Wheeler", "Truck", "Pedestrian"]

    def _update_environment(self):
        """Simulates changing weather every 100 frames."""
        if self.frame_id % 100 == 0:
            self.current_env = random.choice(self.env_states)

    def _get_env_confidence_multiplier(self) -> float:
        """PDF Page 5: Lowers AI confidence based on noise (Rain/Fog)."""
        modifiers = {"CLEAR": 1.0, "HEAVY_RAIN": 0.75, "DENSE_FOG": 0.60, "LOW_LIGHT": 0.85}
        return modifiers.get(self.current_env, 1.0)

    def _spawn_object(self):
        """Creates a new object entering from a valid PDF Entry Zone."""
        self.next_id += 1
        entry = random.choice(["NORTH", "SOUTH", "EAST", "WEST"])
        obj_class = random.choice(self.classes)
        
        # Initial Physics based on Zone
        pos = [400, 400]
        if entry == "NORTH": pos = [random.randint(380, 420), 0]
        if entry == "SOUTH": pos = [random.randint(380, 420), 800]
        if entry == "EAST":  pos = [800, random.randint(380, 420)]
        if entry == "WEST":  pos = [0, random.randint(380, 420)]

        self.active_objects[str(self.next_id)] = {
            "class": obj_class,
            "pos": pos,
            "speed": random.uniform(25, 45), # Initial speed km/h
            "entry": entry,
            "is_stalling": False,
            "is_braking": False
        }

    def get_latest_frame(self) -> List[Dict[str, Any]]:
        """
        The Master API for the Perception Layer.
        Returns a list of detected objects with full metadata (PDF Page 11).
        """
        self.frame_id += 1
        self._update_environment()
        
        # 1. Randomly spawn new vehicles
        if random.random() < 0.3: # 30% chance per frame
            self._spawn_object()

        processed_frame = []
        cleanup_ids = []

        for oid, data in self.active_objects.items():
            # 2. SIMULATE PHYSICS & ANOMALIES (PDF Page 6)
            
            # Injection: Randomly force a stall (2% chance)
            if not data["is_stalling"] and 350 < data["pos"][0] < 450 and random.random() < 0.02:
                data["is_stalling"] = True
            
            # Injection: Randomly force an accident/sudden stop (1% chance)
            if not data["is_braking"] and random.random() < 0.01:
                data["is_braking"] = True

            # Calculate Movement
            if data["is_stalling"]:
                data["speed"] = max(0, data["speed"] - 5.0) # Slow to a halt
            elif data["is_braking"]:
                data["speed"] = max(0, data["speed"] - 20.0) # Sudden Braking Physics
            
            # Update Coordinates based on direction
            move_dist = data["speed"] * 0.1 # simplified delta
            if data["entry"] == "NORTH": data["pos"][1] += move_dist
            if data["entry"] == "SOUTH": data["pos"][1] -= move_dist
            if data["entry"] == "EAST":  data["pos"][0] -= move_dist
            if data["entry"] == "WEST":  data["pos"][0] += move_dist

            # 3. FORMAT PRODUCTION METADATA (PDF Page 11)
            confidence = random.uniform(0.85, 0.99) * self._get_env_confidence_multiplier()
            
            processed_frame.append({
                "id": oid,
                "class": data["class"],
                "x": int(data["pos"][0]),
                "y": int(data["pos"][1]),
                "speed": round(data["speed"], 2),
                "confidence": round(confidence, 2),
                "metadata": {
                    "environment": self.current_env,
                    "sensor_id": "PUNE_CAM_01_CENTER"
                }
            })

            # Cleanup if object leaves junction (800x800 bounds)
            if not (0 <= data["pos"][0] <= 800 and 0 <= data["pos"][1] <= 800):
                cleanup_ids.append(oid)

        for cid in cleanup_ids:
            del self.active_objects[cid]

        return processed_frame