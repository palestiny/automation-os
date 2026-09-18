from uuid import uuid4

from app.application.workflow_start_request import WorkflowStartRequest


def test_workflow_start_request_carries_workflow_identity():
    workflow_id = uuid4()

    request = WorkflowStartRequest(workflow_id=workflow_id)

    assert request.workflow_id == workflow_id
