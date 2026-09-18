from io import BytesIO

from app.infrastructure.content_publishing.youtube import GoogleYouTubeClient


class FakeInsertRequest:
    def __init__(self, response):
        self.response = response

    def execute(self):
        return self.response


class FakeVideos:
    def __init__(self):
        self.calls = []

    def insert(self, *, part, body, media_body):
        self.calls.append((part, body, media_body))
        return FakeInsertRequest({"id": "youtube-123"})


class FakeService:
    def __init__(self):
        self._videos = FakeVideos()

    def videos(self):
        return self._videos


def test_google_youtube_client_maps_upload_to_youtube_service():
    service = FakeService()
    client = GoogleYouTubeClient(service)

    external_reference = client.upload_video(
        b"video-bytes",
        title="Test title",
        description="Test description",
        privacy_status="private",
    )

    assert external_reference == "youtube-123"
    part, body, media = service._videos.calls[0]
    assert part == "snippet,status"
    assert body == {
        "snippet": {
            "title": "Test title",
            "description": "Test description",
        },
        "status": {"privacyStatus": "private"},
    }
    assert media.resumable() is True
    assert media.mimetype() == "video/*"
    media._fd.seek(0)
    assert media._fd.read() == b"video-bytes"
