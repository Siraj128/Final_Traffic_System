---
description: How to let friends in different cities use your app
---

# 🌍 Connecting Friends from Different Cities

Because your friend is in a different city, they cannot use your local IP (`192.168.0.102`). You need to create a **Public Tunnel** using a tool called **ngrok**.

### 1. Install ngrok
1. Download it from [ngrok.com](https://ngrok.com/download).
2. Sign up for a free account to get an "Authtoken".
3. Run this in your terminal to authenticate:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

### 2. Create the Tunnels
You need two tunnels (one for Backend, one for AI). Run these in separate terminal windows:

**For Backend (Port 5000):**
```bash
ngrok http 5000
```

**For AI Engine (Port 5001 - Optional):**
```bash
ngrok http 5001
```

### 3. Update the App Code
Ngrok will give you a URL like `https://a1b2-c3d4.ngrok-free.app`.
1. Open `lib/services/api_service.dart`.
2. Replace the `baseUrl` and `aiUrl` with your new ngrok URLs.

### 4. Build & Send New APK
1. Build a new release APK:
   ```bash
   flutter build apk --release
   ```
2. Send this **new APK** to your friend. Now they can connect from anywhere in the world! 🚀
