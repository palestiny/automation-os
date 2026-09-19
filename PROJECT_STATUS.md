# Automation OS — Project Status

> **Single entry point for current project state.**
>
> Read this file first when you want to know where the project stands, what has been completed, and what is allowed next.

## Current State

| Item | Status |
|---|---|
| Current phase | **Phase 8.4 — Scheduling / Triggers** |
| Phase status | **DESIGN PREPARATION — decision pending** |
| Active implementation | **Roadmap realignment completed; Phase 8.4 design preparation active** |
| GitHub source of truth | `master` |
| Latest documented milestone | **Master roadmap + logical workflow map established** |
| Next major capability | **Scheduling / Triggers** |
| Next decision gate | **Phase 8.4 Scheduling / Triggers Design Gate — Option A/B** |

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

The current work is Phase 8.4 Scheduling / Triggers. Its Design Gate is intentionally still pending the Project Owner's architecture choice between the two documented alternatives.

## Current Position

Completed:

`Phase 7 → hardening → Phase 8.1 Builder → Phase 8.2 Conditions → Phase 8.3 HITL`

Current:

`Phase 8.4 Scheduling / Triggers — Design Preparation`

Next after successful completion:

`Phase 8.5 Capability Provider System`

The implementation must not silently skip the Phase 8.4 decision gate or pull later capabilities into its scope.

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
- end-to-end concurrent workflow-start idempotency for the current in-memory persistence model;
- explicit human decision requests and deterministic decision handling.

## Phase 7 Reliability Limitation

The atomic idempotency guarantee is verified for the current in-memory persistence model.

Durable persistence must provide an equivalent transaction/atomic persistence primitive before it can claim the same contract.

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
