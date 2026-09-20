# Phase 8.10 — AI Planning Layer Design Gate

## Status

**Accepted — architecture approved; implementation may proceed.**

## 1. Problem

Automation OS now has deterministic workflow composition, validation, execution, provider resolution, durable persistence, recovery, immutable workflow versions, and operational metrics.

The next capability is an AI Planning Layer that can help transform structured intent into an executable plan using those deterministic primitives.

The architectural risk is allowing an AI model to become an implicit execution authority, workflow-definition authority, or provider-specific dependency.

## 2. Goal

Define the smallest stable planner boundary that can:
- accept structured intent/context;
- inspect eligible workflow/capability information;
- propose a plan;
- identify required parameters or clarification;
- select an existing published workflow/version using explicit rules;
- pass the result through deterministic validation;
- remain independent of a specific AI provider/model;
- fail safely without mutating Execution state.

Execution remains deterministic and authoritative.

## 3. Non-Negotiable Constraints

1. AI must never directly mutate Execution state.
2. AI output must never bypass deterministic workflow validation.
3. AI output must never become an implicit lifecycle transition.
4. Model/provider implementations must remain replaceable behind an explicit boundary.
5. Planner output must be structured and validated, not trusted as arbitrary executable code.
6. Published WorkflowVersion artifacts remain immutable.
7. Running executions are not migrated by planning.
8. Planning must be testable without a live AI provider.
9. Deterministic behavior remains available where AI is unnecessary.
10. Planner uncertainty, clarification, and failure are explicit outcomes.
11. Provider-specific model APIs must not leak into domain objects.
12. No autonomous background agents, queues, or distributed orchestration in the first increment.

## 4. Approved Architecture

### A — AI as Plan Proposal

Flow:

**Intent → Planner Port → Structured Plan Proposal → Deterministic Validation/Resolution → Validated Plan**

The AI produces a constrained proposal. The application validates it, resolves an existing published workflow/version, validates parameters, and returns a validated plan.

The first increment does **not** create new WorkflowVersions and does **not** start execution.

This preserves the boundary:

**AI = replaceable planning/tooling**  
**Execution + deterministic domain rules = platform authority**

## 5. Approved Decisions

### Q1 — Primary planner architecture

**Decision: A — AI as Plan Proposal.**

AI produces a structured proposal rather than a complete executable workflow definition.

### Q2 — Planning output authority

**Decision: select existing published WorkflowVersions only.**

The first increment must not create or publish AI-generated WorkflowVersions. Draft WorkflowVersion generation remains a future Design Gate.

### Q3 — Execution coupling

**Decision: stop at a validated plan.**

The first planner increment must not directly invoke the workflow-start application boundary. Execution remains a separate explicit application action.

### Q4 — Clarification semantics

**Decision: first-class CLARIFICATION_REQUIRED outcome.**

Insufficient or ambiguous information must be surfaced explicitly rather than guessed.

### Q5 — Model/provider boundary

**Decision: provider-neutral PlannerPort.**

Concrete model providers are adapters behind the port. Provider-specific APIs must not leak into domain objects or planner contracts.

## 6. Proposed First-Increment Scope

1. Planner input DTO.
2. Provider-neutral PlannerPort.
3. Structured Plan Proposal DTO.
4. Explicit outcomes: PLANNED, CLARIFICATION_REQUIRED, NO_PLAN, PLANNER_FAILED.
5. Deterministic proposal validator.
6. Workflow/version resolution against existing published artifacts.
7. Parameter validation.
8. Fake planner adapter for tests.
9. One concrete external model adapter behind the port.
10. Focused TDD and full CI verification.

Not included: autonomous agents, direct model-to-execution control, arbitrary generated code, automatic publication of AI-created versions, background planning workers, self-modifying workflows, automatic planner retries, marketplace negotiation, business analytics, or distributed agent orchestration.

## 7. TDD / Verification Plan

RED should establish:
- valid structured proposals;
- unknown workflow/version rejection;
- unpublished-version rejection;
- workflow/version ownership mismatch rejection;
- invalid parameter rejection;
- clarification-required and no-plan outcomes;
- provider failure mapping;
- deterministic validation;
- non-mutation of Execution;
- provider-neutral fake adapters;
- repeatable validation.

GREEN must implement only the approved boundary.

REFACTOR must preserve the approved authority boundaries and keep provider-specific concerns outside domain contracts.

## 8. Exit Criteria

Phase 8.10 is complete only when:
- the approved planner architecture is implemented;
- the provider-neutral boundary exists;
- output is structured and validated;
- deterministic workflow/version rules remain authoritative;
- clarification/failure semantics are explicit;
- no planner path mutates Execution lifecycle;
- focused/full CI pass;
- documentation and exit review are complete.

## 9. Decision Record

**Status:** Accepted.

**Decision owner:** Project Owner.

**Approved decisions:** Q1 A; Q2 existing published WorkflowVersions only; Q3 stop at validated plan; Q4 first-class CLARIFICATION_REQUIRED; Q5 provider-neutral PlannerPort.

**Implementation authorization:** Implementation may begin within the approved scope. Any expansion into AI-generated WorkflowVersions, direct execution, autonomous agents, or provider-specific domain coupling requires a new Design Gate.
