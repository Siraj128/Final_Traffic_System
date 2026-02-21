"""
carla_bridge.py  —  CARLA ↔ Traffic System Bridge Server

Receives real-time decisions from main_controller (via HTTP POST)
and translates them into CARLA traffic light commands at a single
Town05 junction.

Architecture:
    main_controller  ──POST /carla/decision──▶  this server  ──carla API──▶  CARLA

Startup:
    1. Start CARLA simulator (Town05)
    2. python carla_integration/generate_traffic_global.py   (spawn cars)
    3. python carla_integration/carla_bridge.py               (this file)
    4. python main_controller.py                              (real AI)
"""
import glob
import json
import math
import os
import sys
import threading
import time

# ── Resolve CARLA egg ────────────────────────────────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Try to find CARLA egg from env var or common install paths
_carla_root = os.getenv("CARLA_ROOT", "")
if not _carla_root:
    # Fallback: check common locations
    _candidates = [
        r"C:\CARLA",
        r"C:\CARLA_0.9.16",
        os.path.expanduser(r"~\Downloads\CARLA_0.9.16"),
    ]
    for c in _candidates:
        if os.path.isdir(c):
            _carla_root = c
            break

if _carla_root:
    try:
        sys.path.append(glob.glob(
            _carla_root + '/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
                sys.version_info.major, sys.version_info.minor,
                'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
    except IndexError:
        pass

import carla  # noqa: E402

# FastAPI for receiving decisions from main_controller
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn

# ── Load config ──────────────────────────────────────────────────
_config_path = os.path.join(_PROJECT_ROOT, "config", "carla_config.json")
with open(_config_path) as f:
    CONFIG = json.load(f)

CARLA_HOST  = CONFIG.get("carla_host", "localhost")
CARLA_PORT  = CONFIG.get("carla_port", 2000)
BRIDGE_PORT = CONFIG.get("bridge_port", 8100)
YELLOW_DUR  = CONFIG.get("yellow_duration_s", 2.0)
ALL_RED_DUR = CONFIG.get("all_red_duration_s", 1.5)
DEFAULT_GREEN = CONFIG.get("default_green_s", 30)
HUD_REFRESH = CONFIG.get("hud_refresh_s", 0.1)
TARGET_JUNCTION_INDEX = CONFIG.get("target_junction_index", 0)
SPECTATOR_HEIGHT = CONFIG.get("spectator_height", 50)

# ── Pydantic Models ──────────────────────────────────────────────
class DecisionPayload(BaseModel):
    winner_phase: str                              # "North" | "South" | "East" | "West"
    allowed_lanes: List[str]                       # ["West_All", "South_Left"]
    allocated_times: Dict[str, int]                # {"North":33, "South":28, ...}
    priority_scores: Dict[str, int]                # {"North":870, ...}
    system_state: str                              # "SAFE" | "LESS_CONGESTION" | ...
    phase_saturations: Optional[Dict[str, float]] = None  # {"North":2.5, ...}


# ══════════════════════════════════════════════════════════════════
# CARLA Junction Controller
# ══════════════════════════════════════════════════════════════════

class JunctionController:
    """
    Maps our 4-direction system (N/S/E/W) to CARLA traffic light actors
    at a single Town05 junction.

    Direction mapping uses yaw-angle clustering:
      - Group lights by junction_id
      - Use reference light's stop-waypoint yaw angle
      - Cluster all lights into 4 quadrants (N/S/E/W) by yaw offset
    """

    DIRECTION_YAWS = {
        # Relative yaw offsets from reference (0°)
        # These get calibrated per-junction from actual light yaws
        "North": 0,
        "East":  90,
        "South": 180,
        "West":  270,
    }

    def __init__(self, world, junction_index=0):
        self.world = world
        self.world_map = world.get_map()
        self.debug = world.debug

        # Current state
        self.current_decision: Optional[DecisionPayload] = None
        self._lock = threading.Lock()
        self._phase_state = "GREEN"  # GREEN → YELLOW → ALL_RED → GREEN
        self._phase_timer = 0.0
        self._green_duration = DEFAULT_GREEN

        # Discover junction
        self._light_groups: Dict[str, list] = {
            "North": [], "South": [], "East": [], "West": []
        }
        self._junction_center = None
        self._discover_junction(junction_index)

    def _discover_junction(self, junction_index):
        """Find all traffic lights, group by junction, pick one, classify by direction."""
        all_lights = self.world.get_actors().filter('traffic.traffic_light')
        if not all_lights:
            print("❌ [Bridge] No traffic lights found in CARLA world!")
            return

        # Group lights by junction_id
        junction_groups = {}
        for light in all_lights:
            light.freeze(True)  # Take manual control
            stop_wps = light.get_stop_waypoints()
            if stop_wps and stop_wps[0].is_junction:
                jid = stop_wps[0].junction_id
                junction_groups.setdefault(jid, []).append(light)

        if not junction_groups:
            print("❌ [Bridge] No junction-linked traffic lights found!")
            return

        # Pick the target junction
        jids = sorted(junction_groups.keys())
        if junction_index >= len(jids):
            junction_index = 0
        target_jid = jids[junction_index]
        lights = junction_groups[target_jid]

        print(f"🎯 [Bridge] Selected Junction #{junction_index} (ID: {target_jid}) with {len(lights)} lights")

        # Compute junction center
        locs = [l.get_location() for l in lights]
        cx = sum(p.x for p in locs) / len(locs)
        cy = sum(p.y for p in locs) / len(locs)
        cz = sum(p.z for p in locs) / len(locs)
        self._junction_center = carla.Location(cx, cy, cz)

        # Classify lights into N/S/E/W by their stop-waypoint yaw angle
        yaw_light_pairs = []
        for light in lights:
            sws = light.get_stop_waypoints()
            if sws:
                yaw = sws[0].transform.rotation.yaw % 360
                yaw_light_pairs.append((yaw, light))

        if not yaw_light_pairs:
            print("❌ [Bridge] No stop waypoints found for lights!")
            return

        # Sort all yaws, find 4 clusters using the median approach
        # Simple: snap each yaw to nearest cardinal direction
        for yaw, light in yaw_light_pairs:
            direction = self._yaw_to_direction(yaw)
            self._light_groups[direction].append(light)

        for d, ls in self._light_groups.items():
            print(f"  🚦 {d}: {len(ls)} lights")

        # Position spectator camera above junction
        spectator = self.world.get_spectator()
        spectator.set_transform(carla.Transform(
            carla.Location(cx, cy, cz + SPECTATOR_HEIGHT),
            carla.Rotation(pitch=-90)  # Top-down view
        ))
        print(f"📷 [Bridge] Spectator camera positioned above junction")

    def _yaw_to_direction(self, yaw: float) -> str:
        """Snap a yaw angle (0-360) to the nearest cardinal direction."""
        # Normalize to 0-360
        yaw = yaw % 360
        if yaw < 45 or yaw >= 315:
            return "North"
        elif 45 <= yaw < 135:
            return "East"
        elif 135 <= yaw < 225:
            return "South"
        else:
            return "West"

    # ── Light Control ────────────────────────────────────────────

    def _set_direction_state(self, direction: str, state):
        """Set all lights in a direction group to a CARLA state."""
        for light in self._light_groups.get(direction, []):
            light.set_state(state)

    def _set_all_red(self):
        """All lights → Red."""
        for direction in self._light_groups:
            self._set_direction_state(direction, carla.TrafficLightState.Red)

    def _apply_allowed_lanes(self, allowed_lanes: List[str]):
        """
        Given our lane names like ["West_All", "South_Left"],
        set the corresponding CARLA light groups to Green.
        All others stay Red.

        Mapping:
          "West_All"   → West direction lights → Green
          "South_Left" → South direction lights → Green
          (In CARLA we can't control individual turn lanes,
           so any mention of a direction = that group goes Green)
        """
        # Start all Red
        self._set_all_red()

        # Extract unique directions from allowed lanes
        green_directions = set()
        for lane_name in allowed_lanes:
            # Parse "West_All" → "West", "South_Left" → "South"
            parts = lane_name.split("_")
            if parts:
                direction = parts[0]
                if direction in self._light_groups:
                    green_directions.add(direction)

        # Set green for allowed directions
        for direction in green_directions:
            self._set_direction_state(direction, carla.TrafficLightState.Green)

        return green_directions

    # ── Decision Processing ──────────────────────────────────────

    def receive_decision(self, decision: DecisionPayload):
        """Thread-safe: store latest decision from main_controller."""
        with self._lock:
            self.current_decision = decision
            # Reset phase to trigger new green cycle
            self._phase_state = "NEW_GREEN"
            self._phase_timer = 0.0
            self._green_duration = decision.allocated_times.get(
                decision.winner_phase, DEFAULT_GREEN
            )

    def tick(self, dt: float):
        """
        Called every HUD_REFRESH seconds. Runs the traffic light FSM:
          NEW_GREEN → GREEN → YELLOW → ALL_RED → (wait for next decision)
        """
        with self._lock:
            decision = self.current_decision

        if decision is None:
            return

        self._phase_timer += dt

        if self._phase_state == "NEW_GREEN":
            # Apply the decision immediately
            green_dirs = self._apply_allowed_lanes(decision.allowed_lanes)
            self._phase_state = "GREEN"
            self._phase_timer = 0.0
            winner = decision.winner_phase
            score = decision.priority_scores.get(winner, 0)
            lanes_str = " + ".join(decision.allowed_lanes)
            print(f"🟢 [Bridge] GREEN → {winner} (Score:{score}) | Lanes: {lanes_str} | Timer: {self._green_duration}s")

        elif self._phase_state == "GREEN":
            if self._phase_timer >= self._green_duration:
                # Transition to YELLOW
                self._phase_state = "YELLOW"
                self._phase_timer = 0.0
                # Set currently green lights to yellow
                green_dirs = set()
                for lane in decision.allowed_lanes:
                    parts = lane.split("_")
                    if parts and parts[0] in self._light_groups:
                        green_dirs.add(parts[0])
                for d in green_dirs:
                    self._set_direction_state(d, carla.TrafficLightState.Yellow)
                print(f"🟡 [Bridge] YELLOW ({YELLOW_DUR}s)")

        elif self._phase_state == "YELLOW":
            if self._phase_timer >= YELLOW_DUR:
                # All red safety gap
                self._set_all_red()
                self._phase_state = "ALL_RED"
                self._phase_timer = 0.0
                print(f"🔴 [Bridge] ALL RED ({ALL_RED_DUR}s)")

        elif self._phase_state == "ALL_RED":
            if self._phase_timer >= ALL_RED_DUR:
                # Wait for the next decision from main_controller
                self._phase_state = "WAITING"
                self._phase_timer = 0.0
                print(f"⏳ [Bridge] Waiting for next decision from main_controller...")

    def draw_hud(self):
        """Draw floating info above the junction in CARLA viewport."""
        with self._lock:
            decision = self.current_decision

        if not decision or not self._junction_center:
            return

        center = self._junction_center
        winner = decision.winner_phase
        score = decision.priority_scores.get(winner, 0)
        lanes_str = " + ".join(decision.allowed_lanes)
        state = decision.system_state

        # Remaining green time
        if self._phase_state == "GREEN":
            remaining = max(0, self._green_duration - self._phase_timer)
            timer_str = f"Green: {remaining:.0f}s"
        elif self._phase_state == "YELLOW":
            timer_str = f"Yellow: {max(0, YELLOW_DUR - self._phase_timer):.1f}s"
        elif self._phase_state == "ALL_RED":
            timer_str = f"All Red: {max(0, ALL_RED_DUR - self._phase_timer):.1f}s"
        else:
            timer_str = "Waiting..."

        # Saturation bar
        sat_str = ""
        if decision.phase_saturations:
            parts = [f"{d[0]}:{v:.1f}" for d, v in decision.phase_saturations.items()]
            sat_str = " | ".join(parts)

        # Draw multi-line HUD
        color_white = carla.Color(255, 255, 255)
        color_yellow = carla.Color(255, 255, 0)
        color_green = carla.Color(0, 255, 100)
        color_cyan = carla.Color(0, 200, 255)

        z = center.z
        lt = HUD_REFRESH + 0.05  # slightly longer than refresh

        self.debug.draw_string(
            center + carla.Location(z=14),
            f"WINNER: {winner} (Score: {score})",
            color=color_green, life_time=lt
        )
        self.debug.draw_string(
            center + carla.Location(z=12),
            f"OPEN: {lanes_str}",
            color=color_yellow, life_time=lt
        )
        self.debug.draw_string(
            center + carla.Location(z=10),
            f"STATE: {state} | {timer_str}",
            color=color_white, life_time=lt
        )
        if sat_str:
            self.debug.draw_string(
                center + carla.Location(z=8),
                sat_str,
                color=color_cyan, life_time=lt
            )

        # Score bars for all 4 directions
        scores = decision.priority_scores
        max_score = max(scores.values()) if scores else 1
        bar_text = "  ".join(
            f"{d[0]}:{'█' * max(1, int(s / max(1, max_score) * 10))}{s}"
            for d, s in scores.items()
        )
        self.debug.draw_string(
            center + carla.Location(z=6),
            bar_text,
            color=carla.Color(200, 200, 200), life_time=lt
        )


# ══════════════════════════════════════════════════════════════════
# FastAPI Server + CARLA Loop
# ══════════════════════════════════════════════════════════════════

app = FastAPI(title="CARLA Bridge", docs_url="/docs")
controller: Optional[JunctionController] = None


@app.post("/carla/decision")
def receive_decision(payload: DecisionPayload):
    """Receive a decision from main_controller and apply it to CARLA."""
    if controller is None:
        return {"status": "ERROR", "message": "CARLA not connected"}
    controller.receive_decision(payload)
    return {"status": "OK", "applied": payload.winner_phase}


@app.get("/carla/status")
def get_status():
    """Quick health check."""
    if controller is None:
        return {"connected": False}
    with controller._lock:
        d = controller.current_decision
    return {
        "connected": True,
        "phase_state": controller._phase_state,
        "current_winner": d.winner_phase if d else None,
        "allowed_lanes": d.allowed_lanes if d else [],
    }


def carla_loop():
    """Background thread: ticks the junction controller + HUD at high frequency."""
    global controller

    print(f"🚀 [Bridge] Connecting to CARLA at {CARLA_HOST}:{CARLA_PORT}...")
    client = carla.Client(CARLA_HOST, CARLA_PORT)
    client.set_timeout(20.0)
    world = client.get_world()
    map_name = world.get_map().name
    print(f"🗺️  [Bridge] Connected! Map: {map_name}")

    # Ensure Town05
    if "Town05" not in map_name:
        print("⚠️  [Bridge] Loading Town05...")
        client.load_world("Town05")
        world = client.get_world()

    controller = JunctionController(world, TARGET_JUNCTION_INDEX)
    print(f"✅ [Bridge] Junction controller ready. Listening on port {BRIDGE_PORT}...")

    last_time = time.time()
    while True:
        try:
            now = time.time()
            dt = now - last_time
            last_time = now

            controller.tick(dt)
            controller.draw_hud()

            time.sleep(HUD_REFRESH)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"⚠️  [Bridge] Loop error: {e}")
            time.sleep(1)


def main():
    # Start CARLA control loop in background thread
    carla_thread = threading.Thread(target=carla_loop, daemon=True)
    carla_thread.start()

    # Start FastAPI server (blocks main thread)
    print(f"🌐 [Bridge] Starting HTTP server on port {BRIDGE_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=BRIDGE_PORT, log_level="warning")


if __name__ == "__main__":
    main()
