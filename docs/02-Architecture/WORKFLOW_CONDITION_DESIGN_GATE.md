# Phase 3 — Workflow Condition Design Gate

Status: Design baseline
Date: 2026-09-18
Issue: #46

## Problem

A workflow step may eventually need to run only when a declared condition is satisfied. The Workflow must describe that constraint without becoming responsible for evaluating runtime state.

## Committed Decisions

### 1. Condition belongs to WorkflowStep

A condition is part of the declarative definition of a step. A step may have no condition or one condition.

WorkflowStep owns the association because the condition determines eligibility of that specific step.

### 2. Condition is a separate domain concept

Condition is not stored as an arbitrary dictionary or opaque field on WorkflowStep. A dedicated concept keeps conditional semantics explicit and allows validation to evolve without turning WorkflowStep into an expression engine.

### 3. The first Condition contract is intentionally minimal

The initial domain contract represents a condition as a provider-neutral declaration with:
- a left operand reference;
- an operator;
- a right operand value.

The contract does not define an expression language, nested boolean trees, scripting, or provider-specific syntax.

### 4. Workflow does not evaluate conditions

Workflow and WorkflowStep only own and validate the declaration.

Evaluation belongs to the application/runtime boundary because evaluation requires ExecutionContext and a concrete evaluation strategy.

### 5. Evaluation is a separate service boundary

A future ConditionEvaluator will accept a Condition plus runtime context and return whether the condition is satisfied. The evaluator contract is not implemented by this design gate.

### 6. Missing condition means unconditional step

A WorkflowStep without a Condition remains eligible for execution without an evaluation step.

### 7. Published workflow immutability applies to conditions

Once a Workflow is published, its step condition definitions cannot be changed through the domain API.

## First Testable Behavior

The first implementation increment should prove only domain ownership and structural validity:
- a WorkflowStep can be created without a condition;
- a WorkflowStep can be created with a valid Condition;
- invalid condition declarations are rejected;
- the condition is exposed as part of the immutable WorkflowStep definition;
- published workflows cannot mutate the condition through the existing public API.

Condition evaluation is deliberately a separate increment.

## Deferred

- expression language;
- nested AND/OR/NOT conditions;
- evaluator implementation;
- type coercion;
- external data lookups;
- condition side effects;
- provider-specific operators;
- persistence schema details for conditions.

## Trade-off

The minimal operand/operator/value representation gives the project a concrete domain boundary without prematurely selecting a DSL. The cost is that richer conditional semantics will require a later extension or migration once a real workflow use case demonstrates the need.

## Gate Result

The domain boundary is sufficiently defined for a focused TDD increment that introduces Condition without implementing runtime evaluation.
