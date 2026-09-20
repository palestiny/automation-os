# Phase 9 — Observability / Metrics Trade-offs

## Decision

**Selected architecture: Option A — derive metrics from existing Execution and ExecutionHistory evidence.**

The Project Owner approved Option A as the initial observability source-of-truth model.

## Why A

- Reuses durable execution evidence already present in the domain and persistence layers.
- Avoids introducing a second derived state store.
- Keeps Execution as the lifecycle authority.
- Keeps observability read-only.
- Preserves the modular-monolith architecture without premature telemetry infrastructure.
- Allows deterministic in-memory and PostgreSQL verification.

## Trade-offs Accepted

### Performance

Initial aggregation may scan execution/history evidence. PostgreSQL indexing/query optimization can be introduced when measured workload requires it.

### Freshness

Metrics are repository-consistent read snapshots, not a globally synchronized distributed telemetry stream.

### Scale

High-volume streaming metrics are explicitly outside the first increment. If scale later requires pre-aggregation, persisted counters or telemetry can be reconsidered through a new Design Gate.

### Duplicate State

No persisted metric counters are introduced initially. This avoids consistency coupling between lifecycle writes and derived counters.

### Infrastructure

Prometheus, OpenTelemetry, event buses, streaming pipelines, background aggregation workers, and distributed tracing remain deferred.

## Semantic Contract To Be Finalized In RED

The implementation tests will establish the exact DTO and semantics for:

- measurement window;
- state counts;
- duration statistics;
- retry counting;
- recovery counting;
- workflow/version breakdown;
- legacy unversioned executions;
- attempt distribution.

The implementation must not fabricate duration for incomplete executions and must not mutate execution state while calculating metrics.

## Reconsideration Triggers

Option A should be reconsidered only when concrete requirements demonstrate a need for:

- sustained high-volume aggregate reads;
- precomputed dashboard latency;
- external telemetry integration;
- distributed event processing;
- retention/rollup requirements that cannot be served efficiently from existing evidence.

Any move to persisted counters or a telemetry pipeline requires a new architecture decision rather than an implicit implementation change.
