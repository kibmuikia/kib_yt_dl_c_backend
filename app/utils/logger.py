# app/utils/logger.py

import logging
import sys
from typing import Any


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def log_download_start(logger: logging.Logger, url: str, output_dir: str) -> None:
    """Log download initiation."""
    logger.info(f"Starting download: url={url}, output_dir={output_dir}")


def log_download_complete(logger: logging.Logger, filename: str, size_mb: float) -> None:
    """Log successful download completion."""
    logger.info(f"Download complete: file={filename}, size={size_mb}MB")


def log_download_error(logger: logging.Logger, error: str, url: str) -> None:
    """Log download error."""
    logger.error(f"Download failed: url={url}, error={error}")


def log_metadata_fetch(logger: logging.Logger, success: bool, url: str) -> None:
    """Log metadata fetch attempt."""
    status = "success" if success else "failed"
    logger.info(f"Metadata fetch {status}: url={url}")
