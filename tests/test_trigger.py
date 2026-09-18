from uuid import uuid4

from app.application.trigger import Trigger
from app.application.workflow_start_request import WorkflowStartRequest


class FakeTrigger:
    def __init__(self, workflow_id):
        self.workflow_id = workflow_id

    def create_start_request(self):
        return WorkflowStartRequest(workflow_id=self.workflow_id)


def test_trigger_produces_workflow_start_request():
    workflow_id = uuid4()
    trigger: Trigger = FakeTrigger(workflow_id)

    request = trigger.create_start_request()

    assert request.workflow_id == workflow_id
