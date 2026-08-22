from abc import ABC, abstractmethod


class Capability(ABC):

    @abstractmethod
    def execute(self, context):
        pass