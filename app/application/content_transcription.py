from __future__ import annotations

from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext
from app.domain.content import ContentAsset, Transcript


CONTENT_TRANSCRIPT_CONTEXT_KEY = "content.transcript"


class InMemoryContentTranscriptionCapability(Capability):
    """Provider-neutral test implementation of content transcription."""

    def __init__(self, transcript_text: str) -> None:
        self._transcript_text = transcript_text

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        try:
            source_asset = context.get("content.acquired_asset")
        except KeyError:
            return CapabilityResult.failure(
                "Source media is required for transcription"
            )

        if not isinstance(source_asset, ContentAsset):
            return CapabilityResult.failure(
                "Source media must be a ContentAsset instance"
            )

        transcript = Transcript.create(
            text=self._transcript_text,
            source_asset=source_asset,
        )
        context.set(CONTENT_TRANSCRIPT_CONTEXT_KEY, transcript)

        return CapabilityResult.success()
