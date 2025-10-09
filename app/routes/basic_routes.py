# app/routes/basic_routes.py

from app.utils.tool_check import check_tool_exists, get_tool_version

def home():
    return {
        "message": "Welcome to the Kib Youtube Downloader and Converter",
        "status": "OK"
    }

def health():
    status = {
        "status": "healthy",
        "uptime": "running smoothly"
    }

    tools = ["yt-dlp", "ffmpeg", "ffprobe"]
    tool_info = {}
    all_present = True

    for tool in tools:
        exists = check_tool_exists(tool)
        ver = get_tool_version(tool) if exists else None
        tool_info[tool] = {"present": exists, "version": ver}
        if not exists:
            all_present = False

    status["tools"] = tool_info
    status["all_tools_present"] = all_present
    return status

