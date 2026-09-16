from app.application.workflow_builder import WorkflowBuilder


def test_builder_creates_linear_transitions_between_steps() -> None:
    workflow = (
        WorkflowBuilder()
        .name("Linear Workflow")
        .add_step("First", "first-capability")
        .add_step("Second", "second-capability")
        .add_step("Third", "third-capability")
        .build()
    )

    steps = workflow.steps
    transitions = workflow.transitions

    assert len(transitions) == 2
    assert transitions[0].source_step_id == steps[0].id
    assert transitions[0].target_step_id == steps[1].id
    assert transitions[0].condition is None
    assert transitions[1].source_step_id == steps[1].id
    assert transitions[1].target_step_id == steps[2].id
    assert transitions[1].condition is None


def test_builder_creates_no_transition_for_single_step_workflow() -> None:
    workflow = (
        WorkflowBuilder()
        .name("Single Step Workflow")
        .add_step("Only Step", "capability")
        .build()
    )

    assert workflow.transitions == []
