from app.application.capability import Capability


class FakeCapability:
    def execute(self, context):
        return "done"


def test_capability_can_execute():
    capability = FakeCapability()

    result = capability.execute(object())

    assert result == "done"
    assert isinstance(capability, Capability)
