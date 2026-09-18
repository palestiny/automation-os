# Scheduling and Progress Tracking Design Gate

## Status

Proposed — design-only boundary.

## Business Problem

Content automation eventually needs two capabilities: request a workflow execution for a future time, and observe what is happening to an execution. These are related operational concerns but they are not the same lifecycle.

The existing Execution aggregate already owns runtime state. Scheduling must not create a second execution state machine, and progress tracking must not duplicate that state.

## Committed Decisions

1. Scheduling is an application-level trigger mechanism that decides when to start an execution.
2. A scheduled request reuses the existing StartWorkflowExecution use case.
3. Scheduling does not create or own an Execution lifecycle.
4. The minimum scheduled item contains a workflow identifier and a requested execution time.
5. Scheduling uses an injectable clock/time source so tests do not depend on wall-clock time.
6. A due scheduled item is consumed by the scheduler and translated into a normal workflow execution request.
7. Progress tracking is a read/projection concern over existing Execution state.
8. Progress tracking does not introduce a second state machine.
9. Progress should expose execution identity, workflow identity, current step, execution state, attempt, and timestamps already owned by Execution.
10. Capability-specific progress details are not added to the core Execution aggregate.
11. Provider-specific scheduling APIs remain infrastructure concerns.
12. Queue/worker/distributed scheduler infrastructure is deferred.
13. Automatic retry, backoff and distributed idempotency remain separate concerns.
14. Durable schedule persistence is deferred until a concrete scheduling use case requires schedules to survive process restart.

## Initial Scheduling Model

The first conceptual model is ScheduledExecutionRequest: workflow_id and scheduled_at. It represents intent to start an execution at or after a specified time. It does not contain execution state, current step, retry state, provider information, or worker identity.

Once due: ScheduledExecutionRequest → StartWorkflowExecution → Execution.

## Progress Projection

The first progress projection is Execution → ExecutionProgress. ExecutionProgress is a read model, not a domain lifecycle.

Minimum fields: execution_id, workflow_id, current_step, state, attempt, started_at, finished_at.

The projection may later add workflow step name/count through a read-side query, but it must not become a second source of lifecycle truth.

## Clock Boundary

Scheduling requires current time. Production code must not call the system clock directly inside domain/application behavior that needs deterministic tests.

Use an application-facing Clock protocol: Clock.now() → datetime. The first test implementation is a fixed clock. The production implementation may delegate to the system clock.

## First TDD Increments

### Increment 1 — Scheduled request vocabulary
Define and test the minimal scheduled request invariants.

### Increment 2 — Due scheduling use case
Given a scheduled request and current clock time, determine whether it is due and, when due, invoke the existing StartWorkflowExecution path.

### Increment 3 — Progress projection
Create the provider-neutral read model from an existing Execution without changing Execution lifecycle.

### Increment 4 — Application composition
Prove scheduled execution and progress projection together using deterministic in-memory components.

### Increment 5 — Concrete scheduler adapter
Only after a real runtime requirement exists should an OS scheduler, queue, worker, or distributed scheduler be introduced.

## Assumptions

- One scheduled time is sufficient for the first scheduling slice.
- Recurrence is not required yet.
- A scheduled request is one-shot.
- The first scheduler can process due requests synchronously.
- In-memory schedule storage is sufficient for deterministic tests.
- Progress consumers can read existing execution state without a separate event store.

## Open Questions

1. Should scheduled requests be durable before scheduling becomes a production feature?
2. How should missed schedules behave after downtime?
3. Should recurring schedules become a separate domain concept?
4. When should timezone semantics become explicit?
5. Should progress include per-capability output/error information?
6. What API/read-model boundary should expose progress externally?

## Alternatives Considered

### Scheduler-owned execution state
Rejected. It duplicates Execution lifecycle and would create competing sources of truth.

### Progress state machine
Rejected. Execution already owns lifecycle state.

### Queue-first architecture
Deferred. A queue may become necessary for scale or asynchronous work, but it is not required to establish the scheduling boundary.

### Recurring schedule as the first model
Deferred. One-shot scheduling proves the boundary with less domain complexity.

### Persist schedules immediately
Deferred. Persistence should follow a demonstrated restart/durability requirement rather than precede it.

## Trade-offs

### Application scheduler vs provider scheduler
Decision: application-level scheduling boundary. Trade-off: more responsibility remains in Automation OS, but workflow behavior stays provider-neutral and portable.

### Thin progress projection vs rich telemetry
Decision: thin projection of Execution. Trade-off: detailed observability is deferred, but lifecycle duplication is avoided.

### One-shot vs recurring schedules
Decision: one-shot first. Trade-off: recurring automation comes later, but the first model remains simple and testable.

## Deferred Scope

- recurring schedules;
- timezone/calendar rules;
- distributed scheduler;
- worker pools;
- queues;
- durable schedule repository;
- automatic retry/backoff;
- distributed idempotency;
- provider-native scheduling;
- advanced telemetry;
- real-time event streaming.

## Design Gate Exit Criteria

- scheduling boundary is separate from execution lifecycle;
- progress is a projection, not another state machine;
- clock is testable;
- first TDD increment is defined;
- deferred infrastructure is documented;
- StartWorkflowExecution remains the single execution-start path.

## Resolved Progress

Increment 1 is implemented: ScheduledExecutionRequest, Clock/FixedClock, and due-time semantics are covered by deterministic tests.

## Next Implementation Boundary

Increment 2 — Due scheduling use case.
