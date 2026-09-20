# Phase 8.7 — Execution Recovery Trade-offs

## Decision Status
**Accepted**

The Project Owner selected **Option A — stale RUNNING executions become FAILED**.

## Decision Summary
| Decision | Accepted choice | Main reason |
|---|---|---|
| Recovery outcome | RUNNING → FAILED | Preserve lifecycle clarity and avoid implicit re-execution |
| Stale detection | Configurable timeout | Smallest reliable operational model before workers/leases |
| Timeout ownership | Recovery Policy/application configuration | Keep operational timing out of the domain aggregate |
| Recovery execution | State recovery only | Recovery must not duplicate ExecuteWorkflow |
| Retry | Explicit and separate | Avoid silently repeating side effects |
| Invocation | Application service, no new background worker | Deliver recovery semantics without a new runtime |
| Batch | Sequential deterministic recovery | Avoid premature parallel/distributed coordination |
| Concurrency | Conditional persistence transition | Prevent stale recovery from overwriting newer lifecycle state |
| Evidence | Auditable recovery reason/history | Preserve why FAILED was produced |
| WAITING | Remains WAITING until explicit resume | WAITING is not evidence of process failure |
| RECOVERING state | Not introduced | Avoid lifecycle expansion before worker/lease semantics |

## Key Trade-offs

### Timeout vs heartbeat
Timeout is simpler and deterministic, but it can misclassify a legitimately long-running execution if configured too aggressively. Heartbeat provides stronger liveness evidence but requires active worker/runtime infrastructure.

Decision: use timeout now; defer heartbeat until a real worker ownership model exists.

### Timeout vs lease/ownership
A lease can establish which process owns an execution and support safe takeover after expiry. It is stronger for distributed workers but introduces renewal, expiration, takeover, and concurrency semantics.

Decision: defer leases. Phase 8.7 should not create distributed execution infrastructure prematurely.

### FAILED vs RETRYING
Moving stale executions directly to RETRYING would connect recovery to another attempt, but it would make recovery an implicit retry decision. A crash can happen after an external side effect succeeds but before completion is persisted.

Decision: FAILED first. Retry remains an explicit caller/system decision through the existing retry boundary.

### Automatic recovery vs background worker
A background recovery loop would make the feature operationally automatic, but it would introduce scheduling, worker lifecycle, shutdown, and concurrency concerns.

Decision: provide an application recovery boundary now; do not add a new worker/scheduler.

### New RECOVERING state vs existing lifecycle
A RECOVERING state could model richer takeover workflows, but it would expand the core state machine and require broader API, persistence, and migration changes.

Decision: do not add it until the platform has a concrete need for first-class ownership/takeover semantics.

### Sequential vs parallel recovery
Sequential recovery is easier to reason about and test. Parallel recovery could improve throughput but requires stronger locking/ownership guarantees.

Decision: sequential now; distributed/parallel recovery is deferred.

## Side-effect Safety Principle
Recovery must assume that an interrupted RUNNING execution may have performed an external side effect immediately before the process failed.

Examples include sending a message, publishing content, calling an external API, creating a proposal, or uploading an artifact.

Therefore: **A recovered FAILED execution is evidence that an attempt was interrupted, not evidence that no side effect occurred.**

This is the primary reason recovery must not automatically execute or retry the workflow.

## Resulting Architecture Boundary
Recovery Policy → determines whether persisted RUNNING state is stale
RecoverStaleExecution → performs the explicit recovery transition
Execution → remains lifecycle authority
Execution History → records recovery evidence
RetryExecution → remains the explicit retry boundary
StartRetryingExecution → starts a RETRYING execution
ExecuteWorkflow → remains the only workflow execution orchestration boundary

This keeps Phase 8.7 additive rather than creating a competing runtime model.