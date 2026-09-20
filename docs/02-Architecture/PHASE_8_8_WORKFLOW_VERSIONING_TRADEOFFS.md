# Phase 8.8 — Workflow Versioning Trade-offs

## Decision

The Project Owner selected **Option A1: first-class Workflow Version with Workflow retained as the logical container**.

## Why A1

The platform needs two distinct identities:

- Workflow: the stable logical automation artifact used by discovery and ownership boundaries.
- WorkflowVersion: the immutable executable definition selected by an execution.

This separation makes execution history reproducible without forcing marketplace, discovery, and future planning features to treat every revision as a new logical workflow.

## Main trade-offs

| Choice | Benefit | Cost | Decision |
|---|---|---|---|
| First-class version identity | Explicit traceability and stable executable artifact | New domain/repository/schema concepts | **Accepted** |
| Keep existing Workflow identity | Lower migration risk and preserves existing APIs | Transitional overlap between workflow definition and version snapshot | **Accepted** |
| Immutable published versions | Historical executions remain interpretable | New changes require a new version | **Accepted** |
| Explicit version on Execution | Reproducible execution evidence | Execution schema gains another identity | **Accepted** |
| Legacy compatibility | Existing persisted workflows remain usable | Transitional fallback/migration logic | **Accepted** |
| Deterministic default resolution | Existing callers need not provide version IDs | Must define exactly one selected published version | **Accepted** |

## Explicit non-decisions

This phase does not introduce automatic migration, diff/merge, semantic compatibility, rollback automation, AI-generated versions, marketplace negotiation, or distributed rollout.

## Compatibility rule

Existing workflows without a persisted version are treated as legacy definitions. The first version-aware start boundary materializes version 1 without changing the logical workflow identity. New version-aware writes persist the explicit version artifact.

## Version selection rule

When no explicit version is supplied, the application resolves the latest published version deterministically by version number. Explicit version selection is available for reproducible starts.

## Execution rule

An execution stores the selected workflow_version_id. Existing executions without that field remain loadable as legacy executions and retain their existing workflow_id semantics.
