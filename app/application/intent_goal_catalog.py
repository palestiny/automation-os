from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntentGoalCatalog:
    """Provider-neutral catalog of canonical goals accepted by the platform."""

    goals: tuple[str, ...]

    def __post_init__(self) -> None:
        if any(not isinstance(goal, str) or not goal.strip() for goal in self.goals):
            raise ValueError("Intent goals must be non-empty strings")
        if len(set(self.goals)) != len(self.goals):
            raise ValueError("Intent goals must be unique")

    @classmethod
    def create(cls, goals: list[str] | tuple[str, ...]) -> "IntentGoalCatalog":
        return cls(tuple(goal.strip() for goal in goals))

    def contains(self, goal: str) -> bool:
        return goal in self.goals
