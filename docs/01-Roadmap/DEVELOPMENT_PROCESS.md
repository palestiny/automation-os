# Development Process

Status: Accepted baseline

This project is developed as an engineering learning project, not as a sequence of isolated coding tasks.

## Core Loop

Understand → Plan → Document → Implement → Test → Review → Commit → Reflect → Update Documentation → Continue

## Before Implementation

For every meaningful feature:

1. Understand the business/domain problem.
2. Identify the desired outcome and scope.
3. Identify constraints, assumptions and open questions.
4. Locate the feature in the roadmap.
5. Identify affected domain concepts and module boundaries.
6. Decide whether a design gate or ADR is required.
7. Define the first testable behavior.

## During Implementation

- Follow TDD for domain behavior where practical.
- Keep domain logic independent from infrastructure.
- Prefer explicit boundaries over implicit coupling.
- Avoid speculative abstractions.
- Do not introduce provider-specific concepts into the core domain without a documented reason.

## After Implementation

- Run the relevant tests.
- Review the design against the original problem.
- Update documentation and roadmap status.
- Record meaningful decisions and lessons.
- Commit the completed change.
- Push the branch.

## Decision Discipline

Every significant decision should be classified as one of:

- Committed decision — the current project direction.
- Assumption — believed true but not yet sufficiently verified.
- Open question — intentionally unresolved.
- Alternative — another viable design considered.
- Trade-off — an accepted cost resulting from a decision.

The assistant may propose alternatives, but Khaled remains the decision maker for project direction.

## Design Gates

Before a major feature crosses from planning into implementation, confirm:

- the problem is understood;
- the domain model is coherent;
- boundaries are clear;
- important trade-offs are known;
- the first testable behavior is defined;
- the work fits the roadmap.

If these are not clear, stop and resolve the design instead of coding through uncertainty.

## Git Workflow

Default workflow:

Issue → Branch → Implementation → Tests → Review → Merge

Small documentation-only changes may use a direct commit when the change is low risk and review overhead is not useful.

## AI Collaboration Rule

AI is an implementation and reasoning partner, not the project decision maker.

The assistant must preserve the agreed architecture and explicitly surface uncertainty rather than silently changing direction.
