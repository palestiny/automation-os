class ExecutionContext:
    """Execution-scoped application state shared across workflow steps.

    Caller/application input cannot write to the protected runtime namespace.
    Runtime preparation owns values under that namespace.
    """

    _PROTECTED_PREFIX = "runtime."

    def __init__(self) -> None:
        self._data: dict[str, object] = {}

    def set(self, key: str, value: object) -> None:
        if key.startswith(self._PROTECTED_PREFIX):
            raise PermissionError("Protected runtime context keys are application-owned")
        self._data[key] = value

    def get(self, key: str) -> object:
        return self._data[key]

    def _set_runtime(self, key: str, value: object) -> None:
        if not key.startswith(self._PROTECTED_PREFIX):
            raise ValueError("Runtime context keys must use the protected runtime namespace")
        self._data[key] = value

    def get_runtime(self, key: str) -> object:
        if not key.startswith(self._PROTECTED_PREFIX):
            raise ValueError("Runtime context keys must use the protected runtime namespace")
        return self._data[key]
