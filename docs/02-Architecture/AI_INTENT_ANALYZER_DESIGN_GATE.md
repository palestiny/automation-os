# AI Intent Analyzer Design Gate

## Status

Accepted

## Boundary

**Raw request → IntentAnalyzer → Intent**

The AI provider is an adapter behind the existing application protocol.

## Committed Decisions

1. The domain never imports an AI SDK.
2. `IntentAnalyzer` remains the application boundary.
3. The AI adapter is responsible for provider interaction and translating provider output into a validated `Intent`.
4. Invalid structured output is an analysis failure, not a workflow-selection result.
5. Provider failures never start workflow execution.
6. Credentials and model configuration live outside the domain.
7. Tests for selection and execution remain deterministic and provider-independent.
8. The adapter must not select or execute workflows.
9. Intent goals are constrained by the provider-neutral canonical goal catalog when configured.
10. Canonical goal validation is enforced at the application boundary before workflow selection/execution.
9. Intent goals are constrained by the provider-neutral canonical goal catalog when configured.
10. The intent-to-execution boundary validates canonical goals before workflow selection.
9. Canonical intent goals are validated against a provider-neutral goal catalog before workflow execution.
10. No autonomous agent loop, retries, model routing, or conversation memory is introduced in this slice.

## Output Contract

The adapter must produce:

- non-empty goal;
- string parameter names;
- validated parameter mapping.

The existing `Intent.create()` is the domain validation boundary.

The platform additionally validates the analyzed goal against the canonical `IntentGoalCatalog` before workflow selection and execution.

## Failure Boundary

Expected analysis/provider failure is an analysis failure and stops the request path.

Malformed provider output is rejected before producing an Intent.

A non-canonical goal is rejected before workflow selection.

No workflow is selected after analysis or goal validation failure.

## Provider Choice

The first concrete provider adapter is OpenAI, isolated under infrastructure. The application boundary remains provider-neutral and replaceable.

Provider selection is based on structured-output support, SDK stability, testability, cost, and replaceability.

## TDD Order

1. Adapter input/output contract with fake provider.
2. Structured provider response parsing.
3. Invalid-output handling.
4. Provider failure handling.
5. Concrete provider implementation.
6. Application composition: raw request → analyze → validate goal → select → execute.

## Deferred

- model routing;
- fallback providers;
- automatic retries;
- prompt optimization;
- conversation memory;
- agent loops;
- autonomous workflow generation;
- semantic workflow search.

## Implementation Status

Implemented through the provider-neutral IntentAnalyzer boundary, OpenAI adapter, canonical goal catalog, and request-to-execution composition. Concrete provider details remain isolated from the domain.

## Exit Criteria

- provider is replaceable;
- malformed output cannot cross the Intent boundary;
- provider failures cannot trigger execution;
- non-canonical goals cannot trigger execution through the request boundary;
- no AI dependency leaks into domain;
- deterministic tests remain intact.



## Implementation

- `IntentGoalCatalog` defines the canonical provider-neutral goal vocabulary.
- `OpenAIIntentAnalyzer` can constrain structured output to the catalog and rejects unknown goals.
- `ValidateIntent` provides the application validation boundary.
- `ExecuteRequest` validates the analyzed Intent before selection/execution.
- `ExecuteIntent` can independently enforce the same catalog boundary.
- Selection remains deterministic and execution still enters through `StartWorkflowExecution`.

## Verification

The complete test suite passes in CI for the implemented intent-analysis increments.
