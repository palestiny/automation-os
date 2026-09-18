# Execution State Machine

Status: Active contract

The Execution aggregate owns execution lifecycle transitions. The application layer may coordinate these transitions, but it must not bypass the aggregate's lifecycle rules.

## States

| State | Meaning | Lifecycle role |
|---|---|---|
| CREATED | Execution has been created but not started | Active |
| RUNNING | Execution is actively processing | Active |
| WAITING | Execution is paused and can resume | Active |
| RETRYING | A retry has been requested and the next attempt may start | Active |
| FAILED | The current attempt failed; another attempt may be requested | Retryable |
| COMPLETED | Execution finished successfully | Terminal |
| CANCELLED | Execution was cancelled | Terminal |

## Allowed transitions

| From | Operation | To |
|---|---|---|
| CREATED | start() | RUNNING |
| CREATED | cancel() | CANCELLED |
| RUNNING | complete_step() | RUNNING |
| RUNNING | wait() | WAITING |
| RUNNING | complete() | COMPLETED |
| RUNNING | fail() | FAILED |
| RUNNING | cancel() | CANCELLED |
| WAITING | resume() | RUNNING |
| WAITING | cancel() | CANCELLED |
| FAILED | retry() | RETRYING |
| RETRYING | start() | RUNNING |

All other lifecycle operations are rejected by the Execution aggregate.

## Retry semantics

FAILED represents failure of the current attempt, not completion of the overall execution. Therefore finished_at remains unset when an execution enters FAILED.

retry() increments attempt and moves the execution to RETRYING. The separate domain RetryPolicy decides whether another retry is allowed; it does not perform the lifecycle transition.

## Terminal states

COMPLETED and CANCELLED are terminal. They cannot be started, resumed, failed, retried, completed again, or cancelled again.

## Boundary

The state machine is intentionally owned by the domain aggregate. Orchestrator, dispatcher, job manager, and infrastructure components must coordinate around this contract rather than duplicate lifecycle rules.
