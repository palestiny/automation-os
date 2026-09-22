from __future__ import annotations

from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class PublishMarketplaceListing:
    """Validate a listing against its exact immutable WorkflowVersion and publish it."""

    def __init__(
        self,
        workflows: list[Workflow] | list[WorkflowVersion],
        versions: list[WorkflowVersion] | None = None,
    ) -> None:
        if versions is None and all(isinstance(item, WorkflowVersion) for item in workflows):
            versions = workflows
            workflows = []
        if any(not isinstance(workflow, Workflow) for workflow in workflows):
            raise ValueError("Workflows must be Workflow instances")
        if versions is not None and any(
            not isinstance(version, WorkflowVersion) for version in versions
        ):
            raise ValueError("Versions must be WorkflowVersion instances")
        self._workflows = tuple(workflows)
        self._versions = tuple(versions or ())

    def execute(self, listing: MarketplaceListing) -> MarketplaceListing:
        if not isinstance(listing, MarketplaceListing):
            raise TypeError("listing must be a MarketplaceListing instance")

        if listing.workflow_version_id is None:
            raise ValueError("Marketplace listing must reference a workflow version")

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
        if listing.tenant_id != version.tenant_id:
            raise ValueError("Marketplace listing and workflow version belong to different tenants")
        if not set(listing.supported_goals).issubset(set(version.supported_goals)):
            raise ValueError("Marketplace listing goals must be supported by workflow version")

        return listing.publish()
