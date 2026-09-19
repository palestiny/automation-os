import pytest

from app.application.capability_dispatcher import (
    CapabilityDispatcher,
    InvalidCapabilityResultError,
)
from app.application.capability_provider_resolver import CapabilityProviderResolver
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


class FakeProvider:
    provider_id = "provider-a"
    capability_id = "video_download"

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def create(self):
        return FakeCapability(self.result, self.error)


def resolver_for(provider):
    resolver = CapabilityProviderResolver()
    resolver.register(provider, as_default=True)
    return resolver


def test_dispatcher_executes_capability_and_returns_success():
    provider = FakeProvider(CapabilityResult.success())

    result = CapabilityDispatcher(resolver_for(provider)).dispatch(
        "video_download",
        context=ExecutionContext(),
    )

    assert result.succeeded is True


def test_dispatcher_returns_capability_failure():
    provider = FakeProvider(CapabilityResult.failure("Network timeout"))

    result = CapabilityDispatcher(resolver_for(provider)).dispatch(
        "video_download",
        context=ExecutionContext(),
    )

    assert result.succeeded is False
    assert result.error == "Network timeout"


def test_dispatcher_propagates_unexpected_exception():
    error = RuntimeError("provider crashed")
    provider = FakeProvider(error=error)

    with pytest.raises(RuntimeError, match="provider crashed"):
        CapabilityDispatcher(resolver_for(provider)).dispatch(
            "video_download",
            context=ExecutionContext(),
        )


def test_dispatcher_rejects_invalid_result():
    provider = FakeProvider(result="done")

    with pytest.raises(InvalidCapabilityResultError, match="CapabilityResult"):
        CapabilityDispatcher(resolver_for(provider)).dispatch(
            "video_download",
            context=ExecutionContext(),
        )
