# Automation OS — Logical Workflow Map

Status: **CURRENT ARCHITECTURAL MAP**

## A. Runtime flow

```mermaid
flowchart TD
    A[Intent] --> B[Intent Understanding]
    B --> C[Workflow Discovery / Selection]
    C --> D[Workflow Builder if needed]
    D --> E[Validation]
    C --> E
    E --> F[Trigger or Explicit Start]
    F --> G[Start Workflow Execution]
    G --> H[Execution Lifecycle]
    H --> I[Select Next Step]
    I --> J{Condition}
    J -- No --> I
    J -- Yes --> K[Capability Contract]
    K --> L[Provider]
    L --> M[Result / Evidence]
    M --> N{Human Decision?}
    N -- Yes --> O[WAITING]
    O --> P[Human Decision Port]
    P --> H
    N -- No --> I
    H --> Q{Failure?}
    Q -- Yes --> R[Recovery / Retry]
    R --> H
    Q -- No --> S[Completed Outcome]
    H --> T[History / Events]
```

## B. Boundary ownership

| Concern | Authority |
|---|---|
| Intent meaning | Intent/application layer |
| Workflow definition | Workflow domain |
| Workflow construction | Workflow Builder |
| Condition truth | Condition evaluator |
| Trigger matching | Trigger application boundary |
| Execution state | Execution aggregate |
| Capability behavior | Capability contract + provider |
| Human decision | Human Decision Port |
| Lifecycle evidence | History/events |
| Persistence | Repository adapters |
| Recovery | Recovery application boundary |
| Planning | Planner / AI layer |
| Distribution | Marketplace |
| External event detection | External integration layer |

## C. What must not happen

- Trigger layer must not own execution lifecycle.
- AI must not directly mutate execution state.
- Provider implementations must not redefine workflow semantics.
- History/events must not become a second lifecycle authority.
- Human interaction must not be an invisible capability side effect.
- Marketplace installation must not bypass validation.
- Recovery must not invent a second execution model.
- Durable persistence must preserve the atomic contracts already established by Phase 7.

## D. Current implementation position

Completed:
- Core platform
- Phase 7 reliability/hardening
- Builder
- Conditions
- HITL

In design preparation:
- Scheduling / Triggers

Upcoming:
- Capability Providers
- Durable Persistence
- Recovery
- Versioning
- Observability
- AI Planning
- Marketplace Expansion
- External Events
- Multi-tenancy / Authorization
