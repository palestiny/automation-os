# Definition of Done

Status: Accepted baseline

A change is considered done only when the following are true.

## 1. Problem and Scope

- The problem being solved is understood and stated.
- The change belongs to the current roadmap phase.
- Scope and non-goals are clear.

## 2. Design

- Domain behavior is identified before implementation.
- The design fits the current architecture and module boundaries.
- Important alternatives and trade-offs are documented when the decision is non-trivial.
- A new ADR is created when the change introduces or reverses a significant architectural decision.

## 3. Implementation

- Code is placed in the correct layer/module.
- Business rules are not hidden inside infrastructure concerns.
- Public behavior has clear names and responsibilities.
- Existing behavior is preserved unless the change explicitly requires a change.

## 4. Tests

- New behavior has tests.
- Tests cover important invalid states and boundary conditions.
- The relevant test suite passes.
- Tests verify behavior rather than implementation details where practical.

## 5. Documentation

- The roadmap reflects the completed work.
- Relevant architecture/decision documentation is updated.
- The development journal records meaningful milestones or decisions.

## 6. Git

- Work is associated with an issue or clearly defined task.
- The change is committed with a meaningful message.
- The working branch is pushed.
- Review happens before merge when the repository workflow supports it.

## 7. Understanding Gate

For learning milestones, Khaled must be able to explain:

- what was built;
- why it exists;
- why this design was selected;
- what trade-offs were accepted;
- what remains intentionally unresolved.

## Rule

"It works" is not sufficient. A milestone is done when behavior, tests, design, documentation and understanding are aligned.
