from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import psycopg

from app.infrastructure.persistence.migrations import MIGRATIONS

ConnectionFactory = Callable[[], psycopg.Connection[Any]]


class PostgresSchema:
    """Compatibility facade for explicit PostgreSQL migrations.

    New runtime composition must not call this facade. It remains temporarily
    available for legacy tests/consumers while migration ownership moves to the
    dedicated migration boundary.
    """

    @staticmethod
    def initialize(connection: psycopg.Connection[Any]) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            for migration in MIGRATIONS:
                cursor.execute(
                    "SELECT 1 FROM schema_migrations WHERE version = %s",
                    (migration.version,),
                )
                if cursor.fetchone() is not None:
                    continue
                cursor.execute(migration.sql)
                cursor.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (%s, %s)",
                    (migration.version, migration.name),
                )
        connection.commit()


def postgres_connection_factory(database_url: str | None = None) -> ConnectionFactory:
    url = database_url or os.environ.get("AUTOMATION_OS_DATABASE_URL")
    if not url:
        raise RuntimeError("AUTOMATION_OS_DATABASE_URL is required for PostgreSQL persistence")
    return lambda: psycopg.connect(url)


