from __future__ import annotations

import os
from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class HealthStatus:
    status: str
    checks: dict[str, str]


def liveness() -> HealthStatus:
    return HealthStatus(status="ok", checks={"process": "ok"})


def readiness() -> HealthStatus:
    database_url = os.getenv("AUTOMATION_OS_DATABASE_URL")
    if not database_url:
        return HealthStatus(
            status="not_ready",
            checks={"database": "not_configured"},
        )

    try:
        with psycopg.connect(database_url, connect_timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
    except Exception:
        return HealthStatus(
            status="not_ready",
            checks={"database": "unavailable"},
        )

    return HealthStatus(
        status="ready",
        checks={"database": "ok"},
    )
