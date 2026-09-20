from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class InstallMarketplaceWorkflow:
    """Legacy installation path for workflow-backed listings."""

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
        if listing.workflow_version_id is not None:
            raise ValueError("Version-pinned listing requires version-aware installation")

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


class InstallMarketplaceWorkflowVersion:
    """Install the exact immutable WorkflowVersion referenced by a listing."""

    def __init__(self, versions: list[WorkflowVersion]) -> None:
        if any(not isinstance(version, WorkflowVersion) for version in versions):
            raise ValueError("Versions must be WorkflowVersion instances")
        self._versions = tuple(versions)

    def execute(self, listing: MarketplaceListing) -> WorkflowVersion:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")
        if listing.status != ListingStatus.PUBLISHED:
            raise ValueError("Only published marketplace listings can be installed")
        if listing.visibility != ListingVisibility.PUBLIC:
            raise ValueError("Only public marketplace listings can be installed")
        if listing.workflow_version_id is None:
            raise ValueError("Marketplace listing is not version-pinned")

        version = next(
            (item for item in self._versions if item.id == listing.workflow_version_id),
            None,
        )
        if version is None:
            raise ValueError("Marketplace listing references an unknown workflow version")
        if version.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow version must be published")
        if not set(listing.supported_goals).issubset(set(version.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by workflow version")
        return version
