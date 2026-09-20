from __future__ import annotations

from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow
from app.domain.workflow_version import WorkflowVersion


class PublishMarketplaceListing:
    """Validate a listing against one published immutable WorkflowVersion."""

    def __init__(
        self,
        workflows: list[Workflow],
        workflow_versions: list[WorkflowVersion],
    ) -> None:
        self._workflows = {workflow.id: workflow for workflow in workflows}
        self._versions = {version.id: version for version in workflow_versions}

    def execute(self, listing: MarketplaceListing) -> MarketplaceListing:
        workflow = self._workflows.get(listing.workflow_id)
        version = self._versions.get(listing.workflow_version_id)
        if workflow is None:
            raise ValueError("Marketplace listing references an unknown workflow")
        if version is None:
            raise ValueError("Marketplace listing references an unknown workflow version")
        if workflow.id != version.workflow_id or listing.workflow_id != version.workflow_id:
            raise ValueError("Marketplace listing workflow and version do not match")
        from app.domain.workflow import WorkflowState
        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow must be published")
        if version.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow version must be published")
        if not set(listing.supported_goals).issubset(set(version.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by workflow version")
        return listing.publish()
