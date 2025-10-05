import subprocess

def check_tool_exists(tool: str) -> bool:
    """Check if tool is installed (ffmpeg, yt-dlp, etc.)."""
    try:
        flag = "-version" if tool in ("ffmpeg", "ffprobe") else "--version"
        subprocess.run([tool, flag], capture_output=True, text=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_tool_version(tool: str) -> str | None:
    """Get version string for a tool, respecting its specific flag."""
    try:
        flag = "-version" if tool in ("ffmpeg", "ffprobe") else "--version"
        result = subprocess.run([tool, flag], capture_output=True, text=True, check=True)
        return result.stdout.strip().splitlines()[0]
    except Exception:
        return None
