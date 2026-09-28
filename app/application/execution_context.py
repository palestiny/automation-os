class ExecutionContext:
    """Execution-scoped application state shared across workflow steps."""

    _RUNTIME_PREFIX = "runtime."

    def __init__(self) -> None:
        self._data: dict[str, object] = {}
        self._runtime_data: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        """Store caller/workflow state; protected runtime state is write-isolated."""
        if key.startswith(self._RUNTIME_PREFIX):
            raise ValueError("Protected runtime context keys cannot be set directly")
        self._data[key] = value

    def get(self, key: str) -> object:
        """Return caller/workflow state."""
        return self._data[key]

    def set_runtime(self, key: str, value: object) -> None:
        """Store application-prepared runtime state."""
        if not key.startswith(self._RUNTIME_PREFIX):
            raise ValueError("Runtime context keys must use the runtime. prefix")
        self._runtime_data[key] = value

    def get_runtime(self, key: str) -> object:
        """Return application-prepared runtime state."""
        if not key.startswith(self._RUNTIME_PREFIX):
            raise ValueError("Runtime context keys must use the runtime. prefix")
        return self._runtime_data[key]
