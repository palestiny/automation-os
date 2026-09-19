from app.application.capability import Capability
from app.application.capability_provider_resolver import CapabilityProviderResolver
from app.application.capability_result import CapabilityResult
from app.application.execution_context import ExecutionContext


class InvalidCapabilityResultError(TypeError):
    pass


class CapabilityDispatcher:
    """Resolve a configured provider and invoke its capability implementation."""

    def __init__(self, provider_resolver: CapabilityProviderResolver) -> None:
        self._provider_resolver = provider_resolver

    def dispatch(
        self,
        capability_id: str,
        context: ExecutionContext,
    ) -> CapabilityResult:
        provider = self._provider_resolver.resolve(capability_id)
        capability: Capability = provider.create()
        result = capability.execute(context)

        if not isinstance(result, CapabilityResult):
            raise InvalidCapabilityResultError(
                "Capability execution must return a CapabilityResult"
            )

        return result
