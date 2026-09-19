# Execution Cancellation Application Boundary Design Gate

## Status

Accepted / Implemented

## Purpose

Expose the existing Execution cancellation invariant through an explicit application use case.

The domain already owns cancellation rules. The application boundary resolves the persisted Execution, invokes that domain behavior, persists the result, and returns the cancelled Execution.

## Committed Decisions

1. Cancellation operates on an existing Execution identity.
2. ExecutionRepository is the source of truth for loading and persisting the runtime aggregate.
3. The application use case delegates the actual transition to Execution.cancel().
4. Domain rules remain authoritative: CREATED, RUNNING, and WAITING may be cancelled; FAILED, COMPLETED, and CANCELLED may not.
5. A successful cancellation is persisted after the domain transition.
6. Missing executions produce an explicit application error.
7. Repository failures are propagated; the use case does not catch and reinterpret infrastructure errors.
8. No second cancellation state machine is introduced.
9. No workflow mutation is performed.
10. No capability dispatch, retry, scheduling, worker, queue, event bus, or transaction abstraction is introduced.

## TDD Order

### RED

Prove:

- a persisted execution can be cancelled;
- the cancelled state and finished timestamp are preserved;
- missing executions are rejected;
- domain-invalid states are rejected;
- the repository contains the cancelled aggregate after success.

### GREEN

Implement the smallest application use case that loads, delegates to Execution.cancel(), persists, and returns.

### REFACTOR

Keep lifecycle rules in the domain and the use case as orchestration only.

## Explicitly Deferred

- cancellation reasons;
- cancellation authorization/permissions;
- cancellation events;
- distributed cancellation signals;
- worker interruption;
- compensation/rollback of already completed external side effects;
- transactional cancellation across external providers.
