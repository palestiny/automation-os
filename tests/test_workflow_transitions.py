import pytest

from app.domain.transition import Transition
from app.domain.workflow import Workflow, WorkflowStep


def create_workflow() -> tuple[Workflow, WorkflowStep, WorkflowStep]:
    source = WorkflowStep.create("Source", "source-capability")
    target = WorkflowStep.create("Target", "target-capability")
    workflow = Workflow.create("Test Workflow", [source, target])
    return workflow, source, target


def test_workflow_can_add_transition() -> None:
    workflow, source, target = create_workflow()
    transition = Transition.create(source.id, target.id)

    workflow.add_transition(transition)

    assert workflow.transitions == [transition]


def test_workflow_can_get_outgoing_transitions_for_a_step() -> None:
    workflow, source, target = create_workflow()
    second_target = WorkflowStep.create("Second Target", "second-capability")
    workflow.add_step(second_target)

    first = Transition.create(source.id, target.id)
    second = Transition.create(source.id, second_target.id)
    unrelated = Transition.create(target.id, second_target.id)

    workflow.add_transition(first)
    workflow.add_transition(second)
    workflow.add_transition(unrelated)

    assert workflow.outgoing_transitions(source.id) == [first, second]


def test_workflow_rejects_transition_referencing_unknown_step() -> None:
    workflow, source, _ = create_workflow()
    unknown = WorkflowStep.create("Unknown", "unknown-capability")
    transition = Transition.create(source.id, unknown.id)

    with pytest.raises(ValueError, match="must reference steps in the workflow"):
        workflow.add_transition(transition)


def test_workflow_rejects_transitions_after_publishing() -> None:
    workflow, source, target = create_workflow()
    workflow.publish()
    transition = Transition.create(source.id, target.id)

    with pytest.raises(ValueError, match="only be added to a Workflow in DRAFT state"):
        workflow.add_transition(transition)


def test_workflow_transition_collection_cannot_be_mutated_externally() -> None:
    workflow, source, target = create_workflow()
    transition = Transition.create(source.id, target.id)
    workflow.add_transition(transition)

    transitions = workflow.transitions
    transitions.clear()

    assert workflow.transitions == [transition]
