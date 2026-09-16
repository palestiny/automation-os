# Test Strategy

Status: Accepted baseline

The test strategy follows the project's domain-first and TDD approach.

## Test Pyramid

### Unit Tests

Primary tool for domain rules and deterministic application behavior.

Use unit tests for:

- entities and value objects;
- state transitions;
- validation rules;
- retry decisions;
- deterministic services.

### Integration Tests

Use integration tests when multiple modules or infrastructure boundaries must work together.

Examples:

- application service + repository;
- orchestrator + capability dispatcher;
- persistence mappings;
- external-provider adapters with controlled test doubles.

### End-to-End Tests

Use sparingly for critical user-facing workflows. They should validate a complete business scenario rather than duplicate every unit test.

## TDD Cycle

For behavior-driven implementation:

1. RED — write a failing test that expresses the required behavior.
2. GREEN — implement the smallest change that makes it pass.
3. REFACTOR — improve the design without changing behavior.
4. Re-run the relevant suite.

## What We Test

We test observable behavior and domain invariants, especially:

- valid transitions;
- invalid transitions;
- lifecycle completion/failure/cancellation;
- retry behavior;
- boundaries and edge cases;
- collaboration between modules where contracts matter.

## What We Avoid

- Tests coupled unnecessarily to private implementation details.
- Mock-heavy tests that merely reproduce implementation structure.
- Tests for framework behavior we do not own.
- Large end-to-end suites for logic that can be tested faster at the unit level.

## Completion Rule

A feature cannot be considered complete because the happy path works. Important invalid states and domain boundaries must be represented by tests.

## Current Direction

Execution is the first core domain being stabilized. Its state machine and lifecycle behavior remain the reference example for applying this strategy to later modules.
