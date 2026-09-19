# Intent Clarification Outcome Design Gate

## Status

Accepted for the Phase 6 intent boundary.

## Problem

An analyzed Intent can be structurally valid and use a canonical goal while still being unsafe to act on because the platform cannot determine a single executable workflow from the available information.

The existing selection boundary now exposes `CLARIFICATION_REQUIRED` when required information is missing, including the missing parameter names. The intent-to-execution application boundary must preserve that explicit provider-neutral outcome rather than attempting execution.

## Boundary

`Raw request → IntentAnalyzer → Intent → ValidateIntent → SelectWorkflow → IntentExecutionResult`

This increment changes only the application outcome semantics at the intent boundary. It does not introduce an autonomous clarification loop.

## Committed Decisions

1. Introduce `CLARIFICATION_REQUIRED` as an explicit application outcome.
2. The outcome is returned when the Intent is valid/canonical but cannot safely proceed because required information is missing or the selection is ambiguous.
3. `NO_MATCH` remains reserved for the case where no published workflow supports the canonical goal.
4. `INVALID_PARAMETERS` remains a distinct deterministic selection outcome for supplied values that violate a workflow's declared parameter types.
5. The clarification outcome carries no Execution and never starts workflow execution.
6. The platform does not automatically ask a question, retry analysis, loop, or choose a workflow on the user's behalf.
7. The outcome remains provider-neutral and contains no AI/provider-specific data.
8. Deterministic workflow selection remains provider-neutral; its clarification status and missing-parameter metadata are passed through without autonomous resolution.

## Outcome Mapping

| Selection condition | Intent execution outcome |
| --- | --- |
| exactly one valid workflow | `STARTED` |
| no published workflow for goal | `NO_MATCH` |
| matching workflow exists but required input is missing | `CLARIFICATION_REQUIRED` (with missing parameter names) |
| multiple complete workflows match | `CLARIFICATION_REQUIRED` |
| supplied parameter types are invalid | `INVALID_PARAMETERS` |
| canonical goal is invalid | `INVALID_GOAL` |

## Explicit Non-Goals

- no agent loop;
- no conversation memory;
- no automatic follow-up question generation;
- no AI-owned workflow selection;
- no model routing or retries;
- no semantic/vector matching;
- no workflow generation.

## TDD Order

1. RED: verify missing information produces `CLARIFICATION_REQUIRED` without execution.
2. RED: verify ambiguity produces `CLARIFICATION_REQUIRED` without execution.
3. GREEN: map the existing deterministic selection statuses to the new application outcome.
4. REFACTOR: keep selection provider-neutral and unchanged.

## Exit Criteria

- The clarification outcome is explicit and provider-neutral.
- Missing required information and ambiguous selection cannot start execution.
- Existing `NO_MATCH`, `INVALID_PARAMETERS`, `INVALID_GOAL`, and `STARTED` semantics remain intact.
- No autonomous clarification behavior is introduced.
- The existing test suite remains green.
