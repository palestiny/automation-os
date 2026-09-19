from __future__ import annotations

from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState


class PublishMarketplaceListing:
    """Validate a listing against its workflow and publish it."""

    def __init__(self, workflows: list[Workflow]) -> None:
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflows must be Workflow instances")
        self._workflows = tuple(workflows)

    def execute(self, listing: MarketplaceListing) -> MarketplaceListing:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")

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

        return listing.publish()
