# Mistakes and Recovery

## Documentation Drift

Problem:
Documentation directories existed but many files were empty or duplicated.

Recovery:
Establish a smaller set of authoritative documents and explicitly define their responsibilities.

## Git Tracking Confusion

Problem:
Files were created locally but remained untracked.

Recovery:
Understand the three important states:

Working tree
→ Staging area
→ Commit
→ Remote

`git add` moves changes to staging.

`git commit` records staged changes locally.

`git push` publishes commits to the remote repository.

## Test Environment Confusion

Problem:
`pytest -q` produced `ModuleNotFoundError: app`, while:

`python -m pytest -q`

passed all tests.

Recovery:
Verify the interpreter and import path before changing application code.
