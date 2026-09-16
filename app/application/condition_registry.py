from collections.abc import Callable

from app.application.execution_context import ExecutionContext


Condition = Callable[[ExecutionContext], bool]


class ConditionRegistry:
    def __init__(self) -> None:
        self._conditions: dict[str, Condition] = {}

    def register(self, name: str, condition: Condition) -> None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Condition name cannot be blank")
        if normalized_name in self._conditions:
            raise ValueError("Condition is already registered")
        self._conditions[normalized_name] = condition

    def evaluate(self, name: str, context: ExecutionContext) -> bool:
        normalized_name = name.strip()
        condition = self._conditions.get(normalized_name)
        if condition is None:
            raise ValueError("Condition is not registered")
        return condition(context)
