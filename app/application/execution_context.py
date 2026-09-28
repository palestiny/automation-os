class ExecutionContext:
    """Execution-scoped application state shared across workflow steps."""

    _RUNTIME_KEYS = frozenset({"runtime.connections"})

    def __init__(self) -> None:
        self._data: dict[str, object] = {}
        self._runtime_data: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        """Store caller-owned execution state; runtime-owned keys are protected."""
        if key in self._RUNTIME_KEYS:
            raise ValueError(f"Runtime-owned context key cannot be set directly: {key}")
        self._data[key] = value

    def set_runtime(self, key: str, value: object) -> None:
        """Store application-prepared runtime state."""
        if key not in self._RUNTIME_KEYS:
            raise ValueError(f"Unknown runtime-owned context key: {key}")
        self._runtime_data[key] = value

    def contains_runtime(self, key: str) -> bool:
        return key in self._runtime_data

    def get(self, key: str) -> object:
        """Return caller-owned or runtime-prepared execution state."""
        if key in self._RUNTIME_KEYS:
            return self._runtime_data[key]
        return self._data[key]
