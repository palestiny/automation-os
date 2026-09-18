import pytest

from app.application.capability import Capability
from app.application.capability_result import CapabilityResult
from app.application.content_acquisition import (
    ACQUIRED_CONTENT_ASSET_CONTEXT_KEY,
    CONTENT_SOURCE_CONTEXT_KEY,
    InMemoryContentAcquisitionCapability,
)
from app.application.execution_context import ExecutionContext
from app.domain.content import ContentAsset, ContentSource


def test_acquisition_capability_uses_the_existing_capability_contract():
    capability = InMemoryContentAcquisitionCapability()

    assert isinstance(capability, Capability)


def test_acquisition_capability_produces_content_asset_from_source():
    source = ContentSource.create(
        reference="https://example.com/content/123",
        source_type="url",
    )
    context = ExecutionContext()
    context.set(CONTENT_SOURCE_CONTEXT_KEY, source)

    capability = InMemoryContentAcquisitionCapability(
        asset_reference="asset://source-media/123",
    )

    result = capability.execute(context)

    assert isinstance(result, CapabilityResult)
    assert result.succeeded is True

    asset = context.get(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY)

    assert isinstance(asset, ContentAsset)
    assert asset.asset_type == "source_media"
    assert asset.reference == "asset://source-media/123"
    assert asset.source == source


def test_acquisition_capability_fails_when_source_is_missing():
    context = ExecutionContext()
    capability = InMemoryContentAcquisitionCapability(
        asset_reference="asset://source-media/123",
    )

    result = capability.execute(context)

    assert result.succeeded is False
    assert "content source" in str(result.error).lower()
    with pytest.raises(KeyError):
        context.get(ACQUIRED_CONTENT_ASSET_CONTEXT_KEY)


def test_acquisition_capability_does_not_modify_unrelated_context_state():
    source = ContentSource.create(
        reference="https://example.com/content/123",
        source_type="url",
    )
    context = ExecutionContext()
    context.set(CONTENT_SOURCE_CONTEXT_KEY, source)
    context.set("unrelated", "value")

    capability = InMemoryContentAcquisitionCapability(
        asset_reference="asset://source-media/123",
    )

    capability.execute(context)

    assert context.get("unrelated") == "value"
