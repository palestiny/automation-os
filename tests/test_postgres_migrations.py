from __future__ import annotations

import os

import pytest

from app.infrastructure.persistence.migrations import PostgresMigrationRunner
from app.infrastructure.persistence.postgres import postgres_connection_factory


DATABASE_URL = os.environ.get("AUTOMATION_OS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="AUTOMATION_OS_TEST_DATABASE_URL is required for PostgreSQL migration tests",
)


def test_postgres_migrations_apply_once_and_record_versions():
    factory = postgres_connection_factory(DATABASE_URL)

    first = PostgresMigrationRunner(factory).apply()
    second = PostgresMigrationRunner(factory).apply()

    assert first == (1,)
    assert second == ()

    with factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT version, name FROM schema_migrations ORDER BY version"
            )
            rows = cursor.fetchall()

    assert rows == [(1, "initial_automation_os_schema")]


def test_runtime_persistence_requires_preexisting_schema():
    factory = postgres_connection_factory(DATABASE_URL)

    with factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT to_regclass('public.schema_migrations')"
            )
            assert cursor.fetchone()[0] == "schema_migrations"

            cursor.execute(
                "SELECT to_regclass('public.workflows')"
            )
            assert cursor.fetchone()[0] == "workflows"
