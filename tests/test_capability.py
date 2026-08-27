from app.core.capabilities.capability import Capability
from app.application.capability_result import CapabilityResult



class FakeCapability(Capability):

    def execute(self, context):
        return CapabilityResult.success()


def test_capability_can_execute():
    capability = FakeCapability()

    result = capability.execute(object())

    assert isinstance(result, CapabilityResult)
    assert result.succeeded is True


def test_capability_returns_capability_result():
    capability = FakeCapability()

    result = capability.execute(object())

    assert isinstance(result, CapabilityResult)