# app/utils/ytdlp_helper.py

import json
import subprocess
from typing import Optional, Dict
from dataclasses import dataclass
import logging


@dataclass
class VideoMetadata:
    """Structured video metadata from yt-dlp."""
    id: str
    title: str
    duration: Optional[int]
    uploader: Optional[str]
    upload_date: Optional[str]
    view_count: Optional[int]
    thumbnail: Optional[str]
    
    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "duration": self.duration,
            "uploader": self.uploader,
            "upload_date": self.upload_date,
            "view_count": self.view_count,
            "thumbnail": self.thumbnail,
        }


def fetch_video_metadata(logger: logging.Logger, url: str, timeout: int = 30) -> Optional[VideoMetadata]:
    """
    Fetch video metadata from yt-dlp.
    
    Args:
        logger: Logger instance for recording metadata fetch events
        url: YouTube video URL
        timeout: Command timeout in seconds
        
    Returns:
        VideoMetadata object or None if fetch fails
    """
    try:
        cmd = ["yt-dlp", "-j", "--no-warnings", url]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout
        )
        
        if result.returncode != 0:
            logger.error(f"yt-dlp command failed: returncode={result.returncode}, stderr={result.stderr}")
            return None
            
        data = json.loads(result.stdout)
        result = VideoMetadata(
            id=data.get("id", ""),
            title=data.get("title", ""),
            duration=data.get("duration"),
            uploader=data.get("uploader"),
            upload_date=data.get("upload_date"),
            view_count=data.get("view_count"),
            thumbnail=data.get("thumbnail"),
        )
        logger.info(f"Metadata fetch success: url={url}, result={result}")
        return result
    except (json.JSONDecodeError, subprocess.TimeoutExpired, Exception) as e:
        logger.error(f"Failed to fetch metadata for {url}: {type(e).__name__}: {e}")
        return None


def build_download_command(url: str, output_template: str, streaming: bool = False) -> list[str]:
    """
    Build yt-dlp download command with appropriate flags.
    
    Args:
        url: YouTube video URL
        output_template: Output path template
        streaming: Whether to include progress flags for streaming
        
    Returns:
        Command list for subprocess
    """
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "--merge-output-format", "mp4",
    ]
    
    if streaming:
        cmd.extend(["--newline", "--progress"])
    
    cmd.extend(["-o", output_template, url])
    return cmd


def parse_progress_line(line: str) -> Optional[Dict[str, any]]:
    """
    Parse yt-dlp progress output line.
    
    Args:
        line: Output line from yt-dlp
        
    Returns:
        Dictionary with progress data or None if not a progress line
    """
    if '[download]' not in line or '%' not in line:
        return None
    
    try:
        parts = line.split()
        if len(parts) < 2:
            return None
        
        percent_str = parts[1].rstrip('%')
        percent = float(percent_str)
        
        progress_data: dict[str, any] = {"percent": percent}
        
        # Extract optional fields
        if 'of' in parts:
            idx = parts.index('of')
            if idx + 1 < len(parts):
                progress_data["total_size"] = parts[idx + 1]
        
        if 'at' in parts:
            idx = parts.index('at')
            if idx + 1 < len(parts):
                progress_data["speed"] = parts[idx + 1]
        
        if 'ETA' in parts:
            idx = parts.index('ETA')
            if idx + 1 < len(parts):
                progress_data["eta"] = parts[idx + 1]
        
        return progress_data
    except (ValueError, IndexError):
        return None


def detect_stream_type(line: str) -> Optional[str]:
    """
    Detect stream type (audio/video) from yt-dlp output.
    
    Args:
        line: Output line from yt-dlp
        
    Returns:
        'audio' or 'video' or None
    """
    if '[download] Destination:' not in line:
        return None
    
    line_lower = line.lower()
    
    # Audio extensions
    if any(ext in line_lower for ext in ['.m4a', '.webm', '.opus']) or 'audio' in line_lower:
        return 'audio'
    
    # Video extensions
    if any(ext in line_lower for ext in ['.mp4', '.webm']) or 'video' in line_lower:
        return 'video'
    
    return None
