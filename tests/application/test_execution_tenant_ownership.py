from uuid import uuid4

from app.application.start_workflow_execution import StartWorkflowExecution
from app.domain.execution import Execution


def test_execution_carries_tenant_ownership():
    tenant_id = uuid4()
    workflow_id = uuid4()
    execution = Execution.create(workflow_id, tenant_id=tenant_id)
    assert execution.tenant_id == tenant_id


def test_start_workflow_execution_binds_workflow_tenant_to_execution():
    tenant_id = uuid4()

    class WorkflowRepo:
        def get(self, workflow_id):
            from app.domain.workflow import Workflow
            workflow = Workflow.create(
                name="tenant workflow",
                tenant_id=tenant_id,
                steps=[],
            )
            workflow.publish()
            return workflow

    class ExecutionRepo:
        def save(self, execution):
            self.execution = execution

    repo = ExecutionRepo()
    use_case = StartWorkflowExecution(WorkflowRepo(), repo)
    execution = use_case.execute(uuid4())
    assert execution.tenant_id == tenant_id
