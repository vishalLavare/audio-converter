# 📱 Mobile App Setup & Build Guide (Android & iOS)

This application has been configured with **Capacitor**, transforming the React web application into a high-performance **native mobile application** for Android and iOS.

---

## 🏗️ Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│             Mobile Device (Android / iOS)              │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │   Capacitor Native Container                   │   │
│   │   • Responsive Glassmorphic UI                 │   │
│   │   • Native Haptic Vibration Feedback           │   │
│   │   • Native File System & Share Sheet (Save/Share)│ │
│   │   • Dark Status Bar Integration                │   │
│   │   • Dynamic Server IP / URL Switcher           │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ HTTP / REST API
                            ▼
┌────────────────────────────────────────────────────────┐
│             Backend Server (FastAPI + FFmpeg)          │
│   • Local Wi-Fi Network (http://192.168.x.x:8000)      │
│     OR Cloud Host (e.g., Render, Railway, AWS, VPS)    │
│   • Runs yt-dlp media extraction & FFmpeg transcoding   │
└────────────────────────────────────────────────────────┘
```

---

---

## 🚀 Building the APK (No Android Studio Needed!)

The standalone **Android Command Line SDK** and **Gradle** are configured at `H:\android-sdk`. You can compile the `.apk` file without downloading Android Studio!

### 🎯 Your Ready-to-Install APK File
The APK has already been compiled and is ready for your phone:
- **Location:** [`H:\audio converter\AudioConverter-app.apk`](file:///H:/audio%20converter/AudioConverter-app.apk)
- **Size:** ~4.35 MB

### 🔄 How to Re-Build the APK Anytime:
Whenever you make any changes and want to generate a new APK, simply run either:

**Option A (1-Click Batch Script):**
- Double-click [`build-apk.bat`](file:///h:/audio%20converter/build-apk.bat) in the project root folder.

**Option B (From Terminal):**
```powershell
cd "h:\audio converter\frontend"
npm run build:apk
```

---

## 📲 How to Install the APK on Your Android Phone

1. Transfer [`AudioConverter-app.apk`](file:///H:/audio%20converter/AudioConverter-app.apk) to your phone (via USB cable, WhatsApp, Google Drive, or email).
2. On your phone, tap the `.apk` file to install it.
   *(If prompted, allow "Install unknown apps" from your file manager / browser).*
3. Open the **Audio & Video Converter** app on your phone!
4. Tap the **Server** button (gear icon in the top right) to connect to your backend IP (e.g. `http://192.168.x.x:8000`).

---

## 💻 Running the Backend for Your Phone

When running the backend for mobile devices on your Wi-Fi:

```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> **Find your computer's local IP address:**  
> Run `ipconfig` in PowerShell and look for **IPv4 Address** under your Wi-Fi adapter (e.g., `192.168.1.25`).

2. Select your connected phone (via USB debugging) or an Android Virtual Device (AVD).
3. Click the green **Run (▶)** button to install and launch the app!

---

### 4. Build a Standalone APK for Your Phone

To generate an `.apk` file that you can transfer directly to any Android phone:
1. In Android Studio, go to the top menu: **Build → Build Bundle(s) / APK(s) → Build APK(s)**.
2. When finished, click **locate** in the popup (the `.apk` will be in `frontend/android/app/build/outputs/apk/debug/app-debug.apk`).
3. Send this file to your phone via USB, WhatsApp, Google Drive, etc., and tap it to install.

---

## ⚙️ In-App Server Configuration

The mobile app includes a built-in **Server Settings** modal:

1. Tap the **Server** button (gear icon) in the top-right corner of the mobile app.
2. Enter your backend host:
   - **Local Wi-Fi Testing:** `http://192.168.X.X:8000` *(replace with your PC's IP)*
   - **Android Emulator:** `http://10.0.2.2:8000` *(special alias for host machine in Android emulator)*
   - **Production Cloud Host:** `https://your-backend-api.com`
3. Tap **Test Connection** to verify that the mobile app can reach the backend.
4. Tap **Save & Apply**. The app will immediately use this endpoint.

---

## 🍎 iOS Support (Mac with Xcode)

If you have a Mac and wish to build for iPhone:

```bash
cd frontend
npx cap add ios
npx cap open ios
```

In Xcode, select your simulator or plugged-in iPhone and hit **Run**.

---

## 📦 Installed Mobile Plugins & Features

- **`@capacitor/core` & `@capacitor/android`**: Native runtime container.
- **`@capacitor/share`**: Native mobile share sheet allowing users to directly share or save downloaded MP3s and MP4s to Files, WhatsApp, etc.
- **`@capacitor/filesystem`**: Secure device storage writing.
- **`@capacitor/haptics`**: Tactile feedback on taps and conversions.
- **`@capacitor/status-bar`**: Styled dark status bar that seamlessly blends with the app theme.
