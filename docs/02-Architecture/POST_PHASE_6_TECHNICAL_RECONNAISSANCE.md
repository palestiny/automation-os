# Post-Phase 6 Technical Reconnaissance

## Status

Neutral reconnaissance only. No post-Phase-6 capability is selected by this document.

## Verified execution baseline

The current Execution aggregate is the single lifecycle state holder. Its states are CREATED, RUNNING, WAITING, RETRYING, COMPLETED, FAILED, and CANCELLED.

The aggregate also owns current step, attempt, start time, finish time, and lifecycle transition validation.

## Verified persistence baseline

ExecutionRepository currently exposes only save(execution), get(execution_id), and all().

There is no repository contract in this boundary for command/idempotency records, execution history records, or structured event storage.

## Verified start boundary

StartWorkflowExecution.execute(workflow_id):

1. loads the workflow;
2. requires PUBLISHED;
3. creates a new Execution;
4. persists it;
5. starts it;
6. persists it again;
7. returns the Execution.

This makes the start use case a concrete candidate boundary for a future reliability/idempotency design, but this document does not select that capability.

## Verified read boundary

GetExecutionProgress projects the persisted Execution into an immutable ExecutionProgress read model.

The HTTP execution API exposes start workflow execution, list executions, get execution, cancel, resume, retry, and retry-and-execute.

The API reads execution state through the existing application projection and does not define a second execution state model.

## Implications by capability

### A — Execution Reliability / Visibility

The most directly identifiable existing boundary is StartWorkflowExecution, with ExecutionRepository as the persistence boundary and Execution as the lifecycle authority.

The major unresolved design questions remain:

- idempotency key and lifetime;
- duplicate response semantics;
- history versus telemetry;
- event persistence ownership;
- persistence failure semantics.

No implementation should assume answers to these questions.

### B — Ownership / Authorization

The inspected execution API currently accepts resource identifiers without an ownership context. A future ownership gate would therefore need an explicit identity/owner model before changing application contracts.

### C — Planning / Generation

The inspected execution boundary provides a clear deterministic handoff point: planner-produced workflow data must not bypass existing workflow validation, selection, and execution rules. The exact planner output contract is still intentionally unspecified.

### D — Product / API

The execution API already provides concrete HTTP operations, but the repository does not currently establish a public consumer contract, compatibility policy, or identity model. Those decisions should be driven by a selected consumer rather than by generic API expansion.

## TDD-ready starting points

- A: duplicate invocation of the selected command.
- B: unauthorized access to a selected owned resource.
- C: malformed or incomplete planner output rejected before execution.
- D: first stable consumer endpoint contract.

## Explicit non-decision

This reconnaissance does not:

- select A, B, C, or D;
- introduce production behavior;
- change the Execution lifecycle;
- define an idempotency policy;
- define ownership semantics;
- authorize AI planning;
- freeze a public API contract.

The next implementation step remains dependent on the Project Owner's capability selection.
