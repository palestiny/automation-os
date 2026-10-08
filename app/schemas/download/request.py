from urllib.parse import urlsplit

from pydantic import BaseModel, HttpUrl, field_validator


_ALLOWED_VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


class DownloadRequest(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def require_allowed_https_video_url(cls, value: HttpUrl) -> HttpUrl:
        parsed = urlsplit(str(value))
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme.lower() != "https":
            raise ValueError("Only HTTPS video URLs are allowed")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Credentials in video URLs are not allowed")
        if host not in _ALLOWED_VIDEO_HOSTS:
            raise ValueError("Only supported YouTube video URLs are allowed")
        return value
