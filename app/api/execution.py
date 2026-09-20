from uuid import UUID

from app.domain.execution import ExecutionState

from fastapi import APIRouter, Header, HTTPException

from app.application.execution_progress import ExecutionProgressNotFoundError
from app.core.execution_dependencies import (
    cancel_execution,
    execution_progress,
    discover_executions,
    start_workflow_execution,
    execution_repository,
    workflow_repository,
    resume_execution,
    retry_and_execute_execution,
    retry_execution,
)
from app.schemas.execution.response import ExecutionResponse

router = APIRouter(prefix="/executions", tags=["executions"])


@router.post("/workflows/{workflow_id}", response_model=ExecutionResponse)
def start_workflow_execution_endpoint(
    workflow_id: UUID,
    workflow_version_id: UUID | None = None,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    try:
        execution = start_workflow_execution.execute(
            workflow_id,
            idempotency_key=idempotency_key,
            workflow_version_id=workflow_version_id,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 404 if detail.startswith("Workflow not found") else 409
        raise HTTPException(status_code=status_code, detail=detail)
    return _response(execution.id)


def _ensure_exists(execution_id: UUID) -> None:
    if execution_repository.get(execution_id) is None:
        raise HTTPException(status_code=404, detail="Execution not found")


def _response(execution_id: UUID) -> ExecutionResponse:
    try:
        progress = execution_progress.execute(execution_id)
    except ExecutionProgressNotFoundError:
        raise HTTPException(status_code=404, detail="Execution not found")

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


@router.get("", response_model=list[ExecutionResponse])
def list_executions(
    workflow_id: UUID | None = None,
    state: ExecutionState | None = None,
):
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
        for progress in discover_executions.execute(
            workflow_id=workflow_id,
            state=state,
        )
    ]


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: UUID):
    return _response(execution_id)


@router.post("/{execution_id}/cancel", response_model=ExecutionResponse)
def cancel_execution_endpoint(execution_id: UUID):
    _ensure_exists(execution_id)
    try:
        cancel_execution.execute(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return _response(execution_id)


@router.post("/{execution_id}/resume", response_model=ExecutionResponse)
def resume_execution_endpoint(execution_id: UUID):
    _ensure_exists(execution_id)
    try:
        resume_execution.execute(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return _response(execution_id)


@router.post("/{execution_id}/retry", response_model=ExecutionResponse)
def retry_execution_endpoint(execution_id: UUID):
    _ensure_exists(execution_id)
    try:
        retry_execution.execute(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return _response(execution_id)


@router.post("/{execution_id}/retry-and-execute", response_model=ExecutionResponse)
def retry_and_execute_endpoint(execution_id: UUID):
    _ensure_exists(execution_id)
    try:
        retry_and_execute_execution.execute(execution_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return _response(execution_id)
