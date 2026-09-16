from typing import Protocol

from app.application.execution_context import ExecutionContext


class ConditionEvaluator(Protocol):
    def evaluate(
        self,
        condition: str,
        context: ExecutionContext,
    ) -> bool:
        """Return whether a named condition is satisfied for the context."""
        ...
