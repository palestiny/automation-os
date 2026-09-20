# Phase 8.8 — Workflow Versioning Exit Review

## Status

**Completed — A1 implemented, verified, merged, and master state is aligned.**

## 1. Selected Architecture

The Project Owner approved **Option A1**:

- Workflow remains the logical workflow container.
- WorkflowVersion is the first-class immutable executable artifact.
- Published workflow versions cannot be mutated.
- Executions persist the selected workflow_version_id.
- Start without an explicit version deterministically resolves the latest published version.
- Explicit version selection is supported.
- Version resolution remains outside the Execution aggregate.
- Existing legacy executions with no version identity remain loadable and use the existing logical Workflow definition as a backward-compatible fallback.
- No automatic migration of running executions to newer versions is performed.

## 2. Delivered

### Domain

- Added WorkflowVersion with stable identity, workflow ownership, version number, definition snapshot, and DRAFT/PUBLISHED lifecycle.
- Added domain validation for executable version definitions.
- Added published-version immutability guards.
- Added cloning from the logical Workflow and from an existing version.

### Application

- Added workflow-version creation boundary.
- Added workflow-version publication boundary.
- Extended workflow start to resolve or explicitly select a published version.
- Ensured execution step execution uses the version selected by the Execution rather than silently reading a newer logical Workflow definition.

### Persistence

- Added in-memory workflow-version repository.
- Added PostgreSQL workflow_versions persistence with unique (workflow_id, version_number).
- Added nullable workflow_version_id to executions for migration compatibility.
- Added atomic save_if_absent semantics for first-start version materialization.
- Extended execution persistence and conditional updates to retain version identity.

### API / Projection

- Added workflow_version_id to execution progress and HTTP responses.
- Added optional workflow_version_id to workflow-start API requests.

### Verification

- Added TDD coverage for creation, cloning, publication, immutability, deterministic resolution, explicit selection, execution/version binding, and PostgreSQL persistence.
- Corrected the existing PostgreSQL repository contract test after the version repository was introduced.
- GitHub Actions run #1167 completed successfully for implementation head commit 7b0eaeb44d09593ab42a83778e53eb905cf098.
- The workflow job completed all setup, dependency, test, and teardown steps successfully.

## 3. Migration / Compatibility Result

The implementation intentionally avoids a destructive rewrite of existing workflow or execution identities.

- Existing Workflow identities remain valid.
- Existing Execution rows may have workflow_version_id = NULL.
- Newly started executions receive a version identity when the version repository is configured.
- A legacy published workflow can materialize version 1 on first start.
- The atomic version materialization path prevents duplicate version-1 artifacts under concurrent first-start attempts.

## 4. Deferred Scope

The following remain intentionally outside Phase 8.8:

- automatic migration of running executions;
- workflow diff/merge tooling;
- semantic compatibility scoring;
- version rollback automation;
- distributed rollout/deployment strategies;
- AI-generated versions;
- marketplace version negotiation;
- multi-tenant authorization;
- background version allocation workers or queues;
- broad marketplace/discovery migration from logical Workflow identity to version identity.

Concurrent allocation of arbitrary new draft version numbers is also not expanded into a separate allocation service in this phase; the atomic save_if_absent path specifically protects first-start materialization.

## 5. Exit Assessment

The selected A1 model is implemented across domain, application, persistence, execution, API projection, tests, and documentation.

Phase 8.8 is therefore **complete**. PR #242 was merged and the repository state is aligned.
