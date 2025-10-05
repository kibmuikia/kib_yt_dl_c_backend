import os
import json
from app.utils.tool_check import check_tool_exists, get_tool_version
from app.utils.url_validator import is_valid_youtube_url
from app.utils.shell_tools import run_shell_command


def yt_download(url: str, output_dir: str = "downloads"):
    """
    Download a YouTube video using yt-dlp.
    Validates URL, checks dependencies, and executes the download command safely.

    Args:
        url (str): YouTube video URL.
        output_dir (str): Directory to save downloaded video.

    Returns:
        dict: Status, message, and metadata.
    """
    
    try:
        # 1️⃣ Validate URL
        if not is_valid_youtube_url(url):
            return {
                "status": "error",
                "message": "Invalid YouTube URL provided.",
                "file": None,
            }

        # 2️⃣ Check for required tools
        required_tools = ["yt-dlp", "ffmpeg"]
        missing = [tool for tool in required_tools if not check_tool_exists(tool)]

        if missing:
            return {
                "status": "error",
                "message": f"Missing required tool(s): {', '.join(missing)}. Please install them before using this endpoint.",
                "tools": {tool: False for tool in missing},
                "file": None,
            }

        # 3️⃣ Get tool versions
        tool_versions = {tool: get_tool_version(tool) for tool in required_tools}

        # 4️⃣ Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # 5️⃣ Build yt-dlp download command
        # We’ll download the best available quality, save as mp4
        # and use a clean naming template.
        output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
        cmd = f'yt-dlp -f "bestvideo+bestaudio/best" --merge-output-format mp4 -o "{output_template}" "{url}"'

        # 6️⃣ Run the command
        output = run_shell_command(cmd)

        # 7️⃣ Handle errors
        if output.startswith("Error:"):
            return {
                "status": "error",
                "message": output,
                "tool_versions": tool_versions,
                "file": None,
            }

        # 8️⃣ Use yt-dlp to fetch metadata about the downloaded file
        meta_cmd = f'yt-dlp -j --no-warnings "{url}"'
        meta_output = run_shell_command(meta_cmd)

        if meta_output.startswith("Error:"):
            return {
                "status": "error",
                "message": "Video downloaded, but failed to retrieve metadata.",
                "tool_versions": tool_versions,
                "file": None,
            }

        data = json.loads(meta_output)
        filename = f"{data.get('title')}.mp4"
        filepath = os.path.join(output_dir, filename)

        return {
            "status": "success",
            "message": "Video downloaded successfully.",
            "file": {
                "name": filename,
                "path": filepath,
                "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2)
                if os.path.exists(filepath)
                else None,
            },
            "tool_versions": tool_versions,
            "yt_data": {
                "title": data.get("title"),
                "duration": data.get("duration"),
                "uploader": data.get("uploader"),
                "upload_date": data.get("upload_date"),
                "view_count": data.get("view_count"),
                "thumbnail": data.get("thumbnail"),
            },
        }

    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Failed to parse metadata from yt-dlp output.",
            "tool_versions": tool_versions,
            "file": None,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "tool_versions": tool_versions,
            "file": None,
        }
