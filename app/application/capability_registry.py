from app.application.capability import Capability


class CapabilityNotFoundError(Exception):
    pass


class InvalidCapabilityError(TypeError):
    pass


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, Capability] = {}

    def register(self, capability_id: str, capability: Capability) -> None:
        if not isinstance(capability_id, str) or not capability_id.strip():
            raise ValueError("Capability id cannot be empty")

        if not isinstance(capability, Capability):
            raise InvalidCapabilityError(
                "Registered capability must implement the Capability contract"
            )

        self._capabilities[capability_id] = capability

    def resolve(self, capability_id: str) -> Capability:
        if capability_id not in self._capabilities:
            raise CapabilityNotFoundError(
                f"Capability not found: {capability_id}"
            )

        return self._capabilities[capability_id]
