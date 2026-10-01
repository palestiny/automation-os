from __future__ import annotations

import os

import pytest

from app.infrastructure.persistence.migrations import Migration, PostgresMigrationRunner
from app.infrastructure.persistence.postgres import postgres_connection_factory


DATABASE_URL = os.environ.get("AUTOMATION_OS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="AUTOMATION_OS_TEST_DATABASE_URL is required for PostgreSQL migration tests",
)


def test_postgres_migrations_apply_once_and_record_versions():
    factory = postgres_connection_factory(DATABASE_URL)
    migration = Migration(
        version=9001,
        name="test_migration_boundary",
        sql="CREATE TABLE IF NOT EXISTS migration_boundary_probe (id INTEGER PRIMARY KEY)",
    )
    runner = PostgresMigrationRunner(factory, migrations=(migration,))

    first = runner.apply()
    second = runner.apply()

    assert first == (9001,)
    assert second == ()

    with factory() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT version, name FROM schema_migrations WHERE version = 9001"
            )
            assert cursor.fetchone() == (9001, "test_migration_boundary")
            cursor.execute("DROP TABLE migration_boundary_probe")
            cursor.execute("DELETE FROM schema_migrations WHERE version = 9001")
        connection.commit()


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
