# Phase 5 — Content Publishing Design Gate

Status: Design Baseline
Date: 2026-09-18
Issue: #85

## Purpose

Define the provider-neutral publishing boundary for Content Automation Slice B before implementation.

Publishing extends the established transformation path:

`Source → Acquire → Transcribe → Extract Clip → Publish → Outcome`

The design must preserve the project constitution:

- domain first;
- application orchestration second;
- infrastructure last;
- providers are replaceable;
- AI is replaceable;
- Workflow is not the product;
- Execution remains the central runtime concern;
- capabilities are adapters, not a second execution model;
- TDD is the default implementation method;
- major features require an explicit Design Gate.

---

## Business Outcome

The publishing slice answers:

**Given a produced content asset and a provider-neutral publication request, publish that asset through a selected provider and expose the business-level publication result.**

The workflow must ask for publication, not for a specific platform SDK.

Example workflow step:

`WorkflowStep(capability="content_publish")`

not:

`WorkflowStep(capability="youtube_publish")`

---

## Scope

### In scope

- provider-neutral publication request;
- provider-neutral publication result;
- publishing capability boundary;
- application-level composition;
- provider adapter boundary;
- reuse of existing Execution and CapabilityResult failure semantics;
- deterministic fake-provider tests;
- first concrete publishing provider adapter only after the provider-neutral contract is tested.

### Out of scope

- scheduling;
- background workers;
- queues/message brokers;
- automatic retry/backoff;
- multi-provider fan-out;
- provider auto-selection;
- analytics;
- recommendation;
- monetization;
- user accounts/tenancy;
- production database/ORM;
- marketplace/plugin discovery;
- credential-management platform;
- distributed execution.

---

## Architectural Boundary

### Domain

Owns provider-neutral business concepts:

- the asset being published;
- publication destination as business data;
- publication request;
- successful publication result;
- invariants that are meaningful independently of a provider.

The domain must not import:

- YouTube SDK objects;
- TikTok/Instagram SDK objects;
- HTTP clients;
- credential objects;
- provider response payloads.

### Application

Coordinates:

- retrieving the clip/content asset from execution context;
- constructing the provider-neutral publication request;
- invoking the publishing capability;
- storing the provider-neutral publication result in execution context;
- relying on existing Execution lifecycle semantics.

Application code does not parse provider response payloads.

### Capability

Publishing uses the existing boundary:

`Capability.execute(context) -> CapabilityResult`

The capability:

1. reads the required content asset/request;
2. invokes a provider adapter;
3. translates expected provider-level failures into `CapabilityResult.failure(...)`;
4. stores the provider-neutral publication result in context on success;
5. returns `CapabilityResult.success()`.

The capability does not:

- advance Execution;
- complete Execution;
- decide retry count;
- own provider credentials;
- expose provider SDK objects.

### Infrastructure

Owns:

- platform API clients;
- authentication mechanisms;
- HTTP/network behavior;
- provider request/response mapping;
- provider-specific error classification;
- technical publication identifiers.

Infrastructure returns data through a small provider adapter contract rather than leaking SDK objects into application/domain code.

---

## Domain Model Decision

### PublicationRequest

For the first implementation, publication intent is represented as a small provider-neutral request value object.

Minimum information:

- content asset to publish;
- destination/platform identifier.

Optional metadata such as title/caption should be introduced only when the first concrete provider requires a tested business requirement.

The request is not an Execution state and has no lifecycle.

### Publication

A successful publication is represented as a provider-neutral business result.

Minimum information:

- publication identity;
- published content asset;
- destination/platform identifier;
- provider-issued external reference, represented only as an opaque string.

Publication does not own a state machine.

A publication object represents a completed business result. Pending/failed execution remains owned by Execution.

This prevents publication from becoming a second runtime lifecycle.

### Outcome

Outcome remains the higher-level business result of the workflow.

For the first publishing slice, the application may expose the produced Publication as part of the content workflow outcome/context without creating a separate Outcome state machine.

A later vertical slice may introduce an explicit Outcome aggregate if durable business reporting requires it.

---

## ExecutionContext Boundary

The execution context may carry:

- produced clip/content asset;
- publication request;
- successful publication result.

Suggested provider-neutral keys:

- `content.clip`;
- `content.publication_request`;
- `content.publication`.

These are execution-scoped references.

If publication records must survive after an execution completes, persistence requirements must introduce an explicit repository/domain boundary rather than silently turning ExecutionContext into storage.

---

## Provider Boundary

The application/capability layer should depend on a small provider-neutral technical contract.

Conceptually:

`publish(request) -> provider-neutral publication data`

The concrete provider adapter maps:

`PublicationRequest → Provider API → Provider Response → Publication`

The provider response itself never crosses the infrastructure boundary.

Multiple providers may implement the same publishing contract.

The workflow capability identifier remains:

`content_publish`

Provider selection is composition/infrastructure configuration, not workflow identity.

---

## Credentials

Credentials belong entirely outside the domain and workflow definition.

The first adapter may receive a configured provider client or credential-aware adapter through construction.

The publishing capability must not:

- read environment variables directly;
- construct authentication clients;
- store credentials in ExecutionContext;
- place secrets in domain objects;
- expose credentials in errors or reports.

Credential lifecycle and secret storage are deferred infrastructure concerns.

---

## Failure Semantics

Existing Phase 4 semantics remain authoritative.

### Expected provider failure

A known operational/provider failure becomes:

`CapabilityResult.failure(message)`

`ExecuteWorkflowStep` then applies the established Execution failure semantics.

### Unexpected exception

Unexpected exceptions propagate through the existing runtime behavior and Execution is marked failed by the application boundary.

### No step advancement on failure

A failed publication must not advance the workflow step or complete the Execution.

### Retry

Publishing does not implement retry internally.

Explicit Execution retry remains the runtime mechanism.

Automatic retry, transient classification, backoff, and idempotency infrastructure are deferred.

---

## Idempotency

The first publishing implementation must not invent a distributed idempotency system.

However, duplicate publication is a real business risk.

Therefore:

- the provider adapter may expose a provider-specific idempotency mechanism if one naturally exists;
- the core workflow must not depend on provider-specific idempotency fields;
- a durable duplicate-prevention policy is deferred until an actual scheduling/retry requirement makes it necessary.

This keeps the first publishing slice small without denying the future requirement.

---

## First Vertical Slice

The smallest useful publishing slice is:

1. existing source-to-clip workflow produces a clip;
2. a publication request identifies the clip and destination;
3. `content_publish` capability receives the request;
4. a deterministic fake provider produces a provider-neutral publication result;
5. the result is stored in ExecutionContext;
6. the workflow completes normally;
7. the result can be inspected without exposing provider SDK data.

No live provider call is required for this first TDD increment.

---

## Concrete Provider Adapter

Only after the provider-neutral contract is tested:

1. select one concrete publishing provider;
2. isolate its client/API model under infrastructure;
3. inject it into the publishing capability;
4. test mapping with deterministic provider fixtures/mocks;
5. prove provider failures map to the existing capability failure boundary;
6. avoid live network calls in the default test suite.

Production credentials and real external calls are not part of the first provider-adapter test.

---

## TDD Implementation Order

### Increment 1 — Publication vocabulary

RED:

- request requires a publishable content asset;
- destination is nonempty;
- successful publication has an identity, asset, destination, and opaque external reference;
- publication is immutable;
- publication has no execution lifecycle state.

GREEN:

- implement only the minimum request/result domain objects.

REFACTOR:

- keep provider terms out of the model.

### Increment 2 — Publishing capability boundary

RED:

- missing publication request fails;
- invalid request fails;
- successful fake provider produces a Publication;
- publication is stored in ExecutionContext;
- capability uses the existing Capability contract.

GREEN:

- implement the capability with an injected provider-neutral adapter.

REFACTOR:

- keep orchestration out of the capability.

### Increment 3 — End-to-end workflow composition

RED:

- source-to-clip workflow followed by publication completes;
- publication result survives through ExecutionContext;
- a publishing failure leaves Execution failed and does not advance.

GREEN:

- compose `content_publish` into the existing runtime.

REFACTOR:

- preserve the existing Workflow/Execution boundaries.

### Increment 4 — Concrete provider adapter

RED:

- deterministic provider mapping tests;
- expected provider failures;
- provider-neutral result mapping.

GREEN:

- implement one real provider adapter.

REFACTOR:

- isolate provider-specific technical details.

### Increment 5 — Business outcome refinement

Only if the concrete use case proves a need for durable Outcome/Publication persistence, introduce that model and repository through a separate design decision.

---

## Media Asset Access Boundary

The first publishing provider needs access to the actual media artifact represented by a `ContentAsset`. The core model intentionally stores only an opaque `reference` and must not know whether that reference points to a local file, object storage, URL, or another provider.

Therefore the application boundary introduces `MediaAssetReader`:

`read(asset: ContentAsset) -> bytes`

Responsibilities:

- accept a provider-neutral `ContentAsset`;
- resolve its artifact through infrastructure/composition;
- return media bytes to the caller;
- raise a typed `MediaAssetNotFoundError` when the artifact cannot be resolved.

The initial implementation is an in-memory reader for deterministic tests. A filesystem/object-storage implementation is deferred until an actual storage requirement exists.

The reader must not:

- add storage state to `ContentAsset`;
- expose filesystem paths as domain concepts;
- expose provider SDK objects;
- perform publishing;
- own retries.

## Committed Decisions

1. Publishing uses the existing Workflow → Execution → Capability architecture.
2. The workflow capability identifier is provider-neutral: `content_publish`.
3. Publication intent is represented by a provider-neutral `PublicationRequest`.
4. A successful publication is represented by a provider-neutral `Publication` business result.
5. Publication has no independent runtime state machine.
6. Execution owns pending/running/failed/completed lifecycle.
7. ExecutionContext may carry the request and successful publication result for one execution.
8. Provider SDKs, credentials, HTTP clients, and provider response objects remain infrastructure concerns.
9. Publishing capability uses an injected provider adapter.
10. CapabilityResult remains the operation-level technical result boundary.
11. Existing Execution failure/retry semantics remain authoritative.
12. The first implementation uses deterministic fake providers and no live network.
13. Automatic retry, scheduling, worker infrastructure, and distributed idempotency are deferred.
14. Durable Publication/Outcome persistence is deferred until a concrete business requirement proves it necessary.
15. Increment 1 is complete: the provider-neutral `PublicationRequest` and `Publication` vocabulary is implemented and tested.
16. Increment 2 is complete: `ContentPublishingCapability` uses an injected provider-neutral `PublicationProvider` boundary and preserves existing failure semantics.
17. Increment 3 is complete: the content workflow composition executes the publishing capability through the existing Workflow → Execution runtime and exposes the resulting Publication in execution context.
18. Publishing media access uses a provider-neutral `MediaAssetReader` application boundary; storage implementation remains outside the domain.
19. The first concrete publishing provider is YouTube, isolated under infrastructure behind `PublicationProvider`.
20. The YouTube adapter receives media through `MediaAssetReader`; Google API client/auth objects remain infrastructure concerns.
21. The first YouTube adapter defaults uploads to private visibility and uses configurable provider-level title/description defaults; YouTube-specific fields do not enter the domain model.
22. Durable Publication/Outcome persistence is explicitly deferred by `PUBLICATION_OUTCOME_PERSISTENCE_DESIGN_GATE.md` until a concrete post-execution business requirement exists.

---

## Assumptions

- One destination is sufficient for the first publishing slice.
- An opaque provider external reference is sufficient for the first Publication model.
- Title/caption/media metadata can remain outside the first request until a real provider requirement needs them.
- Provider selection can remain construction/composition configuration.
- A synchronous publishing capability is sufficient for the first implementation.

These are working assumptions and may be revised only through explicit design evidence.

---

## Resolved Implementation Progress

- **Increment 1 complete:** `PublicationRequest` and `Publication` are immutable provider-neutral domain concepts with the committed minimum invariants.
- **Increment 2 complete:** `ContentPublishingCapability` validates the execution-scoped request, delegates to an injected `PublicationProvider`, translates expected provider failures, and stores the provider-neutral Publication result.
- **Increment 3 complete:** `ContentWorkflowComposition` registers `content_publish`; the integration path now proves source → acquire → transcribe → clip → publish with the existing runtime lifecycle.
- **Media access boundary complete:** `MediaAssetReader` provides a provider-neutral read contract and deterministic in-memory implementation for tests; no storage technology is coupled to the domain.
- **Increment 4 complete:** the first concrete provider adapter is YouTube, with deterministic mapping tests and no live network dependency.

## Open Questions

1. Which concrete publishing provider should be the first adapter?
2. Which publication metadata is a genuine business requirement rather than provider detail?
3. When should Publication become durable across executions?
4. What idempotency semantics are required once automatic retry or scheduling is introduced?
5. Should a future Outcome aggregate contain Publication directly or reference it?

These questions are intentionally deferred to the implementation increments that require them.

---

## Alternatives Considered

### Provider-specific publishing capabilities

Rejected.

They would couple workflow definitions to a platform and make provider replacement harder.

### Put provider response objects in ExecutionContext

Rejected.

ExecutionContext is application state, not a provider integration boundary.

### Publication as another Execution state machine

Rejected.

Execution already owns runtime lifecycle. A second lifecycle would duplicate semantics and create ambiguity.

### Outcome-only model with no Publication concept

Deferred as the long-term possibility, but rejected for the first publishing slice because the successful publication result has a distinct business identity and external reference that may need to be carried independently of the technical capability result.

### Build multi-platform publishing orchestration immediately

Deferred.

One provider-neutral boundary plus one concrete adapter is enough to prove the design.

### Build scheduler before publishing

Rejected for this slice.

Scheduling is a separate concern and must request/start executions rather than create another lifecycle.

---

## Trade-offs

### Explicit Publication model vs minimal Outcome-only model

Decision: use a minimal Publication result.

Trade-off: introduces one small domain concept earlier, but gives the business result a clear identity without creating another lifecycle.

### Provider neutrality vs implementation speed

Decision: provider-neutral request/result and injected adapter.

Trade-off: requires a mapping boundary before the first live provider can be used.

### ExecutionContext vs persistence

Decision: keep the first result execution-scoped.

Trade-off: a completed publication is not automatically durable; persistence will require a later explicit decision.

### No automatic retry

Decision: reuse current explicit Execution retry semantics.

Trade-off: transient provider failures require an explicit retry until a future retry design is committed.

---

## Deferred Scope

- scheduling;
- automatic retry;
- backoff/jitter;
- worker pools;
- queues;
- distributed execution;
- multi-platform fan-out;
- provider auto-selection;
- durable publication repository;
- production Outcome aggregate;
- analytics;
- provider marketplace;
- credential-management service;
- live-network integration tests;
- distributed idempotency infrastructure.

---

## Design Gate Exit Criteria

The publishing design is ready for implementation when:

- provider-neutral request/result boundaries are explicit;
- Publication does not duplicate Execution lifecycle;
- provider SDK and credentials are isolated;
- ExecutionContext responsibility is bounded;
- failure/retry semantics reuse the existing runtime;
- TDD increments are defined;
- deferred scope is recorded.

## Persistence Decision

The persistence design gate confirms that no database/repository is justified by the current Phase 5 use case. Publication remains execution-scoped for now. Reopen this decision only when reporting, historical queries, downstream workflows, reconciliation, or durable audit becomes an implemented requirement.

## Next Implementation Boundary

The next implementation boundary is **Increment 5 — Business outcome refinement**, only if the concrete use case proves a need for durable Outcome/Publication persistence.

The adapter must be introduced behind the provider-neutral `PublicationProvider` contract, with deterministic mapping/failure tests and no live network dependency in the default suite. No scheduling, worker, automatic retry, or durable publication persistence should be introduced.
