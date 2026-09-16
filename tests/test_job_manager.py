from uuid import uuid4

from app.core.job_manager import JobManager


def test_job_manager_creates_job_with_execution_reference():
    manager = JobManager()
    execution_id = uuid4()

    job_id = manager.create_job(execution_id=execution_id)

    job = manager.get_job(job_id)

    assert job["id"] == job_id
    assert job["execution_id"] == execution_id
    assert job["status"] == "pending"


def test_job_manager_does_not_own_execution_lifecycle():
    manager = JobManager()
    execution_id = uuid4()

    job_id = manager.create_job(execution_id=execution_id)

    manager.update_progress(
        job_id,
        progress=50,
        status="running",
        message="Execution is running",
    )

    job = manager.get_job(job_id)

    assert job["execution_id"] == execution_id
    assert job["status"] == "running"
    assert job["progress"] == 50


def test_job_manager_returns_none_for_unknown_job():
    manager = JobManager()

    assert manager.get_job("missing") is None
