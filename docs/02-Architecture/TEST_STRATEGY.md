# Test Strategy

- Status: Initial strategy committed for Phase 3
- Scope: Automated tests for the domain and application layers

## 1. Purpose

The test suite protects business behavior and architectural boundaries while the workflow engine evolves.

Tests should describe behavior and invariants rather than mirror implementation details.

## 2. Test Layers

### Domain tests

Use domain tests for rules owned directly by domain objects.

Examples:

- Workflow and WorkflowStep invariants.
- Transition validity.
- Workflow publication and immutability rules.
- Execution lifecycle and progression invariants.
- Structural graph validation.

Domain tests should avoid external systems and application services.

### Application tests

Use application tests for coordination between domain objects and application boundaries.

Examples:

- Orchestrator capability dispatch.
- Condition evaluation and transition selection.
- ExecutionContext flow.
- Retry-policy decisions.
- WorkflowBuilder construction behavior.

Application tests may use fakes/stubs for capabilities, evaluators, and policies.

### Integration tests

Use integration tests when more than one application component must work together to prove an important flow.

Current examples include:

- CapabilityRegistry → CapabilityDispatcher → Orchestrator.
- ConditionRegistry → ConditionEvaluator boundary → Orchestrator routing.
- CapabilityResult → ExecutionContext → subsequent capability.

## 3. TDD Workflow

For behavior changes, follow:

```text
RED
  -> write a failing behavior test
GREEN
  -> implement the minimum behavior
REFACTOR
  -> simplify without changing behavior
```

Documentation and design decisions are updated before or alongside implementation when the change affects domain meaning or architecture.

## 4. What Tests Should Protect

Tests should protect:

- Business invariants.
- Ownership boundaries.
- Runtime lifecycle rules.
- Explicit routing semantics.
- Failure behavior that callers depend on.
- Public construction APIs where their behavior is committed.

Tests should not lock the project to incidental implementation details when those details are not part of the contract.

## 5. Current Workflow Engine Coverage

The current Phase 3 scope has tests for:

- Workflow definition.
- WorkflowStep validation.
- WorkflowBuilder.
- Explicit transitions.
- Execution applying an explicitly selected target.
- Named condition references.
- ConditionRegistry registration/evaluation behavior.
- Conditional routing through the Orchestrator.
- No-match and multiple-match routing failures.
- Workflow graph reachability.
- Conditional transitions as structural graph edges.

## 6. Test Count Policy

A test count is considered authoritative only when it comes from an actual local test run or CI result tied to the current commit.

Historical counts may be recorded in exit gates, but must not be presented as the current suite status.

If CI is unavailable, the project should state that limitation rather than infer test success from static review.

## 7. Deferred Testing Topics

The strategy does not yet prescribe detailed policies for:

- Persistence integration tests.
- External provider contract tests.
- API/end-to-end tests.
- Performance/load tests.
- Property-based testing.
- Mutation testing.

Those should be introduced when the corresponding product or infrastructure boundaries become concrete.
