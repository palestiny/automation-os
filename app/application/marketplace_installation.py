from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import WorkflowState, Workflow
from app.domain.workflow_version import WorkflowVersion


class InstallMarketplaceWorkflow:
    """Validate a listing and return its exact published WorkflowVersion."""

    def __init__(
        self,
        workflows: list[Workflow],
        workflow_versions: list[WorkflowVersion],
    ) -> None:
        self._workflows = {workflow.id: workflow for workflow in workflows}
        self._versions = {version.id: version for version in workflow_versions}

    def execute(self, listing: MarketplaceListing) -> WorkflowVersion:
        if listing.status != ListingStatus.PUBLISHED:
            raise ValueError("Only published marketplace listings can be installed")
        if listing.visibility != ListingVisibility.PUBLIC:
            raise ValueError("Only public marketplace listings can be installed")
        workflow = self._workflows.get(listing.workflow_id)
        version = self._versions.get(listing.workflow_version_id)
        if workflow is None:
            raise ValueError("Marketplace listing references an unknown workflow")
        if version is None:
            raise ValueError("Marketplace listing references an unknown workflow version")
        if version.workflow_id != workflow.id:
            raise ValueError("Marketplace listing workflow and version do not match")
        if version.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow version must be published")
        if not set(listing.supported_goals).issubset(set(version.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by workflow version")
        return version
