class CapabilityResult:
    def __init__(
        self,
        succeeded: bool,
        error: str | None = None,
    ) -> None:
        self.succeeded = succeeded
        self.error = error

    @classmethod
    def success(cls) -> "CapabilityResult":
        return cls(succeeded=True)

    @classmethod
    def failure(cls, error: Exception) -> "CapabilityResult":
        return cls(
            succeeded=False,
            error=error,
        )