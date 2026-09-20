from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class DiscoverMarketplaceListings:
    """Deterministically discovers public listings backed by published artifacts."""

    def __init__(
        self,
        listings: list[MarketplaceListing],
        workflows: list[Workflow],
        versions: list[WorkflowVersion] | None = None,
    ) -> None:
        if any(not isinstance(listing, MarketplaceListing) for listing in listings):
            raise ValueError("Listing must be a MarketplaceListing instance")
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflow must be a Workflow instance")
        if versions is not None and any(
            not isinstance(version, WorkflowVersion) for version in versions
        ):
            raise ValueError("Versions must be WorkflowVersion instances")

        self._listings = tuple(listings)
        self._workflows = {workflow.id: workflow for workflow in workflows}
        self._versions = {version.id: version for version in (versions or ())}

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
            if listing.status != ListingStatus.PUBLISHED or listing.visibility != ListingVisibility.PUBLIC:
                continue

            if listing.workflow_version_id is not None:
                version = self._versions.get(listing.workflow_version_id)
                if version is None or version.state != WorkflowState.PUBLISHED:
                    continue
                workflow_id = version.workflow_id
                supported_goals = version.supported_goals
            else:
                workflow = self._workflows.get(listing.workflow_id)
                if workflow is None or workflow.state != WorkflowState.PUBLISHED:
                    continue
                supported_goals = workflow.supported_goals
                workflow_id = workflow.id

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
                    *supported_goals,
                )).lower()
                if any(term not in searchable for term in search_terms):
                    continue

            result.append(listing)

        return tuple(result)
