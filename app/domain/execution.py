from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from app.domain.execution_step import ExecutionStep


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
    steps: list[ExecutionStep] | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    @classmethod
    def create(cls, workflow_id: UUID) -> "Execution":
        return cls(
            id=uuid4(),
            workflow_id=workflow_id,
            current_step=0,
            state=ExecutionState.CREATED,
            attempt=1,
        )

    @classmethod
    def create_from_workflow(cls, workflow) -> "Execution":
        execution = cls.create(workflow.id)
        execution.steps = [
            ExecutionStep.create(step.id)
            for step in workflow.steps
        ]
        return execution

    @property
    def current_execution_step(self) -> ExecutionStep:
        if not self.steps or self.current_step >= len(self.steps):
            raise ValueError("Execution has no current step")

        return self.steps[self.current_step]

    @property
    def current_step_id(self) -> UUID:
        return self.current_execution_step.workflow_step_id

    def start(self) -> None:
        if self.state not in (
            ExecutionState.CREATED,
            ExecutionState.RETRYING,
        ):
            raise ValueError(
                "Execution can only be started from CREATED or RETRYING state"
            )

        self.state = ExecutionState.RUNNING

        if self.started_at is None:
            self.started_at = datetime.now()

        if self.steps:
            self.current_execution_step.start()

    def complete_step(self, next_step_id: UUID | None = None) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only complete a step when in RUNNING state"
            )

        if not self.steps:
            self.current_step += 1
            return

        current_step = self.current_execution_step

        if next_step_id is None:
            if self.current_step != len(self.steps) - 1:
                raise ValueError(
                    "Next step must be provided for a non-terminal step"
                )
            current_step.complete()
            self.current_step += 1
            return

        if next_step_id == current_step.workflow_step_id:
            raise ValueError("Next step must differ from the current step")

        next_index = next(
            (
                index
                for index, step in enumerate(self.steps)
                if step.workflow_step_id == next_step_id
            ),
            None,
        )

        if next_index is None:
            raise ValueError("Next step must belong to the execution")

        current_step.complete()
        self.current_step = next_index
        self.current_execution_step.start()

    def fail_current_step(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only fail a step when in RUNNING state"
            )

        self.current_execution_step.fail()

    def retry_current_step(self) -> None:
        if self.state != ExecutionState.RUNNING:
            raise ValueError(
                "Execution can only retry a step when in RUNNING state"
            )

        self.current_execution_step.retry()
        self.current_execution_step.start()

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

        self.attempt += 1
        self.state = ExecutionState.RETRYING

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
