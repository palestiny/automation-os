# Job ↔ Execution Mapping

## Purpose

A Job is an operational handle for observing an execution. It is not a second execution model.

```text
Client / API
     ↓
   Job ID
     ↓
 JobManager
     ↓
Execution ID
     ↓
 Execution
     ↓
Orchestrator
     ↓
Capabilities
```

## Ownership

| Concern | Owner |
|---|---|
| Execution lifecycle | `Execution` |
| Workflow step progression | `Execution` |
| Capability coordination | `Orchestrator` |
| Runtime step-to-step data | `ExecutionContext` |
| Job identifier | `JobManager` |
| Job-to-execution mapping | `JobManager` |
| Display/progress information | `JobManager` / application layer |

## Important Boundary

`JobManager` must not become a parallel lifecycle aggregate.

For example, `JobManager.complete()` means the operational job representation is marked complete; the underlying `Execution.complete()` remains the business lifecycle transition.

The application layer is responsible for keeping the operational projection synchronized with the execution result.

## Current Implementation Limitation

The current JobManager is in-memory. It is therefore suitable for the current modular-monolith execution work but does not yet provide durable recovery or multi-process coordination.

Those concerns are intentionally deferred until asynchronous/background execution is an explicit requirement.
