from app.domain.execution_step import ExecutionStep


def test_execution_step_starts_with_first_attempt():
    step = ExecutionStep.create(
        workflow_step_id="step-1",
    )

    assert step.attempt == 1