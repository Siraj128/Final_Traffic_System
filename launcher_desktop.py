import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os
import tkintermapview # Ensure this is installed: pip install tkintermapview

# --- CONFIGURATION ---
APP_TITLE = "Smart-Net Traffic Command"
THEME_BG = "#1e1e1e"
PANEL_BG = "#252526"
ACCENT_COLOR = "#007acc"
TEXT_COLOR = "#ffffff"
SUBTEXT_COLOR = "#aaaaaa"

# --- TOPOLOGY WITH REGIONS ---
TOPOLOGY_NODES = {
    # WEST (Blue)
    "PUNE_JW_01": { "name": "Bremen Chowk", "lat": 18.5529, "lng": 73.8066, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_02": { "name": "Pune University", "lat": 18.5362, "lng": 73.8306, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_03": { "name": "E-Square Junction", "lat": 18.5320, "lng": 73.8340, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_04": { "name": "Sancheti Hospital", "lat": 18.5284, "lng": 73.8490, "region": "West Corridor", "color": "blue" },
    "PUNE_JW_05": { "name": "Simla Office", "lat": 18.5260, "lng": 73.8500, "region": "West Corridor", "color": "blue" },

    # CORE (Red)
    "PUNE_JW_06": { "name": "Deccan Gymkhana", "lat": 18.5158, "lng": 73.8418, "region": "Core City", "color": "red" },
    "PUNE_JW_07": { "name": "Goodluck Chowk", "lat": 18.5167, "lng": 73.8405, "region": "Core City", "color": "red" },
    "PUNE_JW_08": { "name": "Fergusson College", "lat": 18.5185, "lng": 73.8427, "region": "Core City", "color": "red" },
    
    # KOTHRUD (Orange)
    "PUNE_JW_11": { "name": "Chandani Chowk", "lat": 18.5080, "lng": 73.7920, "region": "Kothrud", "color": "orange" },
    "PUNE_JW_12": { "name": "Paud Phata", "lat": 18.5110, "lng": 73.8180, "region": "Kothrud", "color": "orange" },
    
    # SOUTH (Green)
    "PUNE_JW_17": { "name": "Swargate Jedhe", "lat": 18.5005, "lng": 73.8585, "region": "South Corridor", "color": "green" },
    "PUNE_JW_15": { "name": "Katraj Snake Park", "lat": 18.4575, "lng": 73.8580, "region": "South Corridor", "color": "green" },

    # EAST (Purple)
    "PUNE_JW_20": { "name": "Pune Station", "lat": 18.5289, "lng": 73.8744, "region": "East Corridor", "color": "purple" },
    "PUNE_JW_23": { "name": "Yerwada Gunjan", "lat": 18.5450, "lng": 73.8860, "region": "East Corridor", "color": "purple" },

    # PCMC (Cyan)
    "PUNE_JW_27": { "name": "Nashik Phata", "lat": 18.6038, "lng": 73.8208, "region": "PCMC Link", "color": "cyan" },
    "PUNE_JW_28": { "name": "Kasarwadi", "lat": 18.5866, "lng": 73.8205, "region": "PCMC Link", "color": "cyan" },
    
    # HADAPSAR (Yellow)
    "PUNE_JW_30": { "name": "Magarpatta City", "lat": 18.5144, "lng": 73.9257, "region": "Hadapsar", "color": "yellow" },
}

class ModernLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1100x700")
        self.root.configure(bg=THEME_BG)
        
        # State
        self.selected_node = None

        # --- LAYOUT: 70% Map (Left), 30% Panel (Right) ---
        self.root.grid_columnconfigure(0, weight=3) # Map
        self.root.grid_columnconfigure(1, weight=1) # Panel
        self.root.grid_rowconfigure(0, weight=1)

        # --- 1. LEFT: MAP WIDGET ---
        self.map_frame = tk.Frame(self.root, bg=THEME_BG)
        self.map_frame.grid(row=0, column=0, sticky="nsew")
        
        self.map_widget = tkintermapview.TkinterMapView(self.map_frame, width=800, height=700, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True)
        
        # Map Settings (Google Dark Mode Style approximation)
        self.map_widget.set_position(18.5204, 73.8567) # Center on Pune
        self.map_widget.set_zoom(12)
        self.map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=22)

        # --- 2. RIGHT: CONTROL PANEL ---
        self.panel = tk.Frame(self.root, bg=PANEL_BG, padx=20, pady=20)
        self.panel.grid(row=0, column=1, sticky="nsew")
        self.panel.grid_propagate(False) # Stop shrinking

        # Logo / Title
        tk.Label(self.panel, text="SMART-NET", font=("Segoe UI", 24, "bold"), 
                 bg=PANEL_BG, fg=ACCENT_COLOR).pack(anchor="w", pady=(0, 5))
        tk.Label(self.panel, text="Traffic OS Launcher", font=("Segoe UI", 10), 
                 bg=PANEL_BG, fg=SUBTEXT_COLOR).pack(anchor="w", pady=(0, 30))

        # Divider
        tk.Frame(self.panel, bg="#444", height=1).pack(fill="x", pady=10)

        # Info Card Area (Hidden initially)
        self.info_frame = tk.Frame(self.panel, bg=PANEL_BG)
        self.info_frame.pack(fill="x", pady=20)
        
        self.lbl_region = tk.Label(self.info_frame, text="REGION", font=("Segoe UI", 9, "bold"), 
                                   bg=PANEL_BG, fg=SUBTEXT_COLOR)
        self.lbl_region.pack(anchor="w")
        
        self.lbl_name = tk.Label(self.info_frame, text="Select a Junction", font=("Segoe UI", 18, "bold"), 
                                 bg=PANEL_BG, fg=TEXT_COLOR, wraplength=250, justify="left")
        self.lbl_name.pack(anchor="w", pady=5)
        
        self.lbl_id = tk.Label(self.info_frame, text="--", font=("Segoe UI", 10, "italic"), 
                               bg=PANEL_BG, fg=ACCENT_COLOR)
        self.lbl_id.pack(anchor="w")

        # Coordinates
        self.lbl_coords = tk.Label(self.info_frame, text="", font=("Consolas", 9), 
                                   bg=PANEL_BG, fg="#666")
        self.lbl_coords.pack(anchor="w", pady=10)

        # Divider
        tk.Frame(self.panel, bg="#444", height=1).pack(fill="x", pady=20)

        # Status
        tk.Label(self.panel, text="SYSTEM STATUS", font=("Segoe UI", 9, "bold"), 
                 bg=PANEL_BG, fg=SUBTEXT_COLOR).pack(anchor="w")
        
        self.status_indicator = tk.Label(self.panel, text="● READY", font=("Segoe UI", 10), 
                                         bg=PANEL_BG, fg="#4caf50") # Green
        self.status_indicator.pack(anchor="w", pady=5)

        # Mode Selection
        tk.Label(self.panel, text="OPERATING MODE", font=("Segoe UI", 9, "bold"), 
                 bg=PANEL_BG, fg=SUBTEXT_COLOR).pack(anchor="w", pady=(15, 5))
        
        self.mode_var = tk.StringVar(value="VIDEO")
        self.mode_combo = ttk.Combobox(self.panel, textvariable=self.mode_var, state="readonly",
                                     values=["VIDEO", "CAMERA", "GHOST", "TEST"])
        self.mode_combo.pack(fill="x", pady=5)

        # Launch Button (Big)
        self.btn_launch = tk.Button(self.panel, text="🚀  ACTIVATE NODE", 
                                    font=("Segoe UI", 12, "bold"), bg="#333", fg="#777",
                                    relief="flat", cursor="arrow", state="disabled",
                                    command=self.launch_node)
        self.btn_launch.pack(side="bottom", fill="x", pady=20, ipady=10)

        # --- LOAD PINS ---
        self.load_markers()

    def load_markers(self):
        for j_id, data in TOPOLOGY_NODES.items():
            # Markers with color coding
            # Note: tkintermapview supports basic color markers or images
            self.map_widget.set_marker(
                data["lat"], data["lng"], 
                text=data["name"],
                marker_color_circle=data.get("color", "blue"),
                marker_color_outside=data.get("color", "blue"),
                command=lambda m, j=j_id: self.on_marker_click(j)
            )

    def on_marker_click(self, j_id):
        self.selected_node = j_id
        data = TOPOLOGY_NODES[j_id]
        
        # Update UI Panel
        self.lbl_region.config(text=data["region"].upper(), fg=data["color"])
        self.lbl_name.config(text=data["name"])
        self.lbl_id.config(text=f"ID: {j_id}")
        self.lbl_coords.config(text=f"Lat: {data['lat']}\nLng: {data['lng']}")
        
        # Activate Button
        self.btn_launch.config(state="normal", bg=ACCENT_COLOR, fg="white", cursor="hand2")
        self.status_indicator.config(text=f"● TARGET LOCKED: {j_id}", fg=ACCENT_COLOR)

    def launch_node(self):
        if not self.selected_node: return
        
        mode = self.mode_var.get()
        print(f"🚀 Initializing {mode} Sequence for {self.selected_node}...")
        
        # 1. Update .env with Selected Node
        self.update_env_file(self.selected_node)
        
        python_exe = sys.executable
        script_to_run = "main_controller.py"
        
        if not os.path.exists(script_to_run):
            messagebox.showerror("Error", f"Critical File Missing: {script_to_run}")
            return

        # 2. Construct Flags
        args = [python_exe, script_to_run]
        if mode == "VIDEO": args.append("--video")
        elif mode == "CAMERA": args.append("--camera")
        elif mode == "GHOST": args.append("--ghost")
        
        try:
            # Spawn independent process
            subprocess.Popen(args)
            self.status_indicator.config(text=f"● RUNNING: {self.selected_node} ({mode})", fg="#4caf50")
            
        except Exception as e:
            messagebox.showerror("Launch Error", str(e))

    def update_env_file(self, junction_id):
        """Updates JUNCTION_ID in .env file."""
        env_path = ".env"
        if not os.path.exists(env_path): return
        
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

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernLauncher(root)
    root.mainloop()