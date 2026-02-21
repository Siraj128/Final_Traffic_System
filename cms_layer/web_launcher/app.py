from flask import Flask, render_template, jsonify, request
import subprocess
import sys
import os
import webbrowser
from threading import Timer

app = Flask(__name__)

# --- CONFIGURATION ---
# We assume main.py is in the parent directory of this folder
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MAIN_SCRIPT = os.path.join(PROJECT_ROOT, 'main_controller.py')

# --- TOPOLOGY DATA (Complete 40+ Nodes from Server.py) ---
NODES = {
    # --- WEST CORRIDOR (Blue) ---
    "PUNE_JW_01": { "name": "Bremen Chowk (Aundh)", "lat": 18.5529, "lng": 73.8066, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_02": { "name": "Pune University Circle", "lat": 18.5362, "lng": 73.8306, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_03": { "name": "E-Square Junction", "lat": 18.5320, "lng": 73.8340, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_04": { "name": "Sancheti Hospital Chowk", "lat": 18.5284, "lng": 73.8490, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_05": { "name": "Simla Office Chowk", "lat": 18.5260, "lng": 73.8500, "region": "West Corridor", "color": "blue" },

    # --- CORE LOOP (Red) ---
    "PUNE_JW_06": { "name": "Deccan Gymkhana Bus Stand", "lat": 18.5158, "lng": 73.8418, "region": "Core City", "color": "red" },
    "PUNE_JW_07": { "name": "Goodluck Chowk", "lat": 18.5167, "lng": 73.8405, "region": "Core City", "color": "red" },
    "PUNE_JW_08": { "name": "Fergusson College Gate", "lat": 18.5185, "lng": 73.8427, "region": "Core City", "color": "red" },
    "PUNE_JW_09": { "name": "Dnyaneshwar Paduka Chowk", "lat": 18.5222, "lng": 73.8415, "region": "Core City", "color": "red" },
    "PUNE_JW_10": { "name": "Jhansi Rani Chowk", "lat": 18.5200, "lng": 73.8460, "region": "Core City", "color": "red" },

    # --- KOTHRUD CORRIDOR (Orange) ---
    "PUNE_JW_11": { "name": "Chandani Chowk", "lat": 18.5080, "lng": 73.7920, "region": "Kothrud", "color": "orange" },
    "PUNE_JW_12": { "name": "Paud Phata", "lat": 18.5110, "lng": 73.8180, "region": "Kothrud", "color": "orange" },
    "PUNE_JW_13": { "name": "Nal Stop", "lat": 18.5085, "lng": 73.8240, "region": "Kothrud", "color": "orange" },

    # --- SOUTH CORRIDOR (Green) ---
    "PUNE_JW_15": { "name": "Katraj Snake Park", "lat": 18.4575, "lng": 73.8580, "region": "South Corridor", "color": "green" },
    "PUNE_JW_16": { "name": "Padmavati Chowk", "lat": 18.4800, "lng": 73.8590, "region": "South Corridor", "color": "green" },
    "PUNE_JW_17": { "name": "Swargate Jedhe Chowk", "lat": 18.5005, "lng": 73.8585, "region": "South Corridor", "color": "green" },
    "PUNE_JW_18": { "name": "Sarasbaug Junction", "lat": 18.5040, "lng": 73.8530, "region": "South Corridor", "color": "green" },

    # --- EAST CORRIDOR (Purple) ---
    "PUNE_JW_19": { "name": "Pune RTO Chowk", "lat": 18.5290, "lng": 73.8560, "region": "East Corridor", "color": "purple" },
    "PUNE_JW_20": { "name": "Pune Railway Station", "lat": 18.5289, "lng": 73.8744, "region": "East Corridor", "color": "purple" },
    "PUNE_JW_21": { "name": "Jehangir Hospital Chowk", "lat": 18.5300, "lng": 73.8760, "region": "East Corridor", "color": "purple" },
    "PUNE_JW_22": { "name": "Blue Diamond Chowk", "lat": 18.5380, "lng": 73.8850, "region": "East Corridor", "color": "purple" },
    "PUNE_JW_23": { "name": "Yerwada Gunjan Chowk", "lat": 18.5450, "lng": 73.8860, "region": "East Corridor", "color": "purple" },

    # --- NORTH CORRIDOR (Cyan) ---
    "PUNE_JW_24": { "name": "Viman Nagar Chowk", "lat": 18.5650, "lng": 73.9130, "region": "North Corridor", "color": "cyan" },
    "PUNE_JW_25": { "name": "Hyatt Regency Junction", "lat": 18.5600, "lng": 73.9100, "region": "North Corridor", "color": "cyan" },
    "PUNE_JW_26": { "name": "Shastrinagar Chowk", "lat": 18.5520, "lng": 73.8950, "region": "North Corridor", "color": "cyan" },

    # --- PCMC LINK (Teal) ---
    "PUNE_JW_27": { "name": "Nashik Phata", "lat": 18.6038, "lng": 73.8208, "region": "PCMC Link", "color": "teal" },
    "PUNE_JW_28": { "name": "Kasarwadi", "lat": 18.5866, "lng": 73.8205, "region": "PCMC Link", "color": "teal" },
    "PUNE_JW_29": { "name": "Dapodi", "lat": 18.5724, "lng": 73.8266, "region": "PCMC Link", "color": "teal" },

    # --- HADAPSAR CORRIDOR (Yellow) ---
    "PUNE_JW_30": { "name": "Magarpatta City Main Gate", "lat": 18.5144, "lng": 73.9257, "region": "Hadapsar", "color": "yellow" },
    "PUNE_JW_31": { "name": "Hadapsar Gadital", "lat": 18.5036, "lng": 73.9272, "region": "Hadapsar", "color": "yellow" },
    "PUNE_JW_32": { "name": "Fatima Nagar", "lat": 18.5065, "lng": 73.8990, "region": "Hadapsar", "color": "yellow" },

    # --- KHARADI EXTENSION (Magenta) ---
    "PUNE_JW_33": { "name": "Kharadi Bypass", "lat": 18.5510, "lng": 73.9350, "region": "Kharadi", "color": "magenta" },
    "PUNE_JW_34": { "name": "Phoenix Market City", "lat": 18.5620, "lng": 73.9170, "region": "Kharadi", "color": "magenta" },

    # --- CAMP AREA (Gold) ---
    "PUNE_JW_35": { "name": "Pulgate", "lat": 18.5060, "lng": 73.8790, "region": "Camp Area", "color": "gold" },
    "PUNE_JW_36": { "name": "Golibar Maidan", "lat": 18.5020, "lng": 73.8720, "region": "Camp Area", "color": "gold" }
}

@app.route('/')
def index():
    return render_template('index.html', nodes=NODES)

def update_env_file(junction_id):
    """Updates JUNCTION_ID in .env file."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_path):
        # Create if missing
        with open(env_path, 'w') as f:
            f.write(f"JUNCTION_ID={junction_id}\n")
        return

    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        found = False
        for line in lines:
            if line.startswith("JUNCTION_ID="):
                new_lines.append(f"JUNCTION_ID={junction_id}\n")
                found = True
            else:
                new_lines.append(line)
        
        if not found:
            new_lines.append(f"\nJUNCTION_ID={junction_id}\n")
        
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        print(f"✅ Updated .env with JUNCTION_ID={junction_id}")
        
    except Exception as e:
        print(f"❌ Failed to update .env: {e}")

@app.route('/launch', methods=['POST'])
def launch_node():
    data = request.json
    node_id = data.get('id')
    mode = data.get('mode', 'VIDEO') # Default to VIDEO
    detect_method = data.get('detect_method', 'HYBRID')
    show_video = data.get('show_video', True)
    
    if not node_id:
        return jsonify({"status": "error", "message": "No ID provided"}), 400
        
    print(f"🚀 Launching Node: {node_id} | Mode: {mode} | Method: {detect_method} | Show: {show_video}")
    
    # 1. Update .env
    update_env_file(node_id)
    
    try:
        # 2. Construct Command
        # python main_controller.py --video (or --camera)
        args = [sys.executable, MAIN_SCRIPT]
        
        # Source Mode
        if mode == "VIDEO": args.append("--video")
        elif mode == "CAMERA": args.append("--camera")
        elif mode == "GHOST": args.append("--ghost")
        
        # Detection Method
        if detect_method == "GRID": args.append("--grid")
        elif detect_method == "HYBRID": args.append("--hybrid")
        
        # Visualization
        if show_video: args.append("--show")
        
        # ROI Configuration
        show_roi = data.get('show_roi', True)
        if not show_roi:
            args.append("--no-roi")

        # ANPR Mode (Phase 18)
        anpr_mode = data.get('anpr_mode', 'REAL')
        if anpr_mode == "DUMMY":
            args.append("--dummy-anpr")
        
        # 3. Launch
        subprocess.Popen(args, cwd=PROJECT_ROOT)
        
        return jsonify({"status": "success", "message": f"Node {node_id} Activated ({mode})"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    # Auto-open the browser after 1 second
    Timer(1, open_browser).start()
    app.run(port=5000)