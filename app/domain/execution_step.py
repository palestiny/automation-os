from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4



class ExecutionStepState(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ExecutionStep:
    id: UUID
    workflow_step_id: UUID
    attempt: int
    state: ExecutionStepState

    @classmethod
    def create(cls, workflow_step_id: UUID) -> "ExecutionStep":
        return cls(
            id=uuid4(),
            workflow_step_id=workflow_step_id,
            attempt=1,
            state=ExecutionStepState.CREATED,
        )
    def start(self) -> None:
        if self.state not in (
            ExecutionStepState.CREATED,
            ExecutionStepState.RETRYING,
        ):
            raise ValueError(
                "ExecutionStep can only be started from CREATED or RETRYING state"
            )

        self.state = ExecutionStepState.RUNNING

    def complete(self) -> None:
        if self.state != ExecutionStepState.RUNNING:
            raise ValueError(
                "ExecutionStep can only be completed from RUNNING state"
            )

        self.state = ExecutionStepState.COMPLETED

    def fail(self) -> None:
        if self.state != ExecutionStepState.RUNNING:
            raise ValueError(
                "ExecutionStep can only fail from RUNNING state"
            )

        self.state = ExecutionStepState.FAILED

    def retry(self) -> None:
        if self.state != ExecutionStepState.FAILED:
            raise ValueError(
                "ExecutionStep can only retry from FAILED state"
            )

        self.state = ExecutionStepState.RETRYING
        self.attempt += 1


