---
name: pb-test-driven-development
description: Use when implementing any feature or bugfix, before writing implementation code
---

# pb-test-driven-development

Write failing tests first, then implement to make them pass. Red → Green → Refactor.

**Core principle:** TDD is non-negotiable. Every task starts with a failing test.

## The Cycle

### 1. RED — Write a Failing Test

Write the simplest test that captures the requirement:

- One assertion per test (preferably)
- Test the behavior, not the implementation
- Use descriptive test names that explain the expected behavior
- STOP after writing the test — do not write implementation yet

### 2. Confirm RED — Run the Test

```bash
uv run pytest tests/path/test.py -v
```

The test MUST fail. If it passes, the test is wrong — fix the test, not the code.

Verify it fails for the RIGHT reason (not a syntax error or import failure).

### 3. GREEN — Write Minimal Implementation

Write the MINIMUM code to make the test pass:

- No extra features
- No "while I'm here" improvements
- No premature optimization
- Just enough to satisfy the test

### 4. Confirm GREEN — Run the Test

```bash
uv run pytest tests/path/test.py -v
```

All tests must pass. If not, fix the implementation (not the test).

### 5. REFACTOR — Clean Up (Optional)

If the code needs cleanup:

- Remove duplication
- Improve naming
- Simplify logic

Run tests again after refactoring to confirm no regressions.

## Key Rules

**NEVER:**

- Write implementation before the test
- Skip the RED phase (confirming test fails)
- Change the test to make it pass
- Write multiple tests before implementing
- Skip running tests

**ALWAYS:**

- One test at a time
- Confirm RED before GREEN
- Confirm GREEN before next test
- Run full suite after each task

## Test Design Principles

- **Test behavior, not implementation** — what it does, not how
- **One assertion per test** — keeps failures isolated
- **Descriptive names** — `test_user_creation_with_valid_email`, not `test_create`
- **Arrange-Act-Assert** — clear structure
- **Fast and deterministic** — no network, no sleep, no randomness

## Integration with pb-spec

- **pb-build Generator:** Every task in the BDD+TDD loop follows this cycle
- **pb-build TDD-only tasks:** Pure TDD without BDD outer loop
- **Standalone:** Use for any TDD need outside pb-spec workflow
