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
