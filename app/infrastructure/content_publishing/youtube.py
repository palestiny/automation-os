from __future__ import annotations

from typing import Protocol

from app.application.content_publishing import PublicationProviderError
from app.application.media_access import MediaAssetReader
from app.domain.content import Publication, PublicationRequest


class YouTubeClient(Protocol):
    """Infrastructure boundary around the YouTube API client."""

    def upload_video(
        self,
        media: bytes,
        *,
        title: str,
        description: str,
        privacy_status: str,
    ) -> str:
        ...


class YouTubeContentPublishingProvider:
    """YouTube adapter implementing the provider-neutral publication contract."""

    def __init__(
        self,
        media_reader: MediaAssetReader,
        client: YouTubeClient,
        *,
        privacy_status: str = "private",
    ) -> None:
        if not privacy_status.strip():
            raise ValueError("YouTube privacy_status cannot be empty")
        self._media_reader = media_reader
        self._client = client
        self._privacy_status = privacy_status

    def publish(self, request: PublicationRequest) -> Publication:
        try:
            media = self._media_reader.read(request.asset)
        except Exception as exc:
            if isinstance(exc, PublicationProviderError):
                raise
            raise PublicationProviderError(str(exc)) from exc

        try:
            external_reference = self._client.upload_video(
                media,
                title=request.title,
                description=request.description,
                privacy_status=self._privacy_status,
            )
        except Exception as exc:
            raise PublicationProviderError(str(exc)) from exc

        if not external_reference.strip():
            raise PublicationProviderError(
                "YouTube provider returned an empty external reference"
            )

        return Publication.create(
            asset=request.asset,
            destination=request.destination,
            external_reference=external_reference,
        )
