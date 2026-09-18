import pytest
from dataclasses import FrozenInstanceError
from uuid import UUID

from app.domain.content import ContentAsset, Publication, PublicationRequest


def test_publication_request_can_be_created():
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )

    request = PublicationRequest.create(
        asset=asset,
        destination="video_platform",
    )

    assert request.asset == asset
    assert request.destination == "video_platform"


def test_publication_request_rejects_invalid_asset():
    with pytest.raises(
        ValueError,
        match="PublicationRequest asset must be a ContentAsset instance",
    ):
        PublicationRequest.create(
            asset="not-an-asset",
            destination="video_platform",
        )


def test_publication_request_rejects_empty_destination():
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )

    with pytest.raises(
        ValueError,
        match="PublicationRequest destination cannot be empty",
    ):
        PublicationRequest.create(
            asset=asset,
            destination=" ",
        )


def test_publication_request_is_immutable():
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )
    request = PublicationRequest.create(
        asset=asset,
        destination="video_platform",
    )

    with pytest.raises(FrozenInstanceError):
        request.destination = "other_platform"


def test_publication_can_be_created_with_opaque_external_reference():
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )

    publication = Publication.create(
        asset=asset,
        destination="video_platform",
        external_reference="provider-ref-123",
    )

    assert isinstance(publication.id, UUID)
    assert publication.asset == asset
    assert publication.destination == "video_platform"
    assert publication.external_reference == "provider-ref-123"


@pytest.mark.parametrize("destination", ["", " "])
def test_publication_rejects_empty_destination(destination):
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )

    with pytest.raises(ValueError, match="Publication destination cannot be empty"):
        Publication.create(
            asset=asset,
            destination=destination,
            external_reference="provider-ref-123",
        )


def test_publication_rejects_empty_external_reference():
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )

    with pytest.raises(
        ValueError,
        match="Publication external_reference cannot be empty",
    ):
        Publication.create(
            asset=asset,
            destination="video_platform",
            external_reference=" ",
        )


def test_publication_rejects_invalid_asset():
    with pytest.raises(
        ValueError,
        match="Publication asset must be a ContentAsset instance",
    ):
        Publication.create(
            asset="not-an-asset",
            destination="video_platform",
            external_reference="provider-ref-123",
        )


def test_publication_is_immutable():
    asset = ContentAsset.create(
        asset_type="clip",
        reference="asset://clip/123",
    )
    publication = Publication.create(
        asset=asset,
        destination="video_platform",
        external_reference="provider-ref-123",
    )

    with pytest.raises(FrozenInstanceError):
        publication.external_reference = "changed"
