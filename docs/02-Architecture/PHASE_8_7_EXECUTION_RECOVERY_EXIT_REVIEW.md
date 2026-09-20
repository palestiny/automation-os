# Phase 8.7 — Execution Recovery Exit Review

## Status
**Completed — implementation merged to master and CI-verified**

## Scope Delivered

Phase 8.7 introduced an explicit application recovery boundary for executions that remain persisted in `RUNNING` after process/application failure.

Delivered:

- Configurable stale-timeout policy owned by the application recovery boundary.
- Stale `RUNNING → FAILED` recovery through the existing Execution lifecycle.
- No new `RECOVERING` lifecycle state.
- Recovery does not execute workflow steps and does not create a new execution.
- Recovery does not implicitly retry.
- `WAITING`, `RETRYING`, terminal, and other non-`RUNNING` states remain unchanged.
- Deterministic sequential batch recovery.
- Conditional persistence so a stale observation cannot overwrite a concurrent lifecycle transition.
- In-memory and PostgreSQL repository support for the conditional transition.
- Recovery evidence recorded through the existing append-only execution history.
- PostgreSQL integration coverage for conditional recovery and persisted recovery evidence.

## Verification

GitHub Actions workflow run **#1104** completed successfully for commit `91d29ebf7a10594ae8d1c5d02c943af8b094c5cc`.

The implementation therefore passed the repository's CI verification after the repository-contract test double was updated for the new `save_if_state` contract.

## Architectural Outcome

The accepted recovery lifecycle is:

`RUNNING → FAILED → RETRYING → RUNNING`

Recovery owns only the stale-state transition. Explicit retry remains the responsibility of the existing retry boundary, and workflow execution remains the responsibility of `ExecuteWorkflow`.

This keeps recovery, retry, and execution as separate application responsibilities and avoids silently replaying potentially side-effecting work after a crash.

## Deferred

The following remain intentionally outside Phase 8.7:

- automatic retry and backoff;
- background workers and scheduler loops;
- distributed queues/coordinators;
- heartbeats;
- leases or worker ownership;
- parallel/distributed recovery;
- workflow versioning;
- multi-tenancy and authorization;
- high-availability/replication operations.

## Exit Decision

Phase 8.7 committed scope is implemented, tested, documented, and CI-verified. The phase is complete.

The next work may proceed through a new Design Gate; no automatic retry/worker architecture is implied by this phase.
