# app/routes/yt_download.py

import os
import base64
import subprocess
from typing import Optional, Generator, Dict
from dataclasses import dataclass, asdict

from app.utils.tool_check import check_tool_exists, get_tool_version
from app.utils.url_validator import is_valid_youtube_url
from app.utils.sse_helper import format_sse_event
from app.utils.ytdlp_helper import (
    VideoMetadata,
    fetch_video_metadata,
    build_download_command,
    parse_progress_line,
    detect_stream_type,
)
from app.utils.logger import (
    setup_logger,
    log_download_start,
    log_download_complete,
    log_download_error,
    log_metadata_fetch,
)


# Constants
REQUIRED_TOOLS = ["yt-dlp", "ffmpeg"]
DEFAULT_OUTPUT_DIR = "downloads"
OUTPUT_FORMAT = "mp4"

# Setup logger
logger = setup_logger(__name__)


@dataclass
class DownloadResult:
    """Structured download result."""
    status: str
    message: str
    file: Optional[Dict[str, any]] = None
    tool_versions: Optional[Dict[str, str]] = None
    yt_data: Optional[Dict[str, any]] = None
    video_bytes: Optional[bytes] = None
    video_base64: Optional[str] = None
    content_type: Optional[str] = None
    tools: Optional[Dict[str, bool]] = None
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


def validate_dependencies() -> tuple[bool, Optional[DownloadResult]]:
    """
    Validate required tools are installed.
    
    Returns:
        Tuple of (success, error_result or None)
    """
    missing = [tool for tool in REQUIRED_TOOLS if not check_tool_exists(tool)]
    
    if missing:
        logger.warning(f"Missing required tools: {', '.join(missing)}")
        return False, DownloadResult(
            status="error",
            message=f"Missing required tool(s): {', '.join(missing)}. Please install them before using this endpoint.",
            tools={tool: False for tool in missing}
        )
    
    return True, None


def get_tool_versions_dict() -> Dict[str, str]:
    """Get versions of all required tools."""
    return {tool: get_tool_version(tool) for tool in REQUIRED_TOOLS}


def get_file_size_mb(filepath: str) -> Optional[float]:
    """
    Get file size in MB.
    
    Args:
        filepath: Path to file
        
    Returns:
        Size in MB or None if file doesn't exist
    """
    if not os.path.exists(filepath):
        return None
    return round(os.path.getsize(filepath) / (1024 * 1024), 2)


def construct_filepath(output_dir: str, title: str, extension: str = OUTPUT_FORMAT) -> str:
    """
    Construct full filepath for downloaded video.
    
    Args:
        output_dir: Output directory
        title: Video title
        extension: File extension
        
    Returns:
        Full filepath
    """
    filename = f"{title}.{extension}"
    return os.path.join(output_dir, filename)


def execute_download(url: str, output_dir: str, streaming: bool = False) -> subprocess.CompletedProcess | subprocess.Popen:
    """
    Execute yt-dlp download command.
    
    Args:
        url: YouTube video URL
        output_dir: Output directory
        streaming: Whether to use streaming mode (Popen)
        
    Returns:
        CompletedProcess or Popen object
    """
    output_template = os.path.join(output_dir, f"%(title)s.{OUTPUT_FORMAT}")
    cmd = build_download_command(url, output_template, streaming)
    
    if streaming:
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
    else:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )


def yt_download(
    url: str, 
    output_dir: str = DEFAULT_OUTPUT_DIR, 
    return_binary: bool = False
) -> Dict[str, any]:
    """
    Download a YouTube video using yt-dlp (non-streaming version).
    Validates URL, checks dependencies, and executes the download command safely.

    Args:
        url: YouTube video URL
        output_dir: Directory to save downloaded video
        return_binary: If True, include video binary data in response

    Returns:
        Status, message, metadata, and optionally binary data
    """
    
    # Validate URL
    if not is_valid_youtube_url(url):
        logger.warning(f"Invalid YouTube URL: {url}")
        return DownloadResult(
            status="error",
            message="Invalid YouTube URL provided."
        ).to_dict()
    
    # Check dependencies
    deps_valid, error_result = validate_dependencies()
    if not deps_valid:
        return error_result.to_dict()
    
    tool_versions = get_tool_versions_dict()
    
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Execute download
        log_download_start(logger, url, output_dir)
        result = execute_download(url, output_dir, streaming=False)
        
        if result.returncode != 0:
            error_msg = f"Download failed: {result.stderr}"
            log_download_error(logger, error_msg, url)
            return DownloadResult(
                status="error",
                message=error_msg,
                tool_versions=tool_versions
            ).to_dict()
        
        # Fetch metadata
        metadata = fetch_video_metadata(logger, url)
        log_metadata_fetch(logger, metadata is not None, url)
        
        if not metadata:
            return DownloadResult(
                status="error",
                message="Video downloaded, but failed to retrieve metadata.",
                tool_versions=tool_versions
            ).to_dict()
        
        # Construct file path
        filepath = construct_filepath(output_dir, metadata.title)
        file_size = get_file_size_mb(filepath)
        
        log_download_complete(logger, metadata.title, file_size or 0)
        
        # Build response
        response = DownloadResult(
            status="success",
            message="Video downloaded successfully.",
            file={
                "name": f"{metadata.title}.{OUTPUT_FORMAT}",
                "path": filepath,
                "size_mb": file_size,
            },
            tool_versions=tool_versions,
            yt_data=metadata.to_dict()
        )
        
        # Add binary data if requested
        if return_binary and os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                response.video_bytes = f.read()
            response.content_type = f"video/{OUTPUT_FORMAT}"
        
        return response.to_dict()
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log_download_error(logger, error_msg, url)
        return DownloadResult(
            status="error",
            message=error_msg
        ).to_dict()


def yt_download_streaming(
    url: str, 
    output_dir: str = DEFAULT_OUTPUT_DIR, 
    return_binary: bool = False
) -> Generator[str, None, None]:
    """
    Download a YouTube video with streaming progress updates via Server-Sent Events.

    Args:
        url: YouTube video URL
        output_dir: Directory to save downloaded video
        return_binary: If True, send binary data in final complete event

    Yields:
        SSE-formatted progress updates
    """
    log_download_start(logger, url, output_dir)
    
    try:
        # Validate URL
        if not is_valid_youtube_url(url):
            logger.warning(f"Invalid YouTube URL: {url}")
            yield format_sse_event("error", {
                "status": "error",
                "message": "Invalid YouTube URL provided."
            }, logger)
            return
        
        # Check dependencies
        deps_valid, error_result = validate_dependencies()
        if not deps_valid:
            yield format_sse_event("error", error_result.to_dict(), logger)
            return
        
        tool_versions = get_tool_versions_dict()
        
        yield format_sse_event("info", {
            "status": "starting",
            "message": "Initializing download...",
            "tool_versions": tool_versions
        }, logger)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Start download process
        process = execute_download(url, output_dir, streaming=True)
        current_stream_type: Optional[str] = None
        
        # Stream progress updates
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            
            line = line.strip()
            
            # Detect stream type changes
            new_stream_type = detect_stream_type(line)
            if new_stream_type and new_stream_type != current_stream_type:
                current_stream_type = new_stream_type
                yield format_sse_event("info", {
                    "status": "downloading",
                    "stream_type": current_stream_type,
                    "message": f"Downloading {current_stream_type}..."
                }, logger)
            
            # Parse and send progress
            progress_data = parse_progress_line(line)
            if progress_data:
                progress_data["stream_type"] = current_stream_type
                yield format_sse_event("progress", progress_data, logger)
            
            # Detect merging phase
            if '[Merger]' in line or 'Merging' in line:
                yield format_sse_event("info", {
                    "status": "merging",
                    "message": "Merging video and audio..."
                })
        
        # Wait for process completion
        return_code = process.wait()
        
        if return_code != 0:
            error_msg = "Download failed. Check if the URL is valid and accessible."
            log_download_error(logger, error_msg, url)
            yield format_sse_event("error", {
                "status": "error",
                "message": error_msg
            }, logger)
            return
        
        # Fetch metadata
        metadata = fetch_video_metadata(logger, url, timeout=30)
        log_metadata_fetch(logger, metadata is not None, url)
        
        if metadata:
            filepath = construct_filepath(output_dir, metadata.title)
            file_size = get_file_size_mb(filepath)
            
            log_download_complete(logger, metadata.title, file_size or 0)
            
            complete_data = {
                "status": "success",
                "message": "Video downloaded successfully.",
                "file": {
                    "name": f"{metadata.title}.{OUTPUT_FORMAT}",
                    "path": filepath,
                    "size_mb": file_size,
                },
                "yt_data": metadata.to_dict(),
            }
            
            # Add binary data if requested
            if return_binary and os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    complete_data["video_base64"] = base64.b64encode(f.read()).decode('utf-8')
                complete_data["content_type"] = f"video/{OUTPUT_FORMAT}"
            
            yield format_sse_event("complete", complete_data, logger)
        else:
            yield format_sse_event("complete", {
                "status": "success",
                "message": "Video downloaded successfully (metadata unavailable)."
            }, logger)
    
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log_download_error(logger, error_msg, url)
        yield format_sse_event("error", {
            "status": "error",
            "message": error_msg
        }, logger)
