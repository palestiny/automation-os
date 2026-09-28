from pydantic import BaseModel


class ReviewDecisionRequest(BaseModel):
    expected_revision: str
    reason: str | None = None
