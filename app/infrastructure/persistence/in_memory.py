from __future__ import annotations

from datetime import datetime
from threading import Lock
from uuid import UUID

from app.domain.execution import Execution
from app.domain.execution_event import ExecutionEvent
from app.domain.repositories import (
    ExecutionHistoryRepository,
    ExecutionIdempotencyRecord,
    ExecutionIdempotencyRepository,
    ExecutionStartRepository,
    ExecutionRepository,
    WorkflowRepository,
)
from app.domain.workflow import Workflow


class InMemoryWorkflowRepository(WorkflowRepository):
    """In-memory adapter for Workflow persistence."""

    def __init__(self) -> None:
        self._items: dict[UUID, Workflow] = {}

    def save(self, workflow: Workflow) -> None:
        self._items[workflow.id] = workflow

    def get(self, workflow_id: UUID) -> Workflow | None:
        return self._items.get(workflow_id)

    def all(self) -> tuple[Workflow, ...]:
        return tuple(self._items.values())


class InMemoryExecutionRepository(ExecutionRepository):
    """In-memory adapter for Execution persistence."""

    def __init__(self) -> None:
        self._items: dict[UUID, Execution] = {}

    def save(self, execution: Execution) -> None:
        self._items[execution.id] = execution

    def get(self, execution_id: UUID) -> Execution | None:
        return self._items.get(execution_id)

    def all(self) -> tuple[Execution, ...]:
        return tuple(self._items.values())


class InMemoryExecutionIdempotencyRepository(ExecutionIdempotencyRepository):
    """In-memory adapter for workflow-start idempotency."""

    def __init__(self) -> None:
        self._items: dict[str, ExecutionIdempotencyRecord] = {}
        self._lock = Lock()

    def get(self, key: str) -> ExecutionIdempotencyRecord | None:
        with self._lock:
            return self._items.get(key)

    def reserve(
        self,
        key: str,
        workflow_id: UUID,
        execution_id: UUID,
    ) -> tuple[ExecutionIdempotencyRecord, bool]:
        with self._lock:
            existing = self._items.get(key)
            if existing is not None:
                return existing, False

            record = ExecutionIdempotencyRecord(
                key=key,
                workflow_id=workflow_id,
                execution_id=execution_id,
                created_at=datetime.now(),
            )
            self._items[key] = record
            return record, True

    def release(self, key: str, execution_id: UUID) -> None:
        with self._lock:
            existing = self._items.get(key)
            if existing is not None and existing.execution_id == execution_id:
                del self._items[key]


class InMemoryExecutionStartRepository(ExecutionStartRepository):
    """Atomic in-memory boundary for idempotency registration plus execution save."""

    def __init__(self, execution_repository: ExecutionRepository, idempotency_repository: ExecutionIdempotencyRepository) -> None:
        self._execution_repository = execution_repository
        self._idempotency_repository = idempotency_repository
        self._lock = Lock()

    def get_idempotent(self, key: str, workflow_id: UUID) -> Execution | None:
        with self._lock:
            existing = self._idempotency_repository.get(key)
            if existing is None:
                return None
            if existing.workflow_id != workflow_id:
                raise ValueError(
                    "Idempotency key is already associated with a different workflow"
                )
            execution = self._execution_repository.get(existing.execution_id)
            if execution is None:
                raise RuntimeError(
                    "Idempotency record references a missing execution"
                )
            return execution

    def save_idempotent(
        self,
        execution: Execution,
        key: str,
    ) -> tuple[ExecutionIdempotencyRecord, bool]:
        with self._lock:
            existing = self._idempotency_repository.get(key)
            if existing is not None:
                return existing, False

            record, created = self._idempotency_repository.reserve(
                key,
                execution.workflow_id,
                execution.id,
            )
            if not created:
                return record, False

            try:
                self._execution_repository.save(execution)
            except Exception:
                if self._execution_repository.get(execution.id) is None:
                    self._idempotency_repository.release(key, execution.id)
                raise

            return record, True


class InMemoryExecutionHistoryRepository(ExecutionHistoryRepository):
    """In-memory append-only adapter for execution lifecycle evidence."""

    def __init__(self) -> None:
        self._items: dict[UUID, dict[int, ExecutionEvent]] = {}

    def append(self, event: ExecutionEvent) -> None:
        execution_events = self._items.setdefault(event.execution_id, {})
        existing = execution_events.get(event.sequence)
        if existing is not None:
            if existing != event:
                raise ValueError(
                    "Execution history sequence already contains a different event"
                )
            return

        latest_sequence = max(execution_events, default=0)
        if event.sequence != latest_sequence + 1:
            raise ValueError(
                "Execution history sequence must be appended in order"
            )

        execution_events[event.sequence] = event

    def list(self, execution_id: UUID) -> tuple[ExecutionEvent, ...]:
        execution_events = self._items.get(execution_id, {})
        return tuple(
            execution_events[sequence]
            for sequence in sorted(execution_events)
        )


class EventRecordingExecutionRepository(ExecutionRepository):
    """Execution repository decorator that persists domain lifecycle evidence."""

    def __init__(
        self,
        execution_repository: ExecutionRepository,
        history_repository: ExecutionHistoryRepository,
    ) -> None:
        self._execution_repository = execution_repository
        self._history_repository = history_repository

    def save(self, execution: Execution) -> None:
        self._execution_repository.save(execution)
        for event in execution.events:
            self._history_repository.append(event)

    def get(self, execution_id: UUID) -> Execution | None:
        return self._execution_repository.get(execution_id)

    def all(self) -> tuple[Execution, ...]:
        return self._execution_repository.all()
