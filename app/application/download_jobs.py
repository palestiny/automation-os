from __future__ import annotations

from typing import Protocol
from uuid import UUID


class DownloadJobCapacityExceeded(RuntimeError):
    """Raised when a tenant has reached its active download limit."""


class DownloadJobRepository(Protocol):
    def create(self, tenant_id: UUID, *, max_active: int) -> dict[str, object]: ...
    def get(self, job_id: str, tenant_id: UUID) -> dict[str, object] | None: ...
    def update_progress(
        self, job_id: str, tenant_id: UUID, progress: int, status: str, message: str
    ) -> None: ...
    def set_title(self, job_id: str, tenant_id: UUID, title: str) -> None: ...
    def set_error(self, job_id: str, tenant_id: UUID, error: str) -> None: ...
    def complete(self, job_id: str, tenant_id: UUID, message: str) -> None: ...


class DownloadJobManager:
    """Application service for tenant-owned, bounded download jobs."""

    def __init__(
        self,
        repository: DownloadJobRepository,
        *,
        max_active_per_tenant: int = 2,
    ) -> None:
        if max_active_per_tenant < 1:
            raise ValueError("max_active_per_tenant must be positive")
        self._repository = repository
        self._max_active_per_tenant = max_active_per_tenant

    def create_job(self, tenant_id: UUID) -> str:
        return str(
            self._repository.create(
                tenant_id,
                max_active=self._max_active_per_tenant,
            )["id"]
        )

    def update_progress(
        self,
        job_id: str,
        tenant_id: UUID,
        progress: int,
        status: str | None = None,
        message: str | None = None,
    ) -> None:
        normalized_progress = max(0, min(int(progress), 99))
        normalized_status = status if status in {"pending", "downloading", "processing"} else "downloading"
        self._repository.update_progress(
            job_id,
            tenant_id,
            normalized_progress,
            normalized_status,
            message or "Download in progress",
        )

    def set_title(self, job_id: str, tenant_id: UUID, title: str) -> None:
        self._repository.set_title(job_id, tenant_id, title)

    def set_error(self, job_id: str, tenant_id: UUID, error: str) -> None:
        self._repository.set_error(job_id, tenant_id, error)

    def complete(
        self,
        job_id: str,
        tenant_id: UUID,
        message: str = "Completed successfully",
    ) -> None:
        self._repository.complete(job_id, tenant_id, message)

    def get_job(self, job_id: str, tenant_id: UUID) -> dict[str, object] | None:
        return self._repository.get(job_id, tenant_id)
