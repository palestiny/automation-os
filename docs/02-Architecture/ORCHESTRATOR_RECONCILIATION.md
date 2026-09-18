# Phase 3 — Orchestrator Reconciliation

Status: Design decision
Date: 2026-09-18
Issue: #44

## Decision

`StartWorkflowExecution` is the authoritative application use case for starting an execution from a persisted Workflow.

The existing `Orchestrator.start(workflow)` is retained temporarily as a legacy in-memory orchestration API for compatibility with Phase 2 tests and callers, but it must not become a second persistence-backed execution-start path.

## Rationale

The new use case owns the application boundary because it coordinates:
- WorkflowRepository lookup;
- publication eligibility;
- Execution creation and lifecycle transition;
- ExecutionRepository persistence.

The legacy Orchestrator accepts an already-loaded Workflow and therefore cannot provide the same persistence boundary without changing its contract substantially.

## Migration Rule

New application code that starts executions must use `StartWorkflowExecution`.

The legacy Orchestrator should be removed or repurposed only when all known callers have migrated and its compatibility value is no longer needed.

No new behavior should be added to the legacy Orchestrator.

## Deferred

- replacing the Orchestrator with a compatibility facade;
- deleting the legacy module;
- transaction/Unit of Work integration;
- capability execution orchestration.

## Consequence

There is now one authoritative persisted execution-start path while the Phase 2 compatibility surface remains stable during migration.
