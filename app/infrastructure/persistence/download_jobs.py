from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
from uuid import UUID, uuid4

from psycopg.rows import dict_row

from app.application.download_jobs import DownloadJobCapacityExceeded

ACTIVE_STATUSES = ("pending", "downloading", "processing")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _public_job(row: dict[str, object]) -> dict[str, object]:
    result = dict(row)
    result["id"] = str(result["id"])
    result["created_at"] = _iso(result["created_at"])
    result["updated_at"] = _iso(result["updated_at"])
    result.pop("tenant_id", None)
    return result


def _iso(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class InMemoryDownloadJobRepository:
    """Thread-safe development/test adapter; production should use PostgreSQL."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, object]] = {}
        self._lock = RLock()

    def create(self, tenant_id: UUID, *, max_active: int) -> dict[str, object]:
        with self._lock:
            active = sum(
                job["tenant_id"] == tenant_id and job["status"] in ACTIVE_STATUSES
                for job in self._jobs.values()
            )
            if active >= max_active:
                raise DownloadJobCapacityExceeded("Active download limit reached")
            now = _now()
            job = {
                "id": str(uuid4()),
                "tenant_id": tenant_id,
                "status": "pending",
                "progress": 0,
                "title": None,
                "message": "Waiting to start",
                "error": None,
                "created_at": now,
                "updated_at": now,
            }
            self._jobs[str(job["id"])] = job
            return _public_job(job)

    def get(self, job_id: str, tenant_id: UUID) -> dict[str, object] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job["tenant_id"] != tenant_id:
                return None
            return _public_job(deepcopy(job))

    def update_progress(
        self, job_id: str, tenant_id: UUID, progress: int, status: str, message: str
    ) -> None:
        self._update(job_id, tenant_id, progress=progress, status=status, message=message)

    def set_title(self, job_id: str, tenant_id: UUID, title: str) -> None:
        self._update(job_id, tenant_id, title=title)

    def set_error(self, job_id: str, tenant_id: UUID, error: str) -> None:
        self._update(
            job_id, tenant_id, status="failed", error=error,
            message="Download failed", updated_at=_now(),
        )

    def complete(self, job_id: str, tenant_id: UUID, message: str) -> None:
        self._update(
            job_id, tenant_id, progress=100, status="completed",
            message=message, error=None, updated_at=_now(),
        )

    def _update(self, job_id: str, tenant_id: UUID, **changes: object) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job["tenant_id"] != tenant_id:
                return
            job.update(changes)
            job["updated_at"] = _now()


class PostgresDownloadJobRepository:
    """Durable tenant-scoped download job adapter."""

    def __init__(self, connection_factory) -> None:
        self._connection_factory = connection_factory

    def create(self, tenant_id: UUID, *, max_active: int) -> dict[str, object]:
        now = _now()
        job_id = uuid4()
        with self._connection_factory() as connection:
            with connection.transaction():
                with connection.cursor(row_factory=dict_row) as cursor:
                    # Serialize capacity checks for this tenant across workers.
                    cursor.execute(
                        "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))",
                        (str(tenant_id),),
                    )
                    cursor.execute(
                        "SELECT COUNT(*) AS active_count FROM download_jobs "
                        "WHERE tenant_id = %s AND status = ANY(%s)",
                        (tenant_id, list(ACTIVE_STATUSES)),
                    )
                    if int(cursor.fetchone()["active_count"]) >= max_active:
                        raise DownloadJobCapacityExceeded("Active download limit reached")
                    cursor.execute(
                        """
                        INSERT INTO download_jobs
                            (id, tenant_id, status, progress, title, message, error,
                             created_at, updated_at)
                        VALUES (%s, %s, 'pending', 0, NULL, %s, NULL, %s, %s)
                        RETURNING id, tenant_id, status, progress, title, message,
                                  error, created_at, updated_at
                        """,
                        (job_id, tenant_id, "Waiting to start", now, now),
                    )
                    row = cursor.fetchone()
        return _public_job(row)

    def get(self, job_id: str, tenant_id: UUID) -> dict[str, object] | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, tenant_id, status, progress, title, message, error,
                           created_at, updated_at
                    FROM download_jobs WHERE id = %s AND tenant_id = %s
                    """,
                    (job_id, tenant_id),
                )
                row = cursor.fetchone()
        return _public_job(row) if row else None

    def update_progress(
        self, job_id: str, tenant_id: UUID, progress: int, status: str, message: str
    ) -> None:
        self._update(
            job_id, tenant_id,
            "progress = %s, status = %s, message = %s, updated_at = %s",
            (progress, status, message, _now()),
        )

    def set_title(self, job_id: str, tenant_id: UUID, title: str) -> None:
        self._update(
            job_id, tenant_id, "title = %s, updated_at = %s", (title, _now())
        )

    def set_error(self, job_id: str, tenant_id: UUID, error: str) -> None:
        self._update(
            job_id, tenant_id,
            "status = 'failed', error = %s, message = %s, updated_at = %s",
            (error, "Download failed", _now()),
        )

    def complete(self, job_id: str, tenant_id: UUID, message: str) -> None:
        self._update(
            job_id, tenant_id,
            "status = 'completed', progress = 100, error = NULL, message = %s, updated_at = %s",
            (message, _now()),
        )

    def _update(
        self, job_id: str, tenant_id: UUID, assignments: str, values: tuple[object, ...]
    ) -> None:
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"UPDATE download_jobs SET {assignments} WHERE id = %s AND tenant_id = %s",
                    (*values, job_id, tenant_id),
                )
