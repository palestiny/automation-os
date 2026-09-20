from __future__ import annotations

from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.workflow import WorkflowState
from app.domain.workflow_version import WorkflowVersion


class InstallMarketplaceWorkflow:
    """Validate a marketplace listing and return its exact published WorkflowVersion."""

    def __init__(self, versions: list[WorkflowVersion]) -> None:
        if any(not isinstance(version, WorkflowVersion) for version in versions):
            raise ValueError("Workflow versions must be WorkflowVersion instances")
        self._versions = tuple(versions)

    def execute(self, listing: MarketplaceListing) -> WorkflowVersion:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")
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
        if version.workflow_id != listing.workflow_id:
            raise ValueError("Marketplace listing workflow and version do not match")
        if version.state != WorkflowState.PUBLISHED:
            raise ValueError("Marketplace listing workflow version must be published")
        if not set(listing.supported_goals).issubset(set(version.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by workflow version")

        return version
