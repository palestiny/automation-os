# Phase 8.10 — AI Planning Layer Design Gate

## Status
**APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

## Purpose
Introduce an AI planning boundary that translates structured intent into a validated workflow proposal without allowing an AI/model to become the execution authority.

## Architectural Decision
### Option A — Application-level Planner Port

The application owns a stable planner contract. A concrete AI/model adapter implements that contract and returns a structured workflow plan. The application validates the plan and hands only validated workflow composition to the existing WorkflowBuilder.

The planner does not execute capabilities, start executions, publish workflows automatically, mutate execution lifecycle, select providers, or bypass workflow/version validation.

Flow:
```
Structured Planning Request
          ↓
      Planner Port
          ↓
   AI/Model Adapter
          ↓
  Structured Workflow Plan
          ↓
   Plan Validator
          ↓
   WorkflowBuilder
          ↓
      Draft Workflow
```

## Committed Boundaries
1. Planner is advisory/compositional, not execution authority.
2. AI/model providers are replaceable behind the planner port.
3. Planning output is structured and validated before workflow creation.
4. Invalid/incomplete/unsupported plans fail explicitly.
5. WorkflowBuilder remains composition authority.
6. CapabilityProviderResolver remains provider-selection authority.
7. WorkflowVersion remains immutable executable artifact.
8. No autonomous publishing or execution.
9. No model-specific types in domain entities.
10. Application contract is deterministic/testable; model variability remains adapter concern.

## Initial Scope
- planning request/value object;
- planner protocol;
- structured workflow-plan representation;
- deterministic validation;
- application service converting validated plans into a draft Workflow;
- fake planner and focused tests.

## Deferred
Concrete model adapter, prompt management, model routing, autonomous execution/publishing, approval UI, planner memory, optimization, learning loops, marketplace-generated plans.

## TDD RED
Tests prove valid output creates a draft Workflow, no execution/publish side effects occur, invalid plans are rejected, planner exceptions do not create workflows, and model implementation details stay outside domain objects.

## Exit Criteria
Architecture implemented, planner contract and validation tested, WorkflowBuilder remains composition authority, no execution/publish side effects, full regression passes, and exit review documents deferred AI concerns.
