from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.retry_policy import RetryPolicy
from app.domain.execution import Execution
from app.domain.workflow import Workflow, WorkflowState


class Orchestrator:
    def __init__(
        self,
        dispatcher: CapabilityDispatcher,
        retry_policy: RetryPolicy,
        condition_evaluator: ConditionEvaluator | None = None,
    ) -> None:
        self._dispatcher = dispatcher
        self._retry_policy = retry_policy
        self._condition_evaluator = condition_evaluator

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

                next_step_id = self._next_step_id(
                    workflow,
                    current_step.id,
                    context,
                )
                execution.complete_step(next_step_id=next_step_id)
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

    def _next_step_id(
        self,
        workflow: Workflow,
        current_step_id,
        context: ExecutionContext,
    ):
        transitions = workflow.outgoing_transitions(current_step_id)

        if not transitions:
            return None

        eligible = []

        for transition in transitions:
            if transition.condition is None:
                eligible.append(transition)
                continue

            if self._condition_evaluator is None:
                raise ValueError(
                    "Conditional transitions require a condition evaluator"
                )

            if self._condition_evaluator.evaluate(
                transition.condition,
                context,
            ):
                eligible.append(transition)

        if not eligible:
            raise ValueError(
                "No outgoing transition is eligible"
            )

        if len(eligible) > 1:
            raise ValueError(
                "Multiple outgoing transitions are eligible"
            )

        return eligible[0].target_step_id
