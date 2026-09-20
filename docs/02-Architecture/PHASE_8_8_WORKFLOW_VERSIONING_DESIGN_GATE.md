# Phase 8.8 — Workflow Versioning Design Gate

## Status
**Implemented — Project Owner selected Option A1; implementation and CI verification completed**

## 1. Problem

Automation OS currently persists a Workflow aggregate by one identity. A Workflow starts as DRAFT and can become PUBLISHED; published workflows are not editable through the existing mutation boundaries. Executions reference the workflow identity, but there is currently no explicit immutable workflow revision/version identity.

Durable persistence and execution recovery now make the missing version boundary material: a workflow definition may evolve over time while existing executions and historical evidence must remain interpretable against the definition that was actually executed.

## 2. Goal

Introduce a minimal, explicit versioning boundary that allows:

- immutable published workflow definitions;
- new revisions without mutating the definition used by existing executions;
- execution-to-version traceability;
- deterministic selection/start semantics;
- PostgreSQL durable persistence without weakening existing execution guarantees;
- future marketplace and AI-planning consumers to refer to stable workflow artifacts.

## 3. Repository Evidence

Current Workflow has:
- one UUID identity;
- DRAFT/PUBLISHED lifecycle;
- ordered steps;
- triggers, goals, parameters, domain and discovery tags;
- published workflows reject step mutation.

Current Execution stores only workflow_id, not a workflow revision/version identifier.

Current PostgreSQL schema stores one row per workflow identity and its definition payload.

No version-named domain, repository, schema, or application boundary currently exists.

## 4. Required Semantic Questions

The implementation establishes the following answers:

1. A workflow version has its own UUID identity and belongs to one logical Workflow.
2. A published version is immutable through domain mutation guards.
3. A new version is created as a draft by cloning the latest published version, or by materializing version 1 from the logical Workflow when no prior version exists.
4. Start without an explicit version resolves deterministically to the latest published version.
5. An Execution retains the selected workflow_version_id for its lifetime.
6. Draft versions can be replaced by creating another version; no mutation of published versions is allowed.
7. Workflow discovery remains logical-Workflow based in this phase; version-aware discovery is deferred.
8. Marketplace installation remains logical-Workflow based in this phase; version-aware negotiation is deferred.
9. Existing persisted workflows and executions are preserved without destructive rewrite; legacy executions may retain a null version identity.
10. Version-aware execution APIs expose the selected version identity while preserving the existing workflow-start boundary.

## 5. Selected Model

### Option A1 — Workflow as logical container + WorkflowVersion as immutable executable artifact

A logical workflow identity owns immutable executable versions. A version contains the executable definition and its DRAFT/PUBLISHED lifecycle. Execution stores the selected version identity.

The implementation preserves the current Workflow vocabulary and application boundaries while introducing the missing immutable artifact.

## 6. Implemented Semantics

- A logical Workflow can have multiple versions.
- Each version has immutable definition data and a stable version identity.
- A version moves through DRAFT/PUBLISHED semantics independently.
- Published versions cannot be mutated.
- Creating a new version never mutates an existing published version.
- Execution stores the selected version identity.
- Existing executions keep their original version even when a newer version is published.
- Start without an explicit version resolves deterministically to the latest published version.
- Explicit version selection is supported where the caller requires reproducibility.
- Version resolution remains outside the Execution aggregate.
- No automatic migration of running executions to a newer version.
- Legacy executions without a version identity remain executable through the logical Workflow fallback.

## 7. Migration Constraint

The implementation preserves existing workflows and executions. No destructive rewrite of historical execution identity or evidence is performed.

## 8. Out of Scope

- automatic workflow migration;
- semantic compatibility scoring;
- workflow diff/merge tooling;
- marketplace version negotiation;
- AI-generated workflow versions;
- rollback automation;
- distributed deployment/version rollout;
- multi-tenant authorization;
- version-aware marketplace/discovery migration;
- background version allocation infrastructure.

## 9. TDD / Verification Result

Coverage includes:

- creating a new workflow version;
- published version immutability;
- creating a new version from an existing definition;
- deterministic published-version resolution;
- explicit version selection;
- execution persistence of selected version;
- execution step execution against the selected version definition;
- durable PostgreSQL version persistence;
- migration compatibility with pre-versioning workflows;
- atomic first-start version materialization semantics.

GitHub Actions run **#1167** completed successfully for implementation commit `7b0eaeb44d09593ab42a83778e53eb905cf098`, including the test job and full test step.

## 10. Exit Criteria

The selected model is implemented across domain, application, persistence, execution, API projection, tests, and documentation and has been verified by full GitHub CI.

**Phase 8.8 exit review:** `docs/02-Architecture/PHASE_8_8_WORKFLOW_VERSIONING_EXIT_REVIEW.md`

## 11. Decision Record

**Selected:** Option A — first-class immutable Workflow Version.

**Secondary selection:** A1 — keep Workflow as the logical workflow container and introduce WorkflowVersion as the immutable executable artifact.

**Project Owner approval:** Granted.

## 12. Completion Record

Implementation branch: `feature/phase-8-8-workflow-versioning`

Pull request: #242

Verified implementation head: `7b0eaeb44d09593ab42a83778e53eb905cf098`

CI run: **#1167 — success**
