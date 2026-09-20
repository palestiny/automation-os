from uuid import uuid4

from app.domain.marketplace import MarketplaceListing
from app.infrastructure.persistence.in_memory import InMemoryMarketplaceListingRepository


def test_listing_repository_round_trip():
    repository = InMemoryMarketplaceListingRepository()
    listing = MarketplaceListing.create(
        workflow_id=uuid4(),
        workflow_version_id=uuid4(),
        title="Listing",
        description="Description",
        domain="content",
        supported_goals=("publish",),
        tags=("video",),
    )

    repository.save(listing)

    assert repository.get(listing.id) == listing
    assert repository.all() == (listing,)
