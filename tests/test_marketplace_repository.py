from uuid import uuid4

from app.domain.marketplace import MarketplaceListing
from app.infrastructure.persistence.in_memory import InMemoryMarketplaceListingRepository


def test_in_memory_marketplace_listing_repository_round_trips_listing():
    repository = InMemoryMarketplaceListingRepository()
    listing = MarketplaceListing.create(
        uuid4(),
        "Listing",
        "Description",
        "content",
        ("goal",),
        ("tag",),
    )

    repository.save(listing)

    assert repository.get(listing.id) == listing
    assert repository.all() == (listing,)
