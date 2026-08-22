class ExecutionContext:
    def __init__(self) -> None:
        self._data = {}

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def get(self, key: str):
        return self._data[key]