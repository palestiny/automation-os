from __future__ import annotations

from typing import Protocol

from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.content_acquisition import (
    ACQUIRED_CONTENT_ASSET_CONTEXT_KEY,
    CONTENT_SOURCE_CONTEXT_KEY,
)
from app.application.execution_context import ExecutionContext
from app.domain.content import ContentAsset, ContentSource


class ContentDownloader(Protocol):
    def download(self, source_reference: str) -> str:
        ...


class YtDlpContentAcquisitionCapability(Capability):
    """Concrete acquisition adapter using an injected downloader."""

    def __init__(self, downloader: ContentDownloader) -> None:
        self._downloader = downloader

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        try:
            source = context.get(CONTENT_SOURCE_CONTEXT_KEY)
        except KeyError:
            return CapabilityResult.failure(
                "Content source is required for acquisition"
            )

        if not isinstance(source, ContentSource):
            return CapabilityResult.failure(
                "Content source must be a ContentSource instance"
            )

        try:
            reference = self._downloader.download(source.reference)
        except Exception as exc:
            return CapabilityResult.failure(str(exc))

        asset = ContentAsset.create(
            asset_type="source_media",
            reference=reference,
            source=source,
        )
        context.set(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY, asset)
        return CapabilityResult.success()
