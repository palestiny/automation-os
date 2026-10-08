import pytest
from pydantic import ValidationError

from app.schemas.download.request import DownloadRequest
from app.infrastructure.media.youtube_service import MAX_DOWNLOAD_BYTES, YouTubeService
from yt_dlp.utils import DownloadError


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



def test_downloader_progress_hook_stops_downloads_over_size_limit():
    with pytest.raises(DownloadError, match="size limit"):
        YouTubeService._notify_progress(
            {"status": "downloading", "downloaded_bytes": MAX_DOWNLOAD_BYTES + 1},
            lambda progress: None,
        )



def test_downloader_rejects_non_allowlisted_url_before_network_access(tmp_path):
    service = YouTubeService(tmp_path)
    with pytest.raises(ValueError, match="YouTube"):
        service.get_video_info("https://example.com/video")
