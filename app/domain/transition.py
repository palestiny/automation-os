from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class Transition:
    id: UUID
    source_step_id: UUID
    target_step_id: UUID
    condition: str | None = None

    @classmethod
    def create(
        cls,
        source_step_id: UUID,
        target_step_id: UUID,
        condition: str | None = None,
    ) -> "Transition":
        if source_step_id == target_step_id:
            raise ValueError("Transition cannot point to itself")

        if condition is not None and not condition.strip():
            raise ValueError("Transition condition cannot be blank")

        normalized_condition = condition.strip() if condition is not None else None

        return cls(
            id=uuid4(),
            source_step_id=source_step_id,
            target_step_id=target_step_id,
            condition=normalized_condition,
        )
