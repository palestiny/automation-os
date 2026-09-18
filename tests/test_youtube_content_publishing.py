from dataclasses import dataclass

import pytest

from app.application.content_publishing import PublicationProviderError
from app.application.media_access import InMemoryMediaAssetReader
from app.domain.content import ContentAsset, PublicationRequest
from app.infrastructure.content_publishing.youtube import (
    YouTubeContentPublishingProvider,
)


@dataclass
class FakeYouTubeClient:
    external_reference: str = "youtube-video-123"
    last_media: bytes | None = None
    last_title: str | None = None
    last_description: str | None = None
    last_privacy_status: str | None = None

    def upload_video(
        self,
        media: bytes,
        *,
        title: str,
        description: str,
        privacy_status: str,
    ) -> str:
        self.last_media = media
        self.last_title = title
        self.last_description = description
        self.last_privacy_status = privacy_status
        return self.external_reference


def make_request(destination: str = "youtube") -> PublicationRequest:
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )
    return PublicationRequest.create(asset=asset, destination=destination)


def test_youtube_provider_reads_media_and_maps_provider_result():
    client = FakeYouTubeClient()
    reader = InMemoryMediaAssetReader({"asset://clip/123": b"video-bytes"})
    provider = YouTubeContentPublishingProvider(
        reader,
        client,
        title="Test clip",
        description="Test description",
    )

    publication = provider.publish(make_request())

    assert publication.destination == "youtube"
    assert publication.external_reference == "youtube-video-123"
    assert client.last_media == b"video-bytes"
    assert client.last_title == "Test clip"
    assert client.last_description == "Test description"
    assert client.last_privacy_status == "private"


def test_youtube_provider_rejects_non_youtube_destination():
    provider = YouTubeContentPublishingProvider(
        InMemoryMediaAssetReader({"asset://clip/123": b"video-bytes"}),
        FakeYouTubeClient(),
    )

    with pytest.raises(
        PublicationProviderError,
        match="destination 'youtube'",
    ):
        provider.publish(make_request(destination="other-platform"))


def test_youtube_provider_maps_missing_media_to_provider_failure():
    provider = YouTubeContentPublishingProvider(
        InMemoryMediaAssetReader({}),
        FakeYouTubeClient(),
    )

    with pytest.raises(
        PublicationProviderError,
        match="Media asset was not found",
    ):
        provider.publish(make_request())


def test_youtube_provider_maps_client_failure_to_provider_failure():
    class FailingClient:
        def upload_video(self, media, *, title, description, privacy_status):
            raise RuntimeError("upload failed")

    provider = YouTubeContentPublishingProvider(
        InMemoryMediaAssetReader({"asset://clip/123": b"video-bytes"}),
        FailingClient(),
    )

    with pytest.raises(PublicationProviderError, match="upload failed"):
        provider.publish(make_request())


def test_youtube_provider_rejects_empty_external_reference():
    provider = YouTubeContentPublishingProvider(
        InMemoryMediaAssetReader({"asset://clip/123": b"video-bytes"}),
        FakeYouTubeClient(external_reference=" "),
    )

    with pytest.raises(
        PublicationProviderError,
        match="empty external reference",
    ):
        provider.publish(make_request())
