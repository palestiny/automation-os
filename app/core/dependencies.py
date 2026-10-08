from __future__ import annotations

import os

from app.application.download_jobs import DownloadJobManager
from app.infrastructure.persistence.download_jobs import (
    InMemoryDownloadJobRepository,
    PostgresDownloadJobRepository,
)
from app.infrastructure.persistence.postgres import postgres_connection_factory


def _build_download_job_manager() -> DownloadJobManager:
    database_url = os.environ.get("AUTOMATION_OS_DATABASE_URL")
    environment = os.environ.get("AUTOMATION_OS_ENV", "development").lower()
    if database_url:
        repository = PostgresDownloadJobRepository(
            postgres_connection_factory(database_url)
        )
    elif environment == "production":
        raise RuntimeError(
            "Production download jobs require AUTOMATION_OS_DATABASE_URL"
        )
    else:
        repository = InMemoryDownloadJobRepository()
    return DownloadJobManager(repository)


job_manager = _build_download_job_manager()
