from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.execution_event import ExecutionEvent


class ExecutionState(Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Execution:
    id: UUID
    workflow_id: UUID
    current_step: int
    state: ExecutionState
    attempt: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    _events: list[ExecutionEvent] = field(default_factory=list, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.current_step < 0:
            raise ValueError("Execution current_step cannot be negative")

        if self.attempt < 1:
            raise ValueError("Execution attempt must be at least 1")

    @classmethod
    def create(cls, workflow_id: UUID, execution_id: UUID | None = None) -> "Execution":
        return cls(
            id=execution_id or uuid4(),
            workflow_id=workflow_id,
            current_step=0,
            state=ExecutionState.CREATED,
            attempt=1,
        )

    @property
    def events(self) -> tuple[ExecutionEvent, ...]:
        return tuple(self._events)

    def _record_event(self, event_type: str) -> None:
        self._events.append(
            ExecutionEvent(
                execution_id=self.id,
                workflow_id=self.workflow_id,
                sequence=len(self._events) + 1,
                event_type=event_type,
                state=self.state,
                attempt=self.attempt,
                occurred_at=datetime.now(),
            )
        )

    def start(self) -> None:
        if self.state not in (
            ExecutionState.CREATED,
            ExecutionState.RETRYING,
        ):
            raise ValueError(
                "Execution can only be started from CREATED or RETRYING state"
            )

        self.state = ExecutionState.RUNNING
        self.started_at = datetime.now()
        self._record_event(
            "execution.started"
            if self.attempt == 1
            else "execution.retry_started"
        )

    def complete_step(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only complete a step when in RUNNING state"
            )

        self.current_step += 1
        self._record_event("execution.step_completed")

    def wait(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only wait when in RUNNING state"
            )

        self.state = ExecutionState.WAITING
        self._record_event("execution.waiting")

    def resume(self) -> None:
        if self.state != ExecutionState.WAITING:
            raise ValueError(
                "Execution can only resume when in WAITING state"
            )

        self.state = ExecutionState.RUNNING
        self._record_event("execution.resumed")

    def complete(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only be completed when in RUNNING state"
            )

        self.state = ExecutionState.COMPLETED
        self.finished_at = datetime.now()
        self._record_event("execution.completed")

    def fail(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only fail when in RUNNING state"
            )

        self.state = ExecutionState.FAILED
        self._record_event("execution.failed")

    def recover_stale(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only recover when in RUNNING state"
            )

        self.state = ExecutionState.FAILED
        self._record_event("execution.recovered_stale")

    def retry(self) -> None:
        if self.state != ExecutionState.FAILED:
            raise ValueError(
                "Execution can only retry when in FAILED state"
            )

        self.attempt += 1
        self.state = ExecutionState.RETRYING
        self._record_event("execution.retrying")

    def cancel(self) -> None:
        if self.state not in (
            ExecutionState.CREATED,
            ExecutionState.RUNNING,
            ExecutionState.WAITING,
        ):
            raise ValueError(
                "Execution can only be cancelled when in CREATED, RUNNING, or WAITING state"
            )

        self.state = ExecutionState.CANCELLED
        self.finished_at = datetime.now()
        self._record_event("execution.cancelled")
