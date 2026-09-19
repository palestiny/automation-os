from __future__ import annotations

from uuid import UUID

from app.domain.execution import Execution
from app.domain.repositories import (
    ExecutionIdempotencyRepository,
    ExecutionStartRepository,
    ExecutionRepository,
    WorkflowRepository,
)
from app.domain.workflow import WorkflowState


class StartWorkflowExecution:
    """Application use case for starting a persisted published Workflow."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        execution_repository: ExecutionRepository,
        idempotency_repository: ExecutionIdempotencyRepository | None = None,
        execution_start_repository: ExecutionStartRepository | None = None,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._execution_repository = execution_repository
        self._idempotency_repository = idempotency_repository
        self._execution_start_repository = execution_start_repository

    def execute(
        self,
        workflow_id: UUID,
        idempotency_key: str | None = None,
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

        execution = Execution.create(workflow.id)

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

    @staticmethod
    def _normalize_idempotency_key(key: str | None) -> str | None:
        if key is None:
            return None

        normalized = key.strip()
        if not normalized:
            raise ValueError("Idempotency key cannot be empty")

        return normalized
