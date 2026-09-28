# Automation OS — Post-Roadmap Decision Matrix

## Status

**Decision preparation only — no capability selected or authorized.**

This document refines the post-roadmap capability assessment into a decision-ready comparison. It does not authorize implementation and does not rank the four directions.

## 1. Decision Frame

The current platform already covers the core deterministic runtime lifecycle:

`Intent → Understand → Select/Plan → Compose → Validate → Trigger → Execute → Observe → Recover → Improve`

The next decision should therefore be framed around the product problem to solve, not around a technology to introduce.

The four currently identified directions are:

1. Human Workflow Review / Operations
2. Credential / Secret / Provider Configuration
3. Durable Event / Notification Infrastructure
4. Workflow Productization / Reuse

## 2. Decision Matrix

| Dimension | Human Review / Operations | Credential / Provider Configuration | Durable Events / Notifications | Workflow Productization / Reuse |
|---|---|---|---|---|
| Primary user problem | Safely operate and review generated workflows | Safely connect workflows to external providers | React to and deliver durable events | Reuse and distribute workflow artifacts |
| Existing foundation | Very high | Medium | High | Very high |
| Main new domain concepts | Review decision, reviewer/audit evidence, operational projection | Provider connection, credential reference, secret lifecycle | Event publication, subscription, delivery attempt | Template, product/reuse metadata, compatibility |
| Main application impact | Review/query/decision application services | Configuration + runtime resolution boundaries | Publication/delivery orchestration | Reuse/clone/configuration services |
| Main infrastructure impact | Low initially | Medium–high | High | Medium |
| Security sensitivity | Medium | High | Medium | Medium |
| Tenant impact | Existing tenant context can be extended to review ownership | Credential ownership/isolation is central | Subscriber ownership/isolation required | Tenant-scoped reuse/distribution rules |
| Runtime execution change | None required for first slice | Execution context/provider resolution must gain safe credential access | Existing trigger path can remain separate | Existing execution semantics should remain unchanged |
| Persistence impact | Review state/audit records | Connections, references, lifecycle state | Event/outbox/delivery records | Templates/product metadata and relationships |
| Idempotency impact | Review commands should be safe to retry | Credential operations need stable lifecycle semantics | Delivery requires explicit idempotency | Clone/install operations need deterministic identity rules |
| Versioning impact | Review should target a specific draft/version boundary | Credential configuration must not mutate immutable workflow versions | Event contracts need compatibility rules | Version compatibility becomes a core concern |
| Main failure modes | Duplicate decisions, stale draft, unauthorized review | Secret leakage, wrong tenant, revoked/expired credential | Duplicate delivery, loss, ordering, retry storms | Incompatible template, accidental coupling to deployment |
| Verification burden | Medium | High | High | Medium–high |
| Smallest useful first slice | Draft review + explicit approve/reject + audit | Credential reference + tenant ownership + runtime resolution contract | One concrete durable delivery use case | Template from published version + deterministic clone/customization |
| Explicit non-goal for first slice | Full frontend operations suite | Full secrets-management platform | Generic event bus | Deployment/release platform |

## 3. Existing Contracts Each Direction Can Reuse

### A — Human Review / Operations

Directly reusable boundaries:
- `WorkflowState.DRAFT/PUBLISHED`
- generated DRAFT persistence
- `GetDraftWorkflowForReview`
- `PublishWorkflow`
- authorization/tenant context
- execution discovery/progress
- execution history

The missing boundary is primarily **human decision state**, not workflow execution.

### B — Credential / Provider Configuration

Directly reusable boundaries:
- `CapabilityProviderResolver`
- `CapabilityDispatcher`
- `CapabilityFactory`
- `ExecutionContext`
- authorization/tenant context
- durable persistence
- execution lifecycle/recovery

The missing boundary is **credential ownership and runtime resolution**. Credentials should remain outside Workflow and AI-generated workflow artifacts.

### C — Durable Events / Notifications

Directly reusable boundaries:
- `ExternalEventIntake`
- `TriggerInvocation`
- `TriggerMatcher`
- execution-start idempotency
- execution history
- external-event normalization

The missing boundary is **durable outbound delivery**. Existing inbound trigger handling should not automatically be converted into a generic event bus.

### D — Workflow Productization / Reuse

Directly reusable boundaries:
- `WorkflowVersion`
- immutable published versions
- marketplace listings
- marketplace discovery
- marketplace publication
- exact-version marketplace installation
- workflow generation and validation
- tenant boundaries

The missing boundary is **reusable artifact semantics**: what can be cloned, customized, parameterized, and later upgraded without changing immutable executable history.

## 4. First-Slice Boundaries

### Human Review

Candidate contract:

`ListReviewableDrafts → GetDraft → Validate/Present → Approve OR Reject → Persist Decision`

Required invariant:

> A review decision must never silently start execution.

### Credential Configuration

Candidate contract:

`RegisterConnection → StoreReference → ResolveAtExecution → CapabilityProvider`

Required invariants:

- secret values never enter Workflow definitions;
- AI-generated candidates contain references/requirements, not secret material;
- tenant ownership is enforced;
- revoked/invalid credentials fail explicitly;
- credential resolution happens at execution time.

### Durable Events

Candidate contract:

`Domain/Application Event → Durable Record → Delivery Attempt → Result → Retry/Dead Letter`

Required invariant:

> No generic broker/event bus is introduced unless a concrete delivery requirement justifies it.

### Workflow Productization

Candidate contract:

`Published WorkflowVersion → Reusable Template/Product → Clone/Customize → Validate → Publish`

Required invariant:

> Reuse must not mutate the source immutable WorkflowVersion.

## 5. Cross-Cutting Design Gates

Whichever direction is selected, the Design Gate must explicitly answer:

### Identity
What is the stable identity of the new artifact or operation?

### Ownership
Who owns it, and how does tenant isolation apply?

### Lifecycle
What are the states and legal transitions?

### Persistence
What must be durable before the operation is considered successful?

### Idempotency
What happens when the same request is replayed?

### Versioning
Which immutable artifact/version does the operation refer to?

### Authorization
Who can read, create, modify, publish, revoke, or execute it?

### Failure
What happens after partial persistence, provider failure, retry, or recovery?

### Observability
What evidence is retained to explain what happened?

### Boundary
Which existing aggregate/service owns the behavior, and which behavior must remain outside it?

## 6. What Should Not Be Combined Prematurely

The four directions have dependencies, but they should not be merged into one large capability.

Avoid automatically combining:

- Review + Credentials into a generic "Admin Platform".
- Credentials + Events into a generic integration bus.
- Productization + Marketplace into a deployment/release system.
- Review + UI into a mandatory frontend rewrite.
- Events + Notifications into a generic message broker before a concrete delivery requirement exists.

Each combination would create additional architecture before the product problem is established.

## 7. Decision Inputs Still Missing

The technical inspection cannot determine the product priority by itself.

The missing Project Owner input is the immediate business/product bottleneck:

- **Operate:** existing generated workflows need safe human review and operational control.
- **Connect:** workflows need safe access to real external providers.
- **React/Integrate:** workflows need durable outbound events or notifications.
- **Reuse/Distribute:** workflows need to become reusable products/templates.

Selecting one of these problem statements is sufficient to open its Design Gate.

## 8. Required Next Step

No implementation should start from this document.

Once one problem is selected, create a dedicated Design Gate containing:

`UNDERSTAND → MAP → DESIGN → TRADE-OFFS → DECIDE → RED → GREEN → VERIFY → DOCUMENT → EXIT REVIEW`

The Design Gate must define the smallest useful contract before any infrastructure or UI technology is selected.

## 9. Current Conclusion

The repository is not blocked by an unidentified runtime defect.

The current engineering state is a genuine product/architecture decision boundary. The next meaningful change should be driven by the problem the Project Owner wants Automation OS to solve next, while preserving the existing deterministic execution, publication, versioning, idempotency, tenant, and provider boundaries.
