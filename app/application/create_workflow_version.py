from __future__ import annotations

from uuid import UUID

from app.domain.repositories import WorkflowRepository, WorkflowVersionRepository
from app.domain.workflow import WorkflowState
from app.domain.workflow_version import WorkflowVersion


class CreateWorkflowVersion:
    """Create the next draft executable version for a logical Workflow."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        version_repository: WorkflowVersionRepository,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._version_repository = version_repository

    def execute(self, workflow_id: UUID) -> WorkflowVersion:
        workflow = self._workflow_repository.get(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        if workflow.state is not WorkflowState.PUBLISHED:
            raise ValueError("Workflow must be published before a version can be created")

        latest = self._version_repository.latest_published(workflow_id)
        if latest is None:
            version = WorkflowVersion.create_from_workflow(workflow, 1)
        else:
            version = WorkflowVersion.create_from_version(
                latest,
                latest.version_number + 1,
            )

        self._version_repository.save(version)
        return version
