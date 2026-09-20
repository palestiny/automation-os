from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from app.domain.execution import Execution, ExecutionState
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.execution_event import ExecutionEvent
from app.domain.repositories import (
    ExecutionHistoryRepository,
    MarketplaceListingRepository,
    ExecutionIdempotencyRecord,
    ExecutionIdempotencyRepository,
    ExecutionStartRepository,
    ExecutionRepository,
    WorkflowRepository,
    WorkflowVersionRepository,
)
from app.domain.workflow import (
    Condition,
    Trigger,
    Workflow,
    WorkflowParameter,
    WorkflowState,
    WorkflowStep,
)
from app.domain.workflow_version import WorkflowVersion


ConnectionFactory = Callable[[], psycopg.Connection[Any]]


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS workflows (
    id UUID PRIMARY KEY,
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

CREATE TABLE IF NOT EXISTS workflow_versions (
    id UUID PRIMARY KEY,
    workflow_id UUID NOT NULL,
    version_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    state TEXT NOT NULL,
    payload JSONB NOT NULL,
    UNIQUE (workflow_id, version_number)
);

CREATE TABLE IF NOT EXISTS execution_idempotency (
    key TEXT PRIMARY KEY,
    workflow_id UUID NOT NULL,
    execution_id UUID NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS marketplace_listings (
    id UUID PRIMARY KEY,
    workflow_id UUID NOT NULL,
    workflow_version_id UUID NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    domain TEXT NOT NULL,
    supported_goals JSONB NOT NULL,
    tags JSONB NOT NULL,
    visibility TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_history (
    execution_id UUID NOT NULL,
    workflow_id UUID NOT NULL,
    sequence INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    state TEXT NOT NULL,
    attempt INTEGER NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (execution_id, sequence)
);
"""


class PostgresSchema:
    """Bootstrap the minimum Phase 8.6 PostgreSQL schema."""

    @staticmethod
    def initialize(connection: psycopg.Connection[Any]) -> None:
        with connection.cursor() as cursor:
            cursor.execute(SCHEMA_SQL)
        connection.commit()


class PostgresMarketplaceListingRepository(MarketplaceListingRepository):
    """PostgreSQL adapter for durable marketplace catalog listings."""

    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def save(self, listing: MarketplaceListing) -> None:
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO marketplace_listings
                        (id, workflow_id, workflow_version_id, title, description, domain,
                         supported_goals, tags, visibility, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        workflow_id = EXCLUDED.workflow_id,
                        workflow_version_id = EXCLUDED.workflow_version_id,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        domain = EXCLUDED.domain,
                        supported_goals = EXCLUDED.supported_goals,
                        tags = EXCLUDED.tags,
                        visibility = EXCLUDED.visibility,
                        status = EXCLUDED.status
                    """,
                    (
                        listing.id, listing.workflow_id, listing.workflow_version_id,
                        listing.title, listing.description, listing.domain,
                        json.dumps(list(listing.supported_goals)), json.dumps(list(listing.tags)),
                        listing.visibility.value, listing.status.value,
                    ),
                )
            connection.commit()

    def get(self, listing_id: UUID) -> MarketplaceListing | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT id, workflow_id, workflow_version_id, title, description, domain, supported_goals, tags, visibility, status FROM marketplace_listings WHERE id = %s", (listing_id,))
                row = cursor.fetchone()
        return _marketplace_listing_from_row(row) if row else None

    def all(self) -> tuple[MarketplaceListing, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT id, workflow_id, workflow_version_id, title, description, domain, supported_goals, tags, visibility, status FROM marketplace_listings ORDER BY id")
                rows = cursor.fetchall()
        return tuple(_marketplace_listing_from_row(row) for row in rows)


class PostgresWorkflowRepository(WorkflowRepository):
    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def save(self, workflow: Workflow) -> None:
        payload = {
            "steps": [
                {
                    "id": str(step.id),
                    "name": step.name,
                    "capability": step.capability,
                    "condition": (
                        {
                            "left_operand": step.condition.left_operand,
                            "operator": step.condition.operator,
                            "right_operand": step.condition.right_operand,
                        }
                        if step.condition
                        else None
                    ),
                }
                for step in workflow.steps
            ],
            "triggers": [{"event_type": trigger.event_type} for trigger in workflow.triggers],
            "supported_goals": list(workflow.supported_goals),
            "required_parameters": list(workflow.required_parameters),
            "parameter_types": [
                {"name": parameter.name, "type": parameter.type}
                for parameter in workflow.parameter_types
            ],
            "automation_domain": workflow.automation_domain,
            "discovery_tags": list(workflow.discovery_tags),
        }
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO workflows (id, name, state, payload)
                    VALUES (%s, %s, %s, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        state = EXCLUDED.state,
                        payload = EXCLUDED.payload
                    """,
                    (workflow.id, workflow.name, workflow.state.value, json.dumps(payload)),
                )
            connection.commit()

    def get(self, workflow_id: UUID) -> Workflow | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT id, name, state, payload FROM workflows WHERE id = %s",
                    (workflow_id,),
                )
                row = cursor.fetchone()
        return _workflow_from_row(row) if row else None

    def all(self) -> tuple[Workflow, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT id, name, state, payload FROM workflows ORDER BY id")
                rows = cursor.fetchall()
        return tuple(_workflow_from_row(row) for row in rows)



class PostgresWorkflowVersionRepository(WorkflowVersionRepository):
    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def save(self, version: WorkflowVersion) -> None:
        payload = _workflow_payload(version)
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO workflow_versions
                        (id, workflow_id, version_number, name, state, payload)
                    VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        state = EXCLUDED.state,
                        payload = EXCLUDED.payload
                    """,
                    (
                        version.id,
                        version.workflow_id,
                        version.version_number,
                        version.name,
                        version.state.value,
                        json.dumps(payload),
                    ),
                )
            connection.commit()

    def get(self, version_id: UUID) -> WorkflowVersion | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT id, workflow_id, version_number, name, state, payload "
                    "FROM workflow_versions WHERE id = %s",
                    (version_id,),
                )
                row = cursor.fetchone()
        return _workflow_version_from_row(row) if row else None


    def save_if_absent(self, version: WorkflowVersion) -> WorkflowVersion:
        payload = _workflow_payload(version)
        with self._connection_factory() as connection:
            with connection.transaction():
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO workflow_versions
                            (id, workflow_id, version_number, name, state, payload)
                        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (workflow_id, version_number) DO NOTHING
                        RETURNING id, workflow_id, version_number, name, state, payload
                        """,
                        (
                            version.id,
                            version.workflow_id,
                            version.version_number,
                            version.name,
                            version.state.value,
                            json.dumps(payload),
                        ),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        cursor.execute(
                            """
                            SELECT id, workflow_id, version_number, name, state, payload
                            FROM workflow_versions
                            WHERE workflow_id = %s AND version_number = %s
                            """,
                            (version.workflow_id, version.version_number),
                        )
                        row = cursor.fetchone()
                    if row is None:
                        raise RuntimeError("Failed to materialize workflow version")
        return _workflow_version_from_row(row)

    def latest_published(self, workflow_id: UUID) -> WorkflowVersion | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, workflow_id, version_number, name, state, payload
                    FROM workflow_versions
                    WHERE workflow_id = %s AND state = %s
                    ORDER BY version_number DESC
                    LIMIT 1
                    """,
                    (workflow_id, WorkflowState.PUBLISHED.value),
                )
                row = cursor.fetchone()
        return _workflow_version_from_row(row) if row else None

    def all(self) -> tuple[WorkflowVersion, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT id, workflow_id, version_number, name, state, payload "
                    "FROM workflow_versions ORDER BY workflow_id, version_number"
                )
                rows = cursor.fetchall()
        return tuple(_workflow_version_from_row(row) for row in rows)


class PostgresExecutionRepository(ExecutionRepository):
    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def save(self, execution: Execution) -> None:
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                _upsert_execution(cursor, execution)
                _append_events(cursor, execution.events)
            connection.commit()

    def save_if_state(
        self,
        execution: Execution,
        expected_state: ExecutionState,
    ) -> bool:
        with self._connection_factory() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE executions
                        SET workflow_id = %s,
                            workflow_version_id = %s,
                            current_step = %s,
                            state = %s,
                            attempt = %s,
                            started_at = %s,
                            finished_at = %s
                        WHERE id = %s AND state = %s
                        """,
                        (
                            execution.workflow_id,
                            execution.workflow_version_id,
                            execution.current_step,
                            execution.state.value,
                            execution.attempt,
                            execution.started_at,
                            execution.finished_at,
                            execution.id,
                            expected_state.value,
                        ),
                    )
                    if cursor.rowcount != 1:
                        return False
                    _append_events(cursor, execution.events)
            return True

    def get(self, execution_id: UUID) -> Execution | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, workflow_id, workflow_version_id, current_step, state, attempt, started_at, finished_at
                    FROM executions WHERE id = %s
                    """,
                    (execution_id,),
                )
                row = cursor.fetchone()
                events = _fetch_events(cursor, execution_id)
        return _execution_from_row(row, events) if row else None

    def all(self) -> tuple[Execution, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id, workflow_id, workflow_version_id, current_step, state, attempt, started_at, finished_at
                    FROM executions ORDER BY id
                    """
                )
                rows = cursor.fetchall()
                event_rows = {}
                for row in rows:
                    event_rows[row["id"]] = _fetch_events(cursor, row["id"])
        return tuple(_execution_from_row(row, event_rows[row["id"]]) for row in rows)


class PostgresExecutionIdempotencyRepository(ExecutionIdempotencyRepository):
    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def get(self, key: str) -> ExecutionIdempotencyRecord | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT key, workflow_id, execution_id, created_at
                    FROM execution_idempotency WHERE key = %s
                    """,
                    (key,),
                )
                row = cursor.fetchone()
        return _idempotency_from_row(row) if row else None

    def reserve(
        self,
        key: str,
        workflow_id: UUID,
        execution_id: UUID,
    ) -> tuple[ExecutionIdempotencyRecord, bool]:
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO execution_idempotency
                        (key, workflow_id, execution_id, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO NOTHING
                    RETURNING key, workflow_id, execution_id, created_at
                    """,
                    (key, workflow_id, execution_id, datetime.now()),
                )
                row = cursor.fetchone()
                if row is None:
                    cursor.execute(
                        """
                        SELECT key, workflow_id, execution_id, created_at
                        FROM execution_idempotency WHERE key = %s
                        """,
                        (key,),
                    )
                    row = cursor.fetchone()
                    created = False
                else:
                    created = True
            connection.commit()
        if row is None:
            raise RuntimeError("Failed to persist idempotency record")
        return _idempotency_tuple(row), created

    def release(self, key: str, execution_id: UUID) -> None:
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM execution_idempotency
                    WHERE key = %s AND execution_id = %s
                    """,
                    (key, execution_id),
                )
            connection.commit()


class PostgresExecutionStartRepository(ExecutionStartRepository):
    """Atomic workflow-start boundary owned by one PostgreSQL transaction."""

    def __init__(
        self,
        connection_factory: ConnectionFactory,
    ) -> None:
        self._connection_factory = connection_factory

    def get_idempotent(self, key: str, workflow_id: UUID) -> Execution | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT key, workflow_id, execution_id, created_at
                    FROM execution_idempotency WHERE key = %s
                    """,
                    (key,),
                )
                record = cursor.fetchone()
                if record is None:
                    return None
                if record["workflow_id"] != workflow_id:
                    raise ValueError(
                        "Idempotency key is already associated with a different workflow"
                    )
                cursor.execute(
                    """
                    SELECT id, workflow_id, workflow_version_id, current_step, state, attempt, started_at, finished_at
                    FROM executions WHERE id = %s
                    """,
                    (record["execution_id"],),
                )
                execution = cursor.fetchone()
                if execution is None:
                    raise RuntimeError("Idempotency record references a missing execution")
                events = _fetch_events(cursor, record["execution_id"])
        return _execution_from_row(execution, events)

    def save_idempotent(
        self,
        execution: Execution,
        key: str,
    ) -> tuple[ExecutionIdempotencyRecord, bool]:
        with self._connection_factory() as connection:
            with connection.transaction():
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO execution_idempotency
                            (key, workflow_id, execution_id, created_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (key) DO NOTHING
                        RETURNING key, workflow_id, execution_id, created_at
                        """,
                        (
                            key,
                            execution.workflow_id,
                            execution.id,
                            datetime.now(),
                        ),
                    )
                    record = cursor.fetchone()
                    if record is not None:
                        _upsert_execution(cursor, execution)
                        _append_events(cursor, execution.events)
                        return _idempotency_from_row(record), True

                    cursor.execute(
                        """
                        SELECT key, workflow_id, execution_id, created_at
                        FROM execution_idempotency WHERE key = %s
                        """,
                        (key,),
                    )
                    existing = cursor.fetchone()
                    if existing is None:
                        raise RuntimeError("Failed to read existing idempotency record")
                    if existing["workflow_id"] != execution.workflow_id:
                        return _idempotency_from_row(existing), False

                    return _idempotency_from_row(existing), False


class PostgresExecutionHistoryRepository(ExecutionHistoryRepository):
    def __init__(self, connection_factory: ConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def append(self, event: ExecutionEvent) -> None:
        with self._connection_factory() as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    _insert_event(cursor, event)

    def list(self, execution_id: UUID) -> tuple[ExecutionEvent, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                rows = _fetch_events(cursor, execution_id)
        return tuple(rows)


def postgres_connection_factory(database_url: str | None = None) -> ConnectionFactory:
    url = database_url or os.environ.get("AUTOMATION_OS_DATABASE_URL")
    if not url:
        raise RuntimeError("AUTOMATION_OS_DATABASE_URL is required for PostgreSQL persistence")
    return lambda: psycopg.connect(url)


def _upsert_execution(cursor: Any, execution: Execution) -> None:
    cursor.execute(
        """
        INSERT INTO executions
            (id, workflow_id, workflow_version_id, current_step, state, attempt, started_at, finished_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            workflow_id = EXCLUDED.workflow_id,
            workflow_version_id = EXCLUDED.workflow_version_id,
            current_step = EXCLUDED.current_step,
            state = EXCLUDED.state,
            attempt = EXCLUDED.attempt,
            started_at = EXCLUDED.started_at,
            finished_at = EXCLUDED.finished_at
        """,
        (
            execution.id,
            execution.workflow_id,
            execution.workflow_version_id,
            execution.current_step,
            execution.state.value,
            execution.attempt,
            execution.started_at,
            execution.finished_at,
        ),
    )


def _append_events(cursor: Any, events: tuple[ExecutionEvent, ...]) -> None:
    for event in events:
        _insert_event(cursor, event)


def _insert_event(cursor: Any, event: ExecutionEvent) -> None:
    cursor.execute(
        """
        SELECT workflow_id, event_type, state, attempt, occurred_at
        FROM execution_history
        WHERE execution_id = %s AND sequence = %s
        """,
        (event.execution_id, event.sequence),
    )
    existing = cursor.fetchone()
    if existing is not None:
        if (
            _row_value(existing, "workflow_id", 0) != event.workflow_id
            or _row_value(existing, "event_type", 1) != event.event_type
            or _row_value(existing, "state", 2) != event.state.value
            or _row_value(existing, "attempt", 3) != event.attempt
            or _to_domain_datetime(_row_value(existing, "occurred_at", 4)) != event.occurred_at
        ):
            raise ValueError(
                "Execution history sequence already contains a different event"
            )
        return

    cursor.execute(
        """
        SELECT COALESCE(MAX(sequence), 0)
        FROM execution_history
        WHERE execution_id = %s
        """,
        (event.execution_id,),
    )
    latest_sequence = _row_value(cursor.fetchone(), "coalesce", 0)
    if event.sequence != latest_sequence + 1:
        raise ValueError("Execution history sequence must be appended in order")

    cursor.execute(
        """
        INSERT INTO execution_history
            (execution_id, workflow_id, sequence, event_type, state, attempt, occurred_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            event.execution_id,
            event.workflow_id,
            event.sequence,
            event.event_type,
            event.state.value,
            event.attempt,
            event.occurred_at,
        ),
    )


def _fetch_events(cursor: Any, execution_id: UUID) -> tuple[ExecutionEvent, ...]:
    cursor.execute(
        """
        SELECT execution_id, workflow_id, sequence, event_type, state, attempt, occurred_at
        FROM execution_history
        WHERE execution_id = %s
        ORDER BY sequence
        """,
        (execution_id,),
    )
    return tuple(
        ExecutionEvent(
            execution_id=row["execution_id"],
            workflow_id=row["workflow_id"],
            sequence=row["sequence"],
            event_type=row["event_type"],
            state=ExecutionState(row["state"]),
            attempt=row["attempt"],
            occurred_at=_to_domain_datetime(row["occurred_at"]),
        )
        for row in cursor.fetchall()
    )


def _execution_from_row(row: Any, events: tuple[ExecutionEvent, ...]) -> Execution:
    return Execution(
        id=row["id"],
        workflow_id=row["workflow_id"],
        workflow_version_id=row.get("workflow_version_id"),
        current_step=row["current_step"],
        state=ExecutionState(row["state"]),
        attempt=row["attempt"],
        started_at=_to_domain_datetime(row["started_at"]),
        finished_at=_to_domain_datetime(row["finished_at"]),
        _events=list(events),
    )




def _marketplace_listing_from_row(row: Any) -> MarketplaceListing:
    return MarketplaceListing(
        id=row["id"],
        workflow_id=row["workflow_id"],
        workflow_version_id=row.get("workflow_version_id"),
        title=row["title"],
        description=row["description"],
        domain=row["domain"],
        supported_goals=tuple(row["supported_goals"]),
        tags=tuple(row["tags"]),
        visibility=ListingVisibility(row["visibility"]),
        status=ListingStatus(row["status"]),
    )

def _workflow_payload(workflow: Workflow | WorkflowVersion) -> dict[str, Any]:
    return {
        "steps": [
            {
                "id": str(step.id),
                "name": step.name,
                "capability": step.capability,
                "condition": (
                    {
                        "left_operand": step.condition.left_operand,
                        "operator": step.condition.operator,
                        "right_operand": step.condition.right_operand,
                    }
                    if step.condition
                    else None
                ),
            }
            for step in workflow.steps
        ],
        "triggers": [{"event_type": trigger.event_type} for trigger in workflow.triggers],
        "supported_goals": list(workflow.supported_goals),
        "required_parameters": list(workflow.required_parameters),
        "parameter_types": [
            {"name": parameter.name, "type": parameter.type}
            for parameter in workflow.parameter_types
        ],
        "automation_domain": workflow.automation_domain,
        "discovery_tags": list(workflow.discovery_tags),
    }


def _workflow_version_from_row(row: Any) -> WorkflowVersion:
    payload = row["payload"]
    return WorkflowVersion(
        id=row["id"],
        workflow_id=row["workflow_id"],
        version_number=row["version_number"],
        name=row["name"],
        _steps=[
            WorkflowStep(
                id=UUID(step["id"]),
                name=step["name"],
                capability=step["capability"],
                condition=(
                    Condition(
                        left_operand=step["condition"]["left_operand"],
                        operator=step["condition"]["operator"],
                        right_operand=step["condition"]["right_operand"],
                    )
                    if step["condition"]
                    else None
                ),
            )
            for step in payload["steps"]
        ],
        state=WorkflowState(row["state"]),
        _triggers=[Trigger(event_type=item["event_type"]) for item in payload["triggers"]],
        _supported_goals=tuple(payload["supported_goals"]),
        _required_parameters=tuple(payload["required_parameters"]),
        _parameter_types=tuple(
            WorkflowParameter(name=item["name"], type=item["type"])
            for item in payload["parameter_types"]
        ),
        _automation_domain=payload["automation_domain"],
        _discovery_tags=tuple(payload["discovery_tags"]),
    )


def _workflow_from_row(row: Any) -> Workflow:
    payload = row["payload"]
    return Workflow(
        id=row["id"],
        name=row["name"],
        _steps=[
            WorkflowStep(
                id=UUID(step["id"]),
                name=step["name"],
                capability=step["capability"],
                condition=(
                    Condition(
                        left_operand=step["condition"]["left_operand"],
                        operator=step["condition"]["operator"],
                        right_operand=step["condition"]["right_operand"],
                    )
                    if step["condition"]
                    else None
                ),
            )
            for step in payload["steps"]
        ],
        state=WorkflowState(row["state"]),
        _triggers=[Trigger(event_type=item["event_type"]) for item in payload["triggers"]],
        _supported_goals=tuple(payload["supported_goals"]),
        _required_parameters=tuple(payload["required_parameters"]),
        _parameter_types=tuple(
            WorkflowParameter(name=item["name"], type=item["type"])
            for item in payload["parameter_types"]
        ),
        _automation_domain=payload["automation_domain"],
        _discovery_tags=tuple(payload["discovery_tags"]),
    )




def _row_value(row: Any, key: str, index: int) -> Any:
    if isinstance(row, dict):
        return row[key]
    return row[index]


def _to_domain_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _idempotency_from_row(row: Any) -> ExecutionIdempotencyRecord:
    return ExecutionIdempotencyRecord(
        key=row["key"],
        workflow_id=row["workflow_id"],
        execution_id=row["execution_id"],
        created_at=_to_domain_datetime(row["created_at"]),
    )


def _idempotency_tuple(row: Any) -> ExecutionIdempotencyRecord:
    if isinstance(row, dict):
        return _idempotency_from_row(row)
    return ExecutionIdempotencyRecord(
        key=row[0],
        workflow_id=row[1],
        execution_id=row[2],
        created_at=row[3],
    )
