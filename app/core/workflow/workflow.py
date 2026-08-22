from dataclasses import dataclass, field

from .workflow_step import WorkflowStep


@dataclass
class Workflow:
    name: str
    steps: list[WorkflowStep] = field(default_factory=list)

    def add_step(self, step: WorkflowStep):
        self.steps.append(step)