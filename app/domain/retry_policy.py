from dataclasses import dataclass

from app.domain.execution import Execution


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    def can_retry(self, execution: Execution) -> bool:
        return execution.attempt < self.max_attempts
