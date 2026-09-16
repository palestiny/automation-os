# ADR-008 — Defer JobManager Live Synchronization

**Status:** Accepted

## Context

`JobManager` currently provides an operational job record associated with an `Execution` through `execution_id`.

The execution engine is already responsible for the authoritative execution lifecycle, step progression, retry behavior, completion, failure and cancellation.

A live synchronization mechanism between `Orchestrator` and `JobManager` would require an application-level coordination boundary. The project does not currently have a real requirement for asynchronous jobs, durable job tracking, worker processes, queues, cancellation through the job layer, or persistent progress reporting.

## Decision

Defer live JobManager synchronization from Phase 2.

The current Phase 2 scope is considered satisfied by the explicit Job → Execution mapping and ownership boundary already implemented.

If live job tracking becomes a concrete product requirement, introduce synchronization at the application boundary rather than inside the domain `Execution` aggregate or by giving `JobManager` its own execution lifecycle.

## Ownership

- `Execution` owns execution lifecycle and workflow-step progression.
- `Orchestrator` coordinates capability execution.
- `ExecutionContext` carries runtime step-to-step data.
- `JobManager` owns operational job identity and presentation-oriented job state.
- A future application coordination service may synchronize JobManager from Execution when a real live-tracking requirement exists.

## Trade-offs

### Option A — Implement live synchronization now

**Benefit:** JobManager would immediately expose live execution progress/status.

**Cost:** Adds an application coordination abstraction before the product requires it and increases the surface area of Phase 2.

### Option B — Defer synchronization

**Benefit:** Keeps Phase 2 focused on the execution engine and avoids premature infrastructure while preserving a clear ownership boundary.

**Cost:** The current JobManager cannot yet provide live execution tracking; that capability must be added when the requirement becomes real.

## Consequences

- Phase 2 does not include live JobManager synchronization.
- No second execution lifecycle is introduced.
- No queue, worker, persistence, or durable job-recovery infrastructure is introduced solely to satisfy the Exit Gate.
- Future live tracking must be designed as an application-level concern.

## Related Decisions

- ADR-004 — Execution and step retry semantics
- ADR-005 — Execution owns workflow-step progression
- ADR-007 — JobManager execution mapping
