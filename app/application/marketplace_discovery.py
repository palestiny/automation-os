from __future__ import annotations

from app.domain.marketplace import ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState


class DiscoverMarketplaceListings:
    """Deterministically discovers public listings backed by published workflows."""

    def __init__(
        self,
        listings: list[MarketplaceListing],
        workflows: list[Workflow],
    ) -> None:
        if any(not isinstance(listing, MarketplaceListing) for listing in listings):
            raise ValueError("Listing must be a MarketplaceListing instance")
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflow must be a Workflow instance")

        self._listings = tuple(listings)
        self._workflows = {workflow.id: workflow for workflow in workflows}

    def execute(
        self,
        goal: str | None = None,
        domain: str | None = None,
    ) -> tuple[MarketplaceListing, ...]:
        if goal is not None and (not isinstance(goal, str) or not goal.strip()):
            raise ValueError("goal must be a non-empty string or None")
        if domain is not None and (not isinstance(domain, str) or not domain.strip()):
            raise ValueError("domain must be a non-empty string or None")

        result = []
        for listing in self._listings:
            workflow = self._workflows.get(listing.workflow_id)

            if listing.visibility != ListingVisibility.PUBLIC:
                continue
            if workflow is None or workflow.state != WorkflowState.PUBLISHED:
                continue
            if goal is not None and goal not in listing.supported_goals:
                continue
            if domain is not None and listing.domain != domain:
                continue

            result.append(listing)

        return tuple(result)
