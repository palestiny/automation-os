# Phase H — Scalability / Performance Verification Design Gate

## Status

**ACTIVE — baseline characterization only; persistence-level start/state/history scenarios now included**

Phase G's first operational/CI slice has been independently verified on `master` by GitHub Actions run #2099. Phase H is now activated for measurement planning and baseline collection only. Runtime optimization remains blocked until reproducible evidence establishes a bottleneck.

## Objective

Establish measurable scalability and performance characteristics for the current Automation OS architecture before making optimization or scaling changes.

The reproducible protocol and proposed workload matrix are documented in [`PHASE_H_BASELINE_MEASUREMENT_PROTOCOL.md`](PHASE_H_BASELINE_MEASUREMENT_PROTOCOL.md). It is a plan, not measured evidence; no baseline results are claimed yet.

The goal is to identify actual bottlenecks and capacity limits without prematurely introducing distributed infrastructure, caching, queues, or architectural rewrites.

## Current architectural signals

The repository currently has several areas that require measurement rather than assumption:

- `app/core/execution_dependencies.py` is a large composition boundary and may become a maintainability/performance hotspot.
- `app/infrastructure/persistence/postgres.py` is a large persistence adapter.
- Execution history currently performs sequence checks and reads that must be characterized under concurrent access.
- Metrics and stale-execution recovery have identified full-scan/N+1 patterns that require query-oriented verification.
- PostgreSQL is the authoritative durable runtime persistence boundary.
- Execution semantics, idempotency, tenant isolation, and capability dispatch are correctness boundaries and must not be weakened for performance.

These are hypotheses to measure, not confirmed production bottlenecks.

## Phase H work sequence

### H1 — Workload and measurement plan

Define representative workloads and capture a reproducible environment description before running comparisons.

Workloads:
- single execution;
- multi-step execution;
- concurrent executions;
- execution history growth;
- idempotent replay;
- retry/resume;
- execution discovery;
- stale-execution recovery;
- tenant-scoped workloads;
- capability dispatch with slow external providers.

For each run, record Python and PostgreSQL versions, environment, dataset cardinality, concurrency, workload shape, warm/cold state where relevant, and measurement method. Keep local benchmark evidence distinct from CI evidence.

### H2 — Baseline measurements

Measure at minimum:
- HTTP request latency;
- execution-start latency (current harness measures domain aggregate start plus persistence; full application/HTTP start remains unmeasured);
- execution-state read latency;
- execution-history append/read latency;
- execution discovery latency;
- stale-recovery runtime and database query count;
- query count per operation and full-scan/N+1 behavior;
- executions/sec and history events/sec;
- concurrent active executions;
- process memory and database connection use;
- transaction duration and lock/conflict behavior.

Report p50/p95/p99 only when sample size supports meaningful percentiles. Do not define arbitrary performance targets before observing a representative baseline.

### H3 — Concurrency, load, and soak characterization

Distinguish:
1. **Baseline** — normal representative workload.
2. **Load** — expected sustained workload.
3. **Stress** — progressively exceed expected capacity.
4. **Soak** — sustained operation to expose leaks/drift.
5. **Concurrency characterization** — targeted race/contention tests.

Classify failures as expected contention, retryable conflict, correctness defect, or capacity/resource exhaustion. Chaos testing is deferred until a concrete production deployment topology exists.

### H4 — Bottleneck ranking and proposed changes

Rank findings by impact and confidence. Any optimization proposal must state:
- measured baseline and environment;
- identified bottleneck and evidence;
- expected improvement and correctness risks;
- a measurable before/after criterion;
- targeted regression tests.

No runtime optimization is authorized solely by code size, intuition, or an unmeasured query pattern.

## Backpressure and resource limits

Characterize current behavior when:
- database connections are exhausted;
- execution volume exceeds processing capacity;
- external capability latency increases;
- requests arrive faster than persistence can sustain.

Measure before proposing queues, worker pools, or caching.

## Memory and lifecycle

Measure process memory under sustained execution load, repository object growth, in-memory fallback behavior, history/object retention, and long-running workflow effects. Treat unbounded lifecycle as a reliability concern as well as a performance concern.

## Non-goals

Phase H does not automatically authorize:
- Redis or another cache;
- a message broker;
- distributed workers;
- Kubernetes;
- horizontal autoscaling;
- database sharding;
- CQRS/event sourcing;
- changing execution-state semantics;
- weakening transactional guarantees.

These remain options only if evidence establishes a need and the Project Owner approves the architecture decision.

## Acceptance criteria

Phase H is not complete until:
1. representative workload models are documented;
2. baseline latency and throughput are measured;
3. database query/scaling hotspots are identified;
4. concurrency behavior is characterized;
5. resource/backpressure behavior is characterized;
6. at least one load and one sustained/soak experiment provide evidence;
7. bottlenecks are ranked by impact and confidence;
8. each proposed optimization has a measurable before/after criterion;
9. no correctness regression is introduced;
10. results and remaining capacity risks are documented.

## Exit decision

The Phase H exit review classifies each major concern as:
- **PASS** — measured and within the agreed capacity envelope;
- **GAP** — measurable bottleneck exists and requires remediation;
- **NOT PROVEN** — insufficient evidence.

Phase H may proceed with workload design and baseline measurement now. Any runtime change that affects architecture or execution correctness remains subject to its own design gate and Project Owner decision.
