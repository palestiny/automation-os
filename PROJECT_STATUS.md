# Automation OS — Project Status

> **Single entry point for current project state.**
>
> GitHub `master` is the source of truth. Commit/CI evidence must be verified from GitHub rather than inferred from this document.

## Current State

| Item | Status |
|---|---|
| Current phase | **Phase E — PostgreSQL Execution-History Concurrency Verification** |
| Phase D status | **DONE — PR #372 merged; design gate PASS** |
| Phase E status | **VERIFIED — PR #374 concurrent PostgreSQL test PASS** |
| Phase A — Repository Reconciliation | **DONE — PR #368 merged** |
| Phase B — Database Migration Boundary | **DONE — PR #369 merged** |
| Phase C — Authentication Boundary | **DONE structurally — PR #370 merged; production provider not configured** |
| Phase D — External Side-Effect Semantics | **DONE — CI #2059, #2061 and final PR verification PASS** |
| Production authentication | **NOT COMPLETE — provider/adapter unselected and unconfigured** |
| Production secret provider | **NOT COMPLETE — fail-closed adapter remains** |
| Production readiness | **NO-GO** pending remaining hardening gates |

## Active Hardening Roadmap

1. **Phase A — Repository Reconciliation** — complete.
2. **Phase B — Database Migration Boundary** — complete.
3. **Phase C — Authentication Boundary** — structurally complete; concrete provider remains a deployment/product decision.
4. **Phase D — External Side-Effect Semantics** — complete.
5. **Phase E — PostgreSQL Execution-History Concurrency Verification** — verified; no data-corruption defect observed.
6. **Phase F — Production Secret Provider**.
7. **Phase G — Observability + CI Hardening**.
8. **Phase H — Scalability / Performance Verification**.
9. **Production Readiness Gate**.

## Phase E — PostgreSQL Execution-History Concurrency Verification

PR #374 added a real PostgreSQL concurrency characterization test using two independent connections against the same execution history.

Observed behavior under deterministic overlap:

- both writers can observe the same current `MAX(sequence)`;
- the database primary key `(execution_id, sequence)` prevents duplicate rows;
- exactly one concurrent append commits;
- the conflicting append receives PostgreSQL `UniqueViolation`;
- persisted history remains ordered and contains no duplicate sequence;
- CI run #2066 passed with **761 tests**.

### Phase E decision

The current behavior is treated as **safe against duplicate/corrupt history**, but the loser-side `UniqueViolation` is an optimistic-concurrency conflict rather than a domain-level error.

No sequence-allocation rewrite is authorized from this evidence alone.

Future hardening may introduce a typed history-concurrency error and explicit retry policy if concurrent execution mutation becomes an actual application path. That is a separate design decision.

See `docs/03-Architecture/POSTGRES_EXECUTION_HISTORY_CONCURRENCY.md` for the evidence and trade-off.

## Phase D — External Side-Effect Semantics

PR #372 implemented the approved **Option B — explicit outcome + provider idempotency**.

Implemented:
- explicit capability outcomes: `SUCCEEDED`, `FAILED_BEFORE_SIDE_EFFECT`, `FAILED`, `UNKNOWN`, `SKIPPED`;
- explicit retryability evidence;
- deterministic capability operation identity;
- durable `capability.started` evidence before provider execution;
- durable terminal outcome evidence;
- persisted idempotency-proof evidence;
- automatic retry blocked for unsafe `UNKNOWN`;
- retryability enforced for recorded failures;
- stale recovery converts unresolved durable capability starts to `UNKNOWN`;
- local-persistence-failure-after-external-success coverage;
- PostgreSQL round-trip coverage;
- latest-terminal-event recovery semantics.

Important limitation:
- arbitrary external providers do not receive universal exactly-once semantics;
- automatic retry after `UNKNOWN` requires explicit proven idempotency;
- diagnostic data must remain a safe-data contract. Production hardening should replace unrestricted exception-string persistence with sanitized/allowlisted diagnostics.

## Verified Architectural Contracts

### Workflow / Versioning
- `Workflow` remains the logical workflow container.
- `WorkflowVersion` is the immutable executable artifact.
- Published versions are immutable.
- Executions retain their selected workflow version.
- Runtime start requires persisted PUBLISHED workflow state.
- AI-generated workflows are persisted as DRAFT before review/publication.
- AI cannot publish, execute, or mutate production workflows.

### Execution Authorization
- Tenant execution routes use trusted authorization context.
- Tenant persistence is scoped from authenticated authorization context.
- System context uses system/global persistence boundaries.
- Client identity/tenant headers are not authoritative.

### Runtime Connections
- WorkflowVersion declares provider-neutral, secret-free connection requirements.
- Tenant runtime preparation resolves persisted requirements inside the tenant boundary.
- Domain Connection persists only `secret_reference`, never secret material.
- Runtime connection write access is protected behind the internal preparation boundary.
- The current secret provider fails closed until a production secret manager is configured.

### Human Review
- Approval and publication remain separate boundaries.
- Review evidence is durable and revision-aware.
- Stale review decisions cannot publish a changed revision.

## Known Remaining Production Gaps

### P1
- Concrete authentication provider/adapter is not configured.
- Production secret provider is not implemented/configured.
- Independent post-merge master CI verification is not consistently visible after merges.

### P2
- `app/core/execution_dependencies.py` is approaching composition/God-module complexity.
- `app/infrastructure/persistence/postgres.py` remains a large persistence module.
- API error mapping partly relies on exception/message patterns; typed application errors are a future hardening target.
- Metrics and stale-execution recovery contain full-scan/N+1 patterns that need query-oriented scaling work.
- Observability needs structured logs, correlation IDs, tracing, provider latency/error metrics, and SLO/alerting.
- CI should eventually add linting, type checking, dependency/security/secret scanning, coverage, migration verification, and smoke tests.
- No dedicated load/performance/chaos testing has established production capacity.
- History concurrency currently exposes a raw database conflict to the repository caller; promote it to a typed application-level concurrency boundary if/when concurrent history mutation is an actual runtime path.

## Production Readiness Position

**Controlled hardening: GO**

**Production deployment: NO-GO**

The core architecture does not require a rewrite. Remaining work is boundary hardening, operational readiness, and production infrastructure verification.

## Working Rules

Every major capability follows:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

Safe autonomous work includes repository inspection, dependency mapping, test planning, verification, documentation, and non-direction-changing cleanup.

A significant product or architecture decision remains a Project Owner decision.
