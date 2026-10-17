# 🎬 Universal Video & Audio Converter (Instagram • YouTube • Facebook)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Online%20Preview-brightgreen?style=for-the-badge&logo=googlechrome)](https://vishallavare.github.io/audio-converter/)
<!-- [![Render Backend](https://img.shields.io/badge/Render%20Backend-Live-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://audio-converter-7v1g.onrender.com/api/health) -->
<!-- [![API Docs](https://img.shields.io/badge/Swagger%20UI-Live%20Docs-85EA2D?style=for-the-badge&logo=swagger&logoColor=black)](https://audio-converter-7v1g.onrender.com/docs) -->
<!-- [![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Active-blue?style=for-the-badge&logo=github)](https://vishallavare.github.io/audio-converter/) -->
<!-- [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React%2018-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT) -->

A modern, production-grade, secure, and compliant full-stack web application for downloading public media and extracting high-fidelity MP3 audio from **Instagram Reels & Videos**, **YouTube Videos & Shorts**, and **Facebook Reels & Watch**.

---

## 🌐 Live Deployments

| Component | Status | URL |
| :--- | :--- | :--- |
| **Frontend Web App (GitHub Pages)** | 🟢 Active | [https://vishallavare.github.io/audio-converter/](https://vishallavare.github.io/audio-converter/) |
<!-- | **Backend API (Render Cloud)** | 🟢 Active | [https://audio-converter-7v1g.onrender.com](https://audio-converter-7v1g.onrender.com) | -->
<!-- | **Swagger UI Docs** | 🟢 Active | [https://audio-converter-7v1g.onrender.com/docs](https://audio-converter-7v1g.onrender.com/docs) | -->
| **API Health Check** | 🟢 Healthy | [https://audio-converter-7v1g.onrender.com/api/health](https://audio-converter-7v1g.onrender.com/api/health) |

> 💡 **Seamless Cloud Integration:**
> - The Live Demo on GitHub Pages automatically connects to the live **Render cloud backend** 
<!-- (`https://audio-converter-7v1g.onrender.com`). -->
> - You can also open the **"Server"** icon in the UI anytime to test connection or toggle between Render Cloud and local development (`http://localhost:8000`).

---

## ⚠️ Compliance & Terms of Service Notice

This application is strictly designed for **public media URLs** and content that the user is legally authorized to process and download.

- **No Authentication / Credential Bypass**: Does **not** bypass Instagram, YouTube, or Facebook logins or access private/restricted accounts.
- **No DRM or CAPTCHA Circumvention**: Does not break DRM encryption, bypass CAPTCHA challenges, or circumvent platform rate limits.
- **Compliant Fallback**: If a platform does not provide the media stream to the application, a clear, compliant error message is returned:
  > *"Unable to access this public media. Please verify that the content is publicly accessible and that you have permission to process it."*

---

## ✨ Key Features

### 🌐 Multi-Platform Support
- **Instagram**: Public Reels (`/reel/`, `/reels/`), Posts (`/p/`), and Videos/IGTV (`/tv/`).
- **YouTube**: Standard Videos (`/watch?v=`), Shorts (`/shorts/`), Short URLs (`youtu.be`), and Music links.
- **Facebook**: Public Reels (`/reel/`), Facebook Watch (`/watch?v=`), standard videos (`/videos/`), and Share links (`fb.watch`, `/share/r/`).
- **Automatic & Manual Platform Detection**: Choose a platform tab or let the smart regex engine auto-detect the provider.

### 🎧 High-Performance Audio Extraction
- **FFmpeg Engine**: Safe subprocess execution (no shell injection) utilizing `libmp3lame` and stream verification.
- **Selectable Bitrates**: Supports `128 kbps`, `192 kbps` (recommended default), `256 kbps`, and `320 kbps`.
- **In-Browser Audio Player**: Preview the converted MP3 directly in the browser with interactive seekbar, play/pause controls, and volume adjustments.

### 🎥 Multi-Format Video Downloads
- **Original MP4 Video**: Download the original high-resolution MP4 video file.
- **Smart 16:9 Full-Screen Video (No Black Bars)**: Automatically detects when a video has letterboxing (e.g. horizontal video embedded inside a 9:16 vertical reel) and dynamically crops black bars to render a widescreen 1080p MP4.

### ⚡ Premium Reactive UI
- **Platform-Tailored Themes**: Sleek glassmorphism aesthetic with responsive glowing themes (Instagram gradient, YouTube red, Facebook blue).
- **Multi-Step Live Progress**: Real-time progress bar (Validating → Connecting → Downloading Stream → Extracting Audio → Converting to MP3 → Completed).
- **Media Metadata**: Displays file titles, duration, bitrate, and formatted file sizes.

### 🛡️ Enterprise-Grade Security
- **SSRF Protection**: Resolves and validates hostnames to block private IP addresses (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`, link-local, loopbacks, etc.).
- **Strict Domain Whitelisting**: Rejects non-authorized external domains and arbitrary protocols.
- **Path Traversal Protection**: Validates all job IDs with strict UUID4 regex verification before file system operations.
- **Safe Subprocess Execution**: Strict parameter separation with `shell=False`.
- **Automated Disk Cleanup**: Background daemon cleans up temporary job directories older than 30 minutes.
- **Rate Limiting**: Built-in IP rate limiter (Slowapi).
- **CORS Protection**: Whitelisted origin headers.

---

## 🏗️ Architecture

```
                                       ┌────────────────────────────────┐
                                       │     React 18 + Vite Frontend   │
                                       │  (Tailwind CSS, Audio Player,  │
                                       │   Platform Theme Switcher)     │
                                       └──────────────┬─────────────────┘
                                                      │ HTTP / REST
                                                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (Python 3.12+)                    │
│                                                                      │
│  ┌───────────────────────┐              ┌─────────────────────────┐  │
│  │ Multi-Platform URL &  │              │     Job State Store     │  │
│  │ SSRF Validators       │              │   (In-Memory / Async)   │  │
│  │ (IG / YT / FB)        │              └────────────┬────────────┘  │
│  └──────────┬────────────┘                           │               │
│             │                                        │               │
│             ▼                                        │               │
│  ┌───────────────────────┐              ┌────────────▼────────────┐  │
│  │ Compliant Media       │              │  FFmpeg Engine          │  │
│  │ Retrieval (yt-dlp)    ├─────────────►│  • Audio Extraction     │  │
│  └───────────────────────┘              │  • Auto-Crop Letterbox  │  │
│                                         └────────────┬────────────┘  │
│                                                      │               │
│                                                      ▼               │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │ Temporary Isolated Storage (/tmp/reel_converter/{job_id}/)  │     │
│  │ Automatic Background Cleanup Daemon                         │     │
│  └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
audio-converter/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── PlatformSelector.jsx   # Instagram, YouTube, Facebook tab selector
│   │   │   ├── BrandIcons.jsx         # Custom SVG platform branding icons
│   │   │   ├── UrlInput.jsx           # Input box with paste & URL validation
│   │   │   ├── QualitySelector.jsx    # 128k, 192k, 256k, 320k bitrate pills
│   │   │   ├── Progress.jsx           # Multi-step animated progress bar
│   │   │   ├── AudioPlayer.jsx        # Custom HTML5 audio player preview
│   │   │   └── DownloadButton.jsx     # MP3, MP4 & 16:9 full-screen download actions
│   │   ├── App.jsx                    # Root application component & theme management
│   │   ├── api.js                     # Axios client & API endpoints
│   │   ├── index.css                  # Tailwind styles & gradients
│   │   └── main.jsx                   # React DOM entry point
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── nginx.conf                     # Production Nginx reverse proxy configuration
│   └── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application setup, CORS & lifespan
│   │   ├── config.py                  # Pydantic BaseSettings configuration
│   │   ├── routes/
│   │   │   └── reel.py                # Convert, status, and download endpoints
│   │   ├── services/
│   │   │   ├── media_service.py       # Public stream retrieval via yt-dlp
│   │   │   ├── ffmpeg_service.py      # Audio extraction & 16:9 crop filter
│   │   │   └── cleanup_service.py     # Scheduled temp directory garbage collection
│   │   ├── models/
│   │   │   └── schemas.py             # Pydantic models & validation schemas
│   │   └── utils/
│   │       └── validators.py          # SSRF prevention & platform URL regexes
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_reel.py               # Comprehensive pytest test suite (25 tests)
│   ├── requirements.txt
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` to configure application limits and settings:

| Variable | Default | Description |
|---|---|---|
| `MAX_DOWNLOAD_SIZE_MB` | `100` | Maximum allowable video download size in MB |
| `DOWNLOAD_TIMEOUT_SECONDS` | `60` | Network timeout for media retrieval |
| `CONVERSION_TIMEOUT_SECONDS` | `120` | Timeout for FFmpeg audio extraction |
| `CLEANUP_AFTER_MINUTES` | `30` | Auto-deletion timer for temporary job folders |
| `DEFAULT_BITRATE` | `192k` | Default audio bitrate (`128k`, `192k`, `256k`, `320k`) |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed origins for cross-origin API requests |
| `TEMP_DIR` | `/tmp/reel_converter` | Base temporary storage directory |
| `RATE_LIMIT` | `30/minute` | Rate limit per client IP |
| `FFMPEG_PATH` | *(empty)* | Optional custom path to FFmpeg binary |
| `FFPROBE_PATH` | *(empty)* | Optional custom path to FFprobe binary |

---

## 🚀 Docker Setup (Recommended)

Run the full stack containerized with a single command:

```bash
docker compose up --build
```

- **Frontend Application**: [http://localhost:5173](http://localhost:5173)
- **Backend API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Interactive ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 💻 Local Development Setup

### Prerequisites
- **Node.js**: 18.x or higher & npm
- **Python**: 3.12 or higher
- **FFmpeg**: Installed in system PATH (or automatically detected via bundled `imageio-ffmpeg`)

---

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux / macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Windows (Command Prompt):
.\.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Start FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

---

### 2. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend will start at `http://localhost:5173` with reverse proxy configured to forward `/api` requests to `http://localhost:8000`.

---

### 3. Deploy Frontend Live (GitHub Pages)

This repository includes an automated GitHub Actions CI/CD workflow (`.github/workflows/deploy.yml`):

1. In your GitHub repository, navigate to **Settings** → **Pages**.
2. Under **Build and deployment** → **Source**, select **GitHub Actions**.
3. Every push to the `main` branch will automatically build and publish the live frontend to:
   **`https://vishallavare.github.io/audio-converter/`**

---

## 🧪 Testing

The backend includes a comprehensive pytest suite covering all validation rules, multi-platform URL checks, SSRF filtering, conversion edge cases, and cleanup:

```bash
cd backend

# Run pytest inside the virtual environment
pytest -v
```

### Test Coverage Highlights:
- ✅ **Valid URL Tests**: Public Instagram Reels, YouTube Videos & Shorts, Facebook Reels & Watch.
- ✅ **Invalid URL Tests**: Malformed URLs, non-video paths, private accounts.
- ✅ **Domain Enforcement**: Unsupported third-party domains rejected.
- ✅ **SSRF Protection**: Hostname resolution blocks `localhost`, `127.0.0.1`, `0.0.0.0`, `10.x.x.x`, `192.168.x.x`, and `172.16.x.x`.
- ✅ **Path Traversal Shield**: Strict UUID4 validation on all `:job_id` route parameters.
- ✅ **Bitrate Validation**: Rejects invalid or out-of-range bitrates.
- ✅ **Audio Stream Detection**: Graceful handling of silent/no-audio video streams.
- ✅ **Storage Lifecycle**: Creation, isolation, and auto-cleanup of temporary job directories.
- ✅ **Attachment Headers**: Correct MIME types and `Content-Disposition` headers for downloads.

---

## 📖 API Documentation

### 1. Submit Conversion Job
**`POST /api/reel/convert`**

```json
{
  "url": "https://www.instagram.com/reel/Daf2gF3vCzS/",
  "platform": "instagram",
  "bitrate": "192k"
}
```

> **Note**: `platform` is optional (`"instagram"`, `"youtube"`, `"facebook"`, or `"auto"`).

**Response (`200 OK`):**
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "processing"
}
```

---

### 2. Check Job Status
**`GET /api/reel/status/{job_id}`**

**Response (`200 OK`):**
```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "completed",
  "platform": "instagram",
  "progress": 100,
  "current_step": "Instagram media processed successfully.",
  "download_url": "/api/reel/download/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "video_download_url": "/api/reel/download-video/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "fullscreen_download_url": "/api/reel/download-video-fullscreen/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "metadata": {
    "filename": "instagram_reel_audio.mp3",
    "title": "Public Reel Sound",
    "platform": "instagram",
    "duration": "00:45",
    "duration_seconds": 45.2,
    "bitrate": "192 kbps",
    "file_size": "1.0 MB",
    "file_size_bytes": 1085291
  },
  "video_metadata": {
    "filename": "instagram_reel.mp4",
    "title": "Public Reel Sound",
    "platform": "instagram",
    "file_size": "8.4 MB",
    "file_size_bytes": 8808038
  },
  "fullscreen_metadata": {
    "filename": "Public Reel Sound (Full Screen).mp4",
    "title": "Public Reel Sound",
    "platform": "instagram",
    "file_size": "7.9 MB",
    "file_size_bytes": 8283712
  },
  "error": null
}
```

---

### 3. Download Converted MP3
**`GET /api/reel/download/{job_id}`**
- Returns the converted MP3 file with `Content-Type: audio/mpeg` and `Content-Disposition: attachment; filename="<title>.mp3"`.

### 4. Download Original Video
**`GET /api/reel/download-video/{job_id}`**
- Returns the source MP4 video with `Content-Type: video/mp4` and `Content-Disposition: attachment; filename="<title>.mp4"`.

### 5. Download 16:9 Full-Screen Video
**`GET /api/reel/download-video-fullscreen/{job_id}`**
- Returns the auto-cropped 16:9 widescreen MP4 video without black bars (available if letterboxing was detected).

---

## 🛡️ Security Best Practices

1. **Subprocess Isolation**: FFmpeg commands are strictly invoked using array argument tokens (`subprocess.run(list_of_args)`), preventing shell injection risks (`shell=False`).
2. **SSRF Guard**: Resolves and validates hostnames before any network connection to block local and private CIDR ranges.
3. **No Arbitrary Paths**: Users cannot supply directory paths or file targets; all working directories are isolated using randomized UUID4 identifiers.
4. **Automatic Garbage Collection**: An async background daemon monitors and purges temporary directories exceeding `CLEANUP_AFTER_MINUTES`.
5. **No Malicious Execution**: Downloaded media is treated strictly as data streams and never executed.

---

## ⚖️ Legal & Copyright Notice

This tool is provided for educational and authorized personal use. Users are responsible for complying with the respective platforms' Terms of Service and applicable copyright laws. Only download and convert media for which you possess explicit rights or which has been licensed for public reuse.
