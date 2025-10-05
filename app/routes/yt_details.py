import json
import subprocess
import re
from app.utils.tool_check import check_tool_exists, get_tool_version
from app.utils.url_validator import is_valid_youtube_url
from app.utils.shell_tools import run_shell_command

def yt_details(url: str):
    """Fetch detailed video info using yt-dlp, similar to bash script."""

    # 1️⃣ Validate URL
    if not is_valid_youtube_url(url):
        return {
            "status": "error",
            "message": "Invalid YouTube URL provided.",
            "thumbnail": None,
        }

    try:
        required = ["yt-dlp", "ffmpeg"]
        missing = [t for t in required if not check_tool_exists(t)]

        if missing:
            return {
                "status": "error",
                "message": f"Missing required tool(s): {', '.join(missing)}. "
                        "Please install them before using this endpoint.",
                "tools": {t: False for t in missing}
            }

        tool_versions = {t: get_tool_version(t) for t in required}

        # 3️⃣ Build and run yt-dlp command
        cmd = f'yt-dlp -j --no-warnings "{url}"'
        output = run_shell_command(cmd)

        # 4️⃣ Handle potential errors from shell command
        if output.startswith("Error:"):
            return {
                "status": "error",
                "message": output,
                "tool_versions": tool_versions,
                "data": None,
            }

        data = json.loads(output)

        # Extract key details safely
        info = {
            "id": data.get("id"),
            "title": data.get("title"),
            "uploader": data.get("uploader"),
            "channel_id": data.get("channel_id"),
            "duration": data.get("duration"),
            "duration_string": data.get("duration_string"),
            "view_count": data.get("view_count"),
            "like_count": data.get("like_count"),
            "comment_count": data.get("comment_count"),
            "upload_date": data.get("upload_date"),
            "categories": data.get("categories"),
            "description": data.get("description", "")[:500],  # limit to 500 chars
            "thumbnail": data.get("thumbnail"),
            "formats_available": [
                {
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "resolution": f.get("resolution"),
                    "filesize_approx": f.get("filesize_approx"),
                }
                for f in data.get("formats", [])[:5]  # top 5
            ],
            "tags": data.get("tags", []),
        }

        return {"status": "success", "yt_url": url, "tool_versions": tool_versions, "data": info, "raw": data,}

    except subprocess.CalledProcessError as e:
        return {"status": "error", "error": f"yt-dlp failed: {e.stderr.strip()}", "tool_versions": tool_versions,}
    except json.JSONDecodeError:
        return {"status": "error", "error": "Failed to parse yt-dlp output", "tool_versions": tool_versions,}
    except Exception as e:
        return {"status": "error", "error": str(e), "tool_versions": tool_versions,}
