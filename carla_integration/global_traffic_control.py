import glob
import os
import sys
import time
import math
import carla

# --- CONFIG ---
LOOKBACK_METERS = 80.0     # Depth of queue detection
PRIORITY_THRESHOLD = 8     # Base difference to switch
MIN_GREEN_TIME = 30        # ~3s minimum green
YELLOW_TIME = 20           # ~2s realistic yellow phase
ALL_RED_TIME = 15          # ~1.5s safety gap
MERCY_RATE = 0.8           # Priority growth for waiting lanes
EMERGENCY_BONUS = 500      # Massive weight for emergency vehicles

try:
    carla_root = r"C:\Users\Aynan Parvez Patait\Downloads\CARLA_0.9.16"
    sys.path.append(glob.glob(carla_root + '/PythonAPI/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

def is_aligned(yaw1, yaw2, threshold=45):
    diff = abs(yaw1 - yaw2) % 180
    return diff < threshold or diff > (180 - threshold)

def get_junction_load(vehicles, center_loc, trace_map):
    score_a = 0
    score_b = 0
    alert_a = False
    alert_b = False
    
    for v in vehicles:
        try:
            loc = v.get_location()
            dist = loc.distance(center_loc)
            if dist > LOOKBACK_METERS + 20: continue
            
            wp = v.get_world().get_map().get_waypoint(loc)
            key = (wp.road_id, wp.lane_id)
            
            if key in trace_map:
                # Base weight by distance
                weight = max(2, 12 - (dist / 10.0))
                
                # Emergency Vehicle Preemption
                bp = v.type_id.lower()
                is_emergency = "ambulance" in bp or "police" in bp or "firetruck" in bp
                if is_emergency:
                    weight += EMERGENCY_BONUS
                    if trace_map[key] == 'A': alert_a = True
                    else: alert_b = True
                
                if trace_map[key] == 'A': score_a += weight
                else: score_b += weight
        except: continue
    return score_a, score_b, alert_a, alert_b

def main():
    client = carla.Client('localhost', 2000)
    client.set_timeout(20.0)
    world = client.get_world()
    world_map = world.get_map()
    debug = world.debug

    print("🚥 Initializing Advanced Intelligence Traffic Controller...")
    
    all_lights = world.get_actors().filter('traffic.traffic_light')
    junction_groups = {}
    standalone_lights = []
    
    for l in all_lights:
        l.freeze(True)
        sws = l.get_stop_waypoints()
        if sws and sws[0].is_junction:
            jid = sws[0].junction_id
            if jid not in junction_groups: junction_groups[jid] = []
            junction_groups[jid].append(l)
        else:
            standalone_lights.append(l)

    intersections = []
    for jid, lights in junction_groups.items():
        all_locs = [l.get_location() for l in lights]
        center = carla.Location(sum(a.x for a in all_locs)/len(all_locs), sum(a.y for a in all_locs)/len(all_locs), sum(a.z for a in all_locs)/len(all_locs))
        intersections.append({'center': center, 'lights': lights, 'phase': 'A', 'state': 'GREEN', 'timer': 0, 'initialized': False, 'bonus_a': 0, 'bonus_b': 0, 'trace_map': {}, 'lights_a': [], 'lights_b': [], 'id': f"J-{jid}", 'alert': False})

    for l in standalone_lights:
        loc = l.get_location()
        found = False
        for intersect in intersections:
            if loc.distance(intersect['center']) < 30.0:
                intersect['lights'].append(l)
                found = True
                break
        if not found:
            intersections.append({'center': loc, 'lights': [l], 'phase': 'A', 'state': 'GREEN', 'timer': 0, 'initialized': False, 'bonus_a': 0, 'bonus_b': 0, 'trace_map': {}, 'lights_a': [], 'lights_b': [], 'id': "SA", 'alert': False})

    for junction in intersections:
        lights = junction['lights']
        sws_ref = lights[0].get_stop_waypoints()
        if not sws_ref: continue
        ref_yaw = sws_ref[0].transform.rotation.yaw
        for l in lights:
            sws = l.get_stop_waypoints()
            if not sws: continue
            l_yaw = sws[0].transform.rotation.yaw
            is_a = is_aligned(l_yaw, ref_yaw, threshold=35)
            target_group = 'A' if is_a else 'B'
            if is_a: junction['lights_a'].append(l)
            else: junction['lights_b'].append(l)
            for swp in sws:
                curr = swp
                meters = 0
                while meters < LOOKBACK_METERS:
                    junction['trace_map'][(curr.road_id, curr.lane_id)] = target_group
                    prevs = curr.previous(2.0)
                    if not prevs: break
                    curr = prevs[0]
                    meters += 2.0

    print(f"✅ Intelligence Suite Active: {len(intersections)} junctions upgraded.")

    while True:
        try:
            vehicles = world.get_actors().filter('vehicle.*')
            for junction in intersections:
                # 1. ADVANCED SCORING (Incl. Emergency Preemption)
                raw_a, raw_b, alert_a, alert_b = get_junction_load(vehicles, junction['center'], junction['trace_map'])
                junction['alert'] = alert_a or alert_b
                
                # 2. MERCY SYSTEM
                if junction['phase'] == 'A' and junction['state'] == 'GREEN':
                    junction['bonus_b'] += (MERCY_RATE if raw_b > 0 else 0)
                    junction['bonus_a'] = 0
                elif junction['phase'] == 'B' and junction['state'] == 'GREEN':
                    junction['bonus_a'] += (MERCY_RATE if raw_a > 0 else 0)
                    junction['bonus_b'] = 0
                
                total_a = raw_a + junction['bonus_a']
                total_b = raw_b + junction['bonus_b']

                # 3. ENHANCED DASHBOARD
                if total_a > 0 or total_b > 0:
                    color = carla.Color(255, 0, 0) if junction['alert'] else carla.Color(255, 255, 255)
                    alert_text = " [!] EMERGENCY" if junction['alert'] else ""
                    status = f"{junction['id']} | {junction['phase']} | {junction['state']} | T:{junction['timer']}{alert_text}"
                    debug.draw_string(junction['center'] + carla.Location(z=10), status, color=color, life_time=0.1)
                    debug.draw_string(junction['center'] + carla.Location(z=6), f"Load A:{total_a:.0f} | B:{total_b:.0f}", color=carla.Color(255,255,0), life_time=0.1)

                # 4. ADVANCED FINITE STATE MACHINE (Incl. Yellow Phase)
                junction['timer'] += 1
                
                if junction['state'] == 'GREEN':
                    if junction['timer'] > MIN_GREEN_TIME:
                        # Switch decision (Emergency vehicles override current thresholds)
                        switch = False
                        if junction['phase'] == 'A' and total_b > (total_a + PRIORITY_THRESHOLD): switch = True
                        elif junction['phase'] == 'B' and total_a > (total_b + PRIORITY_THRESHOLD): switch = True
                        
                        if switch:
                            junction['state'] = 'YELLOW'
                            junction['timer'] = 0
                            # Only set the current green lights to Yellow
                            active_lights = junction['lights_a'] if junction['phase'] == 'A' else junction['lights_b']
                            for l in active_lights: l.set_state(carla.TrafficLightState.Yellow)
                
                elif junction['state'] == 'YELLOW':
                    if junction['timer'] > YELLOW_TIME:
                        junction['state'] = 'ALL_RED'
                        junction['timer'] = 0
                        for l in junction['lights']: l.set_state(carla.TrafficLightState.Red)
                
                elif junction['state'] == 'ALL_RED':
                    if junction['timer'] > ALL_RED_TIME:
                        junction['phase'] = 'B' if junction['phase'] == 'A' else 'A'
                        junction['state'] = 'GREEN'
                        junction['timer'] = 0
                        target_group = junction['lights_a'] if junction['phase'] == 'A' else junction['lights_b']
                        for l in target_group: l.set_state(carla.TrafficLightState.Green)

                # INITIAL SYNC
                if not junction['initialized']:
                    junction['initialized'] = True
                    for l in junction['lights_a']: l.set_state(carla.TrafficLightState.Green if junction['phase'] == 'A' else carla.TrafficLightState.Red)
                    for l in junction['lights_b']: l.set_state(carla.TrafficLightState.Green if junction['phase'] == 'B' else carla.TrafficLightState.Red)

            time.sleep(0.1)
        except Exception as e:
            print(f"Update error: {e}")
            time.sleep(1)

if __name__ == '__main__':
    try: main()
    except KeyboardInterrupt: print("\nShutdown complete.")