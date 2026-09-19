# Phase 8.2 Design Gate — Condition / Decision Engine

Status: **APPROVED FOR IMPLEMENTATION — Option A selected by Project Owner**
Capability: **Condition / Decision Engine**
Position: **2 of 13**

## Objective

Provide a deterministic, side-effect-free decision boundary that evaluates workflow conditions against normalized execution context without executing capabilities or reaching into external systems.

## Current repository state

The repository already contains:
- `Condition` as a domain value object;
- `ExecutionContext` as execution-scoped state;
- an application-level `ConditionEvaluator`;
- focused tests for equality and numeric comparison.

Phase 8.2 therefore extends an existing boundary rather than introducing a duplicate evaluator.

## Gap identified

The current evaluator returns `bool`, raises for missing operands and unsupported operators, and supports only equality/ordering operators.

The proposed Phase 8.2 contract adds:
- explicit TRUE/FALSE/INVALID result semantics;
- deterministic missing-value behavior;
- contains/not_contains;
- exists/not_exists;
- explicit operator registry;
- side-effect-free evaluation.

This change must preserve the existing execution-context boundary.

## Scope

### In scope
- extend the existing application ConditionEvaluator;
- deterministic explicit operator registry;
- normalized execution context access;
- explicit ConditionResult;
- equals/not_equals;
- numeric ordering;
- contains/not_contains;
- exists/not_exists;
- deterministic invalid-input semantics;
- focused and full regression tests.

### Out of scope
- branching graph redesign;
- loops;
- scheduling;
- human approval;
- capability/provider execution;
- AI-generated conditions;
- arbitrary expression languages;
- persistent decision history;
- authorization;
- UI.

## Alternatives

### Option A — Small explicit operator registry

Keep a finite set of operators implemented by the platform.

Pros:
- deterministic;
- auditable;
- small test surface;
- no expression parser/security surface;
- compatible with provider-independent execution.

Trade-off:
- advanced expressions require explicitly added operators.

### Option B — General expression language

Introduce an expression syntax for arbitrary boolean conditions.

Pros:
- greater expressiveness.

Trade-off:
- parser, typing, validation, security and deterministic-semantics complexity;
- substantially expands the capability beyond the current domain model.

## Decision

**Option A — Small explicit operator registry** is selected for Phase 8.2.

The evaluator will use a finite, explicit operator set. A general expression language is deferred until a concrete requirement justifies its additional parser, typing, security, and determinism surface. This decision is limited to Phase 8.2 and does not prevent a future explicit design gate for richer expressions.

## RED preparation

The existing evaluator tests are the baseline. Once Option A is selected, RED tests will define the expanded deterministic result contract before implementation.

## Dependency boundaries

Condition evaluation consumes workflow conditions and execution context. It must not execute capabilities, perform network/repository reads, mutate workflow state, or pull scheduling/human approval into this capability.

Human-in-the-Loop can consume decision results later. AI planning can generate declarative conditions later, but all generated conditions must pass this deterministic boundary.
