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
    assert response.json()["state"] == "waiting"


def test_get_execution_returns_404_for_missing_execution():
    response = client.get(f"/executions/{uuid4()}")
    assert response.status_code == 404


def test_cancel_execution_delegates_to_application_boundary():
    execution = _save(ExecutionState.WAITING)
    response = client.post(f"/executions/{execution.id}/cancel")
    assert response.status_code == 200
    assert response.json()["state"] == "cancelled"


def test_retry_execution_delegates_to_application_boundary():
    execution = _save(ExecutionState.FAILED)
    response = client.post(f"/executions/{execution.id}/retry")
    assert response.status_code == 200
    assert response.json()["state"] == "retrying"
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


def test_start_workflow_execution_returns_running_execution():
    from app.core.execution_dependencies import workflow_repository
    from app.domain.workflow import Workflow, WorkflowStep

    workflow = Workflow.create(
        "API Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    workflow.publish()
    workflow_repository.save(workflow)

    response = client.post(f"/executions/workflows/{workflow.id}")

    assert response.status_code == 200
    assert response.json()["workflow_id"] == str(workflow.id)
    assert response.json()["state"] == "running"
    assert response.json()["attempt"] == 1


def test_start_workflow_execution_returns_404_for_unknown_workflow():
    response = client.post(f"/executions/workflows/{uuid4()}")
    assert response.status_code == 404


def test_start_workflow_execution_returns_409_for_draft_workflow():
    from app.core.execution_dependencies import workflow_repository
    from app.domain.workflow import Workflow, WorkflowStep

    workflow = Workflow.create(
        "Draft Pipeline",
        [WorkflowStep.create("Step 1", "test")],
    )
    workflow_repository.save(workflow)

    response = client.post(f"/executions/workflows/{workflow.id}")

    assert response.status_code == 409


def test_list_executions_returns_collection():
    first = _save(ExecutionState.WAITING)
    second = _save(ExecutionState.RUNNING)

    response = client.get("/executions")

    assert response.status_code == 200
    ids = {item["execution_id"] for item in response.json()}
    assert str(first.id) in ids
    assert str(second.id) in ids


def test_list_executions_filters_by_workflow():
    execution = _save(ExecutionState.WAITING)

    response = client.get(
        "/executions",
        params={"workflow_id": str(execution.workflow_id)},
    )

    assert response.status_code == 200
    assert str(execution.id) in [item["execution_id"] for item in response.json()]


def test_list_executions_filters_by_state():
    execution = _save(ExecutionState.FAILED)

    response = client.get("/executions", params={"state": "failed"})

    assert response.status_code == 200
    assert [item["execution_id"] for item in response.json()] == [str(execution.id)]


def test_list_executions_rejects_invalid_state():
    response = client.get("/executions", params={"state": "not-a-state"})

    assert response.status_code == 422
