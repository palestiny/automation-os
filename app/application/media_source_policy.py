from urllib.parse import urlsplit

_ALLOWED_VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def validate_youtube_source_url(value: str) -> None:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError("Malformed video URL") from None

    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme.lower() != "https":
        raise ValueError("Only HTTPS video URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials in video URLs are not allowed")
    if host not in _ALLOWED_VIDEO_HOSTS:
        raise ValueError("Only supported YouTube video URLs are allowed")
    if port not in (None, 443):
        raise ValueError("Non-standard ports in video URLs are not allowed")
