class ExecutionContext:
    def __init__(self) -> None:
        self._data = {}

    def set(self, key, value) -> None:
        self._data[key] = value

    def get(self, key, default=None):
        return self._data.get(key, default)
