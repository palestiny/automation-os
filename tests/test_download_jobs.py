from uuid import uuid4

import pytest

from app.application.download_jobs import DownloadJobCapacityExceeded, DownloadJobManager
from app.infrastructure.persistence.download_jobs import InMemoryDownloadJobRepository


def test_download_jobs_are_tenant_scoped():
    manager = DownloadJobManager(InMemoryDownloadJobRepository())
    owner = uuid4()
    other_tenant = uuid4()
    job_id = manager.create_job(owner)
    assert manager.get_job(job_id, owner) is not None
    assert manager.get_job(job_id, other_tenant) is None


def test_active_download_limit_is_enforced_per_tenant():
    manager = DownloadJobManager(
        InMemoryDownloadJobRepository(),
        max_active_per_tenant=1,
    )
    tenant = uuid4()
    manager.create_job(tenant)
    with pytest.raises(DownloadJobCapacityExceeded):
        manager.create_job(tenant)


def test_download_job_progress_and_completion_are_bounded():
    manager = DownloadJobManager(InMemoryDownloadJobRepository())
    tenant = uuid4()
    job_id = manager.create_job(tenant)
    manager.update_progress(job_id, tenant, 150, "downloading", "Downloading")
    assert manager.get_job(job_id, tenant)["progress"] == 99
    manager.complete(job_id, tenant)
    job = manager.get_job(job_id, tenant)
    assert job["status"] == "completed"
    assert job["progress"] == 100
