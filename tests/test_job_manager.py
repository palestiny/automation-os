from uuid import uuid4

import pytest

from app.domain.execution import Execution
from app.application.job_manager import JobManager


def test_job_manager_registers_and_returns_execution():
    manager = JobManager()
    execution = Execution.create(uuid4())

    execution_id = manager.register(execution)

    assert execution_id == execution.id
    assert manager.get(execution_id) is execution


def test_job_manager_keeps_execution_as_domain_object():
    manager = JobManager()
    execution = Execution.create(uuid4())
    manager.register(execution)

    execution.start()

    assert manager.get(execution.id).state.value == "running"


def test_job_manager_rejects_duplicate_execution_id():
    manager = JobManager()
    execution = Execution.create(uuid4())
    manager.register(execution)

    with pytest.raises(ValueError, match="already registered"):
        manager.register(execution)


def test_job_manager_raises_key_error_for_unknown_execution():
    manager = JobManager()

    with pytest.raises(KeyError):
        manager.get(uuid4())
