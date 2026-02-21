"""
CARLA Bridge — "The Ghost in the Machine" (Phase 13)

This module replaces the computer vision system when running in GHOST mode.
Instead of processing video, it queries the CARLA World State directly.

Functions:
1. Connect to CARLA Server (localhost:2000)
2. get_simulated_lane_data() -> Returns JSON matching DetectionController output
3. apply_light_state() -> Controls CARLA traffic lights
"""

import time
import json
import math
import threading
from typing import Dict, Any, List

try:
    import carla
except ImportError:
    print("⚠️  [CARLA] carla module not found. Install with: pip install carla")
    carla = None

class CarlaBridge:
    def __init__(self, host="localhost", port=2000):
        self.host = host
        self.port = port
        self.client = None
        self.world = None
        self.traffic_manager = None
        self.traffic_lights = {} # { "North": Actor, ... }
        self.connected = False
        
        # Lane Configuration (World Coordinates -> Logic Lane)
        # TODO: Tune these coordinates based on the specific CARLA Map (e.g., Town10_HD)
        self.LANE_ZONES = {
            "North": {"x_min": -10, "x_max": 10, "y_min": 20, "y_max": 50},
            "South": {"x_min": -10, "x_max": 10, "y_min": -50, "y_max": -20},
            "East":  {"x_min": 20, "x_max": 50, "y_min": -10, "y_max": 10},
            "West":  {"x_min": -50, "x_max": -20, "y_min": -10, "y_max": 10}
        }

    def connect(self):
        """Connects to the CARLA Simulator."""
        if not carla:
            return False
            
        try:
            print(f"🔌 [CARLA] Connecting to {self.host}:{self.port}...")
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(5.0)
            self.world = self.client.get_world()
            self.traffic_manager = self.client.get_trafficmanager()
            self.connected = True
            
            print(f"✅ [CARLA] Connected to {self.world.get_map().name}")
            self._scan_traffic_lights()
            return True
        except Exception as e:
            print(f"❌ [CARLA] Connection failed: {e}")
            self.connected = False
            return False

    def _scan_traffic_lights(self):
        """Finds all traffic lights and tries to map them to our phases."""
        if not self.world: return

        # Get all traffic lights
        actors = self.world.get_actors().filter('traffic.traffic_light')
        # Simple heuristic: split by location or just grab the closest ones
        # For now, we'll just store them all and maybe refine mapping later
        # In a real Town10 scenario, we'd filter by junction ID
        
        # Placeholder: assume a single intersection for now
        # We might need to manually map actor IDs if detection by location is unreliable
        pass 

    def get_simulated_lane_data(self) -> Dict[str, Any]:
        """
        Query CARLA actors and format as HTMS Lane Data.
        Returns: { "North": { "q_len": 5, "flow_rate": 10, ... }, ... }
        """
        if not self.connected or not self.world:
            return {}

        lane_data = {
            "North": {"q_len": 0, "avg_speed": 0, "vehicles": []},
            "South": {"q_len": 0, "avg_speed": 0, "vehicles": []},
            "East":  {"q_len": 0, "avg_speed": 0, "vehicles": []},
            "West":  {"q_len": 0, "avg_speed": 0, "vehicles": []}
        }

        # 1. Get all vehicles
        vehicles = self.world.get_actors().filter('vehicle.*')
        
        for v in vehicles:
            loc = v.get_location()
            vel = v.get_velocity()
            speed_kmh = (3.6 * math.sqrt(vel.x**2 + vel.y**2 + vel.z**2))
            
            # 2. Map coordinates to Lanes
            # This is a rudimentary spatial query. 
            # In production, we'd use the Map API to check lane_id.
            
            phase = self._get_phase_from_loc(loc)
            if phase:
                lane_data[phase]["q_len"] += 1
                lane_data[phase]["vehicles"].append({
                    "id": v.id,
                    "speed": speed_kmh,
                    "pos": (loc.x, loc.y)
                })

        # Calculate averages
        for phase, data in lane_data.items():
            count = len(data["vehicles"])
            if count > 0:
                total_speed = sum(v["speed"] for v in data["vehicles"])
                data["avg_speed"] = total_speed / count
            
            # Format explicitly for MainController
            # It expects: {'vehicle_count': N, 'avg_speed_kmh': S, 'congestion_level': 'LOW'}
            data["vehicle_count"] = count
            data["avg_speed_kmh"] = data["avg_speed"]
            # data["congestion_level"] is calculated by HybridCore usually, 
            # but here we can pass raw metrics.

        return lane_data

    def _get_phase_from_loc(self, loc):
        """Simple bounding box check."""
        # This needs calibration with the actual map coordinates!
        for phase, zone in self.LANE_ZONES.items():
            if (zone["x_min"] <= loc.x <= zone["x_max"] and 
                zone["y_min"] <= loc.y <= zone["y_max"]):
                return phase
        return None

    def apply_light_state(self, phase_name: str, state: str):
        """
        Controls the CARLA traffic lights.
        state: "GREEN", "YELLOW", "RED"
        """
        if not self.connected: return
        
        # Map our "GREEN" to carla.TrafficLightState.Green
        carla_state = carla.TrafficLightState.Red
        if state == "GREEN":
            carla_state = carla.TrafficLightState.Green
        elif state == "YELLOW":
            carla_state = carla.TrafficLightState.Yellow
            
        # Find the specific light actor for this phase and apply
        # This requires the explicit mapping to be set up in _scan_traffic_lights
        pass

    def cleanup(self):
        self.connected = False
        print("🔌 [CARLA] Bridge disconnected.")
