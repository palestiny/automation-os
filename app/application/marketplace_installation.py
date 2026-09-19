from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState


class InstallMarketplaceWorkflow:
    """Validate a marketplace listing and return its existing published workflow."""

    def __init__(self, workflows: list[Workflow]) -> None:
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflows must be Workflow instances")
        self._workflows = tuple(workflows)

    def execute(self, listing: MarketplaceListing) -> Workflow:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")
        if listing.status != ListingStatus.PUBLISHED:
            raise ValueError("Only published marketplace listings can be installed")
        if listing.visibility != ListingVisibility.PUBLIC:
            raise ValueError("Only public marketplace listings can be installed")

        workflow = next(
            (item for item in self._workflows if item.id == listing.workflow_id),
            None,
        )
        if workflow is None:
            raise ValueError("Marketplace listing references an unknown workflow")
        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow must be published")
        if not set(listing.supported_goals).issubset(set(workflow.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by workflow")

        return workflow
