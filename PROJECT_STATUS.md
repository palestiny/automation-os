# Automation OS — Project Status

> **Single entry point for current project state.**
>
> Read this file first when you want to know where the project stands, what has been completed, and what is allowed next.

## Current State

| Item | Status |
|---|---|
| Current phase | **Post-Phase-7 capability sequence — completed** |
| Phase status | **All committed post-Phase-7 capabilities completed; current master CI is green** |
| Active implementation | **Post-roadmap maintenance / verification — approved reliability hardening completed** |
| GitHub source of truth | `master` — **mandatory fresh-state read before every autonomous session** |
| Latest verified commit | `cfedbb76e4a7027e0c05308e9d553bbc1ded5c12` — reliability hardening exit-review commit |
| Latest CI verification | **GitHub Actions Tests run #1721 — test job success, 605 passed** |
| Next major capability | **Not yet defined — new capability requires a Design Gate** |
| Next decision gate | **New Design Gate only if durable retry audit storage, workers, or further tenancy expansion is activated** |

## Current Roadmap

The authoritative high-level roadmap is:

- `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md`

The current logical runtime/architecture map is:

- `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md`

The ordered post-Phase-7 capability sequence is:

- `docs/01-Roadmap/POST_PHASE_7_CAPABILITY_EXECUTION_SEQUENCE.md`

## Latest Milestone

The full committed post-Phase-7 capability sequence is complete through Phase 8.13 Multi-tenant / Authorization.

The repository has since undergone additional reliability and verification hardening on `master`, including retry orchestration wiring, execution-history/event persistence verification, tenant-scoped execution/idempotency persistence, and removal of stale duplicate persistence tests.

GitHub Actions Tests run **#1686** passed for commit `c22281645bc060799266099755418df6f4e4aab5`.

## Current Position

Completed:

`Phase 7 → hardening → Phase 8.1 Builder → Phase 8.2 Conditions → Phase 8.3 HITL → Phase 8.4 Triggers → Phase 8.5 Providers → Phase 8.6 Durable Persistence → Phase 8.7 Execution Recovery → Phase 8.8 Workflow Versioning → Phase 8.9 Observability / Metrics → Phase 8.10 AI Planning → Workflow Generation → Phase 8.11 Marketplace Expansion → Phase 8.12 External Event Integration → Phase 8.13 Multi-tenant / Authorization → reliability hardening`

Current:

`Post-roadmap maintenance / verification — reliability hardening gate completed; no new capability activated`

Next:

`Safe maintenance, verification, and Design Gate preparation only. No future major capability is committed.`

## Verified Hardening Work

Recent master-verified work has established:

- condition-evaluation failures transition and persist executions as FAILED;
- PostgreSQL execution/idempotency operations are tenant-scoped where tenant identity is already part of the committed contract;
- execution save and conditional state transitions preserve transactional persistence of execution evidence;
- retry orchestration is fully wired through retry → RETRYING → RUNNING → workflow execution;
- execution history persistence has regression coverage for rollback and sequence ordering;
- stale duplicate persistence tests/imports were removed rather than weakening the current contract;
- the resulting master state is CI-verified.

## Open Architecture Boundaries Requiring Owner Decision

The following were the approved architecture boundaries and are now active implementation tasks:

1. **WorkflowVersion tenant ownership** — the current WorkflowVersion domain/schema does not carry tenant identity, while tenant-scoped Workflow/Execution persistence now exists.
2. **MarketplaceListing tenant ownership** — the schema has a tenant_id column, but the current MarketplaceListing domain/repository contract does not yet carry or enforce tenant ownership.
3. **Manual retry vs RetryPolicy semantics** — the repository has both explicit retry behavior and retry-policy concepts; their authority/interaction needs an explicit decision before expanding retry semantics.

These architecture decisions are recorded in `docs/04-DECISIONS/POST_ROADMAP_RELIABILITY_OWNERSHIP_AND_RETRY_DECISION.md` and are now committed.

## Phase 9 Completion Record

The approved Option A model is implemented and CI-verified.

Delivered:

- read-only `GetExecutionMetrics` application boundary;
- execution totals filtered by a single `started_at` measurement window;
- counts for every execution lifecycle state;
- completed duration statistics only when both timestamps are present;
- retry and stale-recovery lifecycle event counts;
- workflow breakdown;
- workflow-version breakdown with explicit unversioned bucket for legacy executions;
- attempt distribution;
- deterministic, repeatable results;
- no mutation of execution lifecycle state during metric calculation;
- in-memory contract tests;
- PostgreSQL persistence parity verification.

Authoritative records:

- `docs/02-Architecture/PHASE_9_OBSERVABILITY_METRICS_DESIGN_GATE.md`
- `docs/02-Architecture/PHASE_9_OBSERVABILITY_METRICS_TRADEOFFS.md`
- `docs/02-Architecture/PHASE_9_OBSERVABILITY_METRICS_EXIT_REVIEW.md`

## Established Architectural Foundations

The platform currently has verified architectural/runtime foundations for:

- intent analysis and canonical goals;
- deterministic workflow selection;
- workflow composition/builder;
- condition evaluation;
- workflow execution;
- execution lifecycle control;
- execution progress/discovery;
- cancellation;
- resume;
- retry and retry-and-execute boundaries;
- workflow discovery;
- workflow generation boundaries and validation;
- marketplace discovery/publication/installation foundations;
- content automation boundaries already covered by committed design gates;
- execution reliability and operational visibility;
- durable PostgreSQL persistence;
- stale execution recovery with conditional persistence and auditable recovery evidence;
- immutable workflow version artifacts and execution-to-version traceability;
- provider-independent capability resolution with deterministic default-provider selection;
- read-only operational execution metrics derived from existing execution evidence.

## Roadmap Execution Rule

Every major capability follows:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

Safe autonomous work may continue during design preparation, including repository inspection, dependency mapping, test planning, verification, documentation, and non-direction-changing maintenance.

A significant architecture/product decision remains a Project Owner decision.

## Where To Look

| Need | Start here |
|---|---|
| **Where are we?** | **This file** |
| **High-level roadmap** | `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md` |
| **Logical runtime map** | `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md` |
| **Capability sequence** | `docs/01-Roadmap/POST_PHASE_7_CAPABILITY_EXECUTION_SEQUENCE.md` |
| Architecture decisions | `docs/04-DECISIONS/` |
| Development history | `docs/06-Journal/DEVELOPMENT_HISTORY.md` |
| Autonomous work rules | `AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md` |
| Engineering operating rules | `AGENTS.md` |

## Next Decision Boundary

The committed capability sequence and approved reliability hardening are complete. Safe maintenance, verification, and Design Gate preparation may continue. Any future major capability or material architecture change requires an explicit Project Owner decision and approved Design Gate.

## Approved Reliability Hardening Progress

Approved on 2026-09-22: A1 WorkflowVersion tenant ownership, B1 MarketplaceListing tenant ownership with separate visibility, and C2 RetryPolicy/manual retry authority separation.

Implemented so far:
- WorkflowVersion carries tenant_id and tenant-scoped in-memory/PostgreSQL persistence.
- MarketplaceListing carries tenant_id and tenant-scoped in-memory/PostgreSQL persistence; visibility remains separate from ownership.
- PostgreSQL bootstrap preserves nullable legacy/system ownership and uses tenant-aware version uniqueness.
- RetryExecution now supports RetryPolicy enforcement plus explicitly authorized manual override context.
- Focused regression tests were added for tenant isolation and retry override semantics.

Remaining before exit review:
- verify current GitHub Actions results;
- complete legacy/null-tenant compatibility coverage;
- review retry audit persistence boundary and decide whether the current application authorization hook is sufficient;
- full regression and final CI verification.

## Reliability Hardening Exit

The approved A1/B1/C2 reliability hardening gate is complete. Exit review: `docs/02-Architecture/POST_ROADMAP_RELIABILITY_HARDENING_EXIT_REVIEW.md`.

Final verified test evidence: GitHub Actions run #1721 test job completed successfully with 605 passed. Legacy NULL tenant compatibility remains explicit system/global behavior; no automatic tenant reassignment was introduced.
