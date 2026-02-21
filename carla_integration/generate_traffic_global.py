"""
generate_traffic_global.py  —  CARLA Vehicle Spawner

Spawns vehicles on Town05 for the traffic simulation demo.
Positions the spectator camera above the target junction.

Usage:
    python carla_integration/generate_traffic_global.py
"""
import glob
import json
import os
import sys
import time
import random

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# ── Resolve CARLA egg ────────────────────────────────────────────
_carla_root = os.getenv("CARLA_ROOT", "")
if not _carla_root:
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

import carla

# ── Load config ──────────────────────────────────────────────────
_config_path = os.path.join(_PROJECT_ROOT, "config", "carla_config.json")
try:
    with open(_config_path) as f:
        CONFIG = json.load(f)
except FileNotFoundError:
    CONFIG = {}

VEHICLE_COUNT = CONFIG.get("vehicle_count", 40)
SPECTATOR_HEIGHT = CONFIG.get("spectator_height", 50)


def main():
    try:
        host = CONFIG.get("carla_host", "localhost")
        port = CONFIG.get("carla_port", 2000)

        client = carla.Client(host, port)
        client.set_timeout(20.0)

        # 1. Ensure Town05
        world = client.get_world()
        if "Town05" not in world.get_map().name:
            print("⚠️  Loading Town05...")
            client.load_world('Town05')
            world = client.get_world()

        # 2. Clean up old vehicles
        print("🧹 Clearing old vehicles...")
        client.apply_batch([
            carla.command.DestroyActor(x)
            for x in world.get_actors().filter('vehicle.*')
        ])
        time.sleep(1)

        # 3. Set up Traffic Manager
        print(f"🚗 Spawning {VEHICLE_COUNT} vehicles across Town05...")
        traffic_manager = client.get_trafficmanager(8000)
        traffic_manager.set_global_distance_to_leading_vehicle(2.5)
        traffic_manager.set_hybrid_physics_mode(True)

        # 4. Spawn vehicles
        blueprints = world.get_blueprint_library().filter('vehicle.*')
        blueprints = [x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4]
        spawn_points = world.get_map().get_spawn_points()

        batch = []
        for i in range(min(VEHICLE_COUNT, len(spawn_points))):
            bp = random.choice(blueprints)
            bp.set_attribute('role_name', 'autopilot')
            transform = spawn_points[i]
            batch.append(
                carla.command.SpawnActor(bp, transform)
                .then(carla.command.SetAutopilot(
                    carla.command.FutureActor, True,
                    traffic_manager.get_port()
                ))
            )

        responses = client.apply_batch_sync(batch, True)
        success = len([r for r in responses if not r.error])
        print(f"✅ Active Vehicles: {success}/{VEHICLE_COUNT}")

        # 5. Position spectator above first junction (bridge will reposition later)
        all_lights = world.get_actors().filter('traffic.traffic_light')
        if all_lights:
            locs = [l.get_location() for l in all_lights[:4]]
            cx = sum(p.x for p in locs) / len(locs)
            cy = sum(p.y for p in locs) / len(locs)
            cz = sum(p.z for p in locs) / len(locs)
            spectator = world.get_spectator()
            spectator.set_transform(carla.Transform(
                carla.Location(cx, cy, cz + SPECTATOR_HEIGHT),
                carla.Rotation(pitch=-90)
            ))
            print(f"📷 Spectator positioned above junction")

        print("\n✅ Traffic spawned! Now start:")
        print("   python carla_integration/carla_bridge.py")
        print("   python main_controller.py")
        print("\nPress Ctrl+C to stop.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == '__main__':
    main()