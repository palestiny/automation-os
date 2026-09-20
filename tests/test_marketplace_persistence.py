from uuid import uuid4

from app.domain.marketplace import MarketplaceListing
from app.infrastructure.persistence.in_memory import InMemoryMarketplaceListingRepository


def test_in_memory_marketplace_listing_survives_repository_reuse():
    repository = InMemoryMarketplaceListingRepository()
    listing = MarketplaceListing.create(
        uuid4(), uuid4(), "Title", "Description", "business", ("goal",), ()
    )

    repository.save(listing)

    assert repository.get(listing.id) == listing
    assert repository.all() == (listing,)


def test_in_memory_marketplace_listing_has_stable_identity():
    repository = InMemoryMarketplaceListingRepository()
    listing = MarketplaceListing.create(
        uuid4(), uuid4(), "Title", "Description", "business", ("goal",), ()
    )

    repository.save(listing)

    assert repository.get(listing.id).id == listing.id
