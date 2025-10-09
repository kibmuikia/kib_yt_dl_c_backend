# app/routes/yt_thumbnail.py

import json
import subprocess
import requests  # for fetching thumbnail image
from app.utils.tool_check import check_tool_exists, get_tool_version
from app.utils.url_validator import is_valid_youtube_url
from app.utils.shell_tools import run_shell_command


def get_thumbnail_url(url: str, download: bool = False):
    """
    Given a YouTube URL, return the video's thumbnail URL or the actual image.
    Includes validation, dependency checks, and error handling.

    Args:
        url (str): YouTube video URL.
        download (bool): If True, returns image bytes instead of JSON.
    """

    # 1️⃣ Validate URL
    if not is_valid_youtube_url(url):
        return {
            "status": "error",
            "message": "Invalid YouTube URL provided.",
            "thumbnail": None,
        }

    # 2️⃣ Check required tool
    required_tool = "yt-dlp"
    if not check_tool_exists(required_tool):
        return {
            "status": "error",
            "message": f"Missing required tool: {required_tool}. Please install it (brew install yt-dlp).",
            "tools": {required_tool: False},
            "thumbnail": None,
        }

    # 3️⃣ Get tool version
    version = get_tool_version(required_tool)

    # 4️⃣ Use yt-dlp to extract thumbnail metadata
    try:
        # 3️⃣ Build and run yt-dlp command
        cmd = f'yt-dlp -j --no-warnings "{url}"'
        output = run_shell_command(cmd)

        # 4️⃣ Handle potential errors from shell command
        if output.startswith("Error:"):
            return {
                "status": "error",
                "message": output,
                "tool_version": {required_tool: version},
                "data": None,
            }
        
        # data = json.loads(result.stdout)
        data = json.loads(output)

        thumbnail_url = data.get("thumbnail")
        if not thumbnail_url:
            return {
                "status": "error",
                "message": "Thumbnail not found in video metadata.",
                "tool_version": {required_tool: version},
                "thumbnail": None,
            }

        # 5️⃣ Return thumbnail bytes if requested
        if download:
            try:
                response = requests.get(thumbnail_url, timeout=10)
                response.raise_for_status()

                # Construct a binary response dict (to be handled by caller)
                return {
                    "status": "success",
                    "message": "Thumbnail image retrieved successfully.",
                    "image_bytes": response.content,
                    "content_type": response.headers.get("Content-Type", "image/jpeg"),
                    "tool_version": {required_tool: version},
                }

            except requests.exceptions.RequestException as e:
                return {
                    "status": "error",
                    "message": f"Failed to download thumbnail image: {str(e)}",
                    "tool_version": {required_tool: version},
                    "thumbnail": thumbnail_url,
                }

        # Default → return URL as JSON
        return {
            "status": "success",
            "message": "Thumbnail URL retrieved successfully.",
            "thumbnail": thumbnail_url,
            "tool_version": {required_tool: version},
        }

    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"yt-dlp command failed: {e.stderr.strip()}",
            "tool_version": {required_tool: version},
            "thumbnail": None,
        }

    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Failed to parse yt-dlp output (invalid JSON).",
            "tool_version": {required_tool: version},
            "thumbnail": None,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "tool_version": {required_tool: version},
            "thumbnail": None,
        }
