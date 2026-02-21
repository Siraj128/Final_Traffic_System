"""
main_controller.py — The Orchestrator (Part 6, 8, 11)

This is the BRAIN of the HTMS Edge Server.
It manages the complete signal cycle lifecycle:

    GREEN (dynamic) → FREEZE (T-3s) → YELLOW (15s) → DEADLINE (T-10s) → ACTUATION → repeat

Architecture:
    - VisionThread (×4): One per phase camera, feeds SharedQueue
    - DecisionThread (×1): Timer-driven state machine, reads SharedQueue
    - BackgroundThread (×1): Async CMS heartbeat + cloud sync
    - SignalInterface: Actuates the physical/simulated traffic lights

Data Flow:
    Camera → DetectionController → SharedQueue → DecisionMaker → SignalInterface
                                                    ↑
                                             FreezeSnapshot (from Aynan's Local Memory)
"""

import os
import sys
import time
import json
import threading
import traceback
from queue import Queue, Empty
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import config
from core_logic.decision_maker import DecisionMaker
from core_logic.traffic_standards import classify_state
from core_logic.traffic_standards import classify_state
from cms_layer.cms_connector import CMSConnector
from background_service import BackgroundService # Heavy Ops


# =============================================================================
# 1. SHARED QUEUE — Thread-Safe Vision → Logic Bridge
# =============================================================================

class SharedQueue:
    """
    Thread-safe data bridge between Vision threads and the Decision thread.
    
    Vision threads WRITE their latest telemetry here.
    The Decision thread READS all lanes' data when it needs to calculate.
    
    This is NOT a FIFO queue — it's a "latest value" store.
    Each phase overwrites its previous data on every frame.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._data = {}           # {"North": {...lane_data...}, "South": {...}, ...}
        self._raw_detections = {} # {"North": [...bboxes...], ...} for HybridCore
        self._intersection_status = "CLEAR"
        self._last_update = {}    # {"North": timestamp, ...}
        self._last_update = {}    # {"North": timestamp, ...}
        self._frames = {}         # {"North": frame, ...}
        self._active_phase = "North" # Default green phase
    
    def update_frame(self, source, frame):
        """Called by Vision/Monitor threads to push latest video frame."""
        # Using a shallow copy or just ref is fine for display
        with self._lock:
            self._frames[source] = frame.copy() if frame is not None else None

    def get_latest_frames(self):
        """Returns dict of all latest frames."""
        with self._lock:
            return dict(self._frames)
    
    def update_phase(self, phase_name, lane_data, raw_detections=None, intersection_status=None):
        """Called by Vision threads after processing a frame."""
        with self._lock:
            self._data[phase_name] = lane_data
            if raw_detections is not None:
                self._raw_detections[phase_name] = raw_detections
            # intersection_status is now global, managed by Camera 5
            self._last_update[phase_name] = time.time()

    def update_global_status(self, status):
        """Called by IntersectionMonitorThread (Camera 5)."""
        with self._lock:
            self._intersection_status = status

    def set_active_phase(self, phase_name):
        """Called by MainController to set which phase is GREEN."""
        with self._lock:
            self._active_phase = phase_name

    def get_phase_color(self, phase_name):
        """Returns 'GREEN' if active, else 'RED'."""
        with self._lock:
            return "GREEN" if phase_name == self._active_phase else "RED"
    
    def get_snapshot(self):
        """
        Called by Decision thread at Freeze point.
        Returns a COPY of all current data (thread-safe snapshot).
        """
        with self._lock:
            return {
                "lane_data": dict(self._data),
                "raw_detections": dict(self._raw_detections),
                "intersection_status": self._intersection_status,
                "timestamps": dict(self._last_update)
            }
    
    def get_staleness(self, phase_name, current_time=None):
        """Returns how many seconds since a phase last updated. -1 if never."""
        if current_time is None:
            current_time = time.time()
        with self._lock:
            last = self._last_update.get(phase_name)
            if last is None:
                return -1
            return current_time - last


# =============================================================================
# 2. FREEZE SESSION — Aynan's Local Memory (Part 11)
# =============================================================================

class FreezeSession:
    """
    Captures and stores the system state at the T-3s Freeze point.
    This is the "Hot Storage" from Part 11 — Aynan's Edge Database.
    
    In production: backed by SQLite or Redis.
    For now: in-memory with JSON file persistence for crash recovery.
    """
    
    def __init__(self, persist_path=None):
        self._lock = threading.Lock()
        self.snapshot = None
        self.persist_path = persist_path or os.path.join(PROJECT_ROOT, ".freeze_session.json")
    
    def capture(self, shared_queue_snapshot, congestion_state, opened_lanes):
        """Called at T-3s: freeze the current state."""
        with self._lock:
            self.snapshot = {
                "timestamp": time.time(),
                "lane_data": shared_queue_snapshot["lane_data"],
                "raw_detections": shared_queue_snapshot["raw_detections"],
                "intersection_status": shared_queue_snapshot["intersection_status"],
                "congestion_state": congestion_state,
                "opened_lanes": opened_lanes
            }
            # Persist to disk for crash recovery
            self._persist()
        return self.snapshot
    
    def get(self):
        """Called during Processing Window to read the frozen data."""
        with self._lock:
            return self.snapshot
    
    def _persist(self):
        """Write snapshot to JSON file (non-critical, best-effort)."""
        try:
            # Convert non-serializable items
            safe_snapshot = {
                "timestamp": self.snapshot["timestamp"],
                "congestion_state": self.snapshot["congestion_state"],
                "opened_lanes": self.snapshot["opened_lanes"],
                "intersection_status": self.snapshot["intersection_status"]
            }
            with open(self.persist_path, 'w') as f:
                json.dump(safe_snapshot, f, indent=2)
        except Exception:
            pass  # Non-critical — don't crash the system for persistence


# =============================================================================
# 3. SIGNAL INTERFACE — Controls Traffic Lights
# =============================================================================

class SignalInterface:
    """
    Abstraction layer for traffic light control.
    
    In LIVE mode:  Sends GPIO/serial commands to physical lights.
    In GHOST mode: Sends TraCI commands to SUMO simulator.
    In TEST mode:  Just prints state changes.
    """
    
    def __init__(self, mode="TEST"):
        self.mode = mode
        self.current_phase = None
        self.current_signal = "RED_ALL"  # Startup: all red
        self._carla_bridge = None
    
    def set_carla_bridge(self, bridge):
        """Inject CARLA bridge for Ghost mode."""
        self._carla_bridge = bridge
        self.mode = "GHOST"
    
    def actuate(self, winner_phase, allowed_lanes, green_time):
        """
        Change the traffic lights.
        """
        self.current_phase = winner_phase
        self.current_signal = "GREEN"
        
        if self.mode == "TEST":
            print(f"    🚦 [SIGNAL] GREEN → {winner_phase} ({green_time}s)")
            print(f"    🚦 [SIGNAL] Open lanes: {allowed_lanes}")
        elif self.mode == "GHOST" and self._carla_bridge:
            # CARLA Bridge: Set specific phase to GREEN, others to RED implied or handled by bridge logic
            # For now, we only explicitly set the green phase. 
            # Ideally bridge handles clearing others or we call set_all_red first.
            self._carla_bridge.apply_light_state(winner_phase, "GREEN")

    def set_yellow(self):
        """All directions go yellow."""
        self.current_signal = "YELLOW"
        if self.mode == "TEST":
            print(f"    🟡 [SIGNAL] YELLOW — All directions")
        elif self.mode == "GHOST" and self._carla_bridge:
             if self.current_phase:
                self._carla_bridge.apply_light_state(self.current_phase, "YELLOW")
    
    def set_all_red(self):
        """All directions go red (safety clearance)."""
        self.current_signal = "RED_ALL"
        if self.mode == "TEST":
            print(f"    🔴 [SIGNAL] ALL RED — Junction clearing")
        elif self.mode == "GHOST" and self._carla_bridge:
            # Creating a 'RED' call for the last active phase or all
            # Simple approach: explicitly Red the current phase if known
            if self.current_phase:
                 self._carla_bridge.apply_light_state(self.current_phase, "RED")


# =============================================================================
# 4. VISION THREAD — One Per Camera
# =============================================================================

class VisionThread(threading.Thread):
    """
    Runs the detection pipeline on one camera feed.
    Pushes results to the SharedQueue continuously.
    
    In GHOST mode: reads from SUMO instead of a physical camera.
    """
    
    # Default video file mapping: phase name → video path
    VIDEO_MAP = {
        "North": os.path.join(PROJECT_ROOT, "tools", "north.mp4"),
        "South": os.path.join(PROJECT_ROOT, "tools", "south.mp4"),
        "East":  os.path.join(PROJECT_ROOT, "tools", "east.mp4"),
        "West":  os.path.join(PROJECT_ROOT, "tools", "west.mp4"),
    }
    
    def __init__(self, phase_name, shared_queue, source="GHOST", camera_index=None, video_path=None, bridge=None):
        super().__init__(daemon=True, name=f"Vision-{phase_name}")
        self.phase_name = phase_name
        self.shared_queue = shared_queue
        self.source = source
        self.camera_index = camera_index
        self.video_path = video_path or self.VIDEO_MAP.get(phase_name)
        self.bridge = bridge # Store reference to CARLA bridge

        self._stop_event = threading.Event()
        self._detection_controller = None
        self.show_video = False
        self.detect_method = "HYBRID" # Default
        self.show_roi = True
        self.dummy_anpr = False # Default
        
    def configure(self, show_video=False, method="HYBRID", show_roi=True, dummy_anpr=False):
        self.show_video = show_video
        self.detect_method = method
        self.show_roi = show_roi
        self.dummy_anpr = dummy_anpr
        
    def _init_detector(self):
        """Initialize detection controller with phase-specific ROI config."""
        try:
            from vision_fast.detection_controller import DetectionController
            
            # Load the phase's Hybrid ROI config (e.g., config_Phase_North_Hybrid.json)
            config_path = os.path.join(
                PROJECT_ROOT, "config", "Hybrid_Based_System",
                f"config_Phase_{self.phase_name}_Hybrid.json"
            )
            
            phase_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    phase_config = json.load(f)
                print(f"    📄 [Vision-{self.phase_name}] Loaded ROI config: {os.path.basename(config_path)}")
            else:
                print(f"    ⚠️ [Vision-{self.phase_name}] No ROI config at: {config_path}")
            
            # Inject ANPR Mode
            phase_config["anpr_dummy_mode"] = self.dummy_anpr
            
            self._detection_controller = DetectionController(phase_config)
            # Inject Method override if needed
            if hasattr(self._detection_controller, 'set_method'):
                self._detection_controller.set_method(self.detect_method)
            elif self.detect_method == "GRID":
                # Fallback: Modify config directly if supported or print warning
                print(f"    ℹ️ [Vision-{self.phase_name}] Optimized for GRID mode (Lane Counts Only)")
                # (Logic handled inside DetectionController based on config usually, but we forced it)
            
            # Call initialize() to fully set up detector, lane mapper, zone analyzer
            if not self._detection_controller.initialize():
                print(f"    ⚠️ [Vision-{self.phase_name}] Detector initialize() failed — will use raw frames")
                self._detection_controller = None
                
        except Exception as e:
            print(f"    ⚠️ [Vision-{self.phase_name}] Detector init failed: {e}")
            self._detection_controller = None
    
    def run(self):
        """Main loop: capture → detect → push to SharedQueue."""
        print(f"    \U0001f441\ufe0f [Vision-{self.phase_name}] Started ({self.source})")
        
        if self.source == "CAMERA":
            self._init_detector()
            self._run_camera_loop()
        elif self.source == "VIDEO":
            self._init_detector()
            self._run_video_loop()
        elif self.source == "GHOST":
            self._run_ghost_loop()
        else:
            print(f"    \u26a0\ufe0f [Vision-{self.phase_name}] Unknown source: {self.source}")
    
    def _run_camera_loop(self):
        """Process frames from a physical camera."""
        import cv2
        cap = cv2.VideoCapture(self.camera_index or 0)
        
        while not self._stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
                # Check Light State for Reward Logic
                light_state = self.shared_queue.get_phase_color(self.phase_name)
                
                result = self._detection_controller.process_frame(
                    frame, 
                    visualize=self.show_video, 
                    detect_mode=self.detect_method, 
                    show_roi=self.show_roi, 
                    phase_name=self.phase_name,
                    light_state=light_state
                )
                if result.get("status") == "success":
                    self.shared_queue.update_phase(
                        self.phase_name,
                        lane_data=result.get("lane_data", {}),
                        raw_detections=result.get("raw_detections", []),
                        intersection_status=result.get("intersection_status", "CLEAR")
                    )
            
            # Push to SharedQueue for Visualization
            if self.show_video:
                h, w = frame.shape[:2]
                # Add overlay (Bottom Left)
                if self._detection_controller:
                    cv2.putText(frame, f"{self.detect_method}", (10, h-40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"FPS: {int(1.0/(time.time()-t0) if (time.time()-t0)>0 else 0)}", (10, h-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                     cv2.putText(frame, "DETECTOR FAILED", (10, h-20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            
                self.shared_queue.update_frame(self.phase_name, frame)
            
            time.sleep(0.033)  # ~30fps cap
        
        cap.release()
    
    def _run_video_loop(self):
        """
        Process frames from a video file (tools/*.mp4).
        Loops the video on EOF for continuous testing.
        """
        import cv2
        
        if not self.video_path or not os.path.exists(self.video_path):
            print(f"    \u26a0\ufe0f [Vision-{self.phase_name}] Video not found: {self.video_path}")
            return
        
        print(f"    \U0001f3ac [Vision-{self.phase_name}] Playing: {os.path.basename(self.video_path)}")
        
        while not self._stop_event.is_set():
            cap = cv2.VideoCapture(self.video_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_delay = 1.0 / fps
            frame_num = 0
            
            while not self._stop_event.is_set():
                ret, frame = cap.read()
                if not ret:
                    # Video ended — loop back to start
                    print(f"    \U0001f501 [Vision-{self.phase_name}] Looping video...")
                    break
                
                # Cosmetic: Flip frames to simulate different angles if using same video
                # Frame flipping removed to ensure ROI alignment
                pass
                
                frame_num += 1
                result = {} # Initialize default
                
                if self._detection_controller:
                    # Visualization handled here
                    try:
                        light_state = self.shared_queue.get_phase_color(self.phase_name)
                        result = self._detection_controller.process_frame(
                            frame, 
                            visualize=self.show_video, 
                            detect_mode=self.detect_method, 
                            show_roi=self.show_roi, 
                            phase_name=self.phase_name,
                            light_state=light_state
                        )
                        if result.get("status") == "error":
                            print(f"[Vision-{self.phase_name}] Frame Error: {result.get('error')}")
                    except Exception as e:
                        print(f"[Vision-{self.phase_name}] CRITICAL EXCEPTION: {e}")
                        import traceback
                        traceback.print_exc()
                        result = {"status": "error"}
                    if result.get("status") == "success":
                        self.shared_queue.update_phase(
                            self.phase_name,
                            lane_data=result.get("lane_data", {}),
                            raw_detections=result.get("raw_detections", []),
                            intersection_status=result.get("intersection_status", "CLEAR")
                        )
                        # Print progress every 100 frames
                        if frame_num % 100 == 0:
                            vcount = result.get("vehicle_count", 0)
                            print(f"    \U0001f4f9 [Vision-{self.phase_name}] Frame {frame_num}: {vcount} vehicles detected")
                
                
                # Push to SharedQueue for Visualization
                if self.show_video:
                     h, w = frame.shape[:2]
                     # Overlay status handled in Visualizer or here? Better here.
                     color = (0,0,255) if result.get("intersection_status") == "BLOCKED" else (0,255,0)
                     
                     # Create a display copy to apply cosmetic flips (so ROI logic isn't affected!)
                     display_frame = frame.copy()
                     if self.phase_name == "South":
                         pass # Keep original
                     elif self.phase_name == "East":
                         pass # display_frame = cv2.flip(display_frame, 1) # REMOVED: Causes text mirroring
                     elif self.phase_name == "West":
                         pass # display_frame = cv2.flip(display_frame, 1) # REMOVED: Causes text mirroring
                         
                     # Re-draw status on flipped frame?
                     # No, status is text. If we flip after text, text is mirrored.
                     # But 'frame' already has text from process_frame (MODE, ROI).
                     # If we flip 'frame', text is mirrored.
                     # This is unavoidable if we flip strictly for cosmetic reasons on a burnt-in frame.
                     # Unless we flip FIRST, then detect? NO, ROI logic breaks.
                     # Maybe we just don't flip and tell user "It's the same video file"?
                     # Or we flip, and accept mirrored text as "Simulation Artifact".
                     
                     cv2.putText(display_frame, f"STATUS: {result.get('intersection_status')}", (10, h-20), 
                                 cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                     
                     self.shared_queue.update_frame(self.phase_name, display_frame)

                     # VERIFICATION: Print Density/Count to confirm logic flow
                     if self._detection_controller and frame_num % 30 == 0: # Every ~1s
                         ld = result.get("lane_data", {})
                         for lid, metrics in ld.items():
                             print(f"    \U0001f4ca [Vision-{self.phase_name}] {lid}: Density={metrics.get('density',0):.2f} Count={metrics.get('count',0)}")
            
                time.sleep(frame_delay)
            
            cap.release()
    
    def _run_ghost_loop(self):
        """
        In GHOST mode, query the CARLA Bridge for lane data.
        """
        if not self.bridge:
            print(f"⚠️ [Vision-{self.phase_name}] Ghost mode active but no Bridge connected!")
            while not self._stop_event.is_set():
                time.sleep(1.0)
            return

        while not self._stop_event.is_set():
            try:
                # 1. Get Data from Bridge (All Phases)
                full_data = self.bridge.get_simulated_lane_data()
                
                # 2. Extract MY phase data
                my_data = full_data.get(self.phase_name, {})
                
                # 3. Push to SharedQueue
                # Adapting CARLA data to expected format
                formatted_lane_data = {
                    "count": my_data.get("vehicle_count", 0),
                    "speeds": [v["speed"] for v in my_data.get("vehicles", [])],
                    "avg_speed": my_data.get("avg_speed_kmh", 0)
                }
                
                self.shared_queue.update_phase(
                    self.phase_name,
                    lane_data=formatted_lane_data, 
                    raw_detections=[], # No BBoxes in ghost mode usually
                    intersection_status="CLEAR"
                )
                
            except Exception as e:
                print(f"❌ [Vision-{self.phase_name}] CARLA Sync Error: {e}")
            
            time.sleep(0.5) # Poll frequency
    
    def stop(self):
        self._stop_event.set()


# =============================================================================
# 3b. INTERSECTION MONITOR THREAD (Camera 5 - Validated)
# =============================================================================

class IntersectionMonitorThread(threading.Thread):
    def __init__(self, shared_queue, stop_event, mode="TEST", show_video=False):
        super().__init__(daemon=True, name="Monitor-Cam5")
        self.shared_queue = shared_queue
        self._stop_event = stop_event
        self.mode = mode
        self.show_video = show_video
        self.detector = None

    def run(self):
        import cv2
        print(f"👁️  [MONITOR] Starting Camera 5 (Center) in {self.mode} mode...")
        
        # 1. Initialize Detector
        try:
            from vision_fast.intersection_detector import IntersectionDetector
            self.detector = IntersectionDetector()
            if not self.detector.initialize():
                print("⚠️  [MONITOR] Detector Init Failed - Monitoring Disabled")
                return
        except Exception as e:
            print(f"❌ [MONITOR] Import Failed: {e}")
            return

        # 2. Open Source
        cap = None
        source = None
        if self.mode == "VIDEO":
            source = os.path.join(PROJECT_ROOT, "tools", "camera5.mp4")
            if not os.path.exists(source):
                # Fallback to any available video if camera5 missing
                print(f"⚠️  [MONITOR] {source} not found. Using north.mp4 as placeholder.")
                source = os.path.join(PROJECT_ROOT, "tools", "north.mp4")
        elif self.mode == "CAMERA":
            source = 4 # Index 4 (5th camera)
        else:
            print(f"⚠️  [MONITOR] {self.mode} mode does not support Camera 5 monitoring.")
            return # TEST/GHOST mode doesn't need this yet

        if source is None:
            print("⚠️  [MONITOR] No valid source for Camera 5. Monitoring Disabled.")
            return

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"❌ [MONITOR] Could not open video source: {source}")
            print(f"❌ [MONITOR] Could not open video source: {source}")
            return
        
        print(f"✅ [MONITOR] Source Opened: {source}, ShowVideo: {self.show_video}")
        
        while not self._stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                if self.mode == "VIDEO":
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
                    continue
                else:
                    print("⚠️  [MONITOR] Camera 5 feed ended or disconnected.")
                    break
            
            # 3. Detect
            status = self.detector.detect_status(frame)
            
            # 4. Update Global State
            self.shared_queue.update_global_status(status)
            
            # Rate Limit (10 FPS is enough for blocking detection)
            # Push to SharedQueue
            if self.show_video:
                if frame is not None and frame.size > 0:
                    cv2.putText(frame, f"STATUS: {status}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                    self.shared_queue.update_frame("Monitor-Cam5", frame)
                else:
                    print("⚠️ [MONITOR] Frame is empty!")
            
            time.sleep(0.1)
            
        if cap: cap.release()
        print("🛑 [MONITOR] Stopped.")


# =============================================================================
# 5. MAIN CONTROLLER — The Orchestrator
# =============================================================================

class MainController:
    """
    THE ORCHESTRATOR (Part 6, 8)
    
    Manages the complete signal cycle:
        GREEN (dynamic) → FREEZE (T-3s) → YELLOW (15s) → DEADLINE (T-10s) → ACTUATION
    
    State Machine:
        STATE_GREEN     →  Vision active, DecisionMaker idle
        STATE_FREEZE    →  Snapshot captured at T-3s before green ends
        STATE_YELLOW    →  Processing window opens (5 seconds)
        STATE_DEADLINE  →  Calculation must finish, winner selected
        STATE_ACTUATION →  Signal changes, next GREEN begins
    """
    
    # States
    STATE_GREEN = "GREEN"
    STATE_FREEZE = "FREEZE"
    STATE_YELLOW = "YELLOW"
    STATE_DEADLINE = "DEADLINE"
    STATE_ACTUATION = "ACTUATION"
    
    def __init__(self, mode="TEST", detect_mode="HYBRID"):
        """
        Args:
            mode: "TEST" (print only), "CAMERA" (live cameras), "GHOST" (SUMO simulation)
            detect_mode: "HYBRID" or "GRID"
        """
        print("\n" + "=" * 60)
        print("  🚦 HTMS — Hybrid Traffic Management System")
        print("  🧠 Initializing Main Controller...")
        print("=" * 60)
        
        self.mode = mode
        self.show_video = False
        self.detect_method = detect_mode
        self._carla_bridge = None
        
        # Parse args manually if needed (but argparse is better in main block)
        # Checking sys.argv for flags to override defaults
        if "--show" in sys.argv: self.show_video = True
        if "--grid" in sys.argv: self.detect_method = "GRID"
        if "--hybrid" in sys.argv: self.detect_method = "HYBRID"
        
        self.show_roi = True
        if "--no-roi" in sys.argv: self.show_roi = False
        
        self.dummy_anpr = False
        if "--dummy-anpr" in sys.argv: 
            self.dummy_anpr = True
            print("  🎭 [MAIN] ANPR Mode: DUMMY (100 Profiles)")
        else:
            print("  📷 [MAIN] ANPR Mode: REAL (OCR)")

        self._stop_event = threading.Event()
        
        # --- Core Components ---
        self.shared_queue = SharedQueue()
        self.freeze_session = FreezeSession()
        self.signal_interface = SignalInterface(mode=mode)
        self.decision_maker = DecisionMaker()
        
        # --- Timing ---
        self.green_min = config.GREEN_MIN
        self.green_max = config.GREEN_MAX
        self.yellow_duration = config.YELLOW_DURATION
        self.freeze_offset = config.FREEZE_OFFSET
        self.deadline_offset = config.DEADLINE_OFFSET
        
        # --- State ---
        self.state = self.STATE_GREEN
        self.current_green_time = self.green_min  # First cycle: minimum green
        self.current_winner = "North"             # First cycle: default to North
        self.cycle_count = 0
        self.phases = ["North", "South", "East", "West"] # Added for vision thread loop
        
        # --- CMS (Optional) ---
        self.cms_connector = None
        self._cms_override = None
        
        # --- Vision Threads ---
        self.vision_threads = [] # Changed to list for easier management
        self.monitor_thread = None # Added for Camera 5
        self.visualizer = None     # Added for Central Visualization
        
        # --- Background Services ---
        self.bg_service = BackgroundService()
        self._bg_thread = None # Legacy heartbeat thread
        
        print(f"  ⏱️  Timing: GREEN={self.green_min}-{self.green_max}s, "
              f"YELLOW={self.yellow_duration}s, "
              f"FREEZE@T-{self.freeze_offset}s, "
              f"DEADLINE@T-{self.deadline_offset}s")
        print(f"  🎮 Mode: {self.mode}")
        print("=" * 60 + "\n")
    
    def set_carla_bridge(self, bridge):
        self._carla_bridge = bridge
        self.signal_interface.set_carla_bridge(bridge)

    # ─────────────────────────────────────────────────────────
    # STARTUP / SHUTDOWN
    # ─────────────────────────────────────────────────────────
    
    def start(self):
        """Initialize all subsystems and start the main loop."""
        print("🚀 [MAIN] Starting subsystems...")
        
        # 1. Start Vision Threads (one per phase)
        if self.mode in ["VIDEO", "CAMERA"]:
            for phase in self.phases:
                vt = VisionThread(phase, self.shared_queue, source=self.mode)
                vt.configure(show_video=self.show_video, method=self.detect_method, show_roi=self.show_roi, dummy_anpr=self.dummy_anpr)
                self.vision_threads.append(vt)
                vt.start()
            
            # Start Camera 5 Monitor usually doesn't show video unless requested
            # We can enable it if show_video is true logic permits
            # Start Camera 5 Monitor
            self.monitor_thread = IntersectionMonitorThread(self.shared_queue, self._stop_event, mode=self.mode, show_video=self.show_video)
            self.monitor_thread.start()
            
            # Start Central Visualizer
            if self.show_video:
                from vision_fast.visualizer import TrafficVisualizer
                self.visualizer = TrafficVisualizer(self.shared_queue, self._stop_event)
                self.visualizer.set_callback(self._handle_keypress)
                self.visualizer.start()
            
        elif self.mode == "GHOST":
            for phase in self.phases:
                # Pass Bridge to VisionThreads
                vt = VisionThread(phase, self.shared_queue, source="GHOST", bridge=self._carla_bridge)
                self.vision_threads.append(vt)
                vt.start()
        else: # TEST mode or unknown
            print("⚠️  [MAIN] Running in TEST mode, no vision threads started.")
        
        # 2. Start Background Service (Heavy)
        self.bg_service.start()
        
        # 2b. Start Legacy Heartbeat
        self._bg_thread = threading.Thread(
            target=self._background_loop, daemon=True, name="Background"
        )
        self._bg_thread.start()
        
        # 3. Try CMS connection (non-blocking, optional)
        try:
            from config.settings import SystemConfig
            self.cms_connector = CMSConnector(
                intersection_id=SystemConfig.JUNCTION_ID,
                server_url=SystemConfig.CMS_SERVER_URL
            )
            print(f"🌐 [MAIN] CMS Connector initialized for {SystemConfig.JUNCTION_ID} -> {SystemConfig.CMS_SERVER_URL}")
        except Exception:
            print("⚠️  [MAIN] CMS unavailable — running autonomously")
            self.cms_connector = None
        
        # 4. Enter main cycle loop
        print("✅ [MAIN] All systems GO — entering cycle loop\n")
        self._main_loop()
    
    def shutdown(self):
        """Graceful shutdown of all threads."""
        print("\n🛑 [MAIN] Shutdown requested...")
        self._stop_event.set()
        
        # Stop vision threads
        # Stop vision threads
        for vt in self.vision_threads:
            vt.stop()
            vt.join(timeout=2.0)
            
        if self.visualizer:
            self.visualizer.join(timeout=2.0)
            
        self.bg_service.stop()
        
        # Signal all red for safety
        self.signal_interface.set_all_red()
        print("🛑 [MAIN] Shutdown complete — ALL RED\n")
    
    # ─────────────────────────────────────────────────────────
    # MAIN CYCLE LOOP — The Heartbeat
    # ─────────────────────────────────────────────────────────
    
    def _main_loop(self):
        """
        The eternal cycle:
            GREEN → FREEZE → YELLOW → PROCESS → DEADLINE → ACTUATION → GREEN ...
        """
        try:
            while not self._stop_event.is_set():
                self.cycle_count += 1
                print(f"\n{'━' * 50}")
                print(f"  📍 CYCLE #{self.cycle_count} — {self.current_winner} is GREEN "
                      f"({self.current_green_time}s)")
                print(f"{'━' * 50}")
                
                # ── PHASE 1: GREEN ──────────────────────────────
                self.state = self.STATE_GREEN
                self.shared_queue.set_active_phase(self.current_winner) # Notify Vision Threads
                self.signal_interface.actuate(
                    self.current_winner,
                    self.decision_maker.prev_open_lanes,
                    self.current_green_time
                )
                
                # Wait for green duration, but trigger FREEZE at T-3s
                green_wait = self.current_green_time - self.freeze_offset
                if green_wait > 0:
                    self._interruptible_sleep(green_wait)
                
                if self._stop_event.is_set():
                    break
                
                # ── PHASE 2: FREEZE @ T-3s ──────────────────────
                self.state = self.STATE_FREEZE
                print(f"\n  🔒 FREEZE @ T-{self.freeze_offset}s — Capturing snapshot...")
                
                snapshot = self.shared_queue.get_snapshot()
                frozen = self.freeze_session.capture(
                    snapshot,
                    self.decision_maker.current_state,
                    self.decision_maker.prev_open_lanes
                )
                print(f"     State: {frozen['congestion_state']}")
                print(f"     Lanes: {frozen['opened_lanes']}")
                print(f"     Intersection: {frozen['intersection_status']}")
                
                # Wait remaining 3s of green
                self._interruptible_sleep(self.freeze_offset)
                
                if self._stop_event.is_set():
                    break
                
                # ── PHASE 3: YELLOW ─────────────────────────────
                self.state = self.STATE_YELLOW
                self.signal_interface.set_yellow()
                print(f"\n  🟡 YELLOW ({self.yellow_duration}s)")
                
                # Processing Window: first 5 seconds of yellow
                processing_time = self.yellow_duration - self.deadline_offset
                print(f"\n  🧠 PROCESSING WINDOW ({processing_time}s) — Calculating next winner...")
                
                # ── CALCULATE NEXT WINNER ───────────────────────
                result = self._calculate_next_phase(frozen)
                
                # Wait for the remainder of yellow
                self._interruptible_sleep(self.yellow_duration)
                
                if self._stop_event.is_set():
                    break
                
                # ── PHASE 4: ACTUATION ──────────────────────────
                self.state = self.STATE_ACTUATION
                self.signal_interface.set_all_red()
                
                # Brief all-red clearance (2 seconds)
                self._interruptible_sleep(2)
                
                # Apply the decision
                next_winner = result["winner"]
                next_green = result["green_time"]
                
                # CMS Override check
                if self._cms_override:
                    target_lane = self._cms_override["lane"]
                    throttle_time = self._cms_override["value"]
                    print(f"  ⚡ CMS OVERRIDE: Forcing {target_lane} with {throttle_time}s limit")
                    
                    next_winner = target_lane
                    next_green = throttle_time
                    self._cms_override = None
                
                print(f"\n  🏆 WINNER: {next_winner} → GREEN for {next_green}s")
                
                self.current_winner = next_winner
                self.current_green_time = next_green
        
        except KeyboardInterrupt:
            self.shutdown()
        except Exception as e:
             import traceback
             traceback.print_exc()
             self.shutdown()
    
    # ─────────────────────────────────────────────────────────
    # DECISION CALCULATION
    # ─────────────────────────────────────────────────────────
    
    def _calculate_next_phase(self, frozen_data):
        """
        Called during the Processing Window.
        Uses the frozen snapshot to calculate who gets the next green.
        
        Returns:
            {"winner": str, "green_time": int, "scores": dict, "state": str}
        """
        # The frozen data contains raw detections from the Vision threads
        # We pass these to DecisionMaker which feeds HybridCore
        raw_detections = frozen_data.get("raw_detections", {})
        
        # Build vehicle data dict for DecisionMaker
        # If we have raw_detections, use them (HybridCore needs bounding boxes)
        # If we only have telemetry, we construct synthetic data
        vehicle_data = {}
        for phase in ["North", "South", "East", "West"]:
            vehicle_data[phase] = raw_detections.get(phase, [])
        
        # Call DecisionMaker
        result = self.decision_maker.decide_signals(vehicle_data)
        
        # Forward decision to CARLA bridge (non-blocking, fails silently if not running)
        if self.cms_connector:
            try:
                self.cms_connector.push_to_carla(
                    result,
                    lane_combinations=getattr(self.decision_maker, 'lane_combinations', None)
                )
            except Exception:
                pass
        
        # Extract winner
        scores = result.get("priority_scores", {})
        green_times = result.get("allocated_times", {})
        state = result.get("system_state", "SAFE")
        
        if not scores:
            # Fallback: round-robin
            phases = ["North", "South", "East", "West"]
            current_idx = phases.index(self.current_winner) if self.current_winner in phases else 0
            winner = phases[(current_idx + 1) % 4]
            green_time = self.green_min
        else:
            winner = max(scores, key=scores.get)
            green_time = green_times.get(winner, self.green_min)
            green_time = max(self.green_min, min(self.green_max, green_time))
        
        # Log
        print(f"\n     📊 Scores: {scores}")
        print(f"     ⏱️  Times: {green_times}")
        print(f"     🔄 State: {state}")
        
        return {
            "winner": winner,
            "green_time": green_time,
            "scores": scores,
            "state": state
        }
    
    def _background_loop(self):
        """
        Phase 7+8 Turbo Pulse (~300ms):
        1. CMS Heartbeat — real per-phase saturation from DecisionMaker
        2. Directional Counts — Camera 5 drain via IntersectionDetector
        3. Multi-lane throttle — handle list of THROTTLE_ADJUST commands
        4. Cloud sync (placeholder)
        """
        print("  📡 [Background] Service started (Turbo 300ms)")

        while not self._stop_event.is_set():
            try:
                if self.cms_connector:
                    try:
                        # --- 1. Build real per-phase saturation from DecisionMaker ---
                        lane_status = {}
                        green_times = {}
                        last_details = getattr(self.decision_maker, "last_details", {}) or {}

                        for phase in ["North", "South", "East", "West"]:
                            grid_raw = 1.0  # default neutral
                            if phase in last_details:
                                grid_raw = last_details[phase].get("Grid_Raw", 1.0)
                            # Map grid_val (1.0–5.0) → saturation fraction (0.0–1.0)
                            sat_fraction = max(0.0, min(1.0, (grid_raw - 1.0) / 4.0))
                            lane_status[phase] = {
                                "D_i": round(sat_fraction, 4),
                                "Event": "NORMAL"
                            }
                            green_times[phase] = self.current_green_time

                        # --- 2. Drain Camera 5 directional counts (Phase 8) ---
                        directional_counts = None
                        if hasattr(self, "intersection_detector") and self.intersection_detector:
                            try:
                                directional_counts = self.intersection_detector.drain_directional_counts()
                                if any(v > 0 for v in directional_counts.values()):
                                    print(f"  🧭 [Directional] {directional_counts}")
                            except Exception:
                                directional_counts = None

                        # --- 3. Send heartbeat ---
                        decisions = {"state": self.decision_maker.current_state}
                        self.cms_connector.send_data(
                            lane_status, decisions, green_times,
                            directional_counts=directional_counts
                        )

                        # --- 4. Poll for CMS commands (multi-lane throttle) ---
                        overrides = self.cms_connector.check_for_updates()
                        if overrides:
                            for lane, cmd in overrides.items():
                                if cmd.get("command_type") == "THROTTLE_ADJUST":
                                    self._cms_override = {
                                        "lane": lane,
                                        "value": cmd.get("value", 15)
                                    }
                                    print(f"  ⚡ [CMS] THROTTLE {lane} → {cmd.get('value')}s")

                    except Exception as e:
                        pass  # CMS failure is non-critical

                # 5. Cloud sync placeholder
                # self._sync_to_cloud()

            except Exception:
                pass

            # Turbo pulse: 300ms interval with clean stop support
            self._stop_event.wait(timeout=0.3)

        print("  📡 [Background] Service stopped")

    
    # ─────────────────────────────────────────────────────────
    # UTILITY
    # ─────────────────────────────────────────────────────────
    
    def _interruptible_sleep(self, seconds):
        """Sleep that can be interrupted by stop event."""
        self._stop_event.wait(timeout=seconds)

    def _handle_keypress(self, key, frame):
        """Handle keys from Visualizer (Main Thread safe-ish)."""
        if key.lower() == 'v':
            # Lazy import to avoid circular dependency or context issues
            from config.settings import SystemConfig
            
            print("\n  📸 [MANUAL] Triggering Violation Upload...")
            # Submit to Background Service
            self.bg_service.submit_job("violation", {
                "violation_type": "RLV", # Simulate Red Light
                "frame": frame,
                "timestamp": time.time(),
                "junction_id": SystemConfig.JUNCTION_ID,
                "vehicle_bbox": [0,0,100,100] # Dummy bbox
            })
            print("  ✅ [MANUAL] Violation submitted to queue.")


# =============================================================================
# 6. ENTRY POINT
# =============================================================================

def main():
    """
    Launch the HTMS Edge Server.
    
    Usage:
        python main_controller.py              → TEST mode (no cameras, print only)
        python main_controller.py --video      → VIDEO mode (detect on tools/*.mp4)
        python main_controller.py --ghost      → GHOST mode (SUMO simulation)
        python main_controller.py --camera     → CAMERA mode (live feed)
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="HTMS Main Controller")
    parser.add_argument("--video", action="store_true", help="Run detection on video files (tools/*.mp4)")
    parser.add_argument("--ghost", action="store_true", help="Run with SUMO simulation")
    parser.add_argument("--camera", action="store_true", help="Run with live cameras")
    parser.add_argument("--cycles", type=int, default=0, help="Stop after N cycles (0=infinite)")
    # New Flags
    parser.add_argument("--show", action="store_true", help="Show video feed")
    parser.add_argument("--hybrid", action="store_true", help="Use Hybrid Detection (Speed+Queue)")
    parser.add_argument("--grid", action="store_true", help="Use Grid Detection (ROI Only)")
    parser.add_argument("--no-roi", action="store_true", help="Hide ROI lines in video")
    parser.add_argument("--dummy-anpr", action="store_true", help="Enable Dummy ANPR Mode (100 Profiles)")
    
    args = parser.parse_args()
    
    if args.video:
        mode = "VIDEO"
    elif args.ghost:
        mode = "GHOST"
    elif args.camera:
        mode = "CAMERA"
    else:
        mode = "TEST"
        
    # Determine Logic Mode
    detect_mode = "HYBRID"
    if args.grid: detect_mode = "GRID"
    
    print(f"🚀 [MAIN] Starting Controller... Mode={mode}, Logic={detect_mode}")
    
    controller = MainController(mode=mode, detect_mode=detect_mode)
    
    # If GHOST mode, try to attach CARLA Bridge
    if mode == "GHOST":
        try:
            from simulation_interface.carla_bridge import CarlaBridge
            bridge = CarlaBridge()
            if bridge.connect():
                controller.set_carla_bridge(bridge)
                print("🎮 [MAIN] CARLA Ghost Mode activated")
            else:
                 print("⚠️ [MAIN] CARLA Connection failed — falling back to TEST")
                 controller.mode = "TEST"
        except ImportError:
             print("⚠️ [MAIN] carla module missing — falling back to TEST")
             controller.mode = "TEST"
        except Exception as e:
            print(f"⚠️  [MAIN] CARLA error: {e} — falling back to TEST")
            controller.mode = "TEST"
    
    try:
        controller.start()
    except KeyboardInterrupt:
        controller.shutdown()


if __name__ == "__main__":
    main()
