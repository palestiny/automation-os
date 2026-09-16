# Domain Model

## Core Relationship

Intent
→ Workflow
→ Execution
→ Capability
→ Asset
→ Outcome

## Execution

Execution is currently the strongest implemented domain concept.

Important lifecycle concepts include:

- CREATED
- RUNNING
- WAITING
- FAILED
- RETRYING
- COMPLETED
- CANCELLED

The exact state machine is governed by tests and the Execution domain implementation.

Execution owns workflow step progression. The application orchestrator coordinates capability execution and delegates successful step progression to the Execution aggregate.

## Capability Execution Data Flow

A capability returns a `CapabilityResult`. When successful, the result may contain output data. The orchestrator stores that output in the application-level `ExecutionContext`, keyed by the current workflow step identifier, so later capabilities can consume previous step outputs.

This is runtime orchestration data flow. It does not yet define the domain semantics of `Asset` or `Outcome`.

## Architectural Principle

Execution represents the runtime lifecycle.

Workflow represents the plan.

Capability represents an ability.

Plugin represents one implementation of an ability.

ExecutionContext represents runtime data shared during orchestration.

This separation prevents external technologies from becoming the business model.
