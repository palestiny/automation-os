from app.core.capabilities.capability import Capability


class FakeCapability(Capability):

    def execute(self, context):
        return "done"


def test_capability_can_execute():
    capability = FakeCapability()

    result = capability.execute(object())

    assert result == "done"
    