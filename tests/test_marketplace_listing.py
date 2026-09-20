from uuid import uuid4

import pytest

from app.domain.marketplace import ListingVisibility, MarketplaceListing


def test_listing_references_existing_workflow_identity():
    workflow_id = uuid4()

    listing = MarketplaceListing.create(
        workflow_id=workflow_id,
        title="Sales Report",
        description="Generate a sales report",
        domain="business_reporting",
        supported_goals=("generate_business_report",),
        tags=("reporting", "sales"),
    )

    assert listing.workflow_id == workflow_id
    assert listing.visibility == ListingVisibility.PUBLIC
    assert listing.supported_goals == ("generate_business_report",)
    assert listing.tags == ("reporting", "sales")


def test_listing_requires_metadata():
    with pytest.raises(ValueError, match="title"):
        MarketplaceListing.create(
            uuid4(), "", "Description", "business", ("goal",), ()
        )

    with pytest.raises(ValueError, match="description"):
        MarketplaceListing.create(
            uuid4(), "Title", "", "business", ("goal",), ()
        )

    with pytest.raises(ValueError, match="domain"):
        MarketplaceListing.create(
            uuid4(), "Title", "Description", "", ("goal",), ()
        )


def test_listing_rejects_duplicate_tags_and_goals():
    with pytest.raises(ValueError, match="unique"):
        MarketplaceListing.create(
            uuid4(), "Title", "Description", "business",
            ("goal", "goal"), ("tag",),
        )

    with pytest.raises(ValueError, match="unique"):
        MarketplaceListing.create(
            uuid4(), "Title", "Description", "business",
            ("goal",), ("tag", "tag"),
        )


def test_listing_visibility_is_explicit_and_immutable():
    listing = MarketplaceListing.create(
        uuid4(), "Title", "Description", "business", ("goal",), (),
    )

    assert listing.visibility == ListingVisibility.PUBLIC
    with pytest.raises(AttributeError):
        listing.visibility = ListingVisibility.HIDDEN


def test_new_listing_starts_as_draft():
    listing = MarketplaceListing.create(
        uuid4(), "Title", "Description", "business", ("goal",), (),
    )

    assert listing.status.name == "DRAFT"


def test_listing_can_be_published():
    listing = MarketplaceListing.create(
        uuid4(), "Title", "Description", "business", ("goal",), (),
    )

    listing = listing.publish()

    assert listing.status.name == "PUBLISHED"


def test_listing_can_be_withdrawn_after_publication():
    listing = MarketplaceListing.create(
        uuid4(), "Title", "Description", "business", ("goal",), (),
    )

    listing = listing.publish()
    listing = listing.withdraw()

    assert listing.status.name == "WITHDRAWN"


def test_listing_cannot_be_withdrawn_before_publication():
    listing = MarketplaceListing.create(
        uuid4(), "Title", "Description", "business", ("goal",), (),
    )

    with pytest.raises(ValueError, match="published"):
        listing.withdraw()


def test_withdrawn_listing_cannot_be_republished():
    listing = MarketplaceListing.create(
        uuid4(), "Title", "Description", "business", ("goal",), (),
    )

    listing = listing.publish()
    listing = listing.withdraw()

    with pytest.raises(ValueError, match="withdrawn"):
        listing.publish()


def test_listing_has_stable_identity():
    first = MarketplaceListing.create(
        uuid4(), "Title", "Description", "business", ("goal",), (),
    )
    second = MarketplaceListing.create(
        first.workflow_id, "Title", "Description", "business", ("goal",), (),
    )

    assert first.id != second.id
