from app.application.capability import Capability
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext


class CapabilityDispatcher:
    """Resolve and invoke a registered capability."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def dispatch(
        self,
        capability_id: str,
        context: ExecutionContext,
    ) -> CapabilityResult:
        capability: Capability = self._registry.resolve(capability_id)
        return capability.execute(context)
