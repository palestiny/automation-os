from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException

from app.application.authorization import AuthorizationContext
from app.api.auth import get_authorization_context
from app.application.execution_progress import ExecutionProgressNotFoundError
from app.core.execution_dependencies import (
    ExecutionUseCases,
    build_execution_use_cases,
)
from app.domain.execution import ExecutionState
from app.schemas.execution.response import ExecutionResponse

router = APIRouter(prefix="/executions", tags=["executions"])


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ValueError):
        detail = str(exc)
        status_code = 404 if detail.startswith(("Workflow not found", "Execution not found")) else 409
        return HTTPException(status_code=status_code, detail=detail)
    if isinstance(exc, RuntimeError):
        return HTTPException(status_code=503, detail=str(exc))
    raise TypeError("Unsupported execution API exception mapping") from exc


def _response(
    execution_id: UUID,
    services: ExecutionUseCases,
) -> ExecutionResponse:
    try:
        progress = services.execution_progress.execute(execution_id)
    except ExecutionProgressNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Execution not found") from exc

    return ExecutionResponse(
        execution_id=progress.execution_id,
        workflow_id=progress.workflow_id,
        workflow_version_id=progress.workflow_version_id,
        current_step=progress.current_step,
        state=progress.state,
        attempt=progress.attempt,
        started_at=progress.started_at,
        finished_at=progress.finished_at,
    )


def _ensure_exists(execution_id: UUID, services: ExecutionUseCases) -> None:
    try:
        services.execution_progress.execute(execution_id)
    except ExecutionProgressNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Execution not found") from exc


@router.post("/workflows/{workflow_id}", response_model=ExecutionResponse)
def start_workflow_execution_endpoint(
    workflow_id: UUID,
    workflow_version_id: UUID | None = None,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        services = build_execution_use_cases(context)
        execution = services.start_workflow_execution.execute(
            workflow_id,
            idempotency_key=idempotency_key,
            workflow_version_id=workflow_version_id,
        )
        return _response(execution.id, services)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("", response_model=list[ExecutionResponse])
def list_executions(
    workflow_id: UUID | None = None,
    state: ExecutionState | None = None,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        services = build_execution_use_cases(context)
        return [
            ExecutionResponse(
                execution_id=progress.execution_id,
                workflow_id=progress.workflow_id,
                workflow_version_id=progress.workflow_version_id,
                current_step=progress.current_step,
                state=progress.state,
                attempt=progress.attempt,
                started_at=progress.started_at,
                finished_at=progress.finished_at,
            )
            for progress in services.discover_executions.execute(
                workflow_id=workflow_id,
                state=state,
            )
        ]
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(
    execution_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        services = build_execution_use_cases(context)
        return _response(execution_id, services)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
def cancel_execution_endpoint(
    execution_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        services = build_execution_use_cases(context)
        _ensure_exists(execution_id, services)
        services.cancel_execution.execute(execution_id)
        return _response(execution_id, services)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/{execution_id}/resume", response_model=ExecutionResponse)
def resume_execution_endpoint(
    execution_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        services = build_execution_use_cases(context)
        _ensure_exists(execution_id, services)
        services.resume_execution.execute(execution_id)
        return _response(execution_id, services)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/{execution_id}/retry", response_model=ExecutionResponse)
def retry_execution_endpoint(
    execution_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        services = build_execution_use_cases(context)
        _ensure_exists(execution_id, services)
        services.retry_execution.execute(execution_id)
        return _response(execution_id, services)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/{execution_id}/retry-and-execute", response_model=ExecutionResponse)
def retry_and_execute_endpoint(
    execution_id: UUID,
    context: AuthorizationContext = Depends(get_authorization_context),
):
    try:
        services = build_execution_use_cases(context)
        _ensure_exists(execution_id, services)
        services.retry_and_execute_execution.execute(execution_id)
        return _response(execution_id, services)
    except Exception as exc:
        raise _map_error(exc) from exc
