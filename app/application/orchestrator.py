from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.execution_context import ExecutionContext
from app.application.retry_policy import RetryPolicy
from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowState


class Orchestrator:
    def __init__(
        self,
        dispatcher: CapabilityDispatcher,
        retry_policy: RetryPolicy,
    ) -> None:
        self._dispatcher = dispatcher
        self._retry_policy = retry_policy

    def start(self, workflow: Workflow) -> Execution:
        if workflow.state != WorkflowState.PUBLISHED:
            raise ValueError("Only published workflows can be started")

        execution = Execution.create_from_workflow(workflow)
        execution.start()

        context = ExecutionContext()

        while execution.current_step < len(workflow.steps):
            current_step = workflow.steps[execution.current_step]

            result = self._dispatcher.dispatch(
                current_step.capability,
                context,
            )

            if result.succeeded:
                context.set(current_step.id, result.output)
                execution.complete_step()
                continue

            execution.fail_current_step()

            if self._retry_policy.should_retry(
                result.error,
                execution.current_execution_step.attempt,
            ):
                execution.retry_current_step()
                continue

            execution.fail()
            break

        if execution.current_step == len(workflow.steps):
            execution.complete()

        return execution
