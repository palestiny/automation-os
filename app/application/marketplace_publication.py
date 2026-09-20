from __future__ import annotations

from app.domain.marketplace import MarketplaceListing
from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_version import WorkflowVersion


class PublishMarketplaceListing:
    """Validate a listing against its workflow and publish it."""

    def __init__(
        self,
        workflows: list[Workflow],
        versions: list[WorkflowVersion] | None = None,
    ) -> None:
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

        if listing.workflow_version_id is not None:
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
            return listing.publish()

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
