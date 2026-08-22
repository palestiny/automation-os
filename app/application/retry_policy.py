DEFAULT_MAX_ATTEMPTS = 3
FIRST_ATTEMPT = 1

from app.application.errors import NetworkTimeoutError

class RetryPolicy:

    def __init__(
        self,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        if max_attempts < FIRST_ATTEMPT:
            raise ValueError(
                "max_attempts must be at least one"
            )

        self.max_attempts = max_attempts

    def should_retry(
        self,
        error: Exception,
        attempt: int = FIRST_ATTEMPT,
    ) -> bool:
        if not isinstance(error, NetworkTimeoutError):
            return False

        return attempt < self.max_attempts