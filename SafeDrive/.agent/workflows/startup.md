---
description: Manual Startup Guide for SafeDrive Rewards
---

Follow these steps to start the entire ecosystem manually:

### 1. Start the Backend Server
Open a terminal (Command Prompt or PowerShell) and run:
```bash
cd "d:\Antigravity\reward app\backend_server"
node server.js
```
> [!NOTE]
> The server runs on port 5000. Look for the "✅ MongoDB Connected" message.

### 2. Start the AI Detection Engine
Open a **new** terminal and run:
```bash
cd "d:\Antigravity\reward app\ai_detection"
venv\Scripts\python.exe app.py
```
> [!TIP]
> This command bypasses any PowerShell "Script Execution" errors by calling Python directly from the environment.

### 3. Run the Mobile App
Open a **third** terminal and run:
```bash
cd "d:\Antigravity\reward app\reward_user_app"
flutter run
```

### 🚀 Pro Tip: One-Click Startup
I have updated the `start_servers.bat` file in the root directory. You can simply **double-click** it to start both backend servers at once!
