from __future__ import annotations

import json
from uuid import UUID

from psycopg.rows import dict_row

from app.domain.repositories import WorkflowRepository, WorkflowVersionRepository
from app.domain.workflow import Workflow, WorkflowState
from app.domain.workflow_version import WorkflowVersion
from app.infrastructure.persistence.postgres_mapping import (
    _workflow_from_row,
    _workflow_payload,
    _workflow_version_from_row,
)
from app.infrastructure.persistence.postgres_schema import ConnectionFactory


class PostgresWorkflowRepository(WorkflowRepository):
    def __init__(self, connection_factory: ConnectionFactory, tenant_id: UUID | None = None) -> None:
        self._connection_factory = connection_factory
        self._tenant_id = tenant_id

    def save(self, workflow: Workflow) -> None:
        if workflow.tenant_id != self._tenant_id:
            raise ValueError("Workflow belongs to a different tenant")
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
                    INSERT INTO workflows (id, tenant_id, name, state, payload)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        tenant_id = EXCLUDED.tenant_id,
                        name = EXCLUDED.name,
                        state = EXCLUDED.state,
                        payload = EXCLUDED.payload
                    WHERE workflows.tenant_id IS NOT DISTINCT FROM EXCLUDED.tenant_id
                    """,
                    (workflow.id, self._tenant_id, workflow.name, workflow.state.value, json.dumps(payload)),
                )
                if cursor.rowcount != 1:
                    raise ValueError("Workflow already belongs to a different tenant")
            connection.commit()

    def get(self, workflow_id: UUID) -> Workflow | None:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT id, tenant_id, name, state, payload FROM workflows WHERE id = %s AND (CAST(%s AS uuid) IS NULL OR tenant_id = %s)",
                    (workflow_id, self._tenant_id, self._tenant_id),
                )
                row = cursor.fetchone()
        return _workflow_from_row(row) if row else None

    def all(self) -> tuple[Workflow, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT id, tenant_id, name, state, payload FROM workflows WHERE (%s::uuid IS NULL OR tenant_id = %s) ORDER BY id", (self._tenant_id, self._tenant_id))
                rows = cursor.fetchall()
        return tuple(_workflow_from_row(row) for row in rows)



class PostgresWorkflowVersionRepository(WorkflowVersionRepository):
    def __init__(self, connection_factory: ConnectionFactory, tenant_id: UUID | None = None) -> None:
        self._connection_factory = connection_factory
        self._tenant_id = tenant_id

    def save(self, version: WorkflowVersion) -> None:
        if version.tenant_id != self._tenant_id:
            raise ValueError("Workflow version belongs to a different tenant")
        payload = _workflow_payload(version)
        with self._connection_factory() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO workflow_versions
                        (id, tenant_id, workflow_id, version_number, name, state, payload)
                    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (id) DO UPDATE SET
                        tenant_id = EXCLUDED.tenant_id,
                        name = EXCLUDED.name,
                        state = EXCLUDED.state,
                        payload = EXCLUDED.payload
                    WHERE workflow_versions.tenant_id IS NOT DISTINCT FROM EXCLUDED.tenant_id
                    """,
                    (
                        version.id,
                        version.tenant_id,
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
                    "SELECT id, tenant_id, workflow_id, version_number, name, state, payload "
                    "FROM workflow_versions WHERE id = %s AND tenant_id IS NOT DISTINCT FROM %s",
                    (version_id, self._tenant_id),
                )
                row = cursor.fetchone()
        return _workflow_version_from_row(row) if row else None


    def save_if_absent(self, version: WorkflowVersion) -> WorkflowVersion:
        if version.tenant_id != self._tenant_id:
            raise ValueError("Workflow version belongs to a different tenant")
        payload = _workflow_payload(version)
        with self._connection_factory() as connection:
            with connection.transaction():
                with connection.cursor(row_factory=dict_row) as cursor:
                    cursor.execute(
                        """
                        INSERT INTO workflow_versions
                            (id, tenant_id, workflow_id, version_number, name, state, payload)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (tenant_id, workflow_id, version_number) DO NOTHING
                        RETURNING id, tenant_id, workflow_id, version_number, name, state, payload
                        """,
                        (
                            version.id,
                            version.tenant_id,
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
                            SELECT id, tenant_id, workflow_id, version_number, name, state, payload
                            FROM workflow_versions
                            WHERE tenant_id IS NOT DISTINCT FROM %s AND workflow_id = %s AND version_number = %s
                            """,
                            (self._tenant_id, version.workflow_id, version.version_number),
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
                    SELECT id, tenant_id, workflow_id, version_number, name, state, payload
                    FROM workflow_versions
                    WHERE tenant_id IS NOT DISTINCT FROM %s AND workflow_id = %s AND state = %s
                    ORDER BY version_number DESC
                    LIMIT 1
                    """,
                    (self._tenant_id, workflow_id, WorkflowState.PUBLISHED.value),
                )
                row = cursor.fetchone()
        return _workflow_version_from_row(row) if row else None

    def all(self) -> tuple[WorkflowVersion, ...]:
        with self._connection_factory() as connection:
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    "SELECT id, tenant_id, workflow_id, version_number, name, state, payload "
                    "FROM workflow_versions WHERE tenant_id IS NOT DISTINCT FROM %s ORDER BY workflow_id, version_number",
                    (self._tenant_id,),
                )
                rows = cursor.fetchall()
        return tuple(_workflow_version_from_row(row) for row in rows)


