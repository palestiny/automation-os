# Phase D — External Side-Effect Semantics Design Gate

**Status:** PASS — implementation verified
**Phase:** D — External Side-Effect Semantics
**Implementation branch:** `hardening/phase-d-side-effect-semantics-red`
**PR:** #372

## Decision

**Option B — Explicit outcome + provider idempotency** is implemented.

The execution system now distinguishes confirmed success, pre-side-effect failure, confirmed failure, unknown outcome, and skipped execution. Ambiguous external outcomes are durable and are not automatically retried unless idempotency is explicitly proven.

## Verified invariants

1. External ambiguity is never inferred to be a normal failure.
2. `UNKNOWN` without proven idempotency blocks automatic retry.
3. Provider secrets remain outside outcome evidence.
4. Retry policy remains in the application layer.
5. Outcome semantics are provider-neutral.
6. Existing capability compatibility remains intact.
7. Capability-start evidence is durably recorded before provider execution.
8. A local persistence failure after an external success leaves durable start evidence; stale recovery converts it to `UNKNOWN`.
9. Retryability is persisted and enforced for recorded failures.
10. Operation identity is deterministic and stable for the same execution/step.

## Acceptance evidence

- CI #2059: successful, 749 tests passed.
- CI #2061: successful on the final recovery-semantics hardening commit.
- Tests cover:
  - failure before side effect;
  - confirmed success;
  - confirmed failure;
  - ambiguous provider failure;
  - UNKNOWN without idempotency;
  - UNKNOWN with proven idempotency;
  - non-retryable vs retryable failures;
  - external success followed by local persistence failure;
  - stale recovery to UNKNOWN;
  - durable PostgreSQL outcome evidence;
  - latest-terminal-event recovery semantics.
- No distributed transaction/event-bus architecture was introduced.

## Important limitation

Automatic retry safety is proven only when the capability/provider explicitly establishes idempotency. Arbitrary external providers do not receive an exactly-once guarantee.

## Follow-up

Before production readiness, diagnostics must be treated as a strict safe-data contract rather than blindly persisting arbitrary exception strings. Production secret-provider implementation and observability hardening remain separate roadmap items.

**Gate decision: PASS.**