from __future__ import annotations

from dataclasses import dataclass

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.domain.execution import ExecutionState
from app.domain.repositories import ExecutionRepository, WorkflowRepository, WorkflowVersionRepository


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
        workflow_version_repository: WorkflowVersionRepository | None = None,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._execution_repository = execution_repository
        self._dispatcher = dispatcher
        self._condition_evaluator = condition_evaluator
        self._workflow_version_repository = workflow_version_repository

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

        workflow_definition = workflow
        if execution.workflow_version_id is not None:
            if self._workflow_version_repository is None:
                raise RuntimeError("Workflow version persistence is not configured")
            workflow_definition = self._workflow_version_repository.get(
                execution.workflow_version_id
            )
            if workflow_definition is None:
                raise ValueError(
                    f"Workflow version not found: {execution.workflow_version_id}"
                )
            if workflow_definition.workflow_id != execution.workflow_id:
                raise ValueError("Execution workflow version belongs to a different workflow")

        if execution.current_step >= len(workflow_definition.steps):
            raise ValueError(
                f"Execution current step is out of range: {execution.current_step}"
            )

        step = workflow_definition.steps[execution.current_step]
        skipped = False

        if step.condition is not None:
            should_run = self._condition_evaluator.evaluate(
                step.condition,
                context,
            )
            if not should_run:
                skipped = True
            else:
                self._execute_capability_or_fail(
                    execution,
                    step.capability,
                    context,
                )
        else:
            self._execute_capability_or_fail(
                execution,
                step.capability,
                context,
            )

        execution.complete_step()
        has_more_steps = execution.current_step < len(workflow_definition.steps)

        if not has_more_steps:
            execution.complete()

        self._execution_repository.save(execution)

        return StepExecutionResult(
            processed=True,
            skipped=skipped,
            has_more_steps=has_more_steps,
        )

    @staticmethod
    def _ensure_capability_succeeded(result: object) -> None:
        if hasattr(result, "succeeded") and not result.succeeded:
            raise ValueError(
                f"Capability execution failed: {result.error}"
            )

    def _execute_capability_or_fail(
        self,
        execution,
        capability_id: str,
        context: ExecutionContext,
    ) -> None:
        try:
            result = self._dispatcher.dispatch(capability_id, context)
            self._ensure_capability_succeeded(result)
        except Exception:
            execution.fail()
            self._execution_repository.save(execution)
            raise
