import re

def is_valid_youtube_url(url: str) -> bool:
    """
    Validate whether a string is a YouTube or YouTube Music URL.
    Returns True if valid, False otherwise.
    """

    if not isinstance(url, str) or not url.strip():
        return False

    patterns = [
        r"^https?://(www\.)?youtube\.com/watch\?v=",
        r"^https?://youtube\.com/watch\?v=",
        r"^https?://youtu\.be/",
        r"^https?://(www\.)?youtube\.com/embed/",
        r"^https?://music\.youtube\.com/watch\?v=",
        r"^https?://(www\.)?youtube\.com/playlist\?list=",
    ]

    return any(re.match(p, url) for p in patterns)
