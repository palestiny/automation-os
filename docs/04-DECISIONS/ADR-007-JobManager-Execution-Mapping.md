# ADR-007: JobManager Maps to Execution

- Status: Accepted
- Scope: Execution Engine runtime integration

## Context

The existing `JobManager` is an in-memory runtime tracker used for job status, progress, messages and errors. The execution engine now has `Execution` as the authoritative lifecycle model.

Keeping a second lifecycle model inside `JobManager` would create competing sources of truth.

## Decision

`JobManager` is an application/runtime adapter that maps a user-visible job to an `Execution` by storing the corresponding `execution_id`.

`JobManager` may expose operational information such as:

- job identifier;
- execution identifier;
- progress;
- display status;
- message;
- error information.

`Execution` remains the authoritative owner of execution lifecycle and business state transitions.

`JobManager` does not create, retry, complete, fail, or cancel an `Execution` itself.

## Trade-offs

### Benefits

- One lifecycle source of truth: `Execution`.
- Existing job/progress concerns remain available without leaking them into the domain aggregate.
- Future API/UI polling can use job identifiers without exposing internal execution details directly.
- Background execution can be introduced later without redesigning the domain lifecycle.

### Costs

- Job status and execution state can temporarily diverge unless the application layer updates the job projection consistently.
- The in-memory implementation is not durable and is not suitable for multi-process execution yet.
- Progress calculation still needs an explicit policy; it should not be inferred from arbitrary job percentages without workflow semantics.

## Consequences

- `JobManager.create_job()` requires the associated `execution_id`.
- The JobManager remains outside the domain model.
- Persistence, distributed workers, queues and durable job recovery remain future concerns.
