# Repository Reconciliation Decision

Status: **Committed maintenance decision**

Date: 2026-10-01

## Problem

The repository state and `PROJECT_STATUS.md` were inconsistent.

The status document previously claimed:

- 1 branch (`master`);
- 0 open pull requests.

Fresh GitHub state shows:

- `master`;
- 22 additional historical/runtime-connection branches;
- 0 open pull requests.

This is governance drift, not a runtime defect.

## Root Cause

The repository status document was updated as if historical branches had been removed, but the corresponding GitHub refs were still present.

The status tracker therefore stopped reflecting the actual GitHub source of truth.

## Decision

1. GitHub remains the source of truth for branch state.
2. `PROJECT_STATUS.md` must report the verified branch state rather than an intended cleanup state.
3. No branch is deleted automatically in this phase because branch deletion is destructive/irreversible from the project workflow perspective.
4. Historical branches are classified for cleanup rather than silently deleted.
5. Branch deletion, when performed, must be an explicit cleanup action after verifying that each branch is merged/superseded and contains no unique required work.
6. No new major capability is selected by this reconciliation.

## Current Branch Classification

### Keep

- `master` — source-of-truth branch.

### Historical candidates for cleanup

The following non-master branches are historical runtime-connection/protected-context implementation branches and currently have no open PR:

- `docs/runtime-connection-execution-dependency-gate`
- `feat/harden-runtime-context`
- `feat/integrate-runtime-connection-preparation`
- `feat/protect-runtime-context`
- `feat/protected-runtime-context`
- `feat/review-operations-read-models`
- `feat/runtime-connection-context-boundary`
- `feat/runtime-connection-execution-composition`
- `feat/runtime-connection-execution-gate`
- `feat/runtime-connection-execution-gate-v2`
- `feat/runtime-connection-integration`
- `feat/runtime-connection-preparation-integration`
- `feat/runtime-preparation-application-seam`
- `feat/runtime-step-connection-preparation`
- `feat/tenant-aware-runtime-composition`
- `feat/wire-runtime-connection-preparation`
- `fix/protected-runtime-context-current`
- `fix/runtime-connection-boundary-test-suite`
- `fix/runtime-connection-preparation-context`
- `fix/runtime-connection-preparation-context-boundary`
- `fix/runtime-preparation-context-boundary`
- `test/runtime-connection-preparation-integration`

These are candidates, not deleted refs.

## Verification

At reconciliation time:

- open PR count: 0;
- master exists;
- non-master historical branches are present;
- current master status text is stale about branch count.

## Exit Criteria

Phase A is complete when:

- `PROJECT_STATUS.md` reflects the actual GitHub branch state;
- the reconciliation decision is documented;
- no destructive branch deletion is performed implicitly;
- subsequent hardening work uses the corrected status as its source of truth.

Branch deletion remains a separate cleanup operation.
