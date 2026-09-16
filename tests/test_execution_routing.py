import pytest

from app.domain.execution import Execution, ExecutionState
from app.domain.transition import Transition
from app.domain.workflow import Workflow, WorkflowStep


def create_branching_workflow() -> tuple[Workflow, WorkflowStep, WorkflowStep, WorkflowStep]:
    source = WorkflowStep.create("Source", "source-capability")
    yes = WorkflowStep.create("Yes", "yes-capability")
    no = WorkflowStep.create("No", "no-capability")

    workflow = Workflow.create("Branching Workflow", [source, yes, no])
    workflow.add_transition(Transition.create(source.id, yes.id, condition="is_customer"))
    workflow.add_transition(Transition.create(source.id, no.id, condition="is_not_customer"))
    return workflow, source, yes, no


def test_execution_can_move_to_explicit_transition_target() -> None:
    workflow, source, yes, _ = create_branching_workflow()

    execution = Execution.create_from_workflow(workflow)
    execution.start()
    execution.complete_step(next_step_id=yes.id)

    assert execution.current_step_id == yes.id
    assert execution.state == ExecutionState.RUNNING


def test_execution_rejects_transition_target_not_in_execution() -> None:
    workflow, _, _, _ = create_branching_workflow()
    unknown = WorkflowStep.create("Unknown", "unknown-capability")

    execution = Execution.create_from_workflow(workflow)
    execution.start()

    with pytest.raises(ValueError, match="next step must belong to the execution"):
        execution.complete_step(next_step_id=unknown.id)


def test_execution_cannot_complete_current_step_with_same_next_step() -> None:
    workflow, source, _, _ = create_branching_workflow()

    execution = Execution.create_from_workflow(workflow)
    execution.start()

    with pytest.raises(ValueError, match="next step must differ from the current step"):
        execution.complete_step(next_step_id=source.id)
