# Automation OS — Project Status

> **Single entry point for current project state.**
>
> Read this file first when you want to know where the project stands, what has been completed, and what is allowed next.

## Current State

| Item | Status |
|---|---|
| Current phase | **Post-Phase-7 reliability hardening / Workflow Generation runtime-gate verification** |
| Phase status | **Workflow Generation boundary is implemented through persisted publication; workflow-start idempotency regression and replay semantics are merged and master CI-verified; architecture consistency review is closed** |
| Active implementation | **Post-roadmap maintenance / architecture consistency review closed** |
| GitHub source of truth | `master` — **mandatory fresh-state read before every autonomous session** |
| Latest verified commit | `6a7ac344f06b0fe6026b5f7b5a2541504ea251ca` — architecture consistency review closure |
| Latest CI verification | **GitHub Actions Tests run #1848 — success** |
| Repository hygiene | **1 branch (master), 0 open PRs** |
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
- `docs/04-DECISIONS/WORKFLOW_START_ARCHITECTURE_CONSISTENCY_REVIEW.md`

## Latest Verified Milestone

The current master state has completed the workflow-generation publication/runtime boundary, workflow-start idempotency hardening, explicit version-replay characterization, and the architecture consistency review covering the remaining workflow-start design questions.

Verified generation path:

`Intent → Deterministic Selection → NO_MATCH → WorkflowGenerator → WorkflowCandidate → Deterministic Validation → Materialize → Persist DRAFT → Review/Publish → Persist PUBLISHED → StartWorkflowExecution`

Runtime start accepts only persisted `PUBLISHED` workflows. Workflow-version-aware starts additionally require a published workflow version when an explicit version is supplied.

PR #308 is merged and verifies:
- replaying an idempotent start with the same key returns the original execution;
- replaying the same key with a different explicit published workflow version still returns the original execution/version;
- no second execution is persisted.

PR #309 is merged and closes the architecture consistency review. The review decisions are documented without changing production behavior.

## Current Position

Completed / verified:

`Phase 7 reliability foundations → Workflow Versioning → Workflow Generation boundaries → generated DRAFT persistence → explicit publication persistence → runtime publication/version integrity → workflow-start idempotency regression hardening → replay semantics characterization → workflow-start architecture consistency review`

Current:

`Post-roadmap maintenance / verification`

Next:

`Safe documentation reconciliation, dependency/contract inspection, cleanup, and preparation of any future Design Gate only. No future major capability is committed.`

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
- Reuse of an idempotency key is authoritative to the original persisted execution, including its workflow version.
- A replay with a different explicit workflow version does not create or switch the execution.

## Architecture Consistency Review Outcome

The review in `docs/04-DECISIONS/WORKFLOW_START_ARCHITECTURE_CONSISTENCY_REVIEW.md` is **closed**.

1. `idempotency_repository` vs `execution_start_repository`: **KEEP + DOCUMENT**.
2. Same-key replay with a different explicit workflow version: **KEEP + DOCUMENT**.
3. First-start workflow-version materialization: **KEEP for backward compatibility**.
4. Durable atomicity: **KEEP contract + VERIFIED for PostgreSQL**.

No production behavior was changed by the review.

## Verification Evidence

- GitHub Actions Tests run **#1848**: completed successfully for master commit `6a7ac344f06b0fe6026b5f7b5a2541504ea251ca`.
- PR **#309**: merged; architecture consistency review closed.
- PR **#308**: merged; regression coverage for workflow-version replay semantics.
- Workflow generation publication/runtime gate: accepted and implementation-complete.
- Workflow versioning: Phase 8.8 exit review records A1 as implemented, verified, and merged.
- Phase 7 idempotency concurrency decision: Option A atomic reservation + execution persistence is documented as implemented and verified.
- PostgreSQL `PostgresExecutionStartRepository`: source inspection confirms idempotency registration and execution persistence are performed inside one PostgreSQL transaction.

The current master state is therefore CI-verified.

## Repository Hygiene

Current GitHub state:

- `master` is the only branch.
- 0 open pull requests.
- No stale working branch remains from the closed architecture review.

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
| **Architecture consistency review** | `docs/04-DECISIONS/WORKFLOW_START_ARCHITECTURE_CONSISTENCY_REVIEW.md` |
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
