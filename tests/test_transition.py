import pytest

from app.domain.workflow import WorkflowStep
from app.domain.transition import Transition


def test_transition_requires_source_and_target_steps() -> None:
    source = WorkflowStep.create("Source", "source-capability")
    target = WorkflowStep.create("Target", "target-capability")

    transition = Transition.create(source.id, target.id)

    assert transition.source_step_id == source.id
    assert transition.target_step_id == target.id
    assert transition.condition is None


def test_transition_can_reference_a_condition() -> None:
    source = WorkflowStep.create("Source", "source-capability")
    target = WorkflowStep.create("Target", "target-capability")

    transition = Transition.create(
        source.id,
        target.id,
        condition="is_customer",
    )

    assert transition.condition == "is_customer"


def test_transition_cannot_point_to_itself() -> None:
    step = WorkflowStep.create("Step", "capability")

    with pytest.raises(ValueError, match="cannot point to itself"):
        Transition.create(step.id, step.id)


def test_transition_condition_cannot_be_blank() -> None:
    source = WorkflowStep.create("Source", "source-capability")
    target = WorkflowStep.create("Target", "target-capability")

    with pytest.raises(ValueError, match="condition cannot be blank"):
        Transition.create(source.id, target.id, condition=" ")
