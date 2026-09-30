from __future__ import annotations

from app.application.runtime_connection_preparation import PreparedRuntimeConnections


_RUNTIME_CONNECTIONS_KEY = "runtime.connections"


class ExecutionContext:
    """Execution-scoped application state shared across workflow steps."""

    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        """Store caller-owned execution state."""
        if key == _RUNTIME_CONNECTIONS_KEY:
            raise ValueError("runtime connection state is reserved")
        self._data[key] = value

    def get(self, key: str) -> object:
        """Return a caller-owned execution value."""
        return self._data[key]

    def set_runtime_connections(self, connections: PreparedRuntimeConnections) -> None:
        """Set trusted runtime-prepared connections."""
        self._data[_RUNTIME_CONNECTIONS_KEY] = connections

    def get_runtime_connections(self) -> PreparedRuntimeConnections:
        """Return trusted runtime-prepared connections."""
        value = self._data[_RUNTIME_CONNECTIONS_KEY]
        if not isinstance(value, PreparedRuntimeConnections):
            raise TypeError("Invalid runtime connection state")
        return value
