from datetime import datetime
from pydantic import BaseModel


class JobResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):

    id: str

    status: str

    progress: int

    title: str | None = None

    message: str

    error: str | None = None

    created_at: str

    updated_at: str