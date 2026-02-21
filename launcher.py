import subprocess
import sys
import os
import time

def main():
    print("--------------------------------------------------")
    print("🚀 INITIALIZING WEB LAUNCHER SYSTEM...")
    print("--------------------------------------------------")
    
    # Path to the Flask App
    app_script = os.path.join("cms_layer", "web_launcher", "app.py")
    
    if not os.path.exists(app_script):
        print(f"❌ Error: Web Launcher script not found at {app_script}")
        sys.exit(1)
        
    print(f"📂 Target Script: {app_script}")
    print("🌐 Starting Flask Server on port 5000...")
    
    try:
        # Run Flask App
        subprocess.run([sys.executable, app_script])
    except KeyboardInterrupt:
        print("\n🛑 Launcher Process Terminated.")
    except Exception as e:
        print(f"❌ Critical Error: {e}")

if __name__ == "__main__":
    main()
