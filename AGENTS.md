# Automation OS — Autonomous Engineering Instructions

This repository uses autonomous engineering execution.

Before making changes, read:
- `PROJECT_STATUS.md` — **mandatory current-state entry point**
- `AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md`
- the repository README
- applicable architecture/design-gate documentation
- relevant tests and Git history

**Project Status is a maintained project-state contract, not optional documentation.** Before planning significant work, use `PROJECT_STATUS.md` to establish the current phase, latest milestone, active work, and next decision boundary. Do not rely on stale conversation context or infer the current phase from an individual roadmap file.

The autonomous-development rules in `AUTONOMOUS_PROJECT_DEVELOPMENT_MODE.md` are the operating procedure for engineering work in this repository.

Continue through inspect → design → test → implement → verify → document → review → next task without waiting for user confirmation after ordinary engineering steps.

Stop only for the explicit stop conditions defined in that document: human decision required, missing critical information, destructive/irreversible action, external authorization, genuine ambiguity, or tool limitation.

Project/business and major architecture decisions remain owned by the Project Owner.


## Hard State-Drift Guard — Mandatory Before Any Planning

This guard exists specifically to prevent stale conversation/context from causing work to restart from an already-completed phase.

Before **any** planning, design, implementation, or capability selection:

1. Fetch `PROJECT_STATUS.md` from GitHub `master` first.
2. Read its **Current State**, **Latest Milestone**, **Current Position**, and **Next Decision Boundary**.
3. Fetch repository metadata/current default branch and verify the working source is `master` unless an explicitly active feature branch is identified by the status.
4. Treat any conversation summary, memory, previous assistant statement, cached phase number, or historical roadmap state as **stale until reconciled** with the freshly fetched `PROJECT_STATUS.md`.
5. If the freshly fetched status is later than the remembered state, **discard the older state completely**; do not replay, re-plan, or re-implement completed work.
6. Never infer the current phase from the numbered capability sequence alone. The sequence is historical/ordered; `PROJECT_STATUS.md` is the current-state authority.
7. Before starting a capability, establish internally: `CURRENT = <status milestone>; NEXT = <status decision boundary>`. Any task that targets an earlier capability is treated as regression/rework and requires an explicit repository-based reason.
8. If status, roadmap, exit review, and Git history disagree, stop normal execution and reconcile the contradiction before changing code.

**Critical invariant:** a completed milestone must never become the active task again merely because an older conversation context or stale model summary says it is next.

### Recovery Rule After State Drift

If stale-state work is detected:
- stop the stale task immediately;
- re-fetch `PROJECT_STATUS.md` from `master`;
- identify the actual current milestone and next decision boundary;
- document the drift/root cause if it affected repository work;
- resume only from the verified current state.

Do not spend additional turns rediscovering already-completed capabilities.

## Project Status Maintenance Contract

`PROJECT_STATUS.md` is the single entry point for the current project state.

It **must be reviewed at the start of autonomous work and updated whenever a meaningful project-state change occurs**, including when any of the following changes:

- current phase or phase status;
- active implementation or active milestone;
- latest completed milestone;
- next committed milestone or decision gate;
- major architectural boundary;
- explicitly deferred/activated scope.

Before declaring a milestone/capability complete, verify that `PROJECT_STATUS.md` reflects the completed state and links to the authoritative roadmap/Design Gate/exit review.

When work is merged, the status must remain consistent with `master`. If the change affects current project state, update `PROJECT_STATUS.md` in the same logical change/PR whenever practical.

Do not create a second competing project-status tracker. Detailed rationale belongs in roadmap, Design Gate, decision, and journal documents; `PROJECT_STATUS.md` summarizes the authoritative current state and points to those sources.
