import pytest
from dataclasses import FrozenInstanceError

from app.application.content_acquisition import (
    ACQUIRED_CONTENT_ASSET_CONTEXT_KEY,
)
from app.application.content_transcription import CONTENT_TRANSCRIPT_CONTEXT_KEY
from app.application.content_clip_extraction import (
    CLIP_CONTEXT_KEY,
    InMemoryContentClipExtractionCapability,
)
from app.application.execution_context import ExecutionContext
from app.domain.content import ClipSelection, ContentAsset, Transcript


def test_clip_selection_can_represent_explicit_time_range():
    selection = ClipSelection.create(start_seconds=10, end_seconds=40)

    assert selection.start_seconds == 10
    assert selection.end_seconds == 40


@pytest.mark.parametrize(
    ("start", "end"),
    [(-1, 10), (10, 10), (40, 10)],
)
def test_clip_selection_rejects_invalid_time_range(start, end):
    with pytest.raises(ValueError):
        ClipSelection.create(start_seconds=start, end_seconds=end)


def test_clip_selection_is_immutable():
    selection = ClipSelection.create(start_seconds=10, end_seconds=40)

    with pytest.raises(FrozenInstanceError):
        selection.start_seconds = 20


def test_clip_extraction_produces_clip_asset_from_source_and_selection():
    source_asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
    )
    transcript = Transcript.create(text="Hello world", source_asset=source_asset)
    context = ExecutionContext()
    context.set(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY, source_asset)
    context.set(CONTENT_TRANSCRIPT_CONTEXT_KEY, transcript)

    capability = InMemoryContentClipExtractionCapability(
        clip_reference="asset://clip/123",
        selection=ClipSelection.create(start_seconds=10, end_seconds=40),
    )

    result = capability.execute(context)

    assert result.succeeded is True
    clip = context.get(CLIP_CONTEXT_KEY)
    assert isinstance(clip, ContentAsset)
    assert clip.asset_type == "clip"
    assert clip.reference == "asset://clip/123"
    assert clip.derived_from == source_asset


def test_clip_extraction_fails_when_source_media_is_missing():
    context = ExecutionContext()
    capability = InMemoryContentClipExtractionCapability(
        clip_reference="asset://clip/123",
        selection=ClipSelection.create(start_seconds=10, end_seconds=40),
    )

    result = capability.execute(context)

    assert result.succeeded is False
    assert "source media" in str(result.error).lower()


def test_clip_extraction_fails_when_selection_is_missing():
    source_asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
    )
    context = ExecutionContext()
    context.set(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY, source_asset)

    capability = InMemoryContentClipExtractionCapability(
        clip_reference="asset://clip/123",
        selection=None,
    )

    result = capability.execute(context)

    assert result.succeeded is False
    assert "clip selection" in str(result.error).lower()
