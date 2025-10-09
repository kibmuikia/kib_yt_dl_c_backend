# app/utils/sse_helper.py

import json
from typing import Any
import logging


def format_sse_event(event_type: str, data: dict[str, Any], logger: logging.Logger) -> str:
    """
    Format data as Server-Sent Event.
    
    Args:
        event_type: Type of SSE event (info, progress, error, complete)
        data: Data payload to send
        
    Returns:
        Formatted SSE string
    """
    result = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    logger.info(result)
    return result
