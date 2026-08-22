from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry


class FakeCapability:
    def execute(self, context):
        return "done"


def test_dispatcher_executes_capability():
    registry = CapabilityRegistry()

    capability = FakeCapability()

    registry.register("video_download", capability)

    dispatcher = CapabilityDispatcher(registry)

    result = dispatcher.dispatch(
        "video_download",
        context=object(),
    )

    assert result == "done"