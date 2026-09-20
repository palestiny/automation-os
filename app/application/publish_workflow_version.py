from __future__ import annotations

from uuid import UUID

from app.domain.repositories import WorkflowVersionRepository
from app.domain.workflow_version import WorkflowVersion


class PublishWorkflowVersion:
    """Publish one draft WorkflowVersion without mutating prior versions."""

    def __init__(self, version_repository: WorkflowVersionRepository) -> None:
        self._version_repository = version_repository

    def execute(self, version_id: UUID) -> WorkflowVersion:
        version = self._version_repository.get(version_id)
        if version is None:
            raise ValueError(f"Workflow version not found: {version_id}")

        version.publish()
        self._version_repository.save(version)
        return version
