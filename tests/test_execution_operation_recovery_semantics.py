from uuid import uuid4

from app.domain.execution import Execution, ExecutionState


def _running_execution() -> Execution:
    execution = Execution.create(uuid4())
    execution.start()
    return execution


def test_latest_terminal_evidence_clears_older_unresolved_capability_operation() -> None:
    execution = _running_execution()
    execution.begin_capability_operation("op-1")
    execution.record_capability_succeeded("op-1")

    assert execution.has_unresolved_capability_operation() is False
    assert execution.unresolved_capability_operation_id() is None


def test_latest_capability_start_is_unresolved_until_terminal_evidence() -> None:
    execution = _running_execution()
    execution.begin_capability_operation("op-1")
    execution.record_capability_succeeded("op-1")
    execution.current_step += 1
    execution.begin_capability_operation("op-2")

    assert execution.has_unresolved_capability_operation() is True
    assert execution.unresolved_capability_operation_id() == "op-2"


def test_stale_recovery_marks_latest_unresolved_operation_unknown() -> None:
    execution = _running_execution()
    execution.begin_capability_operation("op-1")

    execution.recover_stale()

    assert execution.state is ExecutionState.FAILED
    assert execution.last_outcome == "unknown"
    assert execution.last_operation_id == "op-1"
