from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import WorkflowState
from app.domain.workflow_version import WorkflowVersion


class DiscoverMarketplaceListings:
    """Deterministically discovers public listings backed by published versions."""

    def __init__(
        self,
        listings: list[MarketplaceListing],
        versions: list[WorkflowVersion],
    ) -> None:
        if any(not isinstance(listing, MarketplaceListing) for listing in listings):
            raise ValueError("Listing must be a MarketplaceListing instance")
        if any(not isinstance(version, WorkflowVersion) for version in versions):
            raise ValueError("Workflow version must be a WorkflowVersion instance")

        self._listings = tuple(listings)
        self._versions = {version.id: version for version in versions}

    def execute(
        self,
        goal: str | None = None,
        domain: str | None = None,
        search: str | None = None,
    ) -> tuple[MarketplaceListing, ...]:
        if goal is not None and (not isinstance(goal, str) or not goal.strip()):
            raise ValueError("goal must be a non-empty string or None")
        if domain is not None and (not isinstance(domain, str) or not domain.strip()):
            raise ValueError("domain must be a non-empty string or None")
        if search is not None and (not isinstance(search, str) or not search.strip()):
            raise ValueError("search must be a non-empty string or None")

        search_terms = tuple(search.lower().split()) if search is not None else ()
        result = []
        for listing in self._listings:
            version = self._versions.get(listing.workflow_version_id)

            if listing.status != ListingStatus.PUBLISHED or listing.visibility != ListingVisibility.PUBLIC:
                continue
            if version is None or version.workflow_id != listing.workflow_id:
                continue
            if version.state != WorkflowState.PUBLISHED:
                continue
            if goal is not None and goal not in listing.supported_goals:
                continue
            if domain is not None and domain != listing.domain:
                continue

            if search_terms:
                searchable = " ".join((
                    listing.title,
                    listing.description,
                    listing.domain,
                    *listing.tags,
                    *listing.supported_goals,
                )).lower()
                if any(term not in searchable for term in search_terms):
                    continue

            result.append(listing)

        return tuple(result)
