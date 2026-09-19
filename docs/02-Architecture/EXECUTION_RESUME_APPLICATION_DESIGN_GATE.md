# Execution Resume Application Boundary Design Gate

## Status

Accepted / Implemented

## Purpose

Expose the existing Execution resume invariant through an explicit application use case.

The domain already owns the WAITING → RUNNING transition. The application boundary resolves the persisted Execution, delegates to Execution.resume(), persists the result, and returns it.

## Committed Decisions

1. Resume operates on an existing Execution identity.
2. ExecutionRepository is the lifecycle source of truth.
3. The use case delegates the transition to Execution.resume().
4. Only WAITING executions may resume; all other lifecycle validation remains in the domain.
5. A successful resume is persisted.
6. Missing executions produce an explicit application error.
7. No capability execution occurs during resume.
8. No scheduler, worker, retry, queue, event, or second lifecycle abstraction is introduced.

## TDD Order

RED → GREEN → REFACTOR.

Tests prove successful WAITING → RUNNING persistence, missing execution rejection, and invalid-state rejection.

## Explicitly Deferred

- automatic resume;
- resume authorization;
- resume scheduling;
- worker wake-up/signals;
- distributed coordination;
- persisted suspension reasons.
