import pytest
from dataclasses import FrozenInstanceError

from app.application.content_acquisition import (
    ACQUIRED_CONTENT_ASSET_CONTEXT_KEY,
)
from app.application.content_transcription import (
    CONTENT_TRANSCRIPT_CONTEXT_KEY,
    InMemoryContentTranscriptionCapability,
)
from app.application.execution_context import ExecutionContext
from app.domain.content import ContentAsset, Transcript


def test_transcript_can_be_created_from_source_asset():
    asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
    )

    transcript = Transcript.create(
        text="Hello world",
        source_asset=asset,
    )

    assert transcript.text == "Hello world"
    assert transcript.source_asset == asset


def test_transcript_rejects_empty_text():
    asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
    )

    with pytest.raises(ValueError, match="Transcript text cannot be empty"):
        Transcript.create(text=" ", source_asset=asset)


def test_transcript_requires_source_asset():
    with pytest.raises(ValueError, match="Transcript source_asset must be a ContentAsset instance"):
        Transcript.create(
            text="Hello world",
            source_asset=None,
        )


def test_transcript_is_immutable():
    asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
    )
    transcript = Transcript.create(text="Hello world", source_asset=asset)

    with pytest.raises(FrozenInstanceError):
        transcript.text = "Changed"


def test_transcription_capability_produces_transcript():
    asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
    )
    context = ExecutionContext()
    context.set(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY, asset)

    capability = InMemoryContentTranscriptionCapability(
        transcript_text="Hello world",
    )

    result = capability.execute(context)

    assert result.succeeded is True
    transcript = context.get(CONTENT_TRANSCRIPT_CONTEXT_KEY)
    assert isinstance(transcript, Transcript)
    assert transcript.text == "Hello world"
    assert transcript.source_asset == asset


def test_transcription_capability_fails_when_asset_is_missing():
    context = ExecutionContext()
    capability = InMemoryContentTranscriptionCapability(
        transcript_text="Hello world",
    )

    result = capability.execute(context)

    assert result.succeeded is False
    assert "source media" in str(result.error).lower()
    with pytest.raises(KeyError):
        context.get(CONTENT_TRANSCRIPT_CONTEXT_KEY)
