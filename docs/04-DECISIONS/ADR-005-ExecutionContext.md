# ADR-005 — Execution Context

## Status

Accepted

## Context

Execution needs runtime data that workflow steps can read and produce while the workflow is running. This data must be separated from Execution lifecycle state, Workflow definition, provider implementations, and business artifacts/results.

The Execution aggregate already owns lifecycle, progress, attempt count, and lifecycle timestamps. Detailed waiting context is explicitly assigned to Execution Context by ADR-004.

## Decision

Execution Context is a runtime-data concept associated with an Execution. It exists to carry operational data required by workflow steps without taking ownership of Execution lifecycle or orchestration.

The following boundaries are committed:

1. **Inputs belong to Execution Context.** They are the runtime inputs with which an Execution operates.
2. **Runtime/intermediate outputs belong to Execution Context.** Data produced during execution that is still operational working data remains in Context.
3. **Business artifacts and business results do not belong to Context merely because they are produced during execution.** Meaningful artifacts belong to Asset, and meaningful business results belong to Outcome.
4. **Context is mutable through a controlled API.** Workflow steps may read and write runtime data through explicit Context operations rather than depending on an unrestricted raw dictionary as the domain contract.
5. **Context is subordinate to the Execution lifecycle.** It does not have an independent lifecycle or execution state. Its lifecycle is tied to the Execution it serves.
6. **Provider-specific implementation details do not become Context semantics.** Credentials, plugin implementations, provider-specific configuration, and integration details remain outside the core Execution Context model.

## Conceptual Shape

```text
Execution
  ├── lifecycle / progress
  └── Execution Context
       ├── inputs
       ├── working data
       └── runtime outputs

Asset  ← business-relevant artifacts
Outcome ← meaningful business results
```

## Rationale

A completely unstructured dictionary would provide flexibility but would make ownership and contracts implicit. A controlled Context API preserves the flexibility needed by workflow execution while keeping the domain boundary explicit.

Keeping business artifacts and outcomes outside Context prevents the runtime container from becoming a God object that accumulates every kind of execution data.

Keeping Context subordinate to Execution avoids introducing a second lifecycle model before an actual requirement justifies it.

## Consequences

- Execution remains focused on lifecycle and progress.
- Workflow steps have an explicit place for runtime inputs and intermediate data.
- Asset and Outcome retain ownership of business meaning rather than becoming incidental Context fields.
- Provider implementations remain replaceable and do not define the core Context contract.
- The initial Context API should remain small; additional typed concepts should be introduced only when real workflow requirements justify them.
- Persistence and serialization details remain implementation concerns and are not part of this domain decision.

## Non-Goals

This ADR does not define:

- a persistence mechanism for Context;
- a serialization format;
- provider-specific Context schemas;
- retry policy;
- orchestration behavior;
- a complete typed schema for every possible workflow input/output.

## Review Trigger

Revisit this decision if Context requires an independent lifecycle, if Context data becomes subject to invariants that cannot be maintained through its current API, if persistence/history requires a separate aggregate boundary, or if workflow requirements demonstrate that Asset/Outcome ownership is insufficient for business results.
