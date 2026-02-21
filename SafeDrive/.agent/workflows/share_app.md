---
description: Guide for sharing and installing SafeDrive Rewards on other devices
---

# 📱 Installation Guide for Friends

To install and run this app on a friend's mobile, follow these steps:

### 1. Share the APK
The built APK is located at:
`d:\Antigravity\reward app\reward_user_app\build\app\outputs\flutter-apk\app-release.apk`

You can share it via:
- **WhatsApp**: Send it as a "Document".
- **Google Drive**: Upload it and share the link.
- **USB Cable**: Copy it directly to their "Downloads" folder.

### 2. Enable "Unknown Sources"
When your friend opens the APK, Android will show a security warning. They must:
- Tap **Settings** on the popup.
- Toggle **Allow from this source** (usually Chrome or File Manager).
- Tap **Install**.

### 3. Connect to the Backend (CRITICAL)
Since the server is running on **your computer**, your friend's phone must be able to "see" your computer:
1. **Same Wi-Fi**: Both phones and your computer must be on the **same Wi-Fi network**.
2. **Firewall**: On your Windows computer, make sure your firewall allows incoming connections on port **5000** (Backend) and **5001** (AI).
3. **Check IP**: Ensure your computer's IP address (e.g., `192.168.0.102`) hasn't changed. If it has, you'll need to update `api_service.dart` and build a new APK.

### 🚀 Troubleshooting
- **"App not installed"**: This usually means there's an existing version with the same name. Ask them to uninstall any previous version first.
- **"Network Error"**: This means the phone can't talk to your computer. Check Wi-Fi and Firewall settings.
