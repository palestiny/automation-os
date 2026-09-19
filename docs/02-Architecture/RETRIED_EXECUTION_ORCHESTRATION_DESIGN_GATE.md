# Retried Execution Orchestration Design Gate

## Status

Accepted / Implemented

## Purpose

Define the explicit application composition for a caller-requested retry: FAILED → RETRYING → RUNNING → existing workflow orchestration.

## Committed Decisions

1. Retry remains owned by RetryExecution.
2. Starting a RETRYING execution remains owned by the existing Execution.start() lifecycle through a small application boundary.
3. Workflow execution remains owned by ExecuteWorkflow.
4. The composition performs no automatic retry; it runs only when explicitly invoked.
5. A new ExecutionContext is created for the retry execution.
6. Existing step, capability, condition, failure and persistence boundaries remain unchanged.
7. The retry attempt is incremented by Execution.retry().
8. No retry policy, backoff, retry limit, scheduler, worker, queue or event infrastructure is introduced.
9. No durable context from the failed attempt is restored.
10. The composition returns the final Execution or propagates the existing execution failure.

## Result Contract

**FAILED → RetryExecution → RETRYING → StartRetryingExecution → RUNNING → ExecuteWorkflow → COMPLETED / FAILED**

## TDD Order

RED → GREEN → REFACTOR.

## Explicitly Deferred

- automatic retries;
- backoff/delay;
- retry limits;
- retry scheduling;
- durable retry context;
- worker/queue infrastructure;
- retry classification;
- events;
- compensation of external side effects.
