# Phase 8.2 Design Gate — Condition / Decision Engine

Status: **DESIGN PROPOSAL — implementation decision pending**
Capability: **Condition / Decision Engine**
Position: **2 of 13**

## Objective

Provide a deterministic, side-effect-free decision boundary that evaluates workflow conditions against normalized execution context and produces an explicit decision result without executing capabilities or embedding provider-specific logic.

## Why this follows Phase 8.1

Phase 8.1 established explicit ordered WorkflowStep composition. The domain already carries an optional Condition on a WorkflowStep, but there is not yet a dedicated evaluator/decision boundary. This capability turns that declarative condition data into deterministic runtime decisions.

## Scope

### In scope
- dedicated condition evaluation application/domain service boundary;
- deterministic evaluation of the existing Condition model;
- explicit supported operators;
- normalized left/right operand resolution from execution context;
- explicit result model: TRUE / FALSE / INVALID;
- deterministic validation errors for unsupported operators or invalid operands;
- no capability execution;
- no side effects;
- unit and contract tests;
- compatibility with existing WorkflowStep condition representation.

### Proposed initial operators

- equals
- not_equals
- greater_than
- greater_than_or_equal
- less_than
- less_than_or_equal
- contains
- not_contains
- exists
- not_exists

Operators requiring arbitrary expressions, scripts, code execution, network access, or provider-specific semantics are excluded.

### Out of scope

- branching graph redesign;
- loops;
- scheduling;
- human approval;
- capability/provider execution;
- AI-generated conditions;
- arbitrary expression languages;
- persistent decision history;
- distributed rules engines;
- authorization;
- UI.

## Context model

The evaluator should consume an explicit normalized evaluation context rather than reaching into repositories, HTTP requests, provider SDKs, or global state.

The context must make operand resolution deterministic. A condition must never trigger an external read merely because its left operand references data.

## Result semantics

Recommended result model:

- TRUE — condition evaluated successfully and matched;
- FALSE — condition evaluated successfully and did not match;
- INVALID — condition cannot be evaluated deterministically because the operator or operand contract is invalid.

Invalid input must not silently become FALSE.

The evaluator must not throw for ordinary condition non-match. Structural contract violations may raise a deterministic validation error at composition/evaluation boundaries.

## Alternatives and trade-offs

### A — Small explicit operator registry

Each supported operator is explicitly registered and receives normalized operands.

Pros:
- deterministic;
- easy to test;
- auditable;
- provider-independent;
- easy to extend without introducing an expression language.

Trade-off:
- richer future expressions require additional explicit operators.

### B — General expression language

Allow conditions such as arbitrary boolean expressions.

Pros:
- expressive;
- fewer limits for advanced users.

Trade-off:
- substantially larger parser/security/testing surface;
- ambiguity around types and missing values;
- difficult to keep deterministic and provider-independent.

## Proposed decision

**A — Small explicit operator registry**.

This is the recommended boundary for the first implementation. It keeps decision semantics deterministic and avoids introducing a general-purpose expression language before the platform demonstrates a concrete need.

## TDD contract

RED tests should establish at minimum:

- equals true/false;
- numeric comparisons;
- contains/not_contains;
- exists/not_exists;
- missing operand behavior;
- invalid operand type behavior;
- unsupported operator behavior;
- deterministic result values;
- no capability execution;
- no external side effects;
- same context + same condition produces the same result;
- condition evaluation does not mutate workflow state.

## Dependency boundaries

This capability consumes the Workflow/WorkflowStep/Condition model from Phase 8.1.

Human-in-the-Loop may later consume decision results, but approval/rejection semantics remain outside this capability.

Scheduling/triggers must not be pulled into the evaluator.

AI planning may later generate conditions, but generated conditions must still pass this deterministic evaluator boundary.

## Exit criteria

- design decision resolved;
- RED tests committed;
- GREEN implementation committed;
- focused tests and full regression pass;
- deterministic semantics documented;
- no later capability scope pulled in;
- exit review records limitations and deferred operators/features;
- PROJECT_STATUS updated.

## Decision required

The capability is selected by the Project Owner as the next item in the ordered capability sequence. The remaining architectural decision is whether to adopt Option A (small explicit operator registry) or Option B (general expression language).

No implementation of the decision engine should begin until this design choice is committed.
