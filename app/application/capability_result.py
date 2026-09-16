class CapabilityResult:
    def __init__(
        self,
        succeeded: bool,
        error: Exception | str | None = None,
        output=None,
    ) -> None:
        self.succeeded = succeeded
        self.error = error
        self.output = output

    @classmethod
    def success(cls, output=None) -> "CapabilityResult":
        return cls(succeeded=True, output=output)

    @classmethod
    def failure(cls, error: Exception | str) -> "CapabilityResult":
        return cls(
            succeeded=False,
            error=error,
        )