import cv2
import numpy as np
import time
import threading

class TrafficVisualizer(threading.Thread):
    def __init__(self, shared_queue, stop_event):
        super().__init__(daemon=True, name="Visualizer")
        self.shared_queue = shared_queue
        self._stop_event = stop_event
        self.on_keypress = None # Callback function
        self.window_name = "Smart Traffic Dashboard"
        
        # Layout Config
        self.width = 1280
        self.height = 720
        self.sub_w = self.width // 3
        self.sub_h = self.height // 2
        
        # Black Canvas
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)

    def run(self):
        print(f"    🖥️ [VISUALIZER] Starting Dashboard ({self.width}x{self.height})...")
        
        while not self._stop_event.is_set():
            try:
                # 1. Get Frames from SharedQueue
                frames = self.shared_queue.get_latest_frames()
                
                # 2. Reset Canvas
                self.canvas[:] = (30, 30, 30) # Dark Gray Background
                
                # 3. Draw Quadrants (User Requested: TL, TR, BL, BR)
                # Lane 1 (North) -> Top Left
                self._draw_subframe(frames.get("North"), 0, 0, "NORTH (Lane 1)")
                
                # Lane 2 (East) -> Top Right
                self._draw_subframe(frames.get("East"), self.width - self.sub_w, 0, "EAST (Lane 2)")
                
                # Lane 3 (West) -> Bottom Left (User said BL is Lane 3)
                self._draw_subframe(frames.get("West"), 0, self.height - self.sub_h, "WEST (Lane 3)")
                
                # Lane 4 (South) -> Bottom Right
                self._draw_subframe(frames.get("South"), self.width - self.sub_w, self.height - self.sub_h, "SOUTH (Lane 4)")
                
                # 4. Draw Center (Intersection)
                # Center it
                center_x = (self.width - self.sub_w) // 2
                center_y = (self.height - self.sub_h) // 2
                
                # Highlight the center
                cv2.rectangle(self.canvas, 
                              (center_x-2, center_y-2), 
                              (center_x + self.sub_w+2, center_y + self.sub_h+2), 
                              (0, 255, 255), 2)
                              
                self._draw_subframe(frames.get("Monitor-Cam5"), center_x, center_y, "INTERSECTION (Cam 5)")
                
                # 5. Show
                cv2.imshow(self.window_name, self.canvas)
                
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    self._stop_event.set()
                elif key != 255: # If any other key is pressed
                    if self.on_keypress:
                        # Send key char and a COPY of the canvas
                        try:
                            self.on_keypress(chr(key), self.canvas.copy())
                        except Exception as e:
                            print(f"❌ [VISUALIZER] Callback Error: {e}")
                    
            except Exception as e:
                print(f"❌ [VISUALIZER] Error: {e}")
                time.sleep(1)
        
        cv2.destroyAllWindows()

    def set_callback(self, callback_func):
        """Register a function to call on keypress: func(key_char, frame)"""
        self.on_keypress = callback_func

    def _draw_subframe(self, frame, x, y, label):
        if frame is None:
            # Draw placeholder
            cv2.rectangle(self.canvas, (x, y), (x + self.sub_w, y + self.sub_h), (50, 50, 50), -1)
            cv2.putText(self.canvas, "NO SIGNAL", (x + 20, y + self.sub_h // 2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
        else:
            # Resize
            resized = cv2.resize(frame, (self.sub_w, self.sub_h))
            # Paste
            self.canvas[y:y+self.sub_h, x:x+self.sub_w] = resized
        
        # Label (Always draw on top)
        cv2.putText(self.canvas, label, (x + 10, y + 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
