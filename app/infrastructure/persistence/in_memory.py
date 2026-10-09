from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from uuid import UUID

from app.domain.connection import Connection
from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.domain.marketplace import MarketplaceListing
from app.domain.repositories import (
    ConnectionRepository,
    ExecutionHistoryRepository,
    ExecutionIdempotencyRecord,
    ExecutionIdempotencyRepository,
    ExecutionRepository,
    ExecutionStartRepository,
    MarketplaceListingRepository,
    ReviewDecisionRepository,
    WorkflowRepository,
    WorkflowVersionRepository,
)
from app.domain.review_decision import ReviewDecision
from app.domain.workflow import Workflow
from app.domain.workflow_version import WorkflowVersion


class InMemoryConnectionRepository(ConnectionRepository):
    """In-memory adapter for tenant-owned provider connections."""

    def __init__(self, tenant_id: UUID | None = None) -> None:
        self._items: dict[UUID, Connection] = {}
        self._tenant_id = tenant_id
        self._lock = Lock()

    def save(self, connection: Connection) -> None:
        if connection.tenant_id != self._tenant_id:
            raise ValueError("Connection belongs to a different tenant")
        with self._lock:
            existing = next(
                (
                    item for item in self._items.values()
                    if item.reference == connection.reference
                    and item.provider_id == connection.provider_id
                    and item.tenant_id == self._tenant_id
                    and item.id != connection.id
                ),
                None,
            )
            if existing is not None:
                raise ValueError("Connection reference already exists for provider")
            self._items[connection.id] = connection

    def get(self, connection_id: UUID) -> Connection | None:
        with self._lock:
            item = self._items.get(connection_id)
            return item if item is not None and item.tenant_id == self._tenant_id else None

    def get_by_reference(self, reference: str, provider_id: str) -> Connection | None:
        with self._lock:
            return next(
                (
                    item for item in self._items.values()
                    if item.tenant_id == self._tenant_id
                    and item.reference == reference.strip()
                    and item.provider_id == provider_id.strip()
                ),
                None,
            )

    def all(self) -> tuple[Connection, ...]:
        with self._lock:
            return tuple(sorted(
                (item for item in self._items.values() if item.tenant_id == self._tenant_id),
                key=lambda item: item.id,
            ))


class InMemoryMarketplaceListingRepository(MarketplaceListingRepository):
    """In-memory adapter for tenant-owned marketplace listings."""

    def __init__(self, tenant_id: UUID | None = None) -> None:
        self._items: dict[UUID, MarketplaceListing] = {}
        self._tenant_id = tenant_id
        self._lock = Lock()

    def save(self, listing: MarketplaceListing) -> None:
        if listing.tenant_id != self._tenant_id:
            raise ValueError("Marketplace listing belongs to a different tenant")
        with self._lock:
            self._items[listing.id] = listing

    def get(self, listing_id: UUID) -> MarketplaceListing | None:
        with self._lock:
            listing = self._items.get(listing_id)
            return listing if listing is not None and listing.tenant_id == self._tenant_id else None

    def all(self) -> tuple[MarketplaceListing, ...]:
        with self._lock:
            return tuple(
                sorted((item for item in self._items.values() if item.tenant_id == self._tenant_id), key=lambda item: item.id)
            )


class InMemoryWorkflowRepository(WorkflowRepository):
    """In-memory adapter for tenant-scoped Workflow persistence."""

    def __init__(self, tenant_id: UUID | None = None) -> None:
        self._items: dict[UUID, Workflow] = {}
        self._tenant_id = tenant_id

    def save(self, workflow: Workflow) -> None:
        if workflow.tenant_id != self._tenant_id:
            raise ValueError("Workflow belongs to a different tenant")
        self._items[workflow.id] = workflow

    def get(self, workflow_id: UUID) -> Workflow | None:
        workflow = self._items.get(workflow_id)
        if workflow is None or workflow.tenant_id != self._tenant_id:
            return None
        return workflow

    def all(self) -> tuple[Workflow, ...]:
        return tuple(
            workflow
            for workflow in self._items.values()
            if workflow.tenant_id == self._tenant_id
        )


class InMemoryWorkflowVersionRepository(WorkflowVersionRepository):
    """In-memory adapter for WorkflowVersion persistence."""

    def __init__(self, tenant_id: UUID | None = None) -> None:
        self._items: dict[UUID, WorkflowVersion] = {}
        self._tenant_id = tenant_id
        self._lock = Lock()

    def save(self, version: WorkflowVersion) -> None:
        if version.tenant_id != self._tenant_id:
            raise ValueError("Workflow version belongs to a different tenant")
        with self._lock:
            self._items[version.id] = version

    def get(self, version_id: UUID) -> WorkflowVersion | None:
        with self._lock:
            version = self._items.get(version_id)
            return version if version is not None and version.tenant_id == self._tenant_id else None

    def save_if_absent(self, version: WorkflowVersion) -> WorkflowVersion:
        if version.tenant_id != self._tenant_id:
            raise ValueError("Workflow version belongs to a different tenant")
        with self._lock:
            existing = next(
                (
                    item
                    for item in self._items.values()
                    if item.workflow_id == version.workflow_id
                    and item.version_number == version.version_number
                    and item.tenant_id == self._tenant_id
                ),
                None,
            )
            if existing is not None:
                return existing
            self._items[version.id] = version
            return version

    def latest_published(self, workflow_id: UUID) -> WorkflowVersion | None:
        with self._lock:
            versions = [
                version
                for version in self._items.values()
                if version.workflow_id == workflow_id
                and version.tenant_id == self._tenant_id
                and version.state.value == "published"
            ]
            return max(versions, key=lambda version: version.version_number, default=None)

    def all(self) -> tuple[WorkflowVersion, ...]:
        with self._lock:
            return tuple(version for version in self._items.values() if version.tenant_id == self._tenant_id)


class InMemoryReviewDecisionRepository(ReviewDecisionRepository):
    """In-memory adapter for immutable workflow review decisions."""

    def __init__(self, tenant_id: UUID | None = None) -> None:
        self._items: dict[UUID, ReviewDecision] = {}
        self._tenant_id = tenant_id
        self._lock = Lock()

    def get_by_idempotency_key(self, key: str) -> ReviewDecision | None:
        with self._lock:
            return next(
                (item for item in self._items.values()
                 if item.idempotency_key == key and item.tenant_id == self._tenant_id),
                None,
            )

    def list_by_workflow(self, workflow_id: UUID) -> tuple[ReviewDecision, ...]:
        if not isinstance(workflow_id, UUID):
            raise TypeError("workflow_id must be a UUID")
        with self._lock:
            return tuple(
                sorted(
                    (
                        item
                        for item in self._items.values()
                        if item.workflow_id == workflow_id
                        and item.tenant_id == self._tenant_id
                    ),
                    key=lambda item: (item.created_at, item.id),
                )
            )

    def save_idempotent(self, decision: ReviewDecision) -> tuple[ReviewDecision, bool]:
        if decision.tenant_id != self._tenant_id:
            raise ValueError("Review decision belongs to a different tenant")
        with self._lock:
            existing = next(
                (item for item in self._items.values()
                 if item.idempotency_key == decision.idempotency_key and item.tenant_id == self._tenant_id),
                None,
            )
            if existing is not None:
                return existing, False
            self._items[decision.id] = decision
            return decision, True


class InMemoryExecutionRepository(ExecutionRepository):
    """In-memory adapter for Execution persistence."""

    def __init__(self) -> None:
        self._items: dict[UUID, Execution] = {}
        self._lock = Lock()

    def save(self, execution: Execution) -> None:
        with self._lock:
            self._items[execution.id] = execution

    def save_if_state(
        self,
        execution: Execution,
        expected_state: ExecutionState,
    ) -> bool:
        with self._lock:
            current = self._items.get(execution.id)
            if current is None or current.state is not expected_state:
                return False
            self._items[execution.id] = execution
            return True

    def save_many_if_state(
        self,
        executions: tuple[Execution, ...],
        expected_state: ExecutionState,
    ) -> tuple[UUID, ...]:
        saved: list[UUID] = []
        with self._lock:
            for execution in executions:
                current = self._items.get(execution.id)
                if current is None or current.state is not expected_state:
                    continue
                self._items[execution.id] = execution
                saved.append(execution.id)
        return tuple(saved)

    def get(self, execution_id: UUID) -> Execution | None:
        with self._lock:
            return self._items.get(execution_id)

    def all(self) -> tuple[Execution, ...]:
        with self._lock:
            return tuple(self._items.values())

    def all_metadata(self) -> tuple[Execution, ...]:
        """Return execution aggregates without requiring history reconstruction."""
        return self.all()

    def list_started_between(
        self,
        window_start: datetime,
        window_end: datetime,
    ) -> tuple[Execution, ...]:
        """Return only executions whose start time falls in the half-open window."""
        with self._lock:
            return tuple(sorted(
                (
                    execution
                    for execution in self._items.values()
                    if execution.started_at is not None
                    and window_start <= execution.started_at < window_end
                ),
                key=lambda execution: str(execution.id),
            ))

    def list_running_started_before(self, cutoff: datetime) -> tuple[Execution, ...]:
        """Return only RUNNING executions old enough to be recovery candidates."""
        with self._lock:
            return tuple(sorted(
                (
                    execution
                    for execution in self._items.values()
                    if execution.state is ExecutionState.RUNNING
                    and execution.started_at is not None
                    and execution.started_at <= cutoff
                ),
                key=lambda execution: str(execution.id),
            ))


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
                created_at=datetime.now(timezone.utc),
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
        self._lock = Lock()

    def append(self, event: ExecutionEvent) -> None:
        with self._lock:
            self._append_unlocked(event)

    def _append_unlocked(self, event: ExecutionEvent) -> None:
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
        with self._lock:
            execution_events = self._items.get(execution_id, {})
        return tuple(
            execution_events[sequence]
            for sequence in sorted(execution_events)
        )

    def list_many(
        self,
        execution_ids: tuple[UUID, ...],
    ) -> dict[UUID, tuple[ExecutionEvent, ...]]:
        with self._lock:
            return {
                execution_id: tuple(
                    events[sequence]
                    for sequence in sorted(events)
                )
                for execution_id in execution_ids
                for events in (self._items.get(execution_id, {}),)
            }

class EventRecordingExecutionRepository(ExecutionRepository):
    """Execution repository decorator that persists domain lifecycle evidence."""

    def __init__(self, execution_repository: ExecutionRepository, history_repository: ExecutionHistoryRepository) -> None:
        self._execution_repository = execution_repository
        self._history_repository = history_repository

    def save(self, execution: Execution) -> None:
        self._execution_repository.save(execution)
        for event in execution.events:
            self._history_repository.append(event)

    def save_if_state(self, execution: Execution, expected_state: ExecutionState) -> bool:
        saved = self._execution_repository.save_if_state(execution, expected_state)
        if saved:
            for event in execution.events:
                self._history_repository.append(event)
        return saved

    def save_many_if_state(
        self,
        executions: tuple[Execution, ...],
        expected_state: ExecutionState,
    ) -> tuple[UUID, ...]:
        batch_save = getattr(self._execution_repository, "save_many_if_state", None)
        if callable(batch_save):
            saved_ids = batch_save(executions, expected_state)
        else:
            saved_ids = tuple(
                execution.id
                for execution in executions
                if self._execution_repository.save_if_state(execution, expected_state)
            )
        saved_set = set(saved_ids)
        for execution in executions:
            if execution.id in saved_set and execution.events:
                # Batch recovery creates one new lifecycle event per aggregate.
                # Historical events are already present in the history repository.
                self._history_repository.append(execution.events[-1])
        return tuple(execution.id for execution in executions if execution.id in saved_set)

    def get(self, execution_id: UUID) -> Execution | None:
        return self._execution_repository.get(execution_id)

    def all(self) -> tuple[Execution, ...]:
        return self._execution_repository.all()

    def all_metadata(self) -> tuple[Execution, ...]:
        list_metadata = getattr(self._execution_repository, "all_metadata", None)
        return tuple(list_metadata()) if callable(list_metadata) else self.all()

    def list_started_between(
        self,
        window_start: datetime,
        window_end: datetime,
    ) -> tuple[Execution, ...]:
        list_window = getattr(
            self._execution_repository,
            "list_started_between",
            None,
        )
        if callable(list_window):
            return tuple(list_window(window_start, window_end))
        return tuple(
            execution
            for execution in self.all()
            if execution.started_at is not None
            and window_start <= execution.started_at < window_end
        )

    def list_running_started_before(self, cutoff: datetime) -> tuple[Execution, ...]:
        list_stale = getattr(
            self._execution_repository,
            "list_running_started_before",
            None,
        )
        if callable(list_stale):
            return tuple(list_stale(cutoff))
        return tuple(
            execution
            for execution in self.all()
            if execution.state is ExecutionState.RUNNING
            and execution.started_at is not None
            and execution.started_at <= cutoff
        )

