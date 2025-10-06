# 🎬 YouTube DL Command Backend (Python 3.13)

A lightweight, framework-free Python backend for downloading, inspecting, and extracting metadata from YouTube videos using `yt-dlp` and `ffmpeg`.  
Built with clean modular design.

---

## 📁 Project Structure

```
.
├── app/
│   ├── config.py              # Loads environment settings
│   ├── main.py                # Entry point (HTTP server + routes)
│   ├── routes/                # Application endpoints
│   │   ├── basic_routes.py    # /, /health
│   │   ├── yt_details.py      # Video metadata
│   │   ├── yt_download.py     # Video downloader
│   │   └── yt_thumbnail.py    # Thumbnail retriever
│   └── utils/                 # Utilities and shared logic
│       ├── boot_check.py
│       ├── shell_tools.py
│       ├── tool_check.py
│       └── url_validator.py
├── downloads/                 # Saved video files (git-ignored)
├── env.example                # Example environment variables
├── requirements.txt           # Python dependencies
├── run.sh                     # Local runner script
└── README.md
```

---

## ⚙️ Features

✅ **No framework needed** — uses built-in `http.server`.  
✅ **Cross-platform** — runs on macOS, Linux, or server of choice.  
✅ **Safe subprocess handling** with `run_shell_command`.  
✅ **Environment support** (`.env`, `.env.prod`).  
✅ **Automatic tool check** for `yt-dlp`, `ffmpeg`, etc.  
✅ **Three powerful endpoints:**

| Endpoint | Description |
|-----------|--------------|
| `/` | Welcome page |
| `/health` | Checks system and tool health |
| `/yt_thumbnail?url=<YOUTUBE_URL>[&download=true]` | Fetches or downloads a video thumbnail |
| `/yt_details?url=<YOUTUBE_URL>` | Retrieves full metadata and formats |
| `/yt_download?url=<YOUTUBE_URL>[&download=true]` | Downloads video with optional binary output |

---

## 🧰 Requirements

- **Python** ≥ 3.13  
- **yt-dlp** ≥ 2024.08.06  
- **ffmpeg** ≥ 7.x  
- any Linux host

### Install Tools (macOS)
```bash
brew install yt-dlp ffmpeg
```

### Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🧑‍💻 Local Development

### 1. Setup Environment
```bash
cp env.example .env
```

### 2. Start Server
```bash
./run.sh
```

or manually:
```bash
python3 -m app.main
```

### 3. Test Endpoints
```bash
curl "http://localhost:5000/"
curl "http://localhost:5000/health"
curl "http://localhost:5000/yt_thumbnail?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
curl "http://localhost:5000/yt_details?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
curl "http://localhost:5000/yt_download?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

---

## 🔍 Health Endpoint Example

```bash
curl "http://localhost:5000/health"
```

Response:
```json
{
  "status": "ok",
  "tools": {
    "yt-dlp": "yt-dlp 2025.01.04",
    "ffmpeg": "ffmpeg version 7.1"
  },
  "message": "All required tools are available and healthy."
}
```

---

## 🧠 Internals

| Utility | Responsibility |
|----------|----------------|
| **boot_check.py** | Validates environment and dependency setup on startup |
| **tool_check.py** | Detects tools (yt-dlp, ffmpeg) and their versions |
| **shell_tools.py** | Safe subprocess wrapper for shell command execution |
| **url_validator.py** | Validates YouTube URL patterns |
| **run.sh** | Developer helper script for running locally |

---

## 🧾 Environment Variables

| Variable | Description | Default |
|-----------|-------------|----------|
| `ENV` | Environment mode (`development` / `production`) | `development` |
| `PORT` | HTTP port | `5000` |

---

## 🧼 Git Hygiene

`.gitignore` already excludes:
```
__pycache__/
*.pyc
venv/
.env
.env.prod
downloads/
.DS_Store
.vscode/
.idea/
```

---

## 🧠 Future Enhancements

- [ ] Add async support (aiohttp / FastAPI migration)
- [ ] Live progress streaming via SSE or WebSocket
- [ ] Video/audio-only download options
- [ ] Logging and structured error tracing
- [ ] Authentication layer for protected endpoints

---

## 🧑‍🤝‍🧑 Author

**Kib**  
👨‍💻 Software Engineer | Mobile & Backend Developer (Flutter, Kotlin, Python)  
📍 Nairobi, Kenya  
🌐 [GitHub](https://github.com/kibmuikia)

---

## 🧩 License

MIT License © 2025 KibDev  
Use freely with attribution.
