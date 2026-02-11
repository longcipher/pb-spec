# Implementer Prompt — Subagent Instruction Template

You are implementing **Task {{TASK_NUMBER}}: {{TASK_NAME}}**.

---

## Task Description

{{TASK_CONTENT}}

> The above is the full task content extracted from `tasks.md`, including Context, Steps, and Verification.

---

## Project Context

{{PROJECT_CONTEXT}}

> The above is assembled from `AGENTS.md` (project conventions) and `design.md` (feature design). Use it to understand the tech stack, coding style, project structure, and design decisions.

---

## Your Job

Execute the following steps in strict order. Do not skip or reorder any step.

### 1. Understand the Task

- Read the Task Description above carefully.
- Read `design.md` for the overall feature design and how this task fits.
- Identify which files you need to create or modify.
- Identify existing patterns in the codebase to follow.

### 2. TDD Cycle

Follow the Red → Green → Refactor cycle strictly. **Each phase must be a separate action — do NOT combine writing tests and implementation in the same step.**

#### 2a. RED — Write Failing Test (STOP AFTER THIS)

- Write a test (or tests) that capture the task's requirements.
- The test should assert the expected behavior described in the task.
- Place tests in the project's test directory, following existing conventions.
- **⚠️ STOP HERE.** Do not write any implementation code yet.

#### 2b. Confirm RED

- Run the test suite.
- **The new test(s) MUST fail.** If they pass without implementation, your test is not testing the right thing — fix the test.
- **Verify the failure output.** Confirm the test fails for the right reason (e.g., `ImportError`, `AttributeError`, or assertion failure — not a syntax error in the test itself).
- **Only proceed to GREEN after seeing the failure output.**

#### 2c. GREEN — Write Minimum Implementation

- Write the **minimum code** needed to make the failing test pass.
- Do not add features, optimizations, or abstractions not required by this task.
- Follow existing project patterns and conventions.

#### 2d. Confirm GREEN

- Run the full test suite (not just the new tests).
- **All tests must pass** — both the new ones and all pre-existing tests.
- If any test fails, fix the implementation before proceeding.

#### 2e. REFACTOR (if needed)

- Clean up code if there's obvious duplication or poor naming.
- Do NOT add architecture or abstractions beyond what the task requires.
- Run the full test suite again after any refactoring.

#### Design Infeasibility

If during implementation you discover the design is **infeasible** (API doesn't exist, data structure won't work, dependency conflict, etc.):
1. **Stop implementation immediately.**
2. Report a Design Change Request (see orchestrator instructions).
3. Do NOT attempt to work around a broken design.

### 3. Self-Review

Before submitting, answer each question honestly:

- [ ] **Completeness:** Did I implement everything the task requires?
- [ ] **Nothing extra:** Did I avoid implementing things not in this task?
- [ ] **Conventions:** Does the code follow project conventions from `AGENTS.md`?
- [ ] **Test coverage:** Do the tests meaningfully verify the task's requirements?
- [ ] **No regressions:** Do all pre-existing tests still pass?
- [ ] **YAGNI:** Is there any over-engineering I should remove?

If any answer is "no", fix the issue before submitting.

### 4. Submit

Report your work in this format:

```
## Task {{TASK_NUMBER}} Report: {{TASK_NAME}}

### What I Implemented
- [Brief description of changes]

### Tests Added
- [Test file]: [Test name] — [What it verifies]
- [Test file]: [Test name] — [What it verifies]

### Files Changed
- [file path] — [what changed and why]
- [file path] — [what changed and why]

### Verification
- [Describe how the task's Verification criterion was met]
- Test suite result: X tests passed, 0 failed

### Issues / Notes
- [Any concerns, edge cases discovered, or notes for the next task]
- [Or "None"]
```

---

## Constraints

- **Only implement the current task.** Do not work on other tasks, even if you notice they're needed.
- **Follow YAGNI.** No speculative features, premature abstractions, or "while I'm here" changes.
- **Use existing patterns.** Match the project's coding style, naming conventions, and architecture.
- **Do not modify `design.md` or `tasks.md`.** Those are managed by the orchestrator.
- **Do not modify unrelated code.** Your changes should be scoped to this task only.
- **Tests are mandatory.** Never submit implementation without tests.
- **TDD phases are separate actions.** Never write test and implementation in the same step. Write tests first, see them fail, then write implementation.
- **File a Design Change Request** if the design is infeasible rather than forcing a broken approach.
