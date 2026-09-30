from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.application.runtime_connection_preparation import PreparedRuntimeConnections


_RUNTIME_CONNECTIONS_KEY = "runtime.connections"


class _RuntimeConnectionWriter:
    """Write capability owned by the runtime-connection preparation boundary."""

    def __init__(self, context: "ExecutionContext") -> None:
        self._context = context

    def set(self, connections: "PreparedRuntimeConnections") -> None:
        self._context._set_runtime_connections(connections)


class ExecutionContext:
    """Execution-scoped application state shared across workflow steps."""

    def __init__(self) -> None:
        self._data: dict[str, object] = {}
        self._runtime_connections: PreparedRuntimeConnections | None = None

    def set(self, key: str, value: object) -> None:
        """Store caller-owned execution state."""
        if key == _RUNTIME_CONNECTIONS_KEY:
            raise ValueError("runtime connection state is reserved")
        self._data[key] = value

    def get(self, key: str) -> object:
        """Return a caller-owned execution value."""
        return self._data[key]

    def _set_runtime_connections(self, connections: PreparedRuntimeConnections) -> None:
        """Internal sink used only through RuntimeConnectionWriter."""
        self._runtime_connections = connections

    def get_runtime_connections(self) -> PreparedRuntimeConnections:
        """Return trusted runtime-prepared connections."""
        if self._runtime_connections is None:
            raise KeyError(_RUNTIME_CONNECTIONS_KEY)
        value = self._runtime_connections
        if not hasattr(value, "connections"):
            raise TypeError("Invalid runtime connection state")
        return value  # type: ignore[return-value]


def _create_runtime_connection_writer(context: ExecutionContext) -> _RuntimeConnectionWriter:
    """Create the internal runtime preparation sink; not part of the execution context API."""
    return _RuntimeConnectionWriter(context)
