from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    sql: str


MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        name="initial_automation_os_schema",
        sql="""CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY,
    tenant_id UUID NULL,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS executions (
    id UUID PRIMARY KEY,
    workflow_id UUID NOT NULL,
    workflow_version_id UUID NULL,
    current_step INTEGER NOT NULL,
    state TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    started_at TIMESTAMPTZ NULL,
    finished_at TIMESTAMPTZ NULL
);

ALTER TABLE executions ADD COLUMN IF NOT EXISTS workflow_version_id UUID NULL;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS tenant_id UUID NULL;

CREATE TABLE IF NOT EXISTS workflow_versions (
    id UUID PRIMARY KEY,
    tenant_id UUID NULL,
    workflow_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    payload JSONB NOT NULL
);

ALTER TABLE workflow_versions ADD COLUMN IF NOT EXISTS tenant_id UUID NULL;
ALTER TABLE workflow_versions DROP CONSTRAINT IF EXISTS workflow_versions_workflow_id_version_number_key;
DROP INDEX IF EXISTS workflow_versions_tenant_workflow_version_uq;
CREATE UNIQUE INDEX IF NOT EXISTS workflow_versions_tenant_workflow_version_uq
    ON workflow_versions (tenant_id, workflow_id, version_number) NULLS NOT DISTINCT;

CREATE TABLE IF NOT EXISTS execution_idempotency (
    key TEXT PRIMARY KEY,
    workflow_id UUID NOT NULL,
    execution_id UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS marketplace_listings (
    id UUID PRIMARY KEY,
    tenant_id UUID NULL,
    workflow_id UUID NULL,
    workflow_version_id UUID NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    domain TEXT NOT NULL,
    supported_goals JSONB NOT NULL,
    tags JSONB NOT NULL,
    visibility TEXT NOT NULL,
    status TEXT NOT NULL
);

ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS tenant_id UUID NULL;
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS workflow_id UUID NULL;
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS workflow_version_id UUID NULL;
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS supported_goals JSONB;
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS tags JSONB;
ALTER TABLE marketplace_listings ALTER COLUMN workflow_id DROP NOT NULL;
ALTER TABLE marketplace_listings ALTER COLUMN workflow_version_id DROP NOT NULL;
ALTER TABLE marketplace_listings ADD COLUMN IF NOT EXISTS payload JSONB;
ALTER TABLE marketplace_listings ALTER COLUMN payload DROP NOT NULL;

CREATE TABLE IF NOT EXISTS review_decisions (
    id UUID PRIMARY KEY,
    tenant_id UUID NULL,
    workflow_id UUID NOT NULL,
    workflow_revision TEXT NOT NULL,
    reviewer_principal_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS review_decisions_tenant_key_uq
    ON review_decisions (tenant_id, idempotency_key) NULLS NOT DISTINCT;

CREATE TABLE IF NOT EXISTS connections (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    provider_id TEXT NOT NULL,
    reference TEXT NOT NULL,
    authentication_type TEXT NOT NULL,
    secret_reference TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS connections_tenant_provider_reference_uq
    ON connections (tenant_id, provider_id, reference);

CREATE TABLE IF NOT EXISTS execution_history (
    execution_id UUID NOT NULL,
    tenant_id UUID NULL,
    workflow_id UUID NOT NULL,
    sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    state TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (execution_id, sequence)
);""",
    ),
    Migration(
        version=2,
        name="execution_history_capability_outcome_evidence",
        sql="""
ALTER TABLE execution_history ADD COLUMN IF NOT EXISTS outcome TEXT NULL;
ALTER TABLE execution_history ADD COLUMN IF NOT EXISTS operation_id TEXT NULL;
ALTER TABLE execution_history ADD COLUMN IF NOT EXISTS diagnostic TEXT NULL;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS last_outcome TEXT NULL;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS last_operation_id TEXT NULL;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS last_idempotency_proven BOOLEAN NOT NULL DEFAULT FALSE;
""",
    ),
)


class PostgresMigrationRunner:
    """Applies versioned PostgreSQL schema migrations explicitly.

    Runtime dependency composition must not call this runner. Deployments/tests
    should apply migrations as an explicit database lifecycle step.
    """

    def __init__(self, connection_factory: Callable[[], psycopg.Connection], migrations: Sequence[Migration] = MIGRATIONS):
        self._connection_factory = connection_factory
        self._migrations = tuple(migrations)

    def apply(self) -> tuple[int, ...]:
        versions = [migration.version for migration in self._migrations]
        if versions != sorted(set(versions)):
            raise ValueError("Migration versions must be unique and strictly increasing")

        with self._connection_factory() as connection:
            self._ensure_migration_table(connection)
            applied = self._applied_versions(connection)
            newly_applied: list[int] = []

            for migration in self._migrations:
                if migration.version in applied:
                    continue

                with connection.transaction():
                    with connection.cursor() as cursor:
                        cursor.execute(migration.sql)
                        cursor.execute(
                            """
                            INSERT INTO schema_migrations (version, name)
                            VALUES (%s, %s)
                            """,
                            (migration.version, migration.name),
                        )
                newly_applied.append(migration.version)

            return tuple(newly_applied)

    @staticmethod
    def _ensure_migration_table(connection: psycopg.Connection) -> None:
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
        connection.commit()

    @staticmethod
    def _applied_versions(connection: psycopg.Connection) -> set[int]:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            return {int(row["version"]) for row in cursor.fetchall()}


def apply_postgres_migrations(connection_factory: Callable[[], psycopg.Connection]) -> tuple[int, ...]:
    """Convenience boundary for explicit deployment/test migration steps."""
    return PostgresMigrationRunner(connection_factory).apply()

    Migration(
        version=2,
        name="execution_history_capability_outcome_evidence",
        sql="""
ALTER TABLE execution_history ADD COLUMN IF NOT EXISTS outcome TEXT NULL;
ALTER TABLE execution_history ADD COLUMN IF NOT EXISTS operation_id TEXT NULL;
ALTER TABLE execution_history ADD COLUMN IF NOT EXISTS diagnostic TEXT NULL;
""",
    ),
