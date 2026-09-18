from __future__ import annotations

from app.domain.marketplace import ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState


class InstallMarketplaceWorkflow:
    """Makes an existing published workflow available without executing it."""

    def __init__(self, workflows: list[Workflow]) -> None:
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflow must be a Workflow instance")
        self._workflows = {workflow.id: workflow for workflow in workflows}

    def execute(self, listing: MarketplaceListing) -> Workflow:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")

        if listing.visibility != ListingVisibility.PUBLIC:
            raise ValueError("Marketplace listing must be public")

        workflow = self._workflows.get(listing.workflow_id)
        if workflow is None:
            raise ValueError("Marketplace listing references an unknown workflow")

        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow must be published")

        if not set(listing.supported_goals).issubset(set(workflow.supported_goals)):
            raise ValueError("Marketplace listing contains unsupported workflow goals")

        return workflow
