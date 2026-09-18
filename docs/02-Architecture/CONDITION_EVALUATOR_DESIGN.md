# Phase 3 — Condition Evaluator Design

Status: Design baseline
Date: 2026-09-18
Issue: #48

## Boundary

Condition evaluation is runtime/application behavior. The Workflow domain stores the declaration but never evaluates it.

## Contract

A ConditionEvaluator receives a Condition and an ExecutionContext and returns a boolean eligibility result.

The evaluator resolves the left operand from ExecutionContext, applies the declared operator, and compares it with the right operand.

## Initial Operators

The first implementation supports only:
- equals
- not_equals
- greater_than
- greater_than_or_equal
- less_than
- less_than_or_equal

These operators are sufficient to prove the boundary while remaining provider-neutral.

## Operand Resolution

The left operand is a string key resolved directly from ExecutionContext in the first implementation. Missing keys are an explicit evaluation error rather than silently evaluating false.

## Type Semantics

Comparison uses Python's native comparison semantics for the initial implementation. No coercion or expression-language parsing is introduced.

## Errors

Unsupported operators and missing context values raise ValueError. The evaluator does not swallow errors or convert them into false results.

## Deferred

- nested conditions;
- boolean composition;
- expression parsing;
- type coercion;
- external data sources;
- side effects;
- provider-specific operators.

## Rationale

This keeps evaluation small, deterministic, testable, and independent from providers while leaving room for a richer evaluator only when an actual workflow requirement demonstrates the need.
