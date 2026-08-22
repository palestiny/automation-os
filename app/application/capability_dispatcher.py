from app.application.capability_registry import CapabilityRegistry


class CapabilityDispatcher:

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def dispatch(self, capability_id: str, context):
        capability = self._registry.resolve(capability_id)

        return capability.execute(context)