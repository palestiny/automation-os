class NetworkTimeoutError(Exception):
    pass

class CapabilityExecutionError(Exception):
    """Raised when a capability returns a non-success outcome."""

    def __init__(self, result: object) -> None:
        self.result = result
        error = getattr(result, "error", None)
        super().__init__(str(error) if error is not None else "Capability execution did not succeed")
