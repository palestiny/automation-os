from uuid import uuid4

import pytest

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.capability_result import CapabilityResult
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.application.workflow_execution_orchestration import ExecuteWorkflow
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class RecordingCapability:
    def __init__(self, name: str, failure: Exception | None = None) -> None:
        self.name = name
        self.failure = failure
        self.calls = 0

    def execute(self, context: ExecutionContext) -> CapabilityResult:
        self.calls += 1
        context.set(self.name, self.calls)
        if self.failure is not None:
            return CapabilityResult.failure(self.failure)
        return CapabilityResult.success()


def build_use_case(workflow: Workflow, execution: Execution, capabilities):
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)
    executions.save(execution)

    registry = CapabilityRegistry()
    for capability_id, capability in capabilities.items():
        registry.register(capability_id, capability)

    step_executor = ExecuteWorkflowStep(
        workflows,
        executions,
        CapabilityDispatcher(registry),
        ConditionEvaluator(),
    )
    return ExecuteWorkflow(
        executions,
        step_executor,
    ), executions


def running_execution(workflow: Workflow) -> Execution:
    execution = Execution.create(workflow.id)
    execution.start()
    return execution


def test_execute_workflow_processes_all_steps_in_order():
    workflow = Workflow.create(
        "Pipeline",
        [
            WorkflowStep.create("First", "first"),
            WorkflowStep.create("Second", "second"),
        ],
    )
    execution = running_execution(workflow)
    first = RecordingCapability("first")
    second = RecordingCapability("second")

    use_case, executions = build_use_case(
        workflow,
        execution,
        {"first": first, "second": second},
    )

    context = ExecutionContext()
    result = use_case.execute(execution.id, context)

    assert result is execution
    assert execution.state is ExecutionState.COMPLETED
    assert execution.current_step == 2
    assert first.calls == 1
    assert second.calls == 1
    assert context.get("first") == 1
    assert context.get("second") == 1
    assert executions.get(execution.id) is execution


def test_execute_workflow_propagates_failure_and_stops():
    workflow = Workflow.create(
        "Pipeline",
        [
            WorkflowStep.create("First", "first"),
            WorkflowStep.create("Second", "second"),
        ],
    )
    execution = running_execution(workflow)
    failure = RuntimeError("provider unavailable")
    first = RecordingCapability("first", failure)
    second = RecordingCapability("second")

    use_case, executions = build_use_case(
        workflow,
        execution,
        {"first": first, "second": second},
    )

    with pytest.raises(ValueError, match="Capability execution failed"):
        use_case.execute(execution.id, ExecutionContext())

    assert execution.state is ExecutionState.FAILED
    assert execution.current_step == 0
    assert second.calls == 0
    assert executions.get(execution.id) is execution


@pytest.mark.parametrize(
    "state",
    [
        ExecutionState.CREATED,
        ExecutionState.WAITING,
        ExecutionState.RETRYING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    ],
)
def test_execute_workflow_requires_running_execution(state):
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Only", "test")],
    )
    execution = Execution(
        id=uuid4(),
        workflow_id=workflow.id,
        current_step=0,
        state=state,
        attempt=1,
    )
    capability = RecordingCapability("test")

    use_case, _ = build_use_case(workflow, execution, {"test": capability})

    with pytest.raises(ValueError, match="RUNNING"):
        use_case.execute(execution.id, ExecutionContext())


def test_execute_workflow_rejects_missing_execution():
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Only", "test")],
    )
    execution = running_execution(workflow)
    use_case, _ = build_use_case(workflow, execution, {"test": RecordingCapability("test")})

    with pytest.raises(ValueError, match="Execution not found"):
        use_case.execute(uuid4(), ExecutionContext())
