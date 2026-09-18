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

    @classmethod
    def combine(cls, *catalogs: "IntentGoalCatalog") -> "IntentGoalCatalog":
        if any(not isinstance(catalog, cls) for catalog in catalogs):
            raise TypeError("All catalogs must be IntentGoalCatalog instances")

        goals: list[str] = []
        for catalog in catalogs:
            duplicates = set(goals).intersection(catalog.goals)
            if duplicates:
                duplicate = sorted(duplicates)[0]
                raise ValueError(f"Duplicate intent goal: {duplicate}")
            goals.extend(catalog.goals)

        return cls(tuple(goals))

    def contains(self, goal: str) -> bool:
        return goal in self.goals
