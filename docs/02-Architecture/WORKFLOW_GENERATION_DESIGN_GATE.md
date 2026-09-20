# Workflow Generation Design Gate

## Status

**Accepted — architecture approved; implementation may proceed within this gate.**

## Purpose

Define a safe boundary for generating new workflow definitions when no existing published workflow can satisfy an Intent.

## Problem

Exact canonical-goal selection can return NO_MATCH. Platform generalization eventually needs a way to turn a supported business intent into a candidate workflow without allowing AI to silently modify or execute production workflows.

## Committed Decisions

1. Workflow generation is separate from workflow selection.
2. Generation is allowed only after deterministic selection returns NO_MATCH.
3. Generated workflows are always DRAFT.
4. A generated workflow cannot be executed directly.
5. Publishing remains an explicit workflow lifecycle transition.
6. Generation produces a provider-neutral workflow definition candidate.
7. AI may propose workflow structure, but it does not publish, execute, or mutate an existing workflow.
8. Generated capabilities must reference known capability identities; generation cannot invent executable provider code.
9. Required parameters and supported goals must be explicit in the generated definition.
10. Invalid or unsupported capability references reject the generated candidate.
11. Existing workflow execution remains unchanged.
12. Generation failures are explicit and cannot fall through to execution.
13. Human review/approval remains outside the execution engine; an eventual product/API layer may expose it.
14. No autonomous self-modification, recursive planning, agent loop, or automatic publication is introduced.
15. Capability identity validation is a read-only application boundary. The generator and validator depend on capability identity resolution, not concrete provider implementations.
16. Capability identity resolution must not mutate provider state, install capabilities, or select executable provider behavior as part of generation.

## Boundary

**Intent → Deterministic Selection → NO_MATCH → WorkflowGenerator → WorkflowCandidate → Deterministic Validation → DRAFT Workflow**

The generator is an application boundary.

A dedicated read-only capability identity resolution boundary validates that generated capability references are known. It does not execute capabilities or choose provider implementations.

Concrete AI generation adapters belong in infrastructure, analogous to IntentAnalyzer.

## Safety Invariant

The platform must never transform:

**NO_MATCH → AI-generated workflow → automatic execution**

The required path is:

**NO_MATCH → generate DRAFT → validate → review/publish → normal StartWorkflowExecution**

## TDD Order

1. Generated workflow candidate vocabulary.
2. Generator application boundary.
3. Read-only capability identity resolution boundary.
4. Validation of goals, parameters, steps, and capability identities.
5. AI adapter with deterministic fake provider.
6. NO_MATCH → generate composition.
7. Explicit publish/review boundary.
8. Concrete provider adapter only after the boundary is proven.

## Deferred

- autonomous workflow optimization;
- workflow mutation;
- automatic publishing;
- marketplace templates;
- semantic workflow synthesis;
- recursive planning;
- agent loops.

## Exit Criteria

- generation cannot bypass publication;
- generated workflows are provider-neutral;
- unsupported capabilities are rejected;
- capability identity validation is read-only;
- existing workflows are never silently modified;
- deterministic execution remains the only execution path.
