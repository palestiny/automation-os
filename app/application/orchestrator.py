from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.execution_context import ExecutionContext
from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowState


class Orchestrator:

    def __init__(self, dispatcher: CapabilityDispatcher) -> None:
        self._dispatcher = dispatcher

    def start(self, workflow: Workflow) -> Execution:
        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError(
                "Only published workflows can be started"
            )

        execution = Execution.create(workflow.id)
        execution.start()

        current_step = workflow.steps[execution.current_step]

        context = ExecutionContext()

        result = self._dispatcher.dispatch(
            current_step.capability,
            context,
        )

        if result.succeeded:
            execution.complete_step()

        return execution