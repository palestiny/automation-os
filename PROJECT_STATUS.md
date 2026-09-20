# Automation OS — Project Status

> **Single entry point for current project state.**
>
> Read this file first when you want to know where the project stands, what has been completed, and what is allowed next.

## Current State

| Item | Status |
|---|---|
| Current phase | **Phase 8.7 — Execution Recovery** |
| Phase status | **Phase 8.7 completed — execution recovery merged and CI-verified** |
| Active implementation | **Phase 8.7 Execution Recovery implemented in PR #241; final CI run #1104 passed** |
| GitHub source of truth | `master` |
| Latest documented milestone | **Phase 8.7 Execution Recovery — stale RUNNING recovery, conditional persistence, recovery evidence, CI run #1104 passed** |
| Next major capability | **Next capability requires a new Design Gate** |
| Next decision gate | **To be defined through the next capability mapping/design cycle** |

## Current Roadmap

The authoritative high-level roadmap is:

- `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md`

The current logical runtime/architecture map is:

- `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md`

The ordered post-Phase-7 capability sequence remains:

- `docs/01-Roadmap/POST_PHASE_7_CAPABILITY_EXECUTION_SEQUENCE.md`

The roadmap has now been aligned with the actual repository state and separates:
- completed capabilities;
- the current design-stage capability;
- future capabilities;
- dependency pressure;
- product goals;
- explicit non-goals.

## Active Repository Reconciliation

During Phase 8.4 design preparation, repository inspection found an earlier scheduling/trigger runtime implementation (`Event`, `TriggerMatcher`, `ScheduledExecutionRequest`, and `StartDueWorkflowExecution`). It is retained as repository evidence while the current Design Gate defines the broader trigger-invocation contract. No second competing mechanism will be introduced without an explicit reconciliation decision.

## Latest Milestone

Phase 8.3 Human-in-the-Loop was completed through PR **#236** and CI-verified.

Phase 8.4 Scheduling / Triggers is complete. The application-level Trigger Invocation boundary was merged and master CI was verified on run #1029 with 480 passing tests.

Phase 8.5 Capability Provider System is complete through PR #239. The approved provider resolver was implemented, legacy capability contract duplication was removed, and final implementation branch CI runs #1042 and #1043 passed with 470 tests.

## Current Position

Completed:

`Phase 7 → hardening → Phase 8.1 Builder → Phase 8.2 Conditions → Phase 8.3 HITL → Phase 8.4 Triggers → Phase 8.5 Providers → Phase 8.6 Durable Persistence`

Current:

`Phase 8.7 Execution Recovery — COMPLETED / verified`

Next:

`New capability discovery/design gate required`

Phase 8.5 exit review is recorded in `docs/02-Architecture/PHASE_8_5_CAPABILITY_PROVIDER_EXIT_REVIEW.md`. Phase 8.6 exit review is recorded in `docs/02-Architecture/PHASE_8_6_DURABLE_PERSISTENCE_EXIT_REVIEW.md`. Phase 8.7 exit review is recorded in `docs/02-Architecture/PHASE_8_7_EXECUTION_RECOVERY_EXIT_REVIEW.md`.

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
- Phase 7 execution reliability and operational visibility;
- end-to-end concurrent workflow-start idempotency backed by PostgreSQL durable persistence;
- explicit human decision requests and deterministic decision handling;
- provider-independent capability resolution with deterministic default-provider selection.

## Phase 7 Reliability Limitation

The atomic idempotency guarantee is verified against PostgreSQL under concurrent workflow-start requests. The PostgreSQL execution-start adapter owns the durable transaction boundary and the database uniqueness constraint protects the idempotency invariant.

## Roadmap Execution Rule

Every major capability follows:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

Safe autonomous work may continue during design preparation, including repository inspection, documentation, dependency mapping, test planning, and non-direction-changing maintenance.

A significant architecture/product decision remains a Project Owner decision.

## Where To Look

| Need | Start here |
|---|---|
| **Where are we?** | **This file** |
| **High-level roadmap** | `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md` |
| **Logical runtime map** | `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md` |
| **Capability sequence** | `docs/01-Roadmap/POST_PHASE_7_CAPABILITY_EXECUTION_SEQUENCE.md` |
| **Current Phase 8.4 gate** | `docs/02-Architecture/PHASE_8_4_SCHEDULING_TRIGGERS_DESIGN_GATE.md` |
| Architecture decisions | `docs/04-DECISIONS/` |
| Development history | `docs/06-Journal/DEVELOPMENT_HISTORY.md` |
| Autonomous work rules | `AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md` |
| Engineering operating rules | `AGENTS.md` |


## Phase 8.7 Completion Record

Phase 8.7 Execution Recovery is complete. Stale RUNNING executions transition to FAILED under configurable timeout policy, recovery remains separate from retry and workflow execution, WAITING executions are not automatically changed, recovery is deterministic and sequential, and persistence enforces the conditional transition. Recovery evidence is recorded in execution history. Heartbeats, leases, workers, queues, automatic retry, and distributed recovery remain deferred. CI run #1104 passed for the final implementation commit.
