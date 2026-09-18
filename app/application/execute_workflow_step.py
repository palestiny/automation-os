from __future__ import annotations

from dataclasses import dataclass

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.domain.execution import Execution, ExecutionState
from app.domain.repositories import ExecutionRepository, WorkflowRepository


@dataclass(frozen=True)
class StepExecutionResult:
    processed: bool
    skipped: bool
    has_more_steps: bool


class ExecuteWorkflowStep:
    """Execute the current step of a running Workflow execution."""

    def __init__(
        self,
        workflow_repository: WorkflowRepository,
        execution_repository: ExecutionRepository,
        dispatcher: CapabilityDispatcher,
        condition_evaluator: ConditionEvaluator,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._execution_repository = execution_repository
        self._dispatcher = dispatcher
        self._condition_evaluator = condition_evaluator

    def execute(
        self,
        execution_id,
        context: ExecutionContext,
    ) -> StepExecutionResult:
        execution = self._execution_repository.get(execution_id)
        if execution is None:
            raise ValueError(f"Execution not found: {execution_id}")

        if execution.state is not ExecutionState.RUNNING:
            raise ValueError("Execution must be RUNNING to execute a step")

        workflow = self._workflow_repository.get(execution.workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow not found: {execution.workflow_id}")

        if execution.current_step >= len(workflow.steps):
            raise ValueError(
                f"Execution current step is out of range: {execution.current_step}"
            )

        step = workflow.steps[execution.current_step]

        if step.condition is not None:
            should_run = self._condition_evaluator.evaluate(
                step.condition,
                context,
            )
            if not should_run:
                execution.complete_step()
                self._execution_repository.save(execution)
                return StepExecutionResult(
                    processed=True,
                    skipped=True,
                    has_more_steps=execution.current_step < len(workflow.steps),
                )

        result = self._dispatcher.dispatch(step.capability, context)

        if hasattr(result, "succeeded") and not result.succeeded:
            raise ValueError(
                f"Capability execution failed: {result.error}"
            )

        execution.complete_step()
        self._execution_repository.save(execution)

        return StepExecutionResult(
            processed=True,
            skipped=False,
            has_more_steps=execution.current_step < len(workflow.steps),
        )
