# Phase H — Baseline Measurement Protocol

## Status

**H1 harness available; representative baseline results remain uncollected until the manual workflow is run and reviewed.**

This document defines how Phase H evidence will be gathered. It is not a capacity claim, production SLO, or permission to change runtime behavior. Measurements must be produced by a repeatable harness against a known commit and environment.

## Measurement rules

1. Record the exact Git commit, Python version, PostgreSQL server version, dependency lock/input state, OS/container resources, database configuration, and whether the run is local or CI.
2. Use a disposable database created from the repository's migrations. Never run destructive benchmark setup against a shared or production database.
3. Seed deterministic data with a recorded seed. Report actual row counts, executions per workflow/tenant, and history events per execution.
4. Separate setup/seed time from timed operations. Include warm-up and measured sample counts; preserve raw samples. The harness omits p95 below 20 measured samples and p99 below 100; these are reporting floors, not production capacity guarantees. Do not claim p99 from a small sample.
5. Use an explicit, recorded seed for synthetic identifiers and workload shape. Run each scenario more than once and report run-to-run variation. Do not compare results from different resource limits or database configurations as if they were equivalent.
6. Capture correctness invariants alongside performance: persisted states, history sequence uniqueness/order, idempotent replay result, tenant isolation, and no unintended duplicate execution.
7. Keep application-level timings, database query counts, and whole-process throughput as separate measures. Do not infer database query counts from application method-call counts.
8. Keep CI test success distinct from performance evidence. CI is a correctness gate unless a benchmark job explicitly records controlled, comparable measurements.

## Initial workload matrix

These are proposed characterization points, not targets or expected capacity claims. Adjust only when the available environment cannot support a point, and record the reason.

| Scenario | Dataset / concurrency sweep | Measurements |
|---|---|---|
| Execution create/start and state read | 100, 1,000, and 10,000 persisted executions where practical; concurrency 1, 4, and 16 | operation latency, successful operations/sec, errors, SQL statements per operation |
| Execution history append/read | histories with 1, 5, and 20 events per execution; include a growing-history case | append/read latency, SQL statements, rows read/written, transaction duration |
| Idempotent replay | repeated identical idempotency key and distinct keys | replay latency, database operations, duplicate execution count (must remain zero for a replay) |
| Metrics query | same execution counts with a bounded time window and varying history sizes | total latency, SQL statement count, rows fetched, history reads |
| Stale-execution recovery | no stale rows, sparse stale rows, and high stale-row ratio across increasing execution counts | scan/query behavior, recovered count, latency, state correctness |
| Concurrent history append | existing targeted PostgreSQL race test plus a repeatable contention run | success/conflict distribution, duplicate sequences (must remain zero), transaction duration |
| Sustained/soak | a documented steady workload for a recorded duration | throughput drift, memory trend, connection use, error rate, state/history invariants |

Do not fabricate unavailable measurements. If a scenario cannot run because a live provider, deployment, or resource monitor is absent, mark it **NOT RUN** with the missing prerequisite.

## Harness contract

The baseline harness should:

- require an explicit disposable PostgreSQL test URL and fail closed when it is missing;
- refuse production-looking database targets and clearly print the target host/database before setup;
- use migrations and deterministic seeding;
- provide named scenarios, dataset sizes, concurrency, duration/sample count, and seed as explicit CLI options;
- emit machine-readable JSON containing environment metadata, configuration, raw or aggregatable samples, query counts, throughput, resource samples where supported, and correctness checks;
- distinguish warm-up from measured samples and record failures rather than silently dropping them;
- avoid introducing a mandatory runtime dependency or instrumentation into production code;
- include a small smoke scenario for correctness, separate from longer manual load/soak scenarios.

The first implementation is `scripts/benchmark_phase_h_postgres.py`. It currently characterizes repository-wide execution reads, execution metrics aggregation, and stale-execution recovery; it is not yet the complete Phase H harness.

Example against a local disposable PostgreSQL database:

```powershell
$env:AUTOMATION_OS_BENCHMARK_DATABASE_URL = "postgresql://user:password@localhost:5432/automation_os_benchmark"
python scripts/benchmark_phase_h_postgres.py --confirm-disposable --sizes 100 1000 --repetitions 20 --warmup 3 --seed 20261009 --json-output phase-h-baseline.json
```

The script refuses production-like database names and non-local hosts unless explicitly allowed. It creates a random schema, applies migrations there, seeds only that schema, measures operations with a query-counting connection wrapper, and drops the schema afterward. Review the printed host/database name before running it. Do not use production credentials or a shared database. The regular CI smoke scenario uses small datasets only to verify harness execution. A separate manually dispatched workflow records a larger 100/500-execution characterization report as a downloadable artifact; these GitHub-hosted runner timings are comparative diagnostics, not representative production-capacity evidence. Repeat runs and a controlled local/staging environment are still required before capacity claims.

Before expanding the harness, inspect repository constructors and migration boundaries to reuse supported composition paths rather than duplicating persistence behavior. Benchmark instrumentation must remain outside runtime semantics.

## Initial hypotheses to test (not findings)

- Stale recovery currently enumerates executions and then retrieves each candidate by ID. Measure SQL statement count and rows scanned as total execution count grows.
- Execution metrics currently enumerate executions and read history per selected execution. Measure statement count and rows fetched as selected execution count and history size grow.
- History append/read latency may change with history length and contention. Measure it separately from workflow execution time.

These source-level patterns are reasons to measure, not proof of a production bottleneck. No optimization is justified until the harness produces reproducible evidence and a proposed change has an explicit before/after criterion.

## Required baseline report

For every completed scenario, record:

- commit SHA and environment;
- scenario and all workload parameters;
- seed/data cardinalities;
- warm-up and measured sample counts;
- median and supported tail percentiles, with raw samples retained;
- throughput, error/conflict counts, SQL statement counts, rows scanned/fetched, transaction timing, and resource measurements where available;
- correctness checks and any skipped/unavailable measures;
- repeat-run variation and interpretation limits.

The first report should rank findings by measured impact and confidence, then propose (not silently implement) any runtime changes. Phase H exit criteria remain those in the scalability/performance design gate.
