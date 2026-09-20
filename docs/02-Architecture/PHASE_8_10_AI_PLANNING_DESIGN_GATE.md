# Phase 8.10 — AI Planning Layer Design Gate

## Status
**APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**

## Objective
Introduce an AI-assisted planning boundary that converts validated intent into a deterministic workflow proposal without allowing the AI model to execute capabilities or mutate execution state.

## Decision
**Option A — Application-level Planner Port + deterministic validation and compilation.**

The model/provider produces a structured plan proposal. The application validates it against deterministic capability/workflow contracts and compiles an accepted proposal into a workflow definition/version artifact.

AI remains a replaceable planning tool, not execution authority.

## Runtime Boundary
```
Intent
  ↓
Planner Port
  ↓
Structured Plan Proposal
  ↓
Deterministic Plan Validator
  ↓
Workflow Builder / Version Compiler
  ↓
Workflow + WorkflowVersion
  ↓
Existing Execution Runtime
```

The planner never executes capabilities, starts executions, changes execution state, selects runtime providers dynamically, bypasses validation, or writes lifecycle history.

## Contract
The proposal contains the goal, ordered capability IDs, step names, optional deterministic conditions, required parameters, provider/model metadata, and a plan identifier/version.

Unknown capabilities, malformed steps, unsupported conditions, invalid parameters, provider mismatches, and oversized plans are rejected deterministically.

AI output is structured data, never executable code or an arbitrary expression.

## Workflow Versioning
Planning creates a new workflow/version artifact. Published workflow versions remain immutable. Execution continues through the existing version-aware runtime.

## Human Control
Planning and approval are separate. A generated plan may require the existing Human Decision Port before execution. The planner cannot approve its own output.

## Outcomes
- **PLANNED** — valid proposal.
- **NEEDS_CLARIFICATION** — required information is missing/ambiguous.
- **REJECTED** — deterministic platform constraint violated.

## Provider Boundary
The planner uses an application-level provider port. Model/vendor SDKs stay outside the domain. Provider selection is explicit configuration in this phase; no health scoring, autonomous switching, marketplace selection, or model optimization.

## Options

### Option A — Planner Port + deterministic compiler
Pros: AI remains replaceable; deterministic execution boundary; reusable Builder/WorkflowVersion; testable without a model; clear human approval boundary.
Trade-off: explicit validation and compilation stages.

### Option B — AI directly creates and executes workflows
Pros: fewer visible boundaries.
Trade-offs: couples model output to execution; weakens validation/auditability; makes AI part of runtime authority.

### Option C — AI as a Capability
Pros: reuses capability dispatch.
Trade-offs: planning becomes execution work and encourages AI to become runtime authority.

**Decision: Option A.**

## TDD RED Plan
1. Valid proposal compiles.
2. Unknown capability is rejected.
3. Invalid condition is rejected.
4. Missing required information returns NEEDS_CLARIFICATION.
5. Malformed model output is rejected.
6. Published versions are never mutated.
7. Planner cannot execute capabilities.
8. Planner provider is replaceable.
9. Human approval remains external.
10. Compilation is deterministic for the same proposal.

## GREEN Scope
Implement planner port, structured proposal/result contracts, deterministic validator, compiler integration, and a fake provider with focused tests.

Deferred: autonomous execution, model-specific orchestration, prompt marketplace, health scoring/failover, long-term memory, autonomous self-modification, UI/mobile planning.

## Exit Criteria
Focused tests, full regression, deterministic validation/compilation, immutable version artifacts, deterministic clarification/rejection semantics, and completed exit documentation.
