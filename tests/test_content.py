import pytest
from dataclasses import FrozenInstanceError

from app.domain.content import ContentAsset, ContentSource


def test_content_source_can_be_created():
    source = ContentSource.create(
        reference="https://example.com/content/123",
        source_type="url",
    )

    assert source.reference == "https://example.com/content/123"
    assert source.source_type == "url"


def test_content_source_rejects_empty_reference():
    with pytest.raises(ValueError, match="ContentSource reference cannot be empty"):
        ContentSource.create(reference=" ", source_type="url")


def test_content_source_rejects_empty_source_type():
    with pytest.raises(ValueError, match="ContentSource source_type cannot be empty"):
        ContentSource.create(reference="https://example.com/content/123", source_type=" ")


def test_content_source_is_immutable():
    source = ContentSource.create(
        reference="https://example.com/content/123",
        source_type="url",
    )

    with pytest.raises(FrozenInstanceError):
        source.reference = "changed"


def test_content_asset_can_be_created():
    source = ContentSource.create(
        reference="https://example.com/content/123",
        source_type="url",
    )

    asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
        source=source,
    )

    assert asset.asset_type == "source_media"
    assert asset.reference == "asset://source-media/123"
    assert asset.source == source


def test_content_asset_rejects_empty_type():
    with pytest.raises(ValueError, match="ContentAsset asset_type cannot be empty"):
        ContentAsset.create(
            asset_type=" ",
            reference="asset://source-media/123",
        )


def test_content_asset_rejects_empty_reference():
    with pytest.raises(ValueError, match="ContentAsset reference cannot be empty"):
        ContentAsset.create(
            asset_type="source_media",
            reference=" ",
        )


def test_content_asset_is_immutable():
    asset = ContentAsset.create(
        asset_type="source_media",
        reference="asset://source-media/123",
    )

    with pytest.raises(FrozenInstanceError):
        asset.asset_type = "clip"
