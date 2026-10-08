from pydantic import BaseModel, HttpUrl, field_validator

from app.application.media_source_policy import validate_youtube_source_url


class DownloadRequest(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def require_allowed_https_video_url(cls, value: HttpUrl) -> HttpUrl:
        validate_youtube_source_url(str(value))
        return value
