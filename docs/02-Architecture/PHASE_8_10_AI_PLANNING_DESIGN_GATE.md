# Phase 8.10 — AI Planning Layer Design Gate

## Status

**Draft — decision required before implementation.**

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
- select or propose a workflow/version using explicit rules;
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

## 4. Candidate Architectures

### Option A — AI as Plan Proposal

Flow: Intent → Planner Port → Structured Plan Proposal → Deterministic Validation/Resolution → WorkflowVersion → Start Execution.

AI produces a constrained proposal. The application validates it, resolves known workflows/versions, validates parameters, and exposes a startable plan.

**Benefits:** strongest separation from execution authority; easy provider replacement; deterministic safety boundary; highly testable.

**Trade-offs:** requires explicit proposal DTOs and validation; AI cannot freely invent behavior outside registered capabilities.

### Option B — AI generates a complete workflow definition

Flow: Intent → AI → Workflow Definition → Validation → WorkflowVersion → Execution.

**Benefits:** maximum planning flexibility and a natural path toward AI-generated workflows.

**Trade-offs:** larger trust and validation surface; version creation becomes tightly coupled to planning; harder failure/clarification semantics.

### Option C — Deterministic candidate discovery + AI ranking/composition

Flow: Intent → Deterministic Candidate Discovery → AI ranks/composes candidates → Deterministic Validation → WorkflowVersion/Execution.

**Benefits:** limits model search space; reduces hallucinated capability/workflow references; fits future marketplace expansion.

**Trade-offs:** more first-increment orchestration and discovery/ranking semantics.

## 5. Comparison

| Concern | A — Proposal | B — Full generation | C — Hybrid |
|---|---|---|---|
| AI authority | Low | Higher | Medium |
| Deterministic safety boundary | Strong | Strong but larger validation surface | Strong |
| Initial complexity | Lowest | Medium/High | Medium |
| WorkflowVersion reuse | Strong | Strong after generation | Strong |
| Testability without AI | Strong | Strong | Strong |
| Marketplace coupling | Low | Medium | Higher |

## 6. Decision Questions

### Q1 — Primary planner architecture
Choose A, B, or C.

### Q2 — Planning output authority
Should the first increment select an existing published WorkflowVersion only, create a new draft WorkflowVersion proposal, or support both?

### Q3 — Execution coupling
Should the first planner increment stop at a validated plan, or may it directly invoke the existing workflow-start application boundary after validation?

### Q4 — Clarification semantics
Should the planner return a first-class CLARIFICATION_REQUIRED outcome when intent/parameters are insufficient rather than guessing?

**Recommended baseline: yes.**

### Q5 — Model/provider boundary
Should the application expose a provider-neutral Planner Port, with model providers implemented as adapters?

**Recommended baseline: yes.**

## 7. Recommended Baseline

- Q1: A
- Q2: select existing published versions first; draft creation is a later increment
- Q3: stop at a validated plan in the first increment
- Q4: first-class clarification-required outcome
- Q5: provider-neutral Planner Port

These are recommendations, not Project Owner decisions.

## 8. Proposed First-Increment Scope

1. Planner input DTO.
2. Provider-neutral Planner Port.
3. Structured Plan Proposal DTO.
4. Explicit outcomes: planned, clarification-required, no-plan, planner-failed.
5. Deterministic proposal validator.
6. Workflow/version resolution against existing published artifacts.
7. Parameter validation.
8. Fake planner adapter for tests.
9. One concrete external model adapter behind the port.
10. Focused TDD and full CI verification.

Not included: autonomous agents, direct model-to-execution control, arbitrary generated code, automatic publication of AI-created versions, background planning workers, self-modifying workflows, automatic planner retries, marketplace negotiation, business analytics, or distributed agent orchestration.

## 9. TDD / Verification Plan

RED should establish valid proposals, unknown workflow/version rejection, unpublished-version rejection, invalid parameters, clarification-required/no-plan outcomes, provider failure mapping, deterministic validation, non-mutation of Execution, provider-neutral fake adapters, and repeatable validation.

## 10. Exit Criteria

Phase 8.10 is complete only when planner architecture is approved, the provider-neutral boundary exists, output is structured and validated, deterministic workflow/version rules remain authoritative, clarification/failure semantics are explicit, focused/full CI pass, and documentation/exit review are complete.

## 11. Decision Record

**Status:** Draft.

**Decision owner:** Project Owner.

**Implementation must not begin until Q1–Q5 are resolved or explicitly scoped by the Project Owner.**
