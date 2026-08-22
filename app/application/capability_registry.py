class CapabilityNotFoundError(Exception):
    pass


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities = {}

    def register(self, capability_id: str, capability) -> None:
        self._capabilities[capability_id] = capability

    def resolve(self, capability_id: str):
        if capability_id not in self._capabilities:
            raise CapabilityNotFoundError(
                f"Capability not found: {capability_id}"
            )

        return self._capabilities[capability_id]