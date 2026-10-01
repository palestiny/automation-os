from __future__ import annotations

from dataclasses import dataclass

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_operation_identity import derive_capability_operation_id
from app.application.condition_evaluator import ConditionEvaluator
from app.application.runtime_connection_preparation import PrepareWorkflowRuntimeConnections
from app.application.execution_context import ExecutionContext
from app.application.errors import CapabilityExecutionError
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
        runtime_connection_preparer: PrepareWorkflowRuntimeConnections | None = None,
    ) -> None:
        self._workflow_repository = workflow_repository
        self._execution_repository = execution_repository
        self._dispatcher = dispatcher
        self._condition_evaluator = condition_evaluator
        self._workflow_version_repository = workflow_version_repository
        self._runtime_connection_preparer = runtime_connection_preparer

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

        try:
            if step.condition is not None:
                should_run = self._condition_evaluator.evaluate(
                    step.condition,
                    context,
                )
                if not should_run:
                    skipped = True
                else:
                    self._prepare_runtime_connections(
                        execution,
                        workflow_definition,
                        context,
                    )
                    self._set_capability_operation_id(execution, workflow_definition, context)
                    self._execute_capability_or_fail(
                        execution,
                        step.capability,
                        context,
                    )
            else:
                self._prepare_runtime_connections(
                    execution,
                    workflow_definition,
                    context,
                )
                self._set_capability_operation_id(execution, workflow_definition, context)
                self._execute_capability_or_fail(
                    execution,
                    step.capability,
                    context,
                )
        except Exception:
            if execution.state is ExecutionState.RUNNING:
                execution.fail()
                self._execution_repository.save(execution)
            raise

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

    def _prepare_runtime_connections(
        self,
        execution,
        workflow_definition,
        context: ExecutionContext,
    ) -> None:
        requirements = (
            workflow_definition.connection_requirements
            if hasattr(workflow_definition, "connection_requirements")
            else ()
        )
        if not requirements:
            return
        if self._runtime_connection_preparer is None:
            raise RuntimeError(
                "Workflow requires runtime connections but runtime connection preparation is not configured"
            )
        tenant_id = execution.tenant_id
        if tenant_id is None:
            raise RuntimeError(
                "Workflow requires runtime connections but has no tenant ownership"
            )
        if not self._has_prepared_runtime_connections(context):
            self._runtime_connection_preparer.prepare(
                workflow_version=workflow_definition,
                tenant_id=tenant_id,
                context=context,
            )

    @staticmethod
    def _set_capability_operation_id(execution, workflow_definition, context: ExecutionContext) -> None:
        definition_id = getattr(workflow_definition, "id", execution.workflow_id)
        operation_id = derive_capability_operation_id(
            execution.id,
            definition_id,
            execution.current_step,
        )
        context._set_capability_operation_id(operation_id)

    @staticmethod
    def _has_prepared_runtime_connections(context: ExecutionContext) -> bool:
        try:
            context.get_runtime_connections()
        except KeyError:
            return False
        return True

    @staticmethod
    def _ensure_capability_succeeded(result: object) -> None:
        if hasattr(result, "succeeded") and not result.succeeded:
            raise CapabilityExecutionError(result)

    def _execute_capability_or_fail(
        self,
        execution,
        capability_id: str,
        context: ExecutionContext,
    ) -> None:
        try:
            result = self._dispatcher.dispatch(capability_id, context)
            self._ensure_capability_succeeded(result)
        except CapabilityExecutionError as exc:
            result = exc.result
            execution.fail(
                outcome=getattr(getattr(result, "outcome", None), "value", None),
                operation_id=getattr(result, "operation_id", None),
                diagnostic=str(getattr(result, "error", ""))[:2000] or None,
                idempotency_proven=getattr(result, "idempotency_proven", False),
            )
            self._execution_repository.save(execution)
            raise
        except Exception:
            execution.fail()
            self._execution_repository.save(execution)
            raise
