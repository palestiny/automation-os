from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import WorkflowState, Workflow
from app.domain.workflow_version import WorkflowVersion


class DiscoverMarketplaceListings:
    """Deterministically discovers public listings backed by published versions."""

    def __init__(
        self,
        listings: list[MarketplaceListing],
        workflows: list[Workflow],
        workflow_versions: list[WorkflowVersion],
    ) -> None:
        self._listings = tuple(listings)
        self._workflows = {workflow.id: workflow for workflow in workflows}
        self._versions = {version.id: version for version in workflow_versions}

    def execute(self, goal=None, domain=None, search=None):
        if goal is not None and (not isinstance(goal, str) or not goal.strip()):
            raise ValueError("goal must be a non-empty string or None")
        if domain is not None and (not isinstance(domain, str) or not domain.strip()):
            raise ValueError("domain must be a non-empty string or None")
        if search is not None and (not isinstance(search, str) or not search.strip()):
            raise ValueError("search must be a non-empty string or None")
        terms = tuple(search.lower().split()) if search is not None else ()
        result = []
        for listing in self._listings:
            workflow = self._workflows.get(listing.workflow_id)
            version = self._versions.get(listing.workflow_version_id)
            if listing.status != ListingStatus.PUBLISHED or listing.visibility != ListingVisibility.PUBLIC:
                continue
            if workflow is None or workflow.state != WorkflowState.PUBLISHED:
                continue
            if version is None or version.workflow_id != workflow.id or version.state != WorkflowState.PUBLISHED:
                continue
            if goal is not None and goal not in version.supported_goals:
                continue
            if domain is not None and domain != (version.automation_domain or listing.domain):
                continue
            if terms:
                searchable = " ".join((listing.title, listing.description, listing.domain, *listing.tags, *version.supported_goals)).lower()
                if any(term not in searchable for term in terms):
                    continue
            result.append(listing)
        return tuple(result)
