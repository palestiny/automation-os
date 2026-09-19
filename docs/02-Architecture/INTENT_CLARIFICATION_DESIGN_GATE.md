# Intent Clarification Outcome Design Gate

## Purpose

Define an explicit provider-neutral outcome when an otherwise valid intent cannot be safely executed because required workflow information is missing.

## Decisions

1. Clarification is an application outcome, not an AI-owned loop.
2. Workflow selection remains deterministic.
3. Missing required parameters are represented as `CLARIFICATION_REQUIRED`.
4. The result includes the missing parameter names so a caller can request the missing information.
5. Invalid parameter types remain `INVALID_PARAMETERS`; they are not silently converted into clarification.
6. No execution starts when clarification is required.
7. No conversational memory, automatic follow-up loop, agent loop, or autonomous re-analysis is introduced.
8. Existing `MISSING_PARAMETERS` is retained as a compatibility alias for the new status during this transition.
9. The workflow engine remains responsible for declaring required parameters; the AI analyzer does not infer workflow requirements.
10. A future UI/API may turn this outcome into a user-facing question without changing the execution engine.

## Flow

`Request → Intent → Deterministic Selection → CLARIFICATION_REQUIRED → caller asks for missing values → new Intent → selection`

## Exit Criteria

- callers can distinguish clarification from no-match and invalid parameters;
- missing parameter names are available;
- no execution is created for clarification;
- selection remains deterministic;
- no autonomous clarification loop is introduced.
