from __future__ import annotations

from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext
from app.domain.content import ContentAsset, ContentSource


CONTENT_SOURCE_CONTEXT_KEY = "content.source"
ACQUIRED_CONTENT_ASSET_CONTEXT_KEY = "content.acquired_asset"


class InMemoryContentAcquisitionCapability(Capability):
    """Provider-neutral test implementation of content source acquisition."""

    def __init__(self, asset_reference: str) -> None:
        self._asset_reference = asset_reference

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

        asset = ContentAsset.create(
            asset_type="source_media",
            reference=self._asset_reference,
            source=source,
        )
        context.set(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY, asset)

        return CapabilityResult.success()
