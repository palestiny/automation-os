from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier
from uuid import uuid4

import psycopg
import pytest

from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.infrastructure.persistence.migrations import PostgresMigrationRunner
from app.infrastructure.persistence.postgres import (
    PostgresExecutionHistoryRepository,
    postgres_connection_factory,
)


DATABASE_URL = os.environ.get("AUTOMATION_OS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="AUTOMATION_OS_TEST_DATABASE_URL is required for PostgreSQL persistence tests",
)


def test_concurrent_history_append_preserves_unique_sequence_without_duplicate_rows():
    factory = postgres_connection_factory(DATABASE_URL)
    PostgresMigrationRunner(factory).apply()

    execution = Execution.create(uuid4())
    execution.start()
    first_event = execution.events[0]
    history = PostgresExecutionHistoryRepository(factory)
    history.append(first_event)

    execution_id = execution.id
    workflow_id = execution.workflow_id
    occurred_at = datetime.now(timezone.utc)
    barrier = Barrier(2)

    event_a = ExecutionEvent(
        execution_id=execution_id,
        workflow_id=workflow_id,
        sequence=2,
        event_type="concurrent.a",
        state=ExecutionState.RUNNING,
        attempt=1,
        occurred_at=occurred_at,
    )
    event_b = ExecutionEvent(
        execution_id=execution_id,
        workflow_id=workflow_id,
        sequence=2,
        event_type="concurrent.b",
        state=ExecutionState.RUNNING,
        attempt=1,
        occurred_at=occurred_at,
    )

    setup = factory()
    try:
        with setup.cursor() as cursor:
            cursor.execute(
                """
                CREATE OR REPLACE FUNCTION automation_os_test_delay_history_insert()
                RETURNS trigger
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    PERFORM pg_sleep(0.5);
                    RETURN NEW;
                END;
                $$
                """
            )
            cursor.execute(
                """
                CREATE TRIGGER automation_os_test_delay_history_insert
                BEFORE INSERT ON execution_history
                FOR EACH ROW
                EXECUTE FUNCTION automation_os_test_delay_history_insert()
                """
            )
        setup.commit()

        def append(event: ExecutionEvent):
            barrier.wait(timeout=10)
            try:
                history.append(event)
                return "committed"
            except psycopg.errors.UniqueViolation:
                return "unique_violation"

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = tuple(pool.map(append, (event_a, event_b)))

        assert sorted(results) == ["committed", "unique_violation"]

        persisted = history.list(execution_id)
        assert [event.sequence for event in persisted] == [1, 2]
        assert len({event.sequence for event in persisted}) == len(persisted)
        assert persisted[1].event_type in {"concurrent.a", "concurrent.b"}
    finally:
        with setup.cursor() as cursor:
            cursor.execute(
                "DROP TRIGGER IF EXISTS automation_os_test_delay_history_insert ON execution_history"
            )
            cursor.execute(
                "DROP FUNCTION IF EXISTS automation_os_test_delay_history_insert()"
            )
        setup.commit()
