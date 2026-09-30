from __future__ import annotations

from app.application.secret_provider import SecretResolutionError


class UnconfiguredSecretProvider:
    """Explicit fail-closed adapter until a real secret manager is configured."""

    def get_secret(self, secret_reference: str) -> object:
        raise SecretResolutionError(
            f"Protected secret provider is not configured for reference: {secret_reference}"
        )
