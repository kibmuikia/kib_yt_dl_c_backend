import os
import json
import subprocess
import threading
import queue
from typing import Dict, Any, Generator, Optional
from app.utils.tool_check import check_tool_exists, get_tool_version
from app.utils.url_validator import is_valid_youtube_url


def yt_download(url: str, output_dir: str = "downloads", return_binary: bool = False) -> Dict[str, Any]:
    """
    Download a YouTube video using yt-dlp (non-streaming version).
    Validates URL, checks dependencies, and executes the download command safely.

    Args:
        url: YouTube video URL.
        output_dir: Directory to save downloaded video.
        return_binary: If True, include video binary data in response.

    Returns:
        Status, message, metadata, and optionally binary data.
    """
    try:
        # Validate URL
        if not is_valid_youtube_url(url):
            return {
                "status": "error",
                "message": "Invalid YouTube URL provided.",
                "file": None,
            }

        # Check for required tools
        required_tools = ["yt-dlp", "ffmpeg"]
        missing = [tool for tool in required_tools if not check_tool_exists(tool)]

        if missing:
            return {
                "status": "error",
                "message": f"Missing required tool(s): {', '.join(missing)}. Please install them before using this endpoint.",
                "tools": {tool: False for tool in missing},
                "file": None,
            }

        # Get tool versions
        tool_versions = {tool: get_tool_version(tool) for tool in required_tools}

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Build yt-dlp download command
        output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "-o", output_template,
            url
        ]

        # Run the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            return {
                "status": "error",
                "message": f"Download failed: {result.stderr}",
                "tool_versions": tool_versions,
                "file": None,
            }

        # Fetch metadata about the downloaded file
        meta_cmd = ["yt-dlp", "-j", "--no-warnings", url]
        meta_result = subprocess.run(
            meta_cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if meta_result.returncode != 0:
            return {
                "status": "error",
                "message": "Video downloaded, but failed to retrieve metadata.",
                "tool_versions": tool_versions,
                "file": None,
            }

        data = json.loads(meta_result.stdout)
        filename = f"{data.get('title')}.mp4"
        filepath = os.path.join(output_dir, filename)

        response = {
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
                "id": data.get("id"),
                "title": data.get("title"),
                "duration": data.get("duration"),
                "uploader": data.get("uploader"),
                "upload_date": data.get("upload_date"),
                "view_count": data.get("view_count"),
                "thumbnail": data.get("thumbnail"),
            },
        }

        # Add binary data if requested
        if return_binary and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                response["video_bytes"] = f.read()
            response["content_type"] = "video/mp4"

        return response

    except json.JSONDecodeError:
        return {
            "status": "error",
            "message": "Failed to parse metadata from yt-dlp output.",
            "file": None,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "file": None,
        }


def yt_download_streaming(url: str, output_dir: str = "downloads", return_binary: bool = False) -> Generator[str, None, None]:
    """
    Download a YouTube video with streaming progress updates via Server-Sent Events.

    Args:
        url: YouTube video URL.
        output_dir: Directory to save downloaded video.
        return_binary: If True, send binary data in final complete event.

    Yields:
        SSE-formatted progress updates.
    """
    def send_event(event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    try:
        # Validate URL
        if not is_valid_youtube_url(url):
            yield send_event("error", {
                "status": "error",
                "message": "Invalid YouTube URL provided."
            })
            return

        # Check for required tools
        required_tools = ["yt-dlp", "ffmpeg"]
        missing = [tool for tool in required_tools if not check_tool_exists(tool)]

        if missing:
            yield send_event("error", {
                "status": "error",
                "message": f"Missing required tool(s): {', '.join(missing)}",
                "tools": {tool: False for tool in missing}
            })
            return

        # Get tool versions
        tool_versions = {tool: get_tool_version(tool) for tool in required_tools}
        
        yield send_event("info", {
            "status": "starting",
            "message": "Initializing download...",
            "tool_versions": tool_versions
        })

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Build yt-dlp download command with progress output
        output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "--merge-output-format", "mp4",
            "--newline",
            "--progress",
            "-o", output_template,
            url
        ]

        # Start the download process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        current_stream_type: Optional[str] = None

        # Stream progress updates
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            
            line = line.strip()
            
            # Detect stream type changes
            if '[download] Destination:' in line:
                # Determine stream type from the line
                new_stream_type = None
                line_lower = line.lower()
                
                if any(ext in line_lower for ext in ['.m4a', '.webm', '.opus', 'audio']):
                    new_stream_type = 'audio'
                elif any(ext in line_lower for ext in ['.mp4', '.webm', 'video']):
                    new_stream_type = 'video'
                
                # Send info event when stream type changes
                if new_stream_type and new_stream_type != current_stream_type:
                    current_stream_type = new_stream_type
                    yield send_event("info", {
                        "status": "downloading",
                        "stream_type": current_stream_type,
                        "message": f"Downloading {current_stream_type}..."
                    })
            
            # Parse progress lines
            if '[download]' in line and '%' in line:
                try:
                    parts = line.split()
                    if len(parts) >= 2:
                        percent_str = parts[1].rstrip('%')
                        try:
                            percent = float(percent_str)
                            progress_data = {
                                "percent": percent,
                                "stream_type": current_stream_type
                            }
                            
                            # Extract additional info if available
                            if 'of' in parts:
                                of_idx = parts.index('of')
                                if of_idx + 1 < len(parts):
                                    progress_data["total_size"] = parts[of_idx + 1]
                            
                            if 'at' in parts:
                                at_idx = parts.index('at')
                                if at_idx + 1 < len(parts):
                                    progress_data["speed"] = parts[at_idx + 1]
                            
                            if 'ETA' in parts:
                                eta_idx = parts.index('ETA')
                                if eta_idx + 1 < len(parts):
                                    progress_data["eta"] = parts[eta_idx + 1]
                            
                            yield send_event("progress", progress_data)
                        except (ValueError, IndexError):
                            pass
                except Exception:
                    pass
            
            # Send merging event
            elif '[Merger]' in line or 'Merging' in line:
                yield send_event("info", {
                    "status": "merging",
                    "message": "Merging video and audio..."
                })

        # Wait for process to complete
        return_code = process.wait()

        if return_code != 0:
            yield send_event("error", {
                "status": "error",
                "message": "Download failed. Check if the URL is valid and accessible."
            })
            return

        # Fetch metadata about the downloaded file
        try:
            meta_cmd = ["yt-dlp", "-j", "--no-warnings", url]
            meta_result = subprocess.run(
                meta_cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )

            if meta_result.returncode == 0:
                data = json.loads(meta_result.stdout)
                filename = f"{data.get('title')}.mp4"
                filepath = os.path.join(output_dir, filename)

                file_size = None
                if os.path.exists(filepath):
                    file_size = round(os.path.getsize(filepath) / (1024 * 1024), 2)

                complete_data = {
                    "status": "success",
                    "message": "Video downloaded successfully.",
                    "file": {
                        "name": filename,
                        "path": filepath,
                        "size_mb": file_size,
                    },
                    "yt_data": {
                        "id": data.get("id"),
                        "title": data.get("title"),
                        "duration": data.get("duration"),
                        "uploader": data.get("uploader"),
                        "upload_date": data.get("upload_date"),
                        "view_count": data.get("view_count"),
                        "thumbnail": data.get("thumbnail"),
                    },
                }

                # Add binary data if requested
                if return_binary and os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        import base64
                        complete_data["video_base64"] = base64.b64encode(f.read()).decode('utf-8')
                    complete_data["content_type"] = "video/mp4"

                yield send_event("complete", complete_data)
            else:
                yield send_event("complete", {
                    "status": "success",
                    "message": "Video downloaded successfully (metadata unavailable)."
                })

        except Exception as e:
            yield send_event("complete", {
                "status": "success",
                "message": f"Video downloaded successfully (metadata error: {str(e)})."
            })

    except Exception as e:
        yield send_event("error", {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        })

