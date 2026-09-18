# Workflow Generation Design Gate

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

## Boundary

**Intent → WorkflowGenerator → WorkflowCandidate/DRAFT Workflow**

The generator is an application boundary.

Concrete AI generation adapters belong in infrastructure, analogous to `IntentAnalyzer`.

## Safety Invariant

The platform must never transform:

**NO_MATCH → AI-generated workflow → automatic execution**

The required path is:

**NO_MATCH → generate DRAFT → validate → review/publish → normal StartWorkflowExecution**

## TDD Order

1. Generated workflow candidate vocabulary.
2. Generator application boundary.
3. Validation of goals, parameters, steps, and capability identities.
4. AI adapter with deterministic fake provider.
5. NO_MATCH → generate composition.
6. Explicit publish/review boundary.
7. Concrete provider adapter only after the boundary is proven.

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
- existing workflows are never silently modified;
- deterministic execution remains the only execution path.
