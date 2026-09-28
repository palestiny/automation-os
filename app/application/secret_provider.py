from __future__ import annotations

from typing import Protocol, runtime_checkable


class SecretResolutionError(RuntimeError):
    """Raised when protected secret material cannot be resolved."""


@runtime_checkable
class SecretProvider(Protocol):
    """Protected runtime boundary for resolving secret material by reference."""

    def get_secret(self, secret_reference: str) -> object:
        ...
