from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.repositories import WorkflowVersionRepository
from app.domain.workflow import Workflow, WorkflowState


class DiscoverMarketplaceListings:
    """Deterministically discovers public listings pinned to published versions."""

    def __init__(
        self,
        listings: list[MarketplaceListing],
        workflows: list[Workflow],
        version_repository: WorkflowVersionRepository | None = None,
    ) -> None:
        if any(not isinstance(listing, MarketplaceListing) for listing in listings):
            raise ValueError("Listing must be a MarketplaceListing instance")
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflow must be a Workflow instance")

        self._listings = tuple(listings)
        self._workflows = {workflow.id: workflow for workflow in workflows}
        self._version_repository = version_repository

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
        if self._version_repository is None:
            raise ValueError("WorkflowVersionRepository is required for marketplace discovery")

        search_terms = tuple(search.lower().split()) if search is not None else ()
        result = []
        for listing in self._listings:
            workflow = self._workflows.get(listing.workflow_id)

            if listing.status != ListingStatus.PUBLISHED or listing.visibility != ListingVisibility.PUBLIC:
                continue
            if listing.workflow_version_id is None:
                continue
            if workflow is None or workflow.state != WorkflowState.PUBLISHED:
                continue

            version = self._version_repository.get(listing.workflow_version_id)
            if version is None or version.state != WorkflowState.PUBLISHED:
                continue
            if version.workflow_id != listing.workflow_id:
                continue

            if goal is not None and goal not in listing.supported_goals:
                continue
            if domain is not None and listing.domain != domain:
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
