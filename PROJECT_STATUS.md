# Automation OS — Project Status

> **Single entry point for current project state.**
>
> Read this file first when you want to know where the project stands, what has been completed, and what is allowed next.

## Current State

| Item | Status |
|---|---|
| Current phase | **Post-Phase-7 capability sequence — completed** |
| Phase status | **All committed post-Phase-7 capabilities and approved reliability hardening are complete; latest master CI is green** |
| Active implementation | **Post-roadmap maintenance / verification** |
| GitHub source of truth | `master` — **mandatory fresh-state read before every autonomous session** |
| Latest verified commit | `3a8249dbe48dc2d1f87fbec31df71198cbc47ef6` — current architecture-map reconciliation |
| Latest CI verification | **GitHub Actions Tests run #1725 — success** |
| Latest hardening test evidence | **Run #1721 test job — 605 passed in 3.46s** |
| Next major capability | **Not defined — no future major capability is committed** |
| Next decision gate | **A new Design Gate is required before any future major capability or material architecture change** |

## Current Roadmap

The authoritative high-level roadmap is:

- `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md`

The current logical runtime/architecture map is:

- `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md`

The ordered post-Phase-7 capability sequence is:

- `docs/01-Roadmap/POST_PHASE_7_CAPABILITY_EXECUTION_SEQUENCE.md`

## Latest Milestone

The full committed post-Phase-7 capability sequence is complete through Phase 8.13 Multi-tenant / Authorization.

The repository then completed the approved post-roadmap reliability hardening gate covering:
- WorkflowVersion explicit tenant ownership (A1);
- MarketplaceListing tenant ownership with separate visibility (B1);
- RetryPolicy authority with explicitly authorized manual override (C2).

The hardening exit review is recorded in:

`docs/02-Architecture/POST_ROADMAP_RELIABILITY_HARDENING_EXIT_REVIEW.md`

Latest master commit `3a8249dbe48dc2d1f87fbec31df71198cbc47ef6` reconciles the current logical architecture map. GitHub Actions run #1725 for that commit completed successfully.

## Current Position

Completed:

`Phase 7 → hardening → Phase 8.1 Builder → Phase 8.2 Conditions → Phase 8.3 HITL → Phase 8.4 Triggers → Phase 8.5 Providers → Phase 8.6 Durable Persistence → Phase 8.7 Execution Recovery → Phase 8.8 Workflow Versioning → Phase 8.9 Observability / Metrics → Phase 8.10 AI Planning → Workflow Generation → Phase 8.11 Marketplace Expansion → Phase 8.12 External Event Integration → Phase 8.13 Multi-tenant / Authorization → reliability hardening`

Current:

`Post-roadmap maintenance / verification — no new capability activated`

Next:

`Safe maintenance, behavioral verification, documentation consistency, cleanup, and Design Gate preparation only. No future major capability is committed.`

## Verified Reliability Hardening

The approved A1/B1/C2 hardening work is complete and CI-verified.

Established contracts include:

- WorkflowVersion carries `tenant_id` and its in-memory/PostgreSQL persistence is tenant-scoped.
- MarketplaceListing carries `tenant_id`; ownership is tenant-scoped while PUBLIC/HIDDEN visibility remains separate.
- Marketplace publication/discovery enforce listing/version tenant consistency.
- PostgreSQL workflow-version uniqueness is tenant-aware.
- Nullable legacy/system tenant ownership is preserved without automatic reassignment.
- RetryExecution enforces RetryPolicy for automatic/policy-constrained retries and supports explicitly authorized manual override through actor/reason context.
- Condition-evaluation failures persist executions as FAILED.
- Retry orchestration is wired through retry → RETRYING → RUNNING → workflow execution.
- Execution history/event persistence has regression coverage for rollback and sequence ordering.
- Tenant-scoped execution/idempotency persistence has regression coverage.
- Stale duplicate persistence tests/imports were removed rather than weakening the current contract.

## Verification Evidence

- GitHub Actions Tests run **#1721**: test job completed successfully with **605 passed in 3.46s**.
- GitHub Actions Tests run **#1722**: success.
- GitHub Actions Tests run **#1723**: success.
- GitHub Actions Tests run **#1724**: success.
- GitHub Actions Tests run **#1725**: success for current master commit `3a8249dbe48dc2d1f87fbec31df71198cbc47ef6`.

The current state is therefore CI-verified on master.

## Retry Audit Boundary

Manual retry actor/reason context is currently captured at the application authorization boundary.

There is no committed automatic retry worker or dedicated durable retry-audit repository/event schema. Adding durable platform-owned retry audit storage, an automatic retry worker, or materially expanding retry authorization would require a new architecture decision and Design Gate.

## Migration Boundary

Legacy rows with `NULL tenant_id` remain explicit system/global compatibility artifacts.

No automatic tenant reassignment was introduced. Any future migration that assigns legacy rows to tenants requires an explicit migration policy and Project Owner decision.

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
- read-only operational execution metrics derived from existing execution evidence;
- multi-tenancy and authorization boundaries;
- tenant ownership and isolation for the approved hardening scope.

## Roadmap Execution Rule

Every major capability follows:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

Safe autonomous work may continue during maintenance and design preparation, including repository inspection, dependency mapping, test planning, verification, documentation, and non-direction-changing cleanup.

A significant architecture/product decision remains a Project Owner decision.

## Where To Look

| Need | Start here |
|---|---|
| **Where are we?** | **This file** |
| **High-level roadmap** | `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md` |
| **Logical runtime map** | `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md` |
| **Capability sequence** | `docs/01-Roadmap/POST_PHASE_7_CAPABILITY_EXECUTION_SEQUENCE.md` |
| Architecture decisions | `docs/04-DECISIONS/` |
| Reliability hardening decision | `docs/04-DECISIONS/POST_ROADMAP_RELIABILITY_OWNERSHIP_AND_RETRY_DECISION.md` |
| Reliability hardening exit review | `docs/02-Architecture/POST_ROADMAP_RELIABILITY_HARDENING_EXIT_REVIEW.md` |
| Development history | `docs/06-Journal/DEVELOPMENT_HISTORY.md` |
| Autonomous work rules | `AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md` |
| Engineering operating rules | `AGENTS.md` |

## Next Decision Boundary

The committed capability sequence and approved reliability hardening are complete.

Safe maintenance, verification, documentation reconciliation, cleanup, and future Design Gate preparation may continue.

Any future major capability or material architecture change requires:
1. explicit Project Owner decision;
2. documented trade-offs;
3. an approved Design Gate;
4. implementation followed by RED → GREEN → VERIFY → EXIT REVIEW.

No future major capability is currently committed.
