from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.repositories import WorkflowVersionRepository
from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class InstallMarketplaceWorkflow:
    """Validate a listing and return its exact immutable published WorkflowVersion."""

    def __init__(
        self,
        workflows: list[Workflow],
        version_repository: WorkflowVersionRepository | None = None,
    ) -> None:
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflows must be Workflow instances")
        self._workflows = tuple(workflows)
        self._version_repository = version_repository

    def execute(self, listing: MarketplaceListing) -> WorkflowVersion:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")
        if listing.status != ListingStatus.PUBLISHED:
            raise ValueError("Only published marketplace listings can be installed")
        if listing.visibility != ListingVisibility.PUBLIC:
            raise ValueError("Only public marketplace listings can be installed")
        if listing.workflow_version_id is None:
            raise ValueError("Marketplace listing must pin a WorkflowVersion")
        if self._version_repository is None:
            raise ValueError("WorkflowVersionRepository is required for version-pinned marketplace installation")

        version = self._version_repository.get(listing.workflow_version_id)
        if version is None:
            raise ValueError("Marketplace listing references an unknown WorkflowVersion")
        if version.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing WorkflowVersion must be published")
        if version.workflow_id != listing.workflow_id:
            raise ValueError("Marketplace listing WorkflowVersion must belong to its Workflow")
        if not set(listing.supported_goals).issubset(set(version.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by WorkflowVersion")

        workflow = next(
            (item for item in self._workflows if item.id == listing.workflow_id),
            None,
        )
        if workflow is None:
            raise ValueError("Marketplace listing references an unknown workflow")
        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow must be published")

        return version
