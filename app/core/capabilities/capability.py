from abc import ABC, abstractmethod

from app.application.capability_result import CapabilityResult


class Capability(ABC):

    @abstractmethod
    def execute(self, context) -> CapabilityResult:
        """
        Execute the capability using the provided execution context.

        Every capability must return a CapabilityResult describing
        whether the execution succeeded or failed.
        """
        raise NotImplementedError