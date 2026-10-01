# Phase D — External Side-Effect Semantics Design Gate

**Status:** DESIGN GATE — proposed  
**Phase:** D — External Side-Effect Semantics  
**Branch:** `hardening/phase-d-side-effect-semantics`

## Problem

The current capability contract reports only success/failure. That is insufficient for external side effects.

A capability can successfully perform an external operation and then fail before local persistence completes. A retry can therefore repeat an operation whose external outcome is already committed.

The execution engine must distinguish ordinary failure from an outcome that is unknown after an external side effect may have occurred.

## Invariants

1. The execution engine must never infer that an external side effect did not occur merely because local execution raised an exception.
2. An ambiguous external outcome must not be automatically retried unless an explicit idempotency strategy makes the retry safe.
3. Capability implementations must not persist provider secrets or provider-specific authentication state in domain objects.
4. The application layer owns retry policy; individual capabilities report outcome evidence.
5. The contract must remain provider-neutral and usable for both local and external capabilities.
6. Existing successful capabilities should remain easy to implement.
7. Durable execution history must record the material outcome classification before an automatic retry can proceed from an ambiguous state.

## Proposed outcome model

Replace the boolean-only semantic with an explicit capability outcome:

- **SUCCEEDED** — the capability completed and its intended side effect is known to have succeeded.
- **FAILED_BEFORE_SIDE_EFFECT** — execution failed before the external side effect was attempted.
- **FAILED** — execution failed and the capability can establish that the intended side effect did not occur.
- **UNKNOWN** — the external outcome cannot be established after an ambiguous failure.
- **SKIPPED** — execution intentionally did not perform the capability action.

The model should also carry:

- retryability classification;
- optional external operation/idempotency key;
- safe, non-secret diagnostic information.

## Retry rule

The default safety rule is:

`UNKNOWN + external side effect + no proven idempotency = no automatic retry`

A retry may be permitted only when the capability contract establishes that repeating the operation is safe, for example through a stable external idempotency key accepted by the provider.

Manual retry must not silently convert an unknown outcome into a known failure. The evidence remains UNKNOWN.

## Idempotency strategy

For side-effecting capabilities, the application should provide or derive a stable operation identity from durable execution identity rather than generate a new random key on each retry.

Candidate identity:

`execution_id + workflow_version_id + step identity`

The exact derivation remains a design decision during implementation because step identity must remain stable across retries and workflow versions must not be mixed.

The external provider adapter is responsible for passing the operation identity using the provider's supported idempotency mechanism when available.

## Persistence / evidence

The execution history should preserve the outcome classification and relevant operation identity without storing secrets.

The implementation must avoid claiming external success from a local database commit alone.

## Explicit non-goals

This phase does **not** introduce:

- distributed transactions;
- Kafka/event-bus infrastructure;
- microservices;
- two-phase commit;
- a universal exactly-once guarantee for arbitrary providers.

Exactly-once behavior cannot be assumed for arbitrary external systems. The system instead makes ambiguity explicit and requires provider-supported idempotency where automatic retry is needed.

## Trade-offs

### Option A — Keep boolean success/failure

**Pros:** smallest change.

**Cons:** cannot safely distinguish pre-side-effect failure from ambiguous external outcome; retry can duplicate external effects.

**Decision:** rejected.

### Option B — Explicit outcome + provider idempotency

**Pros:** models the real failure boundary; supports safe retries where providers support idempotency; keeps infrastructure simple.

**Cons:** capability implementations become slightly richer; some providers will remain non-retryable after UNKNOWN.

**Decision:** **proposed**.

### Option C — Distributed transaction / event-driven exactly-once architecture

**Pros:** addresses broader distributed coordination problems.

**Cons:** disproportionate complexity, does not create universal exactly-once semantics across arbitrary providers, and would change the architecture substantially.

**Decision:** rejected for this phase.

## Acceptance criteria for implementation

- Capability outcome is explicit and backward compatibility is deliberate, not accidental.
- UNKNOWN is durable and cannot be silently mapped to ordinary failure.
- Automatic retry is blocked for UNKNOWN unless an explicit safe-idempotency condition is present.
- Stable operation identity is available to side-effecting capabilities.
- Retry tests cover:
  1. failure before side effect;
  2. successful side effect;
  3. ambiguous provider failure;
  4. retry with provider idempotency;
  5. retry without provider idempotency;
  6. local persistence failure after external success.
- Existing non-side-effect capabilities continue to work.
- No secret material appears in outcome evidence, logs, or persisted execution history.

## Gate decision

**Phase D implementation is authorized only against Option B and the invariants above.**

Before coding the concrete API, the remaining implementation detail is to define the exact result object and how durable execution history records the outcome without coupling the domain to any provider.
