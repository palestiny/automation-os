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

## Architectural Principle

Execution represents the runtime lifecycle.

Workflow represents the plan.

Capability represents an ability.

Plugin represents one implementation of an ability.

This separation prevents external technologies from becoming the business model.
