from __future__ import annotations

from typing import Any


class ExecutionContext:
    def __init__(
        self,
        *,
        inputs: dict[str, Any] | None = None,
    ) -> None:
        self._inputs = dict(inputs or {})
        self._working: dict[str, Any] = {}
        self._outputs: dict[str, Any] = {}

    @classmethod
    def create(
        cls,
        *,
        inputs: dict[str, Any] | None = None,
    ) -> "ExecutionContext":
        return cls(inputs=inputs)

    def get_input(self, key: str) -> Any:
        return self._inputs[key]

    def set_working(self, key: str, value: Any) -> None:
        self._working[key] = value

    def get_working(self, key: str) -> Any:
        return self._working[key]

    def set_output(self, key: str, value: Any) -> None:
        self._outputs[key] = value

    def get_output(self, key: str) -> Any:
        return self._outputs[key]
