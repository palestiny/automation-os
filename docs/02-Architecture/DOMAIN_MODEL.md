# Domain Model

Status: Baseline

## Core Relationship

Intent
→ Workflow
→ Execution
→ Execution Context
→ Capability
→ Asset
→ Outcome

This is the conceptual flow, not a statement that every step must be a direct object-to-object dependency.

## Intent

Represents the desired business objective. Intent analysis and workflow selection are later-phase concerns.

## Workflow

Represents the executable plan: ordered steps, rules and required capabilities. It describes what should happen.

## Execution

Represents a runtime instance of a workflow. It is currently the strongest implemented domain concept.

Current lifecycle states:

- CREATED
- RUNNING
- WAITING
- FAILED
- RETRYING
- COMPLETED
- CANCELLED

Current execution data includes workflow identity, current step, state, attempt count and lifecycle timestamps. The exact invariants are defined by the domain implementation and tests.

Execution owns runtime lifecycle, progress, attempt count, and lifecycle timestamps. It does not own retry policy, provider-specific execution details, or workflow completion semantics.

## Execution Context

Represents runtime data required by workflow steps while an Execution is running.

Execution Context is associated with an Execution and is subordinate to its lifecycle. It does not have an independent execution state or lifecycle.

It contains:

- runtime inputs;
- working/intermediate data;
- runtime outputs that are still operational data.

Context is mutable through a controlled API rather than exposing an unrestricted raw dictionary as the domain contract.

Business artifacts and meaningful business results are not treated as generic Context data:

- Asset owns business-relevant artifacts.
- Outcome owns meaningful business results.

Provider-specific credentials, implementations, configuration, and integration details remain outside the core Execution Context model.

The exact Context API and concrete typed schemas should evolve from real workflow requirements rather than being invented in advance.

## Capability

Represents a business-level ability required by a workflow. The capability contract should remain stable while implementations/providers can change.

## Plugin

Represents a replaceable implementation behind a capability boundary. Plugins belong to the integration/extension side of the architecture rather than defining the core business model.

## Asset

Represents a business-relevant artifact consumed or produced by execution. Asset-specific metadata belongs with the asset concept rather than being scattered through execution state or generic Context data.

## Outcome

Represents the meaningful business result of completing automation. Technical completion and business outcome are intentionally distinct concepts.

## Current Boundary

Execution is the core runtime domain. Workflow definition and execution runtime must remain separate. Execution Context carries runtime data without owning lifecycle. Asset and Outcome retain business meaning. Provider technologies must not become domain concepts merely because they are used by the first implementation.
