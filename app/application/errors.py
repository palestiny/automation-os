class NetworkTimeoutError(Exception):
    pass


class CapabilityExecutionError(ValueError):
    """Raised when a capability returns a non-success outcome."""

    def __init__(self, result: object) -> None:
        self.result = result
        error = getattr(result, "error", None)
        detail = str(error) if error is not None else "Capability execution did not succeed"
        super().__init__(f"Capability execution failed: {detail}")
