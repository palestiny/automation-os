from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.execution import ExecutionState


class ExecutionResponse(BaseModel):
    execution_id: UUID
    workflow_id: UUID
    current_step: int
    state: ExecutionState
    attempt: int
    started_at: datetime | None
    finished_at: datetime | None
