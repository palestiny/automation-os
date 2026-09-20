from uuid import uuid4

from app.domain.execution import Execution
from app.domain.workflow import Workflow
from app.domain.repositories import ExecutionRepository, WorkflowRepository


class InMemoryWorkflowRepository:
    def __init__(self) -> None:
        self.items: dict[object, Workflow] = {}

    def save(self, workflow: Workflow) -> None:
        self.items[workflow.id] = workflow

    def get(self, workflow_id):
        return self.items.get(workflow_id)

    def all(self):
        return tuple(self.items.values())


class InMemoryExecutionRepository:
    def __init__(self) -> None:
        self.items: dict[object, Execution] = {}

    def save(self, execution: Execution) -> None:
        self.items[execution.id] = execution

    def save_if_state(self, execution: Execution, expected_state) -> bool:
        current = self.items.get(execution.id)
        if current is None or current.state is not expected_state:
            return False
        self.items[execution.id] = execution
        return True

    def get(self, execution_id):
        return self.items.get(execution_id)

    def all(self):
        return tuple(self.items.values())


def test_workflow_repository_contract_is_aggregate_aligned():
    repository = InMemoryWorkflowRepository()
    workflow = Workflow.create("Pipeline", [])

    repository.save(workflow)

    assert repository.get(workflow.id) is workflow


def test_execution_repository_contract_is_aggregate_aligned():
    repository = InMemoryExecutionRepository()
    workflow_id = uuid4()
    execution = Execution.create(workflow_id)

    repository.save(execution)

    assert repository.get(execution.id) is execution


def test_repository_get_returns_none_for_unknown_id():
    workflow_repository = InMemoryWorkflowRepository()
    execution_repository = InMemoryExecutionRepository()

    assert workflow_repository.get(uuid4()) is None
    assert execution_repository.get(uuid4()) is None


def test_in_memory_repositories_satisfy_contracts():
    assert isinstance(InMemoryWorkflowRepository(), WorkflowRepository)
    assert isinstance(InMemoryExecutionRepository(), ExecutionRepository)
