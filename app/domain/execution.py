
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ExecutionState(Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Execution:
    id: UUID
    workflow_id: UUID
    current_step: int
    state: ExecutionState
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @classmethod
    def create(cls, workflow_id: UUID) -> "Execution":
        return cls(
            id=uuid4(),
            workflow_id=workflow_id,
            current_step=0,
            state=ExecutionState.CREATED,
        )

    def start(self) -> None:
        if self.state != ExecutionState.CREATED:
            raise ValueError(
                "Execution can only be started from CREATED state"
            )

        self.state = ExecutionState.RUNNING
        self.started_at = datetime.now()

    def complete_step(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only complete a step when in RUNNING state"
            )

        self.current_step += 1

    def wait(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only wait when in RUNNING state"
            )

        self.state = ExecutionState.WAITING

    def resume(self) -> None:
        if self.state != ExecutionState.WAITING:
            raise ValueError(
                "Execution can only resume when in WAITING state"
            )

        self.state = ExecutionState.RUNNING

    def complete(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only be completed when in RUNNING state"
            )

        self.state = ExecutionState.COMPLETED
        self.finished_at = datetime.now()

    def fail(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only fail when in RUNNING state"
            )

        self.state = ExecutionState.FAILED

    def retry(self) -> None:
        if self.state != ExecutionState.FAILED:
            raise ValueError(
                "Execution can only retry when in FAILED state"
            )

        self.state = ExecutionState.RUNNING

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