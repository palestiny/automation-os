# ADR-004 — Execution Aggregate Semantics

## Status

Accepted

## Context

Execution is the central runtime domain concept of Automation OS. Before expanding the Execution Engine, its lifecycle and ownership semantics must be explicit so that orchestration, retry policy, and capability execution do not leak into the aggregate.

## Decision

The Execution aggregate owns its runtime lifecycle invariants and progress, with the following semantics:

1. `current_step = 0` represents the first/current step. `complete_step()` advances the execution to the next step.
2. `FAILED` represents failure of the current execution attempt, not necessarily permanent failure of the Execution. Retry follows `FAILED → RETRYING → RUNNING`.
3. `started_at` records the first time the Execution starts and remains unchanged across retries.
4. `WAITING` means the Execution cannot continue at the moment but has not failed or completed. The reason for waiting is not encoded in `ExecutionState`; detailed waiting context belongs to Execution Context.
5. Workflow completion is determined outside the Execution aggregate, by the Orchestrator using the Workflow definition. Execution does not own workflow step-count knowledge.

## Consequences

- Execution remains responsible for lifecycle transitions, progress, attempt count, and lifecycle timestamps.
- Retry policy remains outside the aggregate.
- Workflow definition remains separate from runtime state.
- Provider-specific waiting/failure details do not become Execution states.
- The Orchestrator remains responsible for deciding when the workflow as a whole is complete.
- Additional attempt-specific timestamps or retry metadata are deferred until an actual requirement exists.

## Review Trigger

Revisit this decision if execution history requires per-attempt timestamps, if waiting reasons become part of aggregate invariants, or if workflow completion semantics require information that cannot be supplied by the Orchestrator from the Workflow definition.
