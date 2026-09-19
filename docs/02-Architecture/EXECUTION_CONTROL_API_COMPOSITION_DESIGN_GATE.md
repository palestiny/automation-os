# Execution Control API Composition Design Gate

## Status

Accepted / Implemented

## Purpose

Expose the already-verified Execution application boundaries through a thin HTTP composition layer.

This increment is an API adapter, not a new runtime model. The domain and application use cases remain authoritative for lifecycle rules and persistence.

## Committed Decisions

1. The API operates on an existing Execution identity supplied as a UUID path parameter.
2. ExecutionRepository remains the application source of truth.
3. The API composes existing application use cases for progress, cancellation, resume, retry, and retry-and-execute.
4. The API does not duplicate Execution state-transition rules.
5. Successful commands return the resulting Execution projection.
6. Missing executions map to HTTP 404.
7. Domain-invalid lifecycle transitions map to HTTP 409.
8. Repository/infrastructure failures are not reinterpreted by the API adapter.
9. The current in-memory repository is used as the composition dependency; replacing it with durable persistence is a separate infrastructure decision.
10. No authentication/authorization, background workers, queues, scheduler loop, event bus, or distributed coordination is introduced.
11. The existing legacy /jobs/{job_id} API remains untouched in this increment.

## API Surface

- GET /executions/{execution_id} — persisted execution progress.
- POST /executions/{execution_id}/cancel — cancel.
- POST /executions/{execution_id}/resume — resume.
- POST /executions/{execution_id}/retry — transition FAILED → RETRYING.
- POST /executions/{execution_id}/retry-and-execute — retry, start, and synchronously execute.

## Error Mapping

- Unknown execution → 404.
- Invalid lifecycle transition → 409.
- Successful command → 200.

## TDD Order

### RED

Prove the HTTP adapter maps each command to the existing application boundary, returns the expected projection, and maps missing/invalid executions without introducing lifecycle logic.

### GREEN

Implement thin routes, response schema, and dependency composition.

### REFACTOR

Keep HTTP concerns in app/api, lifecycle rules in app/domain, and orchestration in app/application.

## Explicitly Deferred

- Authentication and authorization.
- Durable database persistence.
- Background execution.
- Cancellation of already-running external processes.
- Retry scheduling, backoff, limits, and automatic retry.
- Events/webhooks.
- Distributed execution control.
