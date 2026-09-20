from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class InstallMarketplaceWorkflow:
    """Compatibility installation path for legacy workflow-backed listings."""

    def __init__(
        self,
        workflows: list[Workflow] | list[WorkflowVersion],
    ) -> None:
        self._workflows = tuple(workflows)
        self._versions = tuple(
            item for item in workflows if isinstance(item, WorkflowVersion)
        )
        if self._versions:
            if any(not isinstance(item, WorkflowVersion) for item in workflows):
                raise ValueError("Workflows and versions cannot be mixed")
        elif any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflows must be Workflow instances")

    def execute(self, listing: MarketplaceListing) -> Workflow | WorkflowVersion:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")
        if listing.status != ListingStatus.PUBLISHED:
            raise ValueError("Only published marketplace listings can be installed")
        if listing.visibility != ListingVisibility.PUBLIC:
            raise ValueError("Only public marketplace listings can be installed")

        if listing.workflow_version_id is not None:
            version = next(
                (item for item in self._versions if item.id == listing.workflow_version_id),
                None,
            )
            if version is None:
                raise ValueError("Marketplace listing references an unknown workflow version")
            if version.state != WorkflowState.PUBLISHED:
                raise ValueError("Marketplace listing workflow version must be published")
            if listing.workflow_id != version.workflow_id:
                raise ValueError("Marketplace listing workflow and version do not match")
            if not set(listing.supported_goals).issubset(set(version.supported_goals)):
                raise ValueError("Marketplace listing goals must be supported by workflow version")
            return version

        workflow = next(
            (item for item in self._workflows if isinstance(item, Workflow) and item.id == listing.workflow_id),
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
        if listing.workflow_version_id is None:
            raise ValueError("Marketplace listing must reference a workflow version")
        if listing.status != ListingStatus.PUBLISHED:
            raise ValueError("Only published marketplace listings can be installed")
        if listing.visibility != ListingVisibility.PUBLIC:
            raise ValueError("Only public marketplace listings can be installed")

        version = next(
            (item for item in self._versions if item.id == listing.workflow_version_id),
            None,
        )
        if version is None:
            raise ValueError("Marketplace listing references an unknown workflow version")
        if version.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow version must be published")
        if listing.workflow_id is not None and listing.workflow_id != version.workflow_id:
            raise ValueError("Marketplace listing workflow and version do not match")
        if not set(listing.supported_goals).issubset(set(version.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by workflow version")

        return version
