from uuid import uuid4

import pytest

from app.application.job_manager import JobManager
from app.application.orchestrator import Orchestrator
from app.domain.execution import ExecutionState
from app.domain.workflow import Workflow, WorkflowStep


def published_workflow() -> Workflow:
    workflow = Workflow.create(
        name="Integration Workflow",
        steps=[WorkflowStep.create(name="Download", capability="video_download")],
    )
    workflow.publish()
    return workflow


def test_orchestrator_and_job_manager_share_same_execution():
    workflow = published_workflow()
    orchestrator = Orchestrator()
    manager = JobManager()

    execution = orchestrator.start(workflow)
    manager.register(execution)

    registered = manager.get(execution.id)

    assert registered is execution
    assert registered.workflow_id == workflow.id
    assert registered.state is ExecutionState.RUNNING
    assert registered.current_step == 0


def test_execution_lifecycle_remains_owned_by_execution_after_registration():
    workflow = published_workflow()
    execution = Orchestrator().start(workflow)
    manager = JobManager()
    manager.register(execution)

    execution.complete_step()
    execution.complete()

    registered = manager.get(execution.id)

    assert registered.state is ExecutionState.COMPLETED
    assert registered.current_step == 1
    assert registered.finished_at is not None


def test_orchestrator_rejects_draft_before_job_registration():
    workflow = Workflow.create(
        name="Draft Workflow",
        steps=[WorkflowStep.create(name="Download", capability="video_download")],
    )
    orchestrator = Orchestrator()
    manager = JobManager()

    with pytest.raises(ValueError):
        orchestrator.start(workflow)

    with pytest.raises(KeyError):
        manager.get(uuid4())
