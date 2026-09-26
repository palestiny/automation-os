# Automation OS — Project Status

> **Single entry point for current project state.**
>
> Read this file first when you want to know where the project stands, what has been completed, and what is allowed next.

## Current State

| Item | Status |
|---|---|
| Current phase | **Post-Phase-7 reliability hardening / Workflow Generation runtime-gate verification** |
| Phase status | **Workflow Generation boundary is implemented through persisted publication; workflow-start idempotency regression coverage is merged and master CI-verified** |
| Active implementation | **Architecture consistency pass / maintenance verification** |
| GitHub source of truth | `master` — **mandatory fresh-state read before every autonomous session** |
| Latest verified commit | `d7964668430658d84cda90cc7c3f9693f6fe7c2c` — merged workflow-start idempotency regression coverage |
| Latest CI verification | **GitHub Actions Tests run #1840 — success** |
| Next major capability | **Not defined — no future major capability is committed** |
| Next decision gate | **Required before any future major capability or material architecture change** |

## Current Roadmap

The authoritative high-level roadmap is:

- `docs/01-Roadmap/AUTOMATION_OS_MASTER_ROADMAP.md`
- `docs/02-Architecture/AUTOMATION_OS_LOGICAL_WORKFLOW_MAP.md`
- `docs/02-Architecture/WORKFLOW_GENERATION_DESIGN_GATE.md`
- `docs/02-Architecture/PHASE_8_8_WORKFLOW_VERSIONING_DESIGN_GATE.md`
- `docs/02-Architecture/PHASE_8_8_WORKFLOW_VERSIONING_EXIT_REVIEW.md`
- `docs/04-DECISIONS/PHASE_7_IDEMPOTENCY_CONCURRENCY_DECISION.md`

## Latest Verified Milestone

The current master state has completed the workflow-generation publication/runtime boundary and the latest workflow-start idempotency regression hardening.

Verified generation path:

`Intent → Deterministic Selection → NO_MATCH → WorkflowGenerator → WorkflowCandidate → Deterministic Validation → Materialize → Persist DRAFT → Review/Publish → Persist PUBLISHED → StartWorkflowExecution`

Runtime start accepts only persisted `PUBLISHED` workflows. Workflow-version-aware starts additionally require a published workflow version when an explicit version is supplied.

PR #306 is merged and verifies:
- replaying the same idempotency key to the same execution;
- conflicting use of the same key across workflows;
- explicit failure for orphaned idempotency records;
- required coordination boundaries for idempotent starts.

## Current Position

Completed / verified:

`Phase 7 reliability foundations → Workflow Versioning → Workflow Generation boundaries → generated DRAFT persistence → explicit publication persistence → runtime publication/version integrity → workflow-start idempotency regression hardening`

Current:

`Post-roadmap maintenance / architecture consistency verification`

Next:

`Documentation reconciliation, dependency/contract inspection, safe cleanup, and preparation of any future Design Gate only. No future major capability is committed.`

## Verified Architectural Contracts

### Workflow Generation

- Generation occurs only after deterministic selection returns `NO_MATCH`.
- Generated candidates are provider-neutral.
- Candidate validation is deterministic and capability identity resolution is read-only.
- Generated workflows are materialized as DRAFT and persisted before review.
- Publication is explicit and persists PUBLISHED state.
- Runtime execution cannot start a DRAFT workflow.
- AI adapters cannot publish, execute, or mutate workflows.
- No autonomous self-modification, recursive planning, agent loop, or automatic publication is introduced.

### Workflow Versioning

- Workflow remains the logical workflow container.
- `WorkflowVersion` is the immutable executable artifact.
- Published versions cannot be mutated.
- Executions retain the selected `workflow_version_id`.
- Start without an explicit version resolves deterministically to the latest published version when the version repository is configured.
- Explicit version selection rejects missing, cross-workflow, and non-published versions.
- Legacy workflows may materialize version 1 on first start for backward compatibility.
- No automatic migration of running executions to newer versions is performed.

### Workflow Start Idempotency

- Idempotency keys are normalized before use.
- A successful key maps to one execution.
- Same-key reuse for a different workflow is a conflict.
- Concurrent duplicate starts use the atomic execution-start persistence boundary.
- An orphaned idempotency reference is an explicit failure rather than silently creating another execution.
- Idempotent starts require both the idempotency and atomic execution-start persistence boundaries.
- The latest regression coverage is merged on master.

## Verification Evidence

- GitHub Actions Tests run **#1840**: completed successfully for master commit `d7964668430658d84cda90cc7c3f9693f6fe7c2c`.
- PR **#306**: merged; regression coverage for workflow-start idempotency contract.
- Workflow generation publication/runtime gate: accepted and implementation-complete.
- Workflow versioning: Phase 8.8 exit review records A1 as implemented, verified, and merged.
- Phase 7 idempotency concurrency decision: Option A atomic reservation + execution persistence is documented as implemented and verified.

The current master state is therefore CI-verified.

## Known Architecture Review Items

These are **review items, not declared defects**:

1. Inspect the role of `idempotency_repository` versus `execution_start_repository` in `StartWorkflowExecution` and determine whether the former is a compatibility/configuration guard or an obsolete dependency.
2. Decide/document semantics when an idempotency key is replayed with a different explicit `workflow_version_id`. Current behavior checks the existing idempotency association before version resolution; this must remain intentional and documented if retained.
3. Reconcile the existing first-start workflow-version materialization fallback with the explicit workflow publication boundary. This behavior is documented as backward-compatible and must not be changed without an architecture decision.
4. Verify durable adapters provide the equivalent atomic idempotency + execution persistence guarantee required by the Phase 7 decision; the in-memory lock alone is not a claim of durable transaction semantics.

No item above authorizes an implementation change by itself.

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
| **Workflow generation gate** | `docs/02-Architecture/WORKFLOW_GENERATION_DESIGN_GATE.md` |
| **Workflow versioning** | `docs/02-Architecture/PHASE_8_8_WORKFLOW_VERSIONING_DESIGN_GATE.md` |
| **Idempotency concurrency decision** | `docs/04-DECISIONS/PHASE_7_IDEMPOTENCY_CONCURRENCY_DECISION.md` |
| Architecture decisions | `docs/04-DECISIONS/` |
| Development history | `docs/06-Journal/DEVELOPMENT_HISTORY.md` |
| Autonomous work rules | `AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md` |
| Engineering operating rules | `AGENTS.md` |

## Next Decision Boundary

The committed capability sequence currently has no new major capability selected.

Safe maintenance, verification, documentation reconciliation, cleanup, and future Design Gate preparation may continue.

Any future major capability or material architecture change requires:
1. explicit Project Owner decision;
2. documented trade-offs;
3. an approved Design Gate;
4. implementation followed by RED → GREEN → VERIFY → EXIT REVIEW.

No future major capability is currently committed.
