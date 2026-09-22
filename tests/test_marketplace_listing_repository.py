from uuid import uuid4

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.infrastructure.persistence.in_memory import InMemoryMarketplaceListingRepository


def make_listing():
    return MarketplaceListing.create(
        workflow_id=uuid4(), title="Listing", description="Description",
        domain="content", supported_goals=("create_short_video",), tags=("content",),
    )


def test_listing_has_stable_identity():
    listing = make_listing()
    assert listing.id is not None
    assert listing.id != make_listing().id


def test_listing_repository_round_trip_and_all_are_deterministic():
    repository = InMemoryMarketplaceListingRepository()
    first, second = make_listing(), make_listing()
    repository.save(second); repository.save(first)
    assert repository.get(first.id) == first
    assert repository.all() == tuple(sorted((first, second), key=lambda item: item.id))


def test_listing_repository_updates_existing_identity():
    repository = InMemoryMarketplaceListingRepository()
    listing = make_listing(); repository.save(listing)
    published = listing.publish(); repository.save(published)
    assert repository.get(listing.id) == published
    assert len(repository.all()) == 1
    assert repository.get(listing.id).status is ListingStatus.PUBLISHED


def test_listing_validation_preserves_visibility_and_status():
    listing = MarketplaceListing.create(
        workflow_id=uuid4(), title=" Listing ", description=" Description ",
        domain=" content ", supported_goals=(" create_short_video ",), tags=(" content ",),
        visibility=ListingVisibility.HIDDEN,
    )
    assert listing.title == "Listing"
    assert listing.domain == "content"
    assert listing.visibility is ListingVisibility.HIDDEN


def test_marketplace_listing_repository_isolates_tenants_in_memory():
    tenant_a = uuid4()
    tenant_b = uuid4()
    listing = MarketplaceListing.create(
        workflow_id=uuid4(),
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("content",),
        tenant_id=tenant_a,
    )
    repository_a = InMemoryMarketplaceListingRepository(tenant_id=tenant_a)
    repository_b = InMemoryMarketplaceListingRepository(tenant_id=tenant_b)

    repository_a.save(listing)

    assert repository_a.get(listing.id) == listing
    assert repository_b.get(listing.id) is None
    assert repository_b.all() == ()


def test_marketplace_listing_rejects_cross_tenant_save_in_memory():
    listing = MarketplaceListing.create(
        workflow_id=uuid4(),
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=("create_short_video",),
        tags=("content",),
        tenant_id=uuid4(),
    )
    repository = InMemoryMarketplaceListingRepository(tenant_id=uuid4())

    with pytest.raises(ValueError, match="different tenant"):
        repository.save(listing)
