from uuid import uuid4

import pytest

from app.application.capability_dispatcher import CapabilityDispatcher
from app.application.capability_registry import CapabilityRegistry
from app.application.condition_evaluator import ConditionEvaluator
from app.application.execution_context import ExecutionContext
from app.application.execute_workflow_step import ExecuteWorkflowStep
from app.domain.execution import Execution, ExecutionState
from app.domain.workflow import Condition, Workflow, WorkflowStep
from app.infrastructure.persistence.in_memory import (
    InMemoryExecutionRepository,
    InMemoryWorkflowRepository,
)


class RecordingCapability:
    def __init__(self, result=None):
        self.calls = 0
        self.result = result

    def execute(self, context):
        self.calls += 1
        return self.result


def make_running_execution(workflow):
    execution = Execution.create(workflow.id)
    execution.start()
    return execution


def make_use_case(workflow, execution, capability):
    workflows = InMemoryWorkflowRepository()
    executions = InMemoryExecutionRepository()
    workflows.save(workflow)
    executions.save(execution)

    registry = CapabilityRegistry()
    registry.register("test", capability)

    return (
        ExecuteWorkflowStep(
            workflows,
            executions,
            CapabilityDispatcher(registry),
            ConditionEvaluator(),
        ),
        executions,
    )


def test_execute_workflow_step_dispatches_and_advances():
    workflow = Workflow.create(
        "Pipeline",
        [
            WorkflowStep.create("Step 1", "test"),
            WorkflowStep.create("Step 2", "test"),
        ],
    )
    execution = make_running_execution(workflow)
    capability = RecordingCapability()

    use_case, executions = make_use_case(workflow, execution, capability)

    result = use_case.execute(execution.id, ExecutionContext())

    assert result.processed is True
    assert result.skipped is False
    assert result.has_more_steps is True
    assert capability.calls == 1
    assert execution.current_step == 1
    assert execution.state is ExecutionState.RUNNING
    assert execution.finished_at is None
    assert executions.get(execution.id) is execution


def test_final_step_completes_execution():
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Final", "test")],
    )
    execution = make_running_execution(workflow)
    capability = RecordingCapability()

    use_case, executions = make_use_case(workflow, execution, capability)

    result = use_case.execute(execution.id, ExecutionContext())

    assert result.has_more_steps is False
    assert execution.current_step == 1
    assert execution.state is ExecutionState.COMPLETED
    assert execution.finished_at is not None
    assert executions.get(execution.id) is execution


def test_false_condition_skips_dispatch_and_advances():
    condition = Condition.create("enabled", "equals", True)
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Conditional", "test", condition)],
    )
    execution = make_running_execution(workflow)
    capability = RecordingCapability()

    use_case, _ = make_use_case(workflow, execution, capability)
    context = ExecutionContext()
    context.set("enabled", False)

    result = use_case.execute(execution.id, context)

    assert result.skipped is True
    assert result.has_more_steps is False
    assert capability.calls == 0
    assert execution.current_step == 1
    assert execution.state is ExecutionState.COMPLETED
    assert execution.finished_at is not None


def test_capability_failure_does_not_advance_or_complete():
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    execution = make_running_execution(workflow)

    from app.application.capability_result import CapabilityResult

    capability = RecordingCapability(CapabilityResult.failure(Exception("boom")))
    use_case, _ = make_use_case(workflow, execution, capability)

    with pytest.raises(ValueError, match="Capability execution failed"):
        use_case.execute(execution.id, ExecutionContext())

    assert execution.current_step == 0
    assert execution.state is ExecutionState.RUNNING
    assert execution.finished_at is None


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
def test_execute_workflow_step_requires_running_execution(state):
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    execution = Execution(
        id=uuid4(),
        workflow_id=workflow.id,
        current_step=0,
        state=state,
        attempt=1,
    )
    capability = RecordingCapability()
    use_case, _ = make_use_case(workflow, execution, capability)

    with pytest.raises(ValueError, match="RUNNING"):
        use_case.execute(execution.id, ExecutionContext())


def test_execute_workflow_step_rejects_missing_execution():
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    execution = make_running_execution(workflow)
    use_case, _ = make_use_case(workflow, execution, RecordingCapability())

    with pytest.raises(ValueError, match="Execution not found"):
        use_case.execute(uuid4(), ExecutionContext())


def test_execute_workflow_step_rejects_invalid_current_step():
    workflow = Workflow.create(
        "Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    execution = make_running_execution(workflow)
    execution.current_step = 1
    use_case, _ = make_use_case(workflow, execution, RecordingCapability())

    with pytest.raises(ValueError, match="out of range"):
        use_case.execute(execution.id, ExecutionContext())
