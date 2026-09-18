# Phase 6 — Intent Analysis & Workflow Selection Exit Review

## Status

Completed for the committed intent-analysis and deterministic workflow-selection slice.

Phase 6 as a whole remains open because workflow generation, multiple automation domains, marketplace/ecosystem foundations, and broader provider abstraction are still deferred.

## Completed Scope

- Provider-neutral `Intent` vocabulary.
- `IntentAnalyzer` application boundary.
- Deterministic workflow selection using explicit `supported_goals`.
- Explicit SELECTED / NO_MATCH / AMBIGUOUS outcomes.
- Intent-to-execution composition through `StartWorkflowExecution`.
- Concrete OpenAI intent-analysis adapter with structured output.
- Canonical `IntentGoalCatalog`.
- Goal validation at the AI adapter boundary when a catalog is configured.
- Goal validation again at the intent-to-execution boundary when a catalog is supplied.
- Raw request → analysis → selection → execution composition.
- No AI dependency in the domain.
- No autonomous agent loop.
- No workflow generation.
- No semantic/vector workflow matching.

## Architectural Invariants

1. AI analyzes language; it does not select or execute workflows.
2. Workflow selection remains deterministic.
3. Existing published workflows are the only executable targets.
4. Execution still starts through `StartWorkflowExecution`.
5. Unknown or invalid goals cannot start execution when the canonical catalog is configured.
6. Provider failures and malformed structured output stop before execution.
7. Concrete AI SDK details remain in infrastructure.
8. No second execution lifecycle was introduced.

## Verification

The implementation was merged through PRs #113, #115, #117, #120, #122, #123, #125, #126, and #130.

The latest hardening change passed CI before merge.

## Deferred

- Workflow generation.
- Autonomous planning/agent loops.
- Semantic/vector matching.
- Model routing and fallback providers.
- Conversation memory.
- Marketplace-owned goal registration.
- Dynamic workflow discovery.
- Multiple concrete automation domains beyond the existing content domain.

## Exit Decision

The intent-analysis and deterministic workflow-selection slice is architecturally understood, tested, documented, and integrated with the existing execution engine.

The next Phase 6 work should expand platform capabilities without weakening these boundaries.
