# Phase 8.8 — Workflow Versioning Design Gate

## Status
**Accepted — Project Owner selected Option A1; implementation may proceed**

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

1. What is the identity of a workflow version?
2. Is a published version immutable?
3. How is a new version created?
4. What version does StartWorkflowExecution select when a workflow has multiple versions?
5. Which version does an existing Execution retain?
6. Can a draft version be replaced/abandoned?
7. What does workflow discovery return: logical workflow, version, or both?
8. What does marketplace installation identify?
9. How are existing persisted workflows migrated?
10. What is the compatibility contract for future version-aware APIs?

## 5. Candidate Models

### Option A — Version as a first-class immutable Workflow Version aggregate

A logical workflow identity owns immutable versions. A version contains the executable definition; publication applies to a specific version. Execution stores the version identity.

Advantages:
- strongest semantic separation between logical workflow and immutable executable artifact;
- execution traceability is explicit;
- marketplace/version-aware APIs have a stable artifact identity;
- future migration and compatibility policies can be expressed without mutating history.

Trade-offs:
- introduces a new domain concept and repository/persistence structures;
- requires migration from current one-row-per-workflow storage;
- discovery/start APIs need explicit logical-workflow versus version semantics.

### Option B — Add version fields directly to Workflow and Execution

Keep Workflow as the primary aggregate and add a version number/revision identifier. Published revisions are immutable; creating a new revision increments the version.

Advantages:
- smaller conceptual change;
- fewer new aggregate types;
- simpler initial migration.

Trade-offs:
- logical identity and executable revision remain mixed inside one aggregate;
- future marketplace/distribution semantics become less explicit;
- repository/API semantics can become ambiguous when callers ask for the workflow versus a version.

### Option C — Snapshot the Workflow definition into Execution only

Keep Workflow identity unchanged and copy its definition into each Execution at start time.

Advantages:
- existing execution remains reproducible without a workflow-version domain concept;
- minimal workflow persistence change.

Trade-offs:
- does not provide versioned reusable workflow artifacts;
- duplicates workflow definitions into executions;
- discovery/marketplace/planning cannot reference stable versions;
- future edits and publication history remain implicit rather than explicit.

## 6. Recommended Direction

Option A — first-class immutable Workflow Version is the recommended architectural direction because the platform roadmap explicitly places Versioning before Marketplace Expansion and AI Planning, while durable execution already requires historical definitions to remain stable.

This is a recommendation, not an implementation decision.

## 7. Important Secondary Decision

If Option A is selected, the next decision is how the existing Workflow identity relates to versions:

- A1: keep Workflow as the logical container and introduce WorkflowVersion as the immutable executable artifact;
- A2: rename/restructure the existing aggregate around versioned definitions.

A1 is the lower-risk migration path because it preserves the current Workflow vocabulary and application boundaries while adding the missing immutable artifact.

## 8. Proposed Initial Semantics if A1 Is Selected

- A logical Workflow can have multiple versions.
- Each version has immutable definition data and a stable version identity.
- A version moves through DRAFT/PUBLISHED semantics independently.
- Published versions cannot be mutated.
- Creating a new version never mutates an existing published version.
- Execution stores the selected version identity.
- Existing executions keep their original version even when a newer version is published.
- Start without an explicit version resolves deterministically to the logical workflow's designated published version.
- Explicit version selection is supported where the caller requires reproducibility.
- Version resolution remains outside the Execution aggregate.
- No automatic migration of running executions to a newer version.

## 9. Migration Constraint

The first implementation must preserve existing workflows and executions. No destructive rewrite of historical execution identity or evidence is acceptable.

## 10. Out of Scope

- automatic workflow migration;
- semantic compatibility scoring;
- workflow diff/merge tooling;
- marketplace version negotiation;
- AI-generated workflow versions;
- rollback automation;
- distributed deployment/version rollout;
- multi-tenant authorization.

## 11. TDD RED Plan After Decision

Tests should cover, at minimum:

- creating a new workflow version;
- published version immutability;
- creating a new version from an existing definition;
- deterministic published-version resolution;
- explicit version selection;
- execution persistence of selected version;
- old execution retaining its original version;
- durable PostgreSQL version persistence;
- migration compatibility with pre-versioning workflows;
- concurrent version creation semantics if required by the selected model.

## 12. Exit Criteria

Phase 8.8 is complete only when the selected model is implemented, persisted, tested against in-memory and PostgreSQL adapters, integrated with workflow start semantics, documented, and verified by full CI.

## 13. Decision Record

**Selected:** Option A — first-class immutable Workflow Version.

**Secondary selection:** A1 — keep Workflow as the logical workflow container and introduce WorkflowVersion as the immutable executable artifact.

The implementation must preserve existing workflow and execution identities, introduce explicit version identity, and maintain backward-compatible loading of pre-versioning persisted workflows.

**Project Owner approval:** Granted.

## 14. Decision Required

Before RED/implementation, the Project Owner must select:

The decision is recorded above; implementation proceeds under A1.
