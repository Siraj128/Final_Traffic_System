import carla
import time

def main():
    client = carla.Client("localhost", 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    print("🔍 Discovering Junctions in Town05...")
    
    all_lights = world.get_actors().filter('traffic.traffic_light')
    
    # Same clustering logic as carla_bridge.py
    junction_groups = {}
    standalone_lights = []
    
    for light in all_lights:
        stop_wps = light.get_stop_waypoints()
        if stop_wps and stop_wps[0].is_junction:
            jid = stop_wps[0].junction_id
            junction_groups.setdefault(jid, []).append(light)
        else:
            standalone_lights.append(light)
            
    clusters = list(junction_groups.values())
    for l in standalone_lights:
        loc = l.get_location()
        found_cluster = False
        for cluster in clusters:
            cx = sum(c.get_location().x for c in cluster) / len(cluster)
            cy = sum(c.get_location().y for c in cluster) / len(cluster)
            cz = sum(c.get_location().z for c in cluster) / len(cluster)
            center = carla.Location(cx, cy, cz)
            if loc.distance(center) < 30.0:
                cluster.append(l)
                found_cluster = True
                break
        if not found_cluster:
            clusters.append([l])
            
    junction_groups = {i: cluster for i, cluster in enumerate(clusters) if len(cluster) > 1}
    jids = sorted(junction_groups.keys())
    
    print(f"\n✅ Found {len(jids)} valid intersections!")
    print("Switch to the CARLA window. We will teleport your camera to each junction.")
    print("Tell me which 'Junction Index' matches the image you uploaded.\n")
    
    spectator = world.get_spectator()
    for index, jid in enumerate(jids):
        lights = junction_groups[jid]
        cx = sum(l.get_location().x for l in lights) / len(lights)
        cy = sum(l.get_location().y for l in lights) / len(lights)
        cz = sum(l.get_location().z for l in lights) / len(lights)
        
        spectator.set_transform(carla.Transform(
            carla.Location(cx, cy, cz + 30),
            carla.Rotation(pitch=-90)
        ))
        
        input(f"📷 This is Junction Index: {index}. Press ENTER to see the next one...")

if __name__ == "__main__":
    main()
