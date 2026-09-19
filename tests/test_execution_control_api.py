from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.core.execution_dependencies import execution_repository
from app.domain.execution import Execution, ExecutionState

client = TestClient(app)


def _save(state: ExecutionState) -> Execution:
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=state,
        attempt=1,
    )
    execution_repository.save(execution)
    return execution


def test_get_execution_returns_projection():
    execution = _save(ExecutionState.WAITING)
    response = client.get(f"/executions/{execution.id}")
    assert response.status_code == 200
    assert response.json()["execution_id"] == str(execution.id)
    assert response.json()["state"] == "WAITING"


def test_get_execution_returns_404_for_missing_execution():
    response = client.get(f"/executions/{uuid4()}")
    assert response.status_code == 404


def test_cancel_execution_delegates_to_application_boundary():
    execution = _save(ExecutionState.WAITING)
    response = client.post(f"/executions/{execution.id}/cancel")
    assert response.status_code == 200
    assert response.json()["state"] == "CANCELLED"


def test_retry_execution_delegates_to_application_boundary():
    execution = _save(ExecutionState.FAILED)
    response = client.post(f"/executions/{execution.id}/retry")
    assert response.status_code == 200
    assert response.json()["state"] == "RETRYING"
    assert response.json()["attempt"] == 2


def test_invalid_transition_returns_409():
    execution = _save(ExecutionState.COMPLETED)
    response = client.post(f"/executions/{execution.id}/retry")
    assert response.status_code == 409

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.core.execution_dependencies import execution_repository
from app.domain.execution import Execution, ExecutionState

client = TestClient(app)


def _save(state: ExecutionState) -> Execution:
    execution = Execution(
        id=uuid4(),
        workflow_id=uuid4(),
        current_step=0,
        state=state,
        attempt=1,
    )
    execution_repository.save(execution)
    return execution


def test_resume_execution_returns_conflict_for_non_waiting():
    execution = _save(ExecutionState.RUNNING)
    response = client.post(f"/executions/{execution.id}/resume")
    assert response.status_code == 409


def test_retry_and_execute_returns_conflict_for_missing_execution():
    response = client.post(f"/executions/{uuid4()}/retry-and-execute")
    assert response.status_code == 404
