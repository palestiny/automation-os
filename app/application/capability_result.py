from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CapabilityOutcome(Enum):
    SUCCEEDED = "succeeded"
    FAILED_BEFORE_SIDE_EFFECT = "failed_before_side_effect"
    FAILED = "failed"
    UNKNOWN = "unknown"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class CapabilityResult:
    """Provider-neutral evidence about a capability attempt.

    The result intentionally carries only safe diagnostics and an optional
    external operation identity. Provider secrets and authentication state do
    not belong here.
    """

    outcome: CapabilityOutcome
    error: str | Exception | None = None
    retryable: bool = False
    operation_id: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.outcome is CapabilityOutcome.SUCCEEDED

    @classmethod
    def success(cls, operation_id: str | None = None) -> "CapabilityResult":
        return cls(
            outcome=CapabilityOutcome.SUCCEEDED,
            operation_id=operation_id,
        )

    @classmethod
    def failed_before_side_effect(
        cls,
        error: str | Exception,
        *,
        retryable: bool = True,
        operation_id: str | None = None,
    ) -> "CapabilityResult":
        return cls(
            outcome=CapabilityOutcome.FAILED_BEFORE_SIDE_EFFECT,
            error=error,
            retryable=retryable,
            operation_id=operation_id,
        )

    @classmethod
    def failure(
        cls,
        error: str | Exception,
        *,
        retryable: bool = False,
        operation_id: str | None = None,
    ) -> "CapabilityResult":
        return cls(
            outcome=CapabilityOutcome.FAILED,
            error=error,
            retryable=retryable,
            operation_id=operation_id,
        )

    @classmethod
    def unknown(
        cls,
        error: str | Exception,
        *,
        operation_id: str | None = None,
    ) -> "CapabilityResult":
        if not operation_id or not operation_id.strip():
            raise ValueError("UNKNOWN capability outcome requires operation_id")
        return cls(
            outcome=CapabilityOutcome.UNKNOWN,
            error=error,
            retryable=False,
            operation_id=operation_id,
        )

    @classmethod
    def skipped(
        cls,
        reason: str | Exception | None = None,
    ) -> "CapabilityResult":
        return cls(
            outcome=CapabilityOutcome.SKIPPED,
            error=reason,
        )

    def __post_init__(self) -> None:
        if self.operation_id is not None and not self.operation_id.strip():
            raise ValueError("operation_id cannot be empty")
        if self.outcome is CapabilityOutcome.UNKNOWN and not self.operation_id:
            raise ValueError("UNKNOWN capability outcome requires operation_id")
