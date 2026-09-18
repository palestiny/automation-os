from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext


class LifecycleProbeCapability:
    def __init__(self):
        self.execute_calls = 0

    def execute(self, context):
        self.execute_calls += 1
        return CapabilityResult.success()


def test_dispatcher_invokes_existing_instance_without_reconstructing_it():
    registry = CapabilityRegistry()
    capability = LifecycleProbeCapability()
    registry.register("probe", capability)

    result = CapabilityDispatcher(registry).dispatch(
        "probe",
        ExecutionContext(),
    )

    assert result.succeeded is True
    assert capability.execute_calls == 1
