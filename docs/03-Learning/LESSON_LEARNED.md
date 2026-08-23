# Lessons Learned

## Lesson 1 — Tests Expose Domain Ambiguity

The retry lifecycle exposed an important distinction between:

- retrying as an action;
- retrying as a state;
- starting after retry.

This forced the execution state machine to become more explicit.

## Lesson 2 — Git Status Has Meaning

`git status` distinguishes:

- modified files;
- staged files;
- deleted files;
- untracked files.

These are different repository states.

## Lesson 3 — Python Test Invocation Matters

`pytest -q` and `python -m pytest -q` can behave differently depending on environment/path configuration.

Using the active virtual environment explicitly helped verify:

```text
python -c "import sys; print(sys.executable)"
python -c "import app; print(app.__file__)"
python -m pytest -q
```

## Lesson 4 — Documentation Must Be Maintained

Creating many empty documentation files does not solve documentation drift.

Documentation must contain current decisions and be updated as the project evolves.
