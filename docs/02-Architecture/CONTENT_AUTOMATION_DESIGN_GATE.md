# Phase 5 — Content Automation Design Gate

Status: Active Implementation Baseline
Date: 2026-09-18
Issue: #68

## Purpose

Define the first concrete automation domain for Automation OS without turning the platform into a YouTube-specific application.

Phase 5 uses content automation as the first real business domain through the existing Workflow → Execution → Capability architecture.

The design must preserve the project constitution:

- domain first;
- application orchestration second;
- infrastructure last;
- providers are replaceable;
- AI is replaceable;
- Workflow is not the product;
- Execution remains the central runtime concern;
- capabilities are adapters, not a second execution model;
- TDD is the default implementation method.

---

## Phase 5 Business Outcome

The first content automation scenario is:

**Given a content source, produce a publishable short-form content asset through a repeatable workflow.**

The initial implementation should prove that Automation OS can execute a real business workflow using multiple interchangeable capabilities.

Conceptually:

`Source → Acquire → Transcribe → Extract Clip → Publish → Outcome`

This is a business scenario, not the permanent architecture of Automation OS.

---

## Domain Boundary

### Content Automation owns

The content domain should own concepts and invariants that are meaningful regardless of provider:

- content source identity/reference;
- source media as a content asset;
- transcript as derived content;
- clip as a derived content asset;
- publication intent/result at the content level;
- relationships between source and derived assets;
- content-oriented metadata and lifecycle rules that are provider-independent.

### Content Automation does not own

The domain must not own:

- YouTube SDK objects;
- yt-dlp objects;
- Whisper/OpenAI SDK objects;
- FFmpeg process objects;
- TikTok/YouTube publishing clients;
- provider credentials;
- HTTP clients;
- filesystem/network implementation;
- queues/workers;
- provider-specific retry policies.

Those belong behind capability/provider boundaries.

---

## Architectural Placement

The existing architecture remains authoritative.

### Domain

Contains provider-neutral business concepts and invariants.

### Application

Coordinates content workflow use cases and execution context.

Application code may compose capabilities such as:

- `content_source_acquire`
- `content_transcribe`
- `content_extract_clip`
- `content_publish`

The exact identifiers are implementation decisions for the corresponding TDD increments and must remain provider-neutral.

### Capability layer

Capabilities expose executable behavior through the existing:

`Capability.execute(context) -> CapabilityResult`

boundary.

A capability may use one or more provider/infrastructure adapters internally, but the workflow contract must not depend on those providers.

### Infrastructure

Contains provider adapters and technical mechanisms:

- YouTube/API adapters;
- download/media acquisition adapters;
- transcription adapters;
- FFmpeg/media-processing adapters;
- publishing adapters;
- filesystem/object-storage adapters;
- future scheduling/queue infrastructure.

Infrastructure must not redefine Workflow or Execution semantics.

---

## Core Domain Language

### Content Source

A provider-neutral reference describing where content originates.

The first baseline should identify a source without embedding provider SDK types.

Possible information:

- source URI/reference;
- source kind/type;
- optional external identifier.

Provider-specific metadata remains outside the core source identity unless a business requirement proves it necessary.

### Content Asset

A content artifact produced or consumed by a content workflow.

Examples:

- source media;
- extracted clip;
- future rendered media.

Asset is about the artifact, not the provider that produced it.

Asset-specific information belongs with the asset. Execution state, retry information, and workflow lifecycle do not belong inside Asset.

### Transcript

A derived representation of source media containing textual content and, when required by the use case, timing information.

The first contract should avoid committing to a particular transcription provider or model.

### Clip

A derived content asset representing a selected segment of source content.

A clip may eventually include:

- source asset reference;
- start/end timing;
- output asset reference;
- title/caption metadata.

The first implementation should introduce only fields required by a tested business invariant.

### Publication

A content-domain representation of a requested or completed publication outcome.

Provider-specific publication response objects must remain outside the domain.

The first baseline should avoid designing a universal social-media publishing model before concrete requirements justify it.

### Outcome

Outcome describes the business result of an execution/workflow rather than the technical result of a capability.

A `CapabilityResult` says whether one capability operation succeeded.

An Outcome answers what the content workflow produced.

These concepts must not be conflated.

---

## Asset and Outcome Boundary

The existing project constitution describes:

`Idea → Intent → Workflow → Execution → Capability → Asset → Outcome`

Phase 5 makes the last two concepts concrete enough to support a real vertical slice without prematurely creating a large content-management subsystem.

### Asset responsibility

Asset represents a content artifact and its content-specific identity/metadata.

Asset does not own:

- workflow execution state;
- capability retry;
- provider lifecycle;
- workflow progression.

### Outcome responsibility

Outcome represents the business-level result produced by the content workflow.

For the first vertical slice, an outcome should be able to communicate that a publishable clip was produced and, when publishing is included, where/what was published at the content level.

Technical provider responses remain capability/infrastructure concerns.

---

## Workflow Composition

A content workflow should be expressed using the existing Workflow and WorkflowStep model.

Example conceptual workflow:

1. Acquire source media.
2. Transcribe media.
3. Extract a clip.
4. Publish the clip.

Each step references a capability identifier rather than a provider.

Example:

`WorkflowStep(capability="content_source_acquire")`

not:

`WorkflowStep(capability="youtube_yt_dlp_download")`

The workflow therefore remains reusable if the source or provider implementation changes.

Conditions and triggers continue to use the existing Phase 3 boundaries.

---

## Minimum Vertical Slice

The first Phase 5 vertical slice should prove the complete business path with the smallest useful implementation.

### Slice A — Source to publishable clip

Input:

- one provider-neutral source reference.

Process:

1. acquire source media;
2. produce a content asset;
3. transcribe the source;
4. produce a transcript;
5. select/extract one clip;
6. produce a clip asset;
7. return a content-level outcome describing the produced clip.

The first slice does **not** need production YouTube publishing.

This keeps the initial domain proof independent from external publishing credentials and platform APIs.

### Slice B — Publishing

After Slice A is stable:

1. take the produced clip;
2. invoke a provider-neutral publishing capability;
3. adapt one concrete publishing provider;
4. represent the business-level publication outcome.

### Slice C — Scheduling

Scheduling is a separate concern from content transformation.

It should be introduced only after the transformation/publishing path is stable.

The scheduling design must distinguish:

- desired publication time;
- scheduler infrastructure;
- execution start;
- provider publication.

Scheduling must not create a second workflow execution lifecycle.

---

## Capability Boundaries

The initial capability set is intentionally small.

### Acquisition capability

Business responsibility:

- obtain source media for the workflow.

Provider responsibility:

- resolve/download/fetch the media using a concrete source adapter.

### Transcription capability

Business responsibility:

- produce a transcript from source media.

Provider responsibility:

- call a transcription engine/model.

### Clip extraction capability

Business responsibility:

- produce a clip asset from source media and selection information.

Provider responsibility:

- perform technical media extraction/rendering.

### Publishing capability

Business responsibility:

- request publication of a content asset and report the publication outcome.

Provider responsibility:

- authenticate and call a concrete publishing platform.

The capability identifiers remain provider-neutral.

---

## Execution Context

The existing `ExecutionContext` remains the short-lived application data carrier between workflow steps.

For the first vertical slice it may carry references/results such as:

- source reference;
- acquired asset reference;
- transcript reference;
- selected clip parameters;
- produced clip asset reference;
- publication request/result reference.

The context must not become an unbounded replacement for the domain model.

If data requires durable identity, business invariants, or lifecycle beyond one execution, it should become an explicit domain concept rather than an arbitrary context key.

---

## Failure and Retry

Phase 4 failure semantics remain authoritative.

A content capability:

- returns `CapabilityResult.success()` or `CapabilityResult.failure(...)` for expected operational outcomes;
- may raise unexpected exceptions;
- never calls Execution lifecycle methods;
- never decides retry count.

`ExecuteWorkflowStep` remains responsible for translating capability failure into the established Execution failure state.

Automatic retry, backoff, provider-specific transient classification, workers, and queue infrastructure remain deferred unless a later design gate commits them.

---

## Provider Isolation

### Source providers

The first concrete provider may be YouTube, but YouTube is an adapter choice rather than a domain identity.

The domain should not require:

- YouTube URL parsing as its only source model;
- YouTube API response structures;
- YouTube-specific authentication;
- yt-dlp types.

### Transcription providers

Whisper, OpenAI, local models, or another transcription service are implementation choices.

The workflow asks for transcription, not for a specific model.

### Media processing providers

FFmpeg is a likely infrastructure implementation, but the content domain must not depend on FFmpeg process objects or command syntax.

### Publishing providers

YouTube, TikTok, Instagram, or other platforms are concrete publishing adapters.

Publishing should be modeled around the business capability rather than platform SDK types.

---

## Progress Tracking

Progress tracking must initially remain execution-oriented.

The system already has:

- Execution state;
- current step;
- attempt;
- capability boundary.

Phase 5 should not immediately introduce a second progress state machine.

A content-specific progress view may later project execution state into user-facing progress information.

The initial rule is:

**Execution owns runtime progress; content assets describe produced artifacts.**

---

## Scheduling

Scheduling is intentionally separated from content transformation.

The first scheduling design must answer:

- what is being scheduled;
- whether scheduling creates an Execution or requests one;
- how scheduled time is persisted;
- how duplicate starts are prevented;
- how cancellation interacts with Execution;
- how provider publication time differs from workflow execution time.

No scheduler/worker implementation is committed by this Design Gate.

---

## Data and Persistence

The existing repository boundaries remain authoritative.

Phase 5 should not introduce a general database schema merely to support the first vertical slice.

Persistence requirements should be derived from actual business needs.

If a content asset needs durable identity across executions, define an explicit repository boundary for that aggregate/entity rather than storing the asset permanently in ExecutionContext.

Production ORM/database selection remains a separate infrastructure decision.

---

## TDD Implementation Order

The implementation should proceed in small vertical increments.

### Increment 1 — Content domain vocabulary

RED:

- tests for the smallest provider-neutral source/asset concepts and their invariants.

GREEN:

- implement only the required domain objects.

REFACTOR:

- keep the model small and provider-neutral.

### Increment 2 — Acquisition capability boundary

RED:

- tests proving acquisition consumes provider-neutral input and produces the expected content artifact/result.

GREEN:

- implement an in-memory/fake capability first.

REFACTOR:

- keep provider code outside the domain.

### Increment 3 — Transcription capability

Repeat RED → GREEN → REFACTOR using a fake provider implementation first.

### Increment 4 — Clip extraction

Introduce the smallest tested clip/selection model required by the business scenario.

### Increment 5 — End-to-end application composition

Compose the capabilities into the existing Workflow/Execution runtime and prove the first vertical slice.

### Increment 6 — Concrete provider adapter

Only after the provider-neutral boundary is stable, introduce the first real provider implementation.

### Increment 7 — Publishing

Design and implement publication after the transformation slice is stable.

### Increment 8 — Scheduling/progress projection

Treat scheduling and user-facing progress as separate increments with their own design decisions where required.

---

## Committed Decisions

1. Phase 5 uses content automation as the first concrete business domain.
2. Content automation is implemented through the existing Workflow → Execution → Capability architecture.
3. YouTube is a provider/adapter, not the content-domain abstraction.
4. Transcription providers and AI models are replaceable implementations.
5. Provider SDKs and technical clients stay outside the domain.
6. Workflow steps reference provider-neutral capability identifiers.
7. Execution remains the central runtime lifecycle and progress owner.
8. ExecutionContext is execution-scoped transport/state, not a permanent domain model.
9. Content assets represent produced/consumed artifacts; they do not own Execution lifecycle.
10. CapabilityResult remains the operation-level result boundary.
11. Outcome represents business-level workflow result and is distinct from CapabilityResult.
12. The first vertical slice targets source → acquired asset → transcript → clip outcome before production publishing.
13. Publishing is a subsequent increment after the transformation slice is stable.
14. Scheduling is a separate concern and must not create a second execution lifecycle.
15. Production persistence, workers, queues, automatic retry, and dynamic provider discovery are not introduced by this gate.

---

## Assumptions

These are working assumptions, not permanent architecture:

- The first concrete source provider may be YouTube.
- The first media processing implementation may use FFmpeg.
- The first transcription implementation may use a Whisper-compatible provider.
- A local/in-memory implementation is sufficient for the first domain TDD increments.
- The first clip-selection rule can be intentionally simple.

Each assumption should be revisited if implementation evidence invalidates it.

---

## Open Questions

1. **Resolved by Increment 1:** the minimum ContentAsset vocabulary is `id`, provider-neutral `asset_type`, provider-neutral `reference`, and an optional `ContentSource` relationship. Durable persistence semantics remain deferred.
2. Should Transcript be an independent aggregate/entity or a value object associated with a source asset?
3. What is the minimum clip selection model: explicit time range, transcript segment, or both?
4. Should publishing be modeled as a content-domain entity or initially only as an Outcome?
5. What persistence is actually required once assets cross execution boundaries?
6. Which source-provider metadata has genuine business value versus adapter-only value?
7. What exact scheduling semantics are required by the first real use case?
8. How should user-facing progress be projected from Execution without creating a second state machine?

These questions must be resolved when the corresponding implementation increment requires them. The resolved item above records the minimum vocabulary chosen by the first TDD increment.

---

## Alternatives Considered

### YouTube-first domain

Rejected for the core architecture.

It would make the first feature easier to build but would couple the content domain to one platform and conflict with provider replacement.

### Generic media platform before content use case

Deferred.

Designing every possible media/content concept before proving one business scenario would create speculative architecture.

### Provider-specific capabilities

Rejected.

Capability identity must remain provider-neutral so provider selection remains a composition concern.

### One giant ContentAutomationService

Rejected.

It would collapse acquisition, transcription, media processing, publishing, and provider integration into one application boundary and reduce replaceability/testability.

### Put all intermediate data in ExecutionContext

Rejected as a long-term model.

ExecutionContext is useful for execution-scoped coordination, but durable business artifacts require explicit domain concepts.

### Build scheduler/worker infrastructure first

Deferred.

The current platform does not yet require a background runtime to prove the content business domain.

---

## Trade-offs

### Small domain model vs early completeness

Decision: prefer the smallest model that supports the first vertical slice.

Trade-off: some concepts will be revisited as real requirements emerge.

### Provider neutrality vs immediate implementation speed

Decision: keep the workflow/provider boundary neutral.

Trade-off: the first provider requires an adapter instead of allowing provider SDK types to flow directly through the workflow.

### ExecutionContext vs durable asset model

Decision: use context for execution-scoped references; introduce durable domain objects only when required.

Trade-off: early implementations may carry references temporarily, but this avoids premature persistence design.

### Transformation before publishing

Decision: prove source-to-clip transformation before production publishing.

Trade-off: the first vertical slice does not yet demonstrate an external platform integration, but it gives the content domain a stable business boundary before credentials and provider APIs complicate the design.

---

## Deferred Scope

Explicitly outside this gate:

- dynamic plugin discovery;
- remote plugins;
- plugin marketplace;
- provider auto-selection;
- automatic retry;
- retry backoff/jitter;
- worker pools;
- message brokers;
- distributed execution;
- production scheduler;
- multi-platform publishing orchestration;
- content recommendation/AI generation;
- automatic clip scoring;
- advanced editing;
- captions/subtitles rendering;
- analytics;
- monetization;
- user accounts/tenancy;
- billing;
- production database/ORM selection;
- distributed storage;
- observability platform;
- complex event payload routing.

These concerns require concrete requirements and dedicated design decisions.

---

## Design Gate Exit Criteria

Phase 5 design is ready for implementation when:

- the content business boundary is understood;
- provider-specific concerns are isolated;
- Asset and Outcome responsibilities are explicit;
- the first vertical slice is bounded;
- the first TDD increments are defined;
- committed decisions are distinguished from assumptions/open questions;
- deferred scope is recorded;
- existing Execution/Workflow/Capability architecture remains intact.

## Next Implementation Boundary

After approval of this gate, the first implementation issue should target **Increment 1 — Content domain vocabulary** only.

No YouTube SDK, transcription SDK, FFmpeg process integration, scheduler, or production publishing implementation should be added before the corresponding provider-neutral contract has tests.
