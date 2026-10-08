import pytest
from pydantic import ValidationError

from app.schemas.download.request import DownloadRequest


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=video123",
        "https://youtu.be/video123",
        "https://m.youtube.com/watch?v=video123",
    ],
)
def test_download_request_accepts_supported_urls(url):
    assert str(DownloadRequest(url=url).url).startswith("https://")


@pytest.mark.parametrize(
    "url",
    [
        "http://www.youtube.com/watch?v=video123",
        "https://example.com/video",
        "https://youtube.com.attacker.example/watch?v=video123",
    ],
)
def test_download_request_rejects_unsafe_urls(url):
    with pytest.raises(ValidationError):
        DownloadRequest(url=url)
