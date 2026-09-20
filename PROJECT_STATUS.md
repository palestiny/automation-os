# Automation OS — Project Status

> **Single entry point for current project state.**
>
> Read this file first when you want to know where the project stands, what has been completed, and what is allowed next.

## Current State

| Item | Status |
|---|---|
| Current phase | **Phase 9 — Observability / Metrics (Implementation)** |
| Phase status | **Phase 9 implementation in progress; Option A accepted** |
| Active implementation | **Read-only operational metrics derived from existing Execution/History evidence** |
| GitHub source of truth | `master` |
| Latest documented milestone | **Phase 8.8 Workflow Versioning — A1 implemented, merged as PR #242; CI run #1167 passed** |
| Next major capability | **Observability / Metrics** |
| Next decision gate | **Phase 9 verification and exit review** |

## Current Roadmap

The authoritative high-level roadmap is:

- `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md`

The current logical runtime/architecture map is:

- `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md`

The ordered post-Phase-7 capability sequence is:

- `docs/01-Roadmap/POST_PHASE_7_CAPABILITY_EXECUTION_SEQUENCE.md`

## Latest Milestone

Phase 8.7 Execution Recovery was completed through PR **#241** and master CI-verified.

Phase 8.8 Workflow Versioning is implemented through PR **#242** using the approved A1 architecture: Workflow remains the logical container and WorkflowVersion is the immutable executable artifact.

GitHub Actions run **#1167** passed for implementation commit `7b0eaeb44d09593ab42a83778e53eb905cf098`.

## Current Position

Completed:

`Phase 7 → hardening → Phase 8.1 Builder → Phase 8.2 Conditions → Phase 8.3 HITL → Phase 8.4 Triggers → Phase 8.5 Providers → Phase 8.6 Durable Persistence → Phase 8.7 Execution Recovery → Phase 8.8 Workflow Versioning`

Current:

`Phase 9 Observability / Metrics — DESIGN GATE`

Phase 9 implementation is proceeding under the accepted Option A architecture: derive metrics from existing Execution and ExecutionHistory evidence.

## Phase 8.8 Completion Record

The approved A1 model is implemented across domain, application, persistence, execution, API projection, tests, and documentation. PR #242 is merged into master.

Delivered:

- first-class WorkflowVersion domain artifact;
- DRAFT/PUBLISHED version lifecycle;
- published-version immutability;
- version cloning and creation;
- deterministic latest-published version resolution;
- explicit version selection;
- execution-to-version persistence;
- execution against the selected version definition;
- in-memory and PostgreSQL version repositories;
- atomic first-start version materialization;
- backward-compatible legacy execution loading;
- version identity in execution progress/API responses.

Deferred by design:

- automatic migration of running executions;
- diff/merge tooling;
- semantic compatibility scoring;
- rollback automation;
- version-aware marketplace/discovery migration;
- AI-generated versions;
- distributed rollout;
- multi-tenant authorization.

Authoritative records:

- `docs/02-Architecture/PHASE_8_8_WORKFLOW_VERSIONING_DESIGN_GATE.md`
- `docs/02-Architecture/PHASE_8_8_WORKFLOW_VERSIONING_EXIT_REVIEW.md`
- `docs/02-Architecture/PHASE_9_OBSERVABILITY_METRICS_DESIGN_GATE.md`

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
- provider-independent capability resolution with deterministic default-provider selection.

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

## Phase 9 Decision Boundary

Phase 9 Observability / Metrics is in implementation under accepted Option A. Metrics are derived from existing Execution and ExecutionHistory evidence through a read-only application boundary. Persisted metric counters and a telemetry/event pipeline remain deferred.

## Phase 8.7 Completion Record

Phase 8.7 Execution Recovery is complete. Stale RUNNING executions transition to FAILED under configurable timeout policy, recovery remains separate from retry and workflow execution, WAITING executions are not automatically changed, recovery is deterministic and sequential, and persistence enforces the conditional transition. Recovery evidence is recorded in execution history. Heartbeats, leases, workers, queues, automatic retry, and distributed recovery remain deferred. CI run #1104 passed for the final implementation commit.
