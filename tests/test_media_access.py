import pytest

from app.application.media_access import (
    InMemoryMediaAssetReader,
    MediaAssetNotFoundError,
    MediaAssetReader,
)
from app.domain.content import ContentAsset


def test_media_asset_reader_is_a_provider_neutral_protocol():
    reader = InMemoryMediaAssetReader({"asset://clip/123": b"video-bytes"})

    assert isinstance(reader, MediaAssetReader)


def test_media_asset_reader_returns_asset_bytes():
    reader = InMemoryMediaAssetReader({"asset://clip/123": b"video-bytes"})
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )

    assert reader.read(asset) == b"video-bytes"


def test_media_asset_reader_does_not_mutate_source_mapping():
    assets = {"asset://clip/123": b"video-bytes"}
    reader = InMemoryMediaAssetReader(assets)
    assets["asset://clip/123"] = b"changed"

    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )

    assert reader.read(asset) == b"video-bytes"


def test_media_asset_reader_raises_typed_error_when_asset_is_missing():
    reader = InMemoryMediaAssetReader({})
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/missing",
    )

    with pytest.raises(
        MediaAssetNotFoundError,
        match="Media asset was not found",
    ):
        reader.read(asset)
