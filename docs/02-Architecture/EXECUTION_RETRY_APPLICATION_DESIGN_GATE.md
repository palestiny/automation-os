# Execution Retry Application Boundary Design Gate

## Status

Accepted / Implemented

## Purpose

Expose the existing Execution retry invariant through an explicit application use case.

The domain already owns retry lifecycle rules. The application boundary resolves the persisted Execution, invokes Execution.retry(), persists the result, and returns it.

## Committed Decisions

1. Retry operates on an existing Execution identity.
2. ExecutionRepository is the source of truth.
3. The application use case delegates the transition to Execution.retry().
4. Only FAILED executions may transition to RETRYING.
5. A successful retry increments the domain-owned attempt counter and persists the result.
6. Missing executions produce an explicit application error.
7. Repository failures are propagated unchanged.
8. No second lifecycle state machine is introduced.
9. No workflow mutation or capability execution occurs.
10. Retry policy, backoff, automatic retry, worker scheduling, queues, events, and orchestration after RETRYING remain outside this increment.

## TDD Order

RED → GREEN → REFACTOR.

## Explicitly Deferred

- automatic retry policy;
- backoff and delay;
- retry limits;
- retry scheduling;
- worker/queue infrastructure;
- retry reason classification;
- durable retry metadata;
- event publication;
- automatic transition RETRYING → RUNNING.
