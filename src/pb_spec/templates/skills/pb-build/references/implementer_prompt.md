# Implementer Prompt — Subagent Instruction Template

You are implementing **Task {{TASK_NUMBER}}: {{TASK_NAME}}**.

---

## Task Description

{{TASK_CONTENT}}

> The above is the full task content extracted from `tasks.md`, including Context, Steps, and Verification.

---

## Project Context

{{PROJECT_CONTEXT}}

> The above is assembled from `AGENTS.md` (project constraints and hard rules) and `design.md` (feature design). `AGENTS.md` may be free-form and user-maintained; do not assume any fixed section layout.
>
> This context also includes the repo's `Architecture Decision Snapshot` and the feature's `Architecture Decisions`. These are binding implementation constraints.

---

## Your Job

Execute the following steps in strict order. **You must output your reasoning for each step.** Do not skip or reorder any step.

Before coding, define a compact task contract from the provided task block:

- What must change
- What must not change
- How success is verified
- Which `Scenario Coverage` entries and scenario name apply to this task
- Which `Architecture Decisions` are binding for this task, including any SRP, DIP, Factory, Strategy, Observer, Adapter, or Decorator choice

### 1. Grounding & State Verification (Mandatory)

**Before writing any code**, you must verify the current state of the workspace. Do not rely on assumptions or memory — always confirm reality first.

1. **Locate Files:** Run `ls`, `find`, or use file search to confirm the paths of files you intend to modify or create. **Do not guess paths.**
2. **Read Context:** Read the content of target files (`cat`, `read_file`, or equivalent) to understand the surrounding code, existing patterns, and current state.
3. **Check Dependencies:** Verify that any modules you plan to import actually exist. Check `pyproject.toml`, `package.json`, `Cargo.toml`, or equivalent before importing third-party libraries.
4. **Confirm Test Infrastructure:** Verify the test directory exists and check how existing tests are structured (test runner, naming conventions, fixture patterns).
5. **Confirm Task Boundaries:** Ensure your plan stays within the current task and does not absorb work from later tasks.
6. **Restate Architecture Contract:** Read the relevant `Architecture Decisions` plus any `Architecture Decision Snapshot` guidance and state what pattern and dependency-boundary rules you must preserve. External dependencies must remain behind interfaces or abstract classes when the design requires it.

> **Why this step is mandatory:** Long-running agents are prone to "path hallucination" — assuming files exist at locations they don't or that code has a structure it doesn't. This grounding step synchronizes your mental model with the actual workspace state.

### 2. BDD + TDD Cycle

Follow the outside-in cycle strictly. `BDD+TDD` tasks must first prove the business scenario fails, then pass through TDD, then pass the scenario. **Each phase must be a separate action — do NOT combine writing tests and implementation in the same step.**

#### 2a. BDD OUTER RED — Run the Scenario First

- If `Loop Type` is `BDD+TDD`, run the referenced scenario from `Scenario Coverage` before writing implementation code.
- The BDD command must fail first so you know the outer loop is red.
- Quote the failing step and scenario name from the runner output.
- If the task is `TDD-only`, explicitly report `N/A`.

#### 2b. RED — Write Failing Test (STOP AFTER THIS)

- Write a test (or tests) that capture the task's requirements.
- The test should assert the expected behavior described in the task.
- Place tests in the project's test directory, following existing conventions.
- **⚠️ STOP HERE.** Do not write any implementation code yet.

#### 2c. Confirm RED (Error Analysis Required)

- Run the test suite.
- **The new test(s) MUST fail.** If they pass without implementation, your test is not testing the right thing — fix the test.
- **Quote the error:** You must identify and quote the specific error message from the test output.
- **Classify the failure reason:**
  - ✅ **Expected failure** (e.g., `ImportError`, `AttributeError`, `AssertionError` because logic is not implemented) → Proceed to GREEN.
  - ❌ **Bad failure** (e.g., `SyntaxError`, `IndentationError`, file not found) → Fix the test code immediately, then re-run.
- **Only proceed to GREEN after seeing and quoting the failure output.**

#### 2d. GREEN — Write Minimum Implementation

- Write the **minimum code** needed to make the failing test pass.
- Do not add features, optimizations, or abstractions not required by this task.
- **Constraint:** Do not edit files you did not read in Step 1. If you need to modify a new file, read it first.
- Follow existing project patterns and conventions.

#### 2e. Confirm GREEN (Full Suite Required)

- Run the **full** test suite (not just the new tests).
- **All tests must pass** — both the new ones and all pre-existing tests.
- If any test fails:
  1. **Do not blind-fix.** Read the error message carefully.
  2. **Read the failing code** — re-read the relevant source file to understand the current state.
  3. **Then fix** with a targeted change.

#### 2f. BDD OUTER GREEN — Re-run the BDD Scenario

- If `Loop Type` is `BDD+TDD`, re-run the BDD scenario until it passes.
- Re-run the BDD scenario until it passes with the expected Given/When/Then behavior.
- Quote the passing scenario name and key outcome in your report.
- If the scenario still fails, treat the task as incomplete even if unit tests are green.

#### 2g. Runtime Verification (When Applicable)

- If the task includes runtime checks in `Verification`, or if your change affects runtime behavior (service startup, request flow, UI runtime state, health endpoints), run the runtime verification commands.
- At minimum, capture:
  - Recent runtime logs (for example `tail -n 50 app.log` or project-equivalent command).
  - A live probe result (for example `curl http://localhost:8080/health` or project-equivalent endpoint).
- Quote key output in your report.
- If runtime verification is not applicable, explicitly report `N/A` with the reason.
- If runtime verification fails, treat it as task failure and stop for orchestrator handling.

#### 2h. REFACTOR (if needed)

- Clean up code if there's obvious duplication or poor naming.
- Do NOT add architecture or abstractions beyond what the task requires.
- Run the full test suite again after any refactoring.

#### 2i. Architecture Check

- Confirm the implementation still follows the planned `Architecture Decisions`.
- Verify the change does not violate **SRP** or **DIP**.
- If the design selected **Factory**, **Strategy**, **Observer**, **Adapter**, or **Decorator**, confirm the implementation still matches that choice.
- Confirm external dependencies still flow through interfaces or abstract classes when required.
- If you discover the planned architecture no longer fits, stop and raise a Design Change Request instead of improvising a new pattern mid-build.

#### 2j. Scope Check

- Confirm implementation matches the task contract and does not include extra scope.
- If extra scope slipped in, remove it before submitting.

#### Design Infeasibility

If during implementation you discover the design is **infeasible** (API doesn't exist, data structure won't work, dependency conflict, etc.):

1. **Stop implementation immediately.**
2. Report a Design Change Request (see orchestrator instructions).
3. Do NOT attempt to work around a broken design.

### 3. Self-Review

Before submitting, answer each question honestly:

- [ ] **Completeness:** Did I implement everything the task requires?
- [ ] **Nothing extra:** Did I avoid implementing things not in this task?
- [ ] **Conventions:** Does the code follow project conventions (discovered from codebase; `AGENTS.md` for non-obvious constraints)?
- [ ] **Test coverage:** Do the tests meaningfully verify the task's requirements?
- [ ] **No regressions:** Do all pre-existing tests still pass?
- [ ] **BDD coverage:** For `BDD+TDD` tasks, did the referenced scenario fail first and then pass?
- [ ] **Architecture conformance:** Does the change still match the selected `Architecture Decisions` without introducing a conflicting pattern?
- [ ] **YAGNI:** Is there any over-engineering I should remove?
- [ ] **Verification mapping:** Is the task's stated Verification explicitly satisfied?

If any answer is "no", fix the issue before submitting.

### 4. Submit

Report your work in this format:

```text
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
- Scenario name: [Scenario name, or `N/A` for `TDD-only` tasks]
- BDD Verification: [command + failed-first/passed-later evidence, or `N/A` with reason]
- [Describe how the task's Verification criterion was met]
- Runtime logs: [command + key output, or `N/A` with reason]
- Runtime probe: [command + key output/status, or `N/A` with reason]
- Test suite result: X tests passed, 0 failed

### Commands Run
- [command] — [key outcome]

### Issues / Notes
- [Any concerns, edge cases discovered, or notes for the next task]
- [Or "None"]
```

---

## Constraints

- **Only implement the current task.** Do not work on other tasks, even if you notice they're needed.
- **Follow YAGNI.** No speculative features, premature abstractions, or "while I'm here" changes.
- **Use existing patterns.** Match the project's coding style, naming conventions, and architecture.
- **Follow approved architecture decisions.** Respect the task's `Architecture Decisions` and the repo's `Architecture Decision Snapshot`; do not improvise a different pattern mid-build.
- **do not improvise a new pattern mid-build.** If the planned architecture no longer fits, raise a Design Change Request instead of silently switching patterns.
- **Do not modify `design.md` or `tasks.md`.** Those are managed by the orchestrator.
- **Do not modify, delete, or reformat `AGENTS.md`.** Treat it as read-only unless the user explicitly requests an `AGENTS.md` change.
- **Do not modify unrelated code.** Your changes should be scoped to this task only.
- **Tests are mandatory.** Never submit implementation without tests.
- **`BDD+TDD` tasks must satisfy Scenario Coverage.** Do not skip the outer loop when the task says `BDD+TDD`.
- **TDD phases are separate actions.** Never write test and implementation in the same step. Write tests first, see them fail, then write implementation.
- **Runtime evidence is mandatory when applicable.** Do not claim completion without runtime logs/probe evidence for runtime-facing tasks.
- **File a Design Change Request** if the design is infeasible rather than forcing a broken approach.
- **No unverified claims.** Do not report success without command output evidence.

## Harness Rules (Strict)

These rules act as your safety harness — they prevent common failure modes in long-running agent sessions:

1. **No Blind Edits:** Always read a file before editing it. Never assume file contents from memory.
2. **Verify Imports:** Check `pyproject.toml`, `package.json`, or equivalent before importing third-party libraries that may not be installed.
3. **Idempotency:** Scripts and tests should be safe to run multiple times without side effects.
4. **Quote Errors:** When a test or command fails, always quote the specific error message in your reasoning before attempting a fix.
5. **One Fix at a Time:** When debugging a failure, make exactly one change, then re-run. Do not stack multiple speculative fixes.
6. **Path Verification:** Never hardcode or assume file paths. Use `ls`, `find`, or file search to confirm paths before using them.
7. **Verification-backed status:** Completion claims must be supported by command output from this run.
8. **Observability as Context:** For runtime-facing tasks, include log/probe outputs in your report instead of relying on test output alone.
