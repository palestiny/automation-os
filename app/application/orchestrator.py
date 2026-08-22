from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowState


class Orchestrator:

    def start(self, workflow: Workflow) -> Execution:
        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError(
                "Only published workflows can be started"
            )

        execution = Execution.create(workflow.id)
        execution.start()

        return execution