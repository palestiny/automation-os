from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.domain.connection import Connection, ConnectionRequirement, ConnectionStatus
from app.domain.execution import Execution, ExecutionState
from app.domain.execution_event import ExecutionEvent
from app.domain.marketplace import ListingStatus, ListingVisibility, MarketplaceListing
from app.domain.repositories import ExecutionIdempotencyRecord
from app.domain.review_decision import ReviewDecision, ReviewDecisionType
from app.domain.workflow import (
    Condition,
    Trigger,
    Workflow,
    WorkflowParameter,
    WorkflowState,
    WorkflowStep,
)
from app.domain.workflow_version import WorkflowVersion


def _execution_from_row(row: Any, events: tuple[ExecutionEvent, ...]) -> Execution:
    return Execution(
        id=row["id"],
        workflow_id=row["workflow_id"],
        workflow_version_id=row.get("workflow_version_id"),
        tenant_id=row.get("tenant_id"),
        current_step=row["current_step"],
        state=ExecutionState(row["state"]),
        attempt=row["attempt"],
        started_at=_to_domain_datetime(row["started_at"]),
        finished_at=_to_domain_datetime(row["finished_at"]),
        last_outcome=row.get("last_outcome"),
        last_operation_id=row.get("last_operation_id"),
        last_idempotency_proven=row.get("last_idempotency_proven", False),
        last_retryable=row.get("last_retryable", False),
        _events=list(events),
    )



def _connection_from_row(row: Any) -> Connection:
    return Connection(
        id=row["id"], tenant_id=row["tenant_id"], provider_id=row["provider_id"],
        reference=row["reference"], authentication_type=row["authentication_type"],
        secret_reference=row["secret_reference"], status=ConnectionStatus(row["status"]),
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def _marketplace_listing_from_row(row: Any) -> MarketplaceListing:
    return MarketplaceListing(
        id=row["id"],
        tenant_id=row["tenant_id"],
        workflow_id=row["workflow_id"],
        workflow_version_id=row["workflow_version_id"],
        title=row["title"],
        description=row["description"],
        domain=row["domain"],
        supported_goals=tuple(row["supported_goals"]),
        tags=tuple(row["tags"]),
        visibility=ListingVisibility(row["visibility"]),
        status=ListingStatus(row["status"]),
    )


def _review_decision_from_row(row: Any) -> ReviewDecision:
    return ReviewDecision(
        id=row["id"],
        workflow_id=row["workflow_id"],
        workflow_revision=row["workflow_revision"],
        tenant_id=row["tenant_id"],
        reviewer_principal_id=row["reviewer_principal_id"],
        decision=ReviewDecisionType(row["decision"]),
        reason=row["reason"],
        idempotency_key=row["idempotency_key"],
        created_at=row["created_at"],
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
        "connection_requirements": [
            {"provider_id": item.provider_id, "reference": item.reference}
            for item in getattr(workflow, "connection_requirements", ())
        ],
    }


def _workflow_version_from_row(row: Any) -> WorkflowVersion:
    payload = row["payload"]
    return WorkflowVersion(
        id=row["id"],
        workflow_id=row["workflow_id"],
        tenant_id=row["tenant_id"],
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
        _connection_requirements=tuple(
            ConnectionRequirement(provider_id=item["provider_id"], reference=item["reference"])
            for item in payload.get("connection_requirements", [])
        ),
    )


def _workflow_from_row(row: Any) -> Workflow:
    payload = row["payload"]
    return Workflow(
        id=row["id"],
        tenant_id=row.get("tenant_id"),
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
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)



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


