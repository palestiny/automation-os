# Post-Phase 6 Design Gate Packet

## Status

Decision-support artifact — no next milestone is selected or committed.

## Purpose

Provide implementation-ready Design Gate starting points for each post-Phase-6 capability area without silently selecting one.

---

## Gate A — Execution Reliability and Operational Visibility

### Problem

The current execution engine exposes current lifecycle state and attempt count, but no committed contract exists for duplicate command protection, historical execution evidence, structured execution events, or operational correlation.

### Candidate outcome

Make execution behavior diagnosable and safely repeatable for a defined command boundary while preserving the existing Execution lifecycle as the single state authority.

### Candidate committed scope

- One explicitly defined idempotency boundary.
- One explicit history/audit contract.
- Minimal structured execution events needed by that contract.
- Correlation between execution-related operations where justified.
- Tests for duplicate requests, history semantics, and failure behavior.

### Non-goals

- Second execution state model.
- Vendor-specific observability.
- Full distributed tracing platform.
- Generic event bus.
- Analytics dashboard.
- Unbounded event persistence.

### Gate questions

- Which command is idempotent first?
- What is the idempotency key and lifetime?
- What response/result is replayed for a duplicate?
- What is immutable history?
- Which events are domain facts versus telemetry?
- What happens if history/event persistence fails?

### TDD entry point

Start with a RED test expressing the selected command's duplicate-request semantics before changing the domain or repository contracts.

### Exit criteria

- Semantics documented.
- Duplicate behavior deterministic.
- History/event ownership explicit.
- Existing lifecycle tests remain valid.
- No second state authority.
- CI verification passes.

---

## Gate B — Ownership and Authorization

### Problem

The current platform does not define resource ownership or authorization semantics for workflows, executions, or marketplace resources.

### Candidate outcome

Define an authoritative ownership/authorization boundary that works consistently for application use cases and transport clients.

### Candidate committed scope

- Identity/owner abstraction required by the chosen product model.
- Ownership rules for explicitly selected resources.
- Authorization policy at the application boundary.
- Persistence isolation guarantees required by the model.
- API enforcement and tests.

### Non-goals

- Selecting an authentication provider without a product requirement.
- Premature role taxonomy.
- Full multi-tenancy unless explicitly selected.
- API-only authorization.

### Gate questions

- Single-user, multi-user, or tenant model?
- Which resources are owned?
- Which actions are authorized?
- Where is policy authoritative?
- What isolation is required from persistence?

### TDD entry point

Start with a RED application-level test proving an unauthorized operation cannot mutate/read the selected resource.

### Exit criteria

- Ownership model explicit.
- Authorization boundary explicit.
- Persistence isolation verified.
- API enforcement is consistent with application policy.
- CI verification passes.

---

## Gate C — Autonomous Planning / Workflow Generation

### Problem

The platform can analyze intents and select existing workflows deterministically, but cannot safely generate or compose new workflows autonomously.

### Candidate outcome

Introduce bounded planning that can propose executable workflow candidates without allowing AI output to bypass deterministic validation and execution authority.

### Candidate committed scope

Must be narrowed by a separate gate to one concrete planning capability, such as candidate generation or parameter inference.

### Non-goals

- Unrestricted autonomous execution.
- AI as domain authority.
- Semantic similarity as authoritative compatibility.
- Provider-specific planner coupling.

### Gate questions

- What may the planner generate?
- What deterministic validation must generated output pass?
- Candidate-only or automatic execution?
- How are ambiguity and unsafe plans represented?
- What happens when the model fails or returns malformed output?

### TDD entry point

Start with a RED test proving invalid or incomplete planner output cannot cross the deterministic execution boundary.

### Exit criteria

- Generated output is bounded.
- Deterministic validation remains authoritative.
- Failure/ambiguity semantics are explicit.
- Provider/model failures cannot corrupt domain state.
- CI verification passes.

---

## Gate D — Product/API Foundation

### Problem

The platform has working HTTP boundaries, but a stable public-product contract, authentication model, versioning policy, and consumer-specific collection behavior are not committed.

### Candidate outcome

Define the API boundary for one concrete consumer/product surface without freezing unstable domain concepts.

### Candidate committed scope

Must be anchored to a concrete consumer and a small set of stable API capabilities.

### Non-goals

- Generic API framework work.
- Premature versioning of unstable endpoints.
- Dashboard implementation inside domain/application layers.
- Authentication without authorization semantics.

### Gate questions

- Who is the consumer?
- Which endpoints are stable enough to publish?
- What compatibility policy is required?
- Which collections need pagination?
- How do identity and authorization interact?

### TDD entry point

Start with a RED contract test for the first stable consumer-facing endpoint.

### Exit criteria

- Consumer identified.
- Public contract bounded.
- Compatibility policy explicit.
- Authentication/authorization relationship defined.
- CI verification passes.

---

## Decision Protocol

Before implementation, the Project Owner selects one capability area and approves its Design Gate.

After approval:

**Design Gate → TDD RED → GREEN → Refactor → Exit Review**

Until that selection is made, these four gates remain alternatives rather than a roadmap commitment.
