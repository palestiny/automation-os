from __future__ import annotations

from uuid import UUID

from app.domain.execution import Execution
from app.domain.repositories import (
    ExecutionIdempotencyRepository,
    ExecutionStartRepository,
    ExecutionRepository,
    WorkflowRepository,
    WorkflowVersionRepository,
)
from app.domain.workflow import WorkflowState
from app.domain.workflow_version import WorkflowVersion


class StartWorkflowExecution:
    """Application use case for starting a persisted published Workflow."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        execution_repository: ExecutionRepository,
        idempotency_repository: ExecutionIdempotencyRepository | None = None,
        execution_start_repository: ExecutionStartRepository | None = None,
        workflow_version_repository: WorkflowVersionRepository | None = None,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._execution_repository = execution_repository
        self._idempotency_repository = idempotency_repository
        self._execution_start_repository = execution_start_repository
        self._workflow_version_repository = workflow_version_repository

    def execute(
        self,
        workflow_id: UUID,
        idempotency_key: str | None = None,
        workflow_version_id: UUID | None = None,
    ) -> Execution:
        normalized_key = self._normalize_idempotency_key(idempotency_key)

        if normalized_key is not None and self._idempotency_repository is None:
            raise RuntimeError(
                "Idempotency is unavailable because no idempotency repository is configured"
            )

        if normalized_key is not None:
            if self._execution_start_repository is None:
                raise RuntimeError(
                    "Atomic execution-start persistence is required for idempotent starts"
                )
            existing_execution = self._execution_start_repository.get_idempotent(
                normalized_key,
                workflow_id,
            )
            if existing_execution is not None:
                return existing_execution

        workflow = self._workflow_repository.get(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError("Only published workflows can be started")

        version = self._resolve_version(workflow, workflow_version_id)
        execution = Execution.create(
            workflow.id,
            workflow_version_id=version.id if version is not None else None,
        )

        execution.start()

        if normalized_key is not None:
            if self._execution_start_repository is None:
                raise RuntimeError(
                    "Atomic execution-start persistence is required for idempotent starts"
                )

            record, created = self._execution_start_repository.save_idempotent(
                execution,
                normalized_key,
            )
            if not created:
                if record.workflow_id != workflow_id:
                    raise ValueError(
                        "Idempotency key is already associated with a different workflow"
                    )
                existing_execution = self._execution_repository.get(
                    record.execution_id
                )
                if existing_execution is None:
                    raise RuntimeError(
                        "Idempotency record references a missing execution"
                    )
                return existing_execution
            return execution

        self._execution_repository.save(execution)
        return execution

    def _resolve_version(
        self,
        workflow: Workflow,
        workflow_version_id: UUID | None,
    ) -> WorkflowVersion | None:
        repository = self._workflow_version_repository
        if repository is None:
            if workflow_version_id is not None:
                raise RuntimeError("Workflow version persistence is not configured")
            return None

        if workflow_version_id is not None:
            version = repository.get(workflow_version_id)
            if version is None:
                raise ValueError(f"Workflow version not found: {workflow_version_id}")
            if version.workflow_id != workflow.id:
                raise ValueError("Workflow version belongs to a different workflow")
            if version.state != WorkflowState.PUBLISHED:
                raise ValueError("Only published workflow versions can be started")
            return version

        version = repository.latest_published(workflow.id)
        if version is not None:
            return version

        version = WorkflowVersion.create_from_workflow(workflow, 1)
        version.publish()
        repository.save(version)
        return version
    @staticmethod
    def _normalize_idempotency_key(key: str | None) -> str | None:
        if key is None:
            return None

        normalized = key.strip()
        if not normalized:
            raise ValueError("Idempotency key cannot be empty")

        return normalized
