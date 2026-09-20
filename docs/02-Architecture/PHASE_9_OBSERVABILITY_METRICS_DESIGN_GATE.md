# Phase 9 — Observability / Metrics Design Gate

## Status

**Accepted — Option A selected by the Project Owner. Implementation may proceed.**

## 1. Problem

Automation OS now has durable Execution identity, structured lifecycle evidence, recovery evidence, retry/cancellation/resume boundaries, and immutable WorkflowVersion identity.

The platform can therefore answer many per-execution questions, but it does not yet expose a coherent operational observability contract for aggregate metrics and execution visibility.

The goal is not to add generic analytics or a premature distributed telemetry platform. The immediate gap is a deterministic, reusable read/measurement boundary over execution evidence.

## 2. Goal

Introduce the smallest stable observability boundary that can answer operational questions such as:

- How many executions were started, completed, failed, cancelled, waiting, or retried?
- What is the completion/failure rate for a defined measurement window?
- How long do completed executions take?
- How many retries/recoveries occur?
- Which workflow/version is producing executions and outcomes?
- Can metrics be derived consistently from durable execution evidence?
- Can the same contract work with in-memory and PostgreSQL persistence?

Observability must remain a read/measurement concern. It must not become a second execution lifecycle authority.

## 3. Current Repository Evidence

Current Execution already contains:

- stable execution identity;
- workflow identity;
- optional immutable workflow_version_id;
- lifecycle state;
- attempt count;
- started_at / finished_at;
- structured domain lifecycle events.

Current lifecycle events include:

- execution.started
- execution.retry_started
- execution.step_completed
- execution.waiting
- execution.resumed
- execution.completed
- execution.failed
- execution.recovered_stale
- execution.retrying
- execution.cancelled

Current persistence already exposes:

- ExecutionRepository;
- append-only ExecutionHistoryRepository;
- PostgreSQL execution_history;
- in-memory execution history;
- execution progress projection.

This means Phase 9 should build on existing evidence rather than introduce a parallel event/lifecycle model.

## 4. Architecture Constraints

1. Execution remains the lifecycle authority.
2. History/events remain evidence, not lifecycle authority.
3. Observability is read-only with respect to execution state.
4. Metrics must have explicit measurement semantics and time-window definitions.
5. Metrics must not mutate executions.
6. Version identity must be available where executions already have it.
7. Legacy executions with null workflow_version_id remain measurable.
8. In-memory and PostgreSQL adapters must preserve the same observable contract.
9. No background worker is required for the first increment.
10. No distributed tracing platform is required for the first increment.
11. No generic event bus is introduced solely for metrics.
12. No product analytics unrelated to operational execution is included.

## 5. Candidate Models

### Option A — Query existing execution/history repositories

Add read-only application services that calculate metrics from existing ExecutionRepository and ExecutionHistoryRepository data.

Advantages:
- smallest architectural surface;
- reuses already durable evidence;
- no duplicate metric state;
- deterministic and easy to test;
- preserves current execution architecture.

Trade-offs:
- aggregate queries may scan substantial history;
- PostgreSQL-specific optimization may eventually be required;
- real-time high-volume metrics are not the immediate target.

### Option B — Persist derived metric counters

Introduce metric/counter tables updated whenever execution evidence is written.

Advantages:
- fast dashboard reads;
- efficient aggregate queries at larger scale.

Trade-offs:
- introduces a second derived state that must remain consistent with execution evidence;
- requires transaction coupling with lifecycle persistence;
- recovery/replay semantics become more complex;
- risks making counters an accidental source of truth.

### Option C — Introduce a telemetry/event pipeline

Publish execution events into a dedicated telemetry/event infrastructure and derive metrics externally.

Advantages:
- future distributed observability;
- scalable stream processing;
- natural path toward tracing and external monitoring.

Trade-offs:
- significantly larger infrastructure boundary;
- delivery/replay/order semantics become new architecture concerns;
- unnecessary for the current modular-monolith stage;
- risks pulling event-bus infrastructure into the platform prematurely.

## 6. Primary Decision

**Decision: A — derive metrics from existing Execution and ExecutionHistory evidence.**

The Project Owner approved Option A. Options B and C remain future alternatives that require a new Design Gate if concrete scale or operational requirements justify them.

### Decision rationale

Option A reuses durable lifecycle evidence, avoids duplicate metric state, preserves Execution as the lifecycle authority, and keeps the first observability increment inside the existing modular-monolith architecture.

## 7. Secondary Semantic Decisions

If Option A is selected, the implementation must explicitly define:

### 7.1 Metric scope

Initial scope should cover operational execution metrics only:

- execution counts by state;
- completion/failure/cancellation/waiting counts;
- retry/recovery counts;
- duration for executions with both started_at and finished_at;
- workflow/workflow-version breakdown;
- attempt distribution.

### 7.2 Time window

Every aggregate metric must define whether the window filters by:

- execution started_at;
- execution finished_at;
- event occurred_at;
- or another explicit timestamp.

The initial contract should use one consistent definition rather than mixing timestamps silently.

### 7.3 Incomplete executions

Executions without a finished_at must not receive fabricated duration values.

### 7.4 Legacy versions

Executions with null workflow_version_id remain included in aggregate metrics and are grouped under an explicit legacy/unversioned bucket where version breakdown is requested.

### 7.5 Event counting

Retry/recovery metrics must define whether they count lifecycle events or distinct executions. The API must not leave this ambiguous.

### 7.6 Read consistency

The first increment may expose repository-consistent snapshots; it does not require a globally synchronized distributed metrics view.

## 8. Proposed Initial API Boundary

A read-only application boundary should expose an operational metrics DTO/query rather than embedding aggregation logic in the HTTP adapter.

Possible initial projection:

- window start/end;
- total executions;
- counts by execution state;
- completed duration statistics;
- retry count;
- recovery count;
- workflow/version breakdown.

The exact DTO shape is a RED-stage decision after the primary architecture choice.

## 9. API / UI Scope

The first increment does not require a dashboard UI.

An HTTP read endpoint may be added only after the application contract is established and tested.

No mobile/dashboard product work is pulled into this phase unless required by a later explicit decision.

## 10. TDD RED Plan After Decision

Tests should establish:

- empty-window behavior;
- deterministic time-window filtering;
- state counts;
- completed-duration calculation;
- exclusion of incomplete durations;
- retry event/execution counting semantics;
- recovery counting semantics;
- workflow breakdown;
- version breakdown;
- legacy unversioned grouping;
- parity between in-memory and PostgreSQL adapters;
- read-only behavior;
- deterministic results for identical evidence.

If Option A is selected, tests should prove metrics are derived from existing evidence and do not introduce a second lifecycle state store.

## 11. Explicitly Deferred

Unless a later Design Gate requires them:

- Prometheus/OpenTelemetry integration;
- distributed tracing;
- event bus;
- streaming metrics;
- alerting engine;
- anomaly detection;
- SLA/SLO platform;
- business/product analytics;
- predictive metrics;
- AI interpretation of metrics;
- background metric aggregation workers;
- metric retention/rollup infrastructure;
- multi-tenant metric isolation.

## 12. Exit Criteria

Phase 9 is complete only when:

- the selected source-of-truth model is implemented;
- metric semantics are explicit;
- application read boundary is tested;
- in-memory and PostgreSQL behavior are verified where applicable;
- existing execution lifecycle semantics remain unchanged;
- focused and full CI verification pass;
- documentation and project status are updated;
- an exit review records limitations and deferred scope.

## 13. Decision Record

**Decision recorded:** Option A — derive metrics from existing Execution and ExecutionHistory evidence.

**Decision owner:** Project Owner.

**Implementation constraint:** observability remains read-only; Execution remains the lifecycle authority; no persisted metric counters or telemetry pipeline are introduced in this increment.
