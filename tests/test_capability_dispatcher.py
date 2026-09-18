import pytest

from app.application.capability_dispatcher import (
    CapabilityDispatcher,
    InvalidCapabilityResultError,
)
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext


class FakeCapability:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def execute(self, context):
        if self.error is not None:
            raise self.error
        return self.result


def test_dispatcher_executes_capability_and_returns_success():
    registry = CapabilityRegistry()
    capability = FakeCapability(CapabilityResult.success())
    registry.register("video_download", capability)

    result = CapabilityDispatcher(registry).dispatch(
        "video_download",
        context=ExecutionContext(),
    )

    assert result.succeeded is True


def test_dispatcher_returns_capability_failure():
    registry = CapabilityRegistry()
    capability = FakeCapability(CapabilityResult.failure("Network timeout"))
    registry.register("video_download", capability)

    result = CapabilityDispatcher(registry).dispatch(
        "video_download",
        context=ExecutionContext(),
    )

    assert result.succeeded is False
    assert result.error == "Network timeout"


def test_dispatcher_propagates_unexpected_exception():
    registry = CapabilityRegistry()
    error = RuntimeError("provider crashed")
    capability = FakeCapability(error=error)
    registry.register("video_download", capability)

    with pytest.raises(RuntimeError, match="provider crashed"):
        CapabilityDispatcher(registry).dispatch(
            "video_download",
            context=ExecutionContext(),
        )


def test_dispatcher_rejects_invalid_result():
    registry = CapabilityRegistry()
    capability = FakeCapability(result="done")
    registry.register("video_download", capability)

    with pytest.raises(InvalidCapabilityResultError, match="CapabilityResult"):
        CapabilityDispatcher(registry).dispatch(
            "video_download",
            context=ExecutionContext(),
        )
