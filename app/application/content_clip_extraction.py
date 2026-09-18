from __future__ import annotations

from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext
from app.domain.content import ClipSelection, ContentAsset


CLIP_CONTEXT_KEY = "content.clip"


class InMemoryContentClipExtractionCapability(Capability):
    """Provider-neutral test implementation of clip extraction."""

    def __init__(
        self,
        clip_reference: str,
        selection: ClipSelection | None,
    ) -> None:
        self._clip_reference = clip_reference
        self._selection = selection

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        try:
            source_asset = context.get("content.acquired_asset")
        except KeyError:
            return CapabilityResult.failure(
                "Source media is required for clip extraction"
            )

        if not isinstance(source_asset, ContentAsset):
            return CapabilityResult.failure(
                "Source media must be a ContentAsset instance"
            )

        if self._selection is None:
            return CapabilityResult.failure(
                "Clip selection is required for clip extraction"
            )

        clip = ContentAsset.create(
            asset_type="clip",
            reference=self._clip_reference,
            source=source_asset.source,
            derived_from=source_asset,
        )
        context.set(CLIP_CONTEXT_KEY, clip)
        return CapabilityResult.success()
