from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.connection_runtime_resolution import ResolvedConnection


class ExecutionContext:
    """Execution-scoped application state shared across workflow steps.

    Runtime-resolved connections use a private application-owned slot. Workflow
    callers can read that slot but cannot populate or replace it through the
    public input API.
    """

    _RUNTIME_CONNECTIONS_KEY = object()

    def __init__(self) -> None:
        self._data: dict[object, object] = {}

    def set(self, key: str, value: object) -> None:
        """Store caller/workflow state under an application key."""
        if not isinstance(key, str):
            raise TypeError("Execution context keys must be strings")
        self._data[key] = value

    def get(self, key: str) -> object:
        """Return caller/workflow state or raise KeyError."""
        return self._data[key]

    def _set_runtime_connections(
        self,
        connections: tuple["ResolvedConnection", ...],
    ) -> None:
        """Store protected runtime connection material for this execution."""
        self._data[self._RUNTIME_CONNECTIONS_KEY] = connections

    def get_runtime_connections(self) -> tuple["ResolvedConnection", ...]:
        """Read the protected runtime connection material."""
        return self._data.get(self._RUNTIME_CONNECTIONS_KEY, ())
