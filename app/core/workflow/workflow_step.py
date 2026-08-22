from dataclasses import dataclass


@dataclass
class WorkflowStep:
    name: str
    capability: str