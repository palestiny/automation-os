from dataclasses import dataclass


@dataclass
class ExecutionStep:
    workflow_step_id: str
    attempt: int

    @classmethod
    def create(cls, workflow_step_id: str) -> "ExecutionStep":
        return cls(
            workflow_step_id=workflow_step_id,
            attempt=1,
        )