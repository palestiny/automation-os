"""RED tests for explicit external side-effect outcome semantics."""

import pytest

from app.application.capability_result import CapabilityResult


def test_capability_result_can_represent_confirmed_success() -> None:
    result = CapabilityResult.success()

    assert result.outcome.value == "succeeded"
    assert result.retryable is False


def test_capability_result_can_represent_failure_before_side_effect() -> None:
    result = CapabilityResult.failed_before_side_effect("provider rejected request")

    assert result.outcome.value == "failed_before_side_effect"
    assert result.retryable is True


def test_capability_result_can_represent_ambiguous_external_outcome() -> None:
    result = CapabilityResult.unknown(
        "connection lost after provider accepted the request",
        operation_id="op-123",
    )

    assert result.outcome.value == "unknown"
    assert result.retryable is False
    assert result.operation_id == "op-123"


def test_unknown_requires_an_explicit_operation_idempotency_identity() -> None:
    with pytest.raises(ValueError, match="operation_id"):
        CapabilityResult.unknown("ambiguous outcome")
