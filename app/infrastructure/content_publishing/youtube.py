from __future__ import annotations

from io import BytesIO
from typing import Protocol

from app.application.content_publishing import PublicationProviderError
from app.application.media_access import MediaAssetNotFoundError, MediaAssetReader
from app.domain.content import Publication, PublicationRequest


class YouTubeClient(Protocol):
    """Minimal provider-client boundary used by the YouTube publisher."""

    def upload_video(
        self,
        media: bytes,
        *,
        title: str,
        description: str,
        privacy_status: str,
    ) -> str:
        ...


class GoogleYouTubeClient:
    """Concrete Google YouTube Data API client adapter."""

    def __init__(self, service: object) -> None:
        self._service = service

    def upload_video(
        self,
        media: bytes,
        *,
        title: str,
        description: str,
        privacy_status: str,
    ) -> str:
        from googleapiclient.http import MediaIoBaseUpload

        body = {
            "snippet": {"title": title, "description": description},
            "status": {"privacyStatus": privacy_status},
        }
        request = self._service.videos().insert(
            part="snippet,status",
            body=body,
            media_body=MediaIoBaseUpload(
                BytesIO(media),
                mimetype="video/*",
                resumable=True,
            ),
        )
        response = request.execute()
        return response["id"]


class YouTubeContentPublishingProvider:
    """YouTube adapter implementing the provider-neutral publication contract."""

    def __init__(
        self,
        media_reader: MediaAssetReader,
        client: YouTubeClient,
        *,
        privacy_status: str = "private",
        title: str = "Automation OS Content",
        description: str = "",
    ) -> None:
        if not privacy_status.strip():
            raise ValueError("YouTube privacy_status cannot be empty")
        if not title.strip():
            raise ValueError("YouTube title cannot be empty")
        self._media_reader = media_reader
        self._client = client
        self._privacy_status = privacy_status
        self._title = title
        self._description = description

    def publish(self, request: PublicationRequest) -> Publication:
        if request.destination != "youtube":
            raise PublicationProviderError(
                "YouTube provider requires destination 'youtube'"
            )

        try:
            media = self._media_reader.read(request.asset)
        except MediaAssetNotFoundError as exc:
            raise PublicationProviderError(str(exc)) from exc

        try:
            external_reference = self._client.upload_video(
                media,
                title=self._title,
                description=self._description,
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
