import pytest

from app.domain.workflow import Condition, Workflow, WorkflowStep


def test_workflow_step_can_be_created_without_condition():
    step = WorkflowStep.create(
        name="Download video",
        capability="video_download",
    )

    assert step.condition is None


def test_workflow_step_can_be_created_with_condition():
    condition = Condition.create(
        left_operand="video.duration",
        operator="greater_than",
        right_operand=60,
    )

    step = WorkflowStep.create(
        name="Create short",
        capability="clip_extraction",
        condition=condition,
    )

    assert step.condition is condition


@pytest.mark.parametrize(
    ("left_operand", "operator"),
    [
        ("", "equals"),
        ("video.duration", ""),
    ],
)
def test_condition_rejects_empty_text_fields(left_operand, operator):
    with pytest.raises(ValueError):
        Condition.create(
            left_operand=left_operand,
            operator=operator,
            right_operand=60,
        )


def test_condition_is_immutable():
    condition = Condition.create(
        left_operand="video.duration",
        operator="greater_than",
        right_operand=60,
    )

    with pytest.raises(AttributeError):
        condition.operator = "equals"


def test_condition_survives_published_workflow_definition():
    condition = Condition.create(
        left_operand="video.duration",
        operator="greater_than",
        right_operand=60,
    )
    step = WorkflowStep.create(
        name="Create short",
        capability="clip_extraction",
        condition=condition,
    )
    workflow = Workflow.create("Pipeline", [step])

    workflow.publish()

    assert workflow.steps[0].condition == condition
