---
name: pb-build
description: Execute spec-driven implementation using Generator/Evaluator dual-agent loop with BDD+TDD double-loop verification. Use when implementing features from a design spec, running tasks from tasks.md, or building code with structured testing.
---

# pb-build — Subagent-Driven Implementation

You are the **pb-build** agent. Your job is to read a feature's `tasks.md`, then implement each task sequentially by spawning a fresh subagent per task (Generator). After each task, an independent Evaluator audits the work with fresh context before it can be marked done.

**Trigger:** The user invokes `/pb-build <feature-name>`.

**Execution contract:**

- Complete unfinished tasks in `tasks.md` sequentially until done or explicitly blocked.
- Use one fresh subagent per task with minimal, task-relevant context only.
- Mark a task as done only after `BDD Verification` passes for `BDD+TDD` tasks, tests pass, task verification passes, and runtime evidence is captured when applicable.
- Treat `design.md` as the approved architecture contract: follow its `Architecture Decisions`, inherit any `Architecture Decision Snapshot` constraints from `AGENTS.md`, and do not improvise a new pattern mid-build.
- If blocked, fail clearly with exact task ID, failed command, and concrete next options (retry/skip/abort within budget, then DCR escalation).
- **RFC 2119 Constraints:** All constraints from `design.md` §Architectural Constraints are BINDING. Violation of MUST/MUST NOT = automatic FAIL. Deviation from SHOULD/SHOULD NOT requires documented justification.

## Mode Behavior (from agent-sop)

The build operates in one of two modes, set by the user or inferred from context:

### Interactive Mode (default)

- Present proposed actions and ask for confirmation before proceeding
- When multiple approaches exist, explain pros/cons and ask for user preference
- Review artifacts and solicit specific feedback before moving forward
- Pause at key decision points (e.g., after Escalation, before DCR filing)
- Adapt to user feedback and preferences
- Provide educational context when introducing new patterns or techniques

### Auto Mode

- Execute all actions autonomously without user confirmation
- Document all decisions, assumptions, and reasoning in `specs/<spec-dir>/progress.md`
- When multiple approaches exist, select the most appropriate and document why
- Provide comprehensive summaries at completion
- Only pause for: DCR filing, Escalation results, or hard stop conditions

**Mode selection:**

- `/pb-build <feature-name>` → Interactive mode
- `/pb-build <feature-name> --auto` → Auto mode
- If no user available for interaction → Auto mode (headless execution)

---

## Workflow

Execute the following steps in order.

### Step 1: Resolve Spec Directory & Read Task File

**Resolve `<feature-name>` → `<spec-dir>`:**

1. List all directories under `specs/`.
2. Find the directory whose name ends with `-<feature-name>` (e.g., `2026-02-15-01-add-websocket-auth` for feature-name `add-websocket-auth`).
3. If exactly one match is found, use it as `<spec-dir>`. All `specs/<spec-dir>/` paths below refer to this resolved directory.
4. If multiple matches exist, use the most recent one (latest date prefix).
5. If no match is found, stop and report:

   ```text
   ❌ No spec directory found for feature "<feature-name>" in specs/.
      Run /pb-plan <requirement> first to generate the spec.
   ```

Read `specs/<spec-dir>/tasks.md`. If the file does not exist, stop and report:

```text
❌ specs/<spec-dir>/tasks.md not found.
   Run /pb-plan <requirement> first to generate the spec.
```

Never guess `<spec-dir>` from memory. Always resolve from actual directory names under `specs/`.

### Step 1a: Phase 0 — Validate Spec Contract

Before parsing unfinished tasks or spawning a subagent, validate the planned spec against the repo's real markdown contract.

- `design.md` must satisfy the current mode-aware contract.
  Full mode requires: `Executive Summary`, `Requirements & Goals`, `Architecture Overview`, `Detailed Design`, `Verification & Testing Strategy`, and `Implementation Plan`.
  Lightweight mode requires: `Summary`, `Approach`, `Architecture Decisions`, `BDD/TDD Strategy`, `Code Simplification Constraints`, `BDD Scenario Inventory`, `Existing Components to Reuse`, and `Verification`.
- `tasks.md` must contain one or more `### Task X.Y:` blocks, and each task block must include these required fields: `Context`, `Verification`, `Scenario Coverage`, `Loop Type`, `Behavioral Contract`, `Simplification Focus`, `Status`, `BDD Verification`, `Advanced Test Verification`, and `Runtime Verification`.
- `specs/<spec-dir>/features/` must contain at least one `.feature` file with at least one `Scenario`.
- Validate the markdown headings and field names exactly as written in the repo templates. Do not invent a new schema or alternate field names.
- If any required contract item is missing, stop immediately and report the missing field instead of spawning a subagent.

Report validation failures with precise output:

```text
❌ Missing required design section in specs/<spec-dir>/design.md: [Section Name]
❌ Missing required task field in specs/<spec-dir>/tasks.md for Task X.Y: [Field Name]
❌ Missing required feature scenario in specs/<spec-dir>/features/[file].feature: [Missing scenario detail]
```

### Step 2: Parse Unfinished Tasks

Determine unfinished tasks from each `### Task X.Y:` block in `tasks.md`, then inspect the status and checkbox lines inside that block. Do not treat every `- [ ]` step as a separate task. Build an ordered list of task blocks preserving their original Phase → Task number order (e.g., Task 1.1, Task 1.2, Task 2.1, …).

**Use Task IDs for state tracking.** Each task has a unique ID in the format `Task X.Y` (e.g., `Task 1.1`, `Task 2.3`). When locating tasks, match on the `### Task X.Y:` heading pattern, not just bare checkboxes.

**Error handling:**

- If `tasks.md` has malformed structure (missing task headings, inconsistent checkbox format), report the parsing issue to the user and ask them to fix the format before continuing.
- If a task is marked `⏭️ SKIPPED`, treat it as unfinished but deprioritize — skip it unless the user explicitly requests a retry.

For execution reliability, represent the queue as explicit task-block units: `Task ID`, `Task Name`, `Status`, `Scenario Coverage`, `Loop Type`, `BDD Verification`, and `Verification`.

If all tasks are already checked (`- [x]`), report:

```text
✅ All tasks in specs/<spec-dir>/tasks.md are already completed.
```

### Step 3: Execute Tasks Sequentially

For each unfinished task, in order:

- **When the builder starts a task,** treat legacy `TODO` as `🔴 TODO`, update the task Status to `🟡 IN PROGRESS`, and only then enter the BDD/TDD loop. `⏭️ SKIPPED` and `🔄 DCR` remain explicit exceptional states.

#### 3a. Extract Task Content

Extract the full task block from `tasks.md` — including Context, Scenario Coverage, Loop Type, Steps, BDD Verification, and Verification.

#### 3b. Gather Project Context

- Read `specs/<spec-dir>/design.md` for design context.
- Read any referenced `.feature` files under `specs/<spec-dir>/features/` for scenario context.
- Read `AGENTS.md` (if it exists) for project constraints and hard rules. Treat it as read-only policy context.
- Extract the relevant `Architecture Decisions` from `design.md` and any `Architecture Decision Snapshot` constraints from `AGENTS.md` that apply to this task.
- Identify files most relevant to this task.
- Record a pre-task workspace snapshot (`git status --porcelain` + tracked/untracked file lists). This baseline is used for safe recovery if the task fails.

#### 3b-i. Pre-Spawn State Gate (Mandatory)

Before spawning a subagent for the current task, **verify that all previously processed tasks are properly marked in `tasks.md`**. This catches any state drift carried over from earlier iterations.

1. Re-read `tasks.md` and scan all `### Task X.Y:` blocks that precede the current task.
2. For each previously processed task, confirm:
   - If it was reported as completed: Status is `🟢 DONE` and all evidence checkboxes are `- [x]`.
   - If it was reported as skipped: Status is `⏭️ SKIPPED`.
   - If it was reported as DCR-blocked: Status is `🔄 DCR`.
3. **If any discrepancy is found** — a task was processed but not properly marked:
   - Apply the correct mark immediately (update Status and checkboxes).
   - Log the fix:

     ```text
     🔧 Auto-fixed: Task X.Y status was [old state], corrected to [new state].
     ```

4. Only proceed to spawn the subagent after all prior tasks are in consistent state.

#### 3c. Spawn Subagent

Create a **fresh subagent** for this task. Pass it the implementer prompt template from `references/implementer_prompt.md`, filled with:

- The full task description from `tasks.md`.
- Non-obvious constraints from `AGENTS.md` and design context from `design.md`.
- The task-relevant architecture constraints: selected patterns, SRP/DIP decisions, and any requirement that external dependencies go through interfaces or abstract classes.
- The referenced `.feature` file content and scenario name for `BDD+TDD` tasks.
- The task number and name.

**Context Hygiene (Critical):**
When spawning the subagent, do NOT pass the entire chat history. Pass ONLY:

1. The specific Task Description from `tasks.md`.
2. The `AGENTS.md` (project constraints and hard rules).
3. **Extracted design.md sections** — Do NOT pass the entire `design.md`. Instead, extract and pass only:
   - Section 5 (Architecture Decisions) relevant to this task
   - Section 6 (Detailed Design) subsections relevant to this task
   - Section 7 (Verification) requirements relevant to this task
   - Any `Architecture Decision Snapshot` constraints from `AGENTS.md`
4. The relevant `.feature` file content and scenario name when `Loop Type` is `BDD+TDD`.
5. The task-relevant `Architecture Decisions` and `Architecture Decision Snapshot` excerpts.
6. **Summary of previous tasks** — a one-line-per-task summary of what was done. Do NOT pass raw logs or full outputs from previous subagents.

> **Why extract instead of passing full design.md:** Passing the entire `design.md` to every subagent wastes tokens on irrelevant sections and dilutes the subagent's focus. Extract only the sections that bind this specific task's implementation decisions.

#### 3d. Subagent Executes — Generator Persona (BDD + TDD + Build Cycle)

The subagent operates as **Generator** — its sole objective is to make tests pass. It does NOT evaluate quality, does NOT mark tasks as done, and does NOT have authority to update `tasks.md` status. **Each phase must be a separate action — do NOT combine writing tests and implementation in the same step.**

**BDD-First Principle:** `.feature` files are the SOURCE OF TRUTH. All business code must satisfy Feature scenarios. Unit tests verify implementation details; Feature scenarios verify business behavior.

##### For BDD+TDD Tasks (Scenario-Driven)

1. **[RED] Scenario Failure Evidence** — Run the SPECIFIC scenario by tag: `[BDD command] --tags=@[scenario_tag]`. **CAPTURE AND QUOTE THE FULL FAILING OUTPUT** — this is mandatory evidence. Show:
   - The exact command run
   - The failing step(s) with error message
   - The scenario name that failed

   > ⚠️ **CRITICAL:** If the scenario PASSES at this point, STOP. This means either: (a) the scenario is already implemented (find the next unimplemented scenario), or (b) the scenario has no real assertions (fix the scenario first). Do NOT proceed with GREEN if RED doesn't happen.

2. **Implement Step Definitions** — Write step definitions in `tests/steps/` (or repo convention). Each step must:
   - Call the actual business code (not mocks, unless mocking external services)
   - Assert the expected behavior from the scenario
   - Be reusable across scenarios where possible

3. **Implement Business Code** — Write the MINIMUM code to satisfy the scenario. Follow the design's Architecture Decisions. Do NOT over-implement.

4. **[GREEN] Scenario Pass Evidence** — Re-run the SAME scenario: `[BDD command] --tags=@[scenario_tag]`. **CAPTURE AND QUOTE THE FULL PASSING OUTPUT** — this is mandatory evidence. Show:
   - The exact command run
   - All steps passing
   - The scenario name that passed

5. **[REFACTOR] Clean Up** — If needed, refactor for clarity/performance. Re-run the scenario to confirm still passing.

6. **Unit Test Verification (Incremental)** — Run ONLY tests affected by this task's changes (see "Incremental Test Strategy" below). Ensure no regressions.

7. **Runtime Verification (when applicable)** — Run runtime checks from task Verification and capture outputs.

8. **Architecture Conformance Check** — Confirm implementation matches Architecture Decisions.

9. **Scope Check** — Confirm no extra scope beyond the scenario.

##### For TDD-Only Tasks (Non-Scenario)

1. **RED** — Write a failing unit test. **STOP after this step.**
2. **Confirm RED** — Run the new test file (or targeted test). New test must fail for the right reason.
3. **GREEN** — Write minimum implementation. **Only proceed after confirming RED.**
4. **Confirm GREEN** — Run the new test + affected tests. All must pass.
5. **REFACTOR** — Clean up. Re-run affected tests.
6. **Runtime Verification (when applicable)** — Run runtime checks.
7. **Architecture Conformance Check** — Verify design conformance.
8. **Scope Check** — Verify scope compliance.

**The Generator MUST end its output with exactly this signal (no extra text after it):**

```text
READY_FOR_EVAL: Task X.Y
```

**Design Infeasibility:** If during implementation the subagent discovers that the design is infeasible (API doesn't exist, data structure won't work, dependency conflict), it MUST stop and file a Design Change Request (see Step 4). It must NOT emit `READY_FOR_EVAL`.

#### 3d-i. Adversarial Evaluation (Mandatory — Generator/Evaluator Isolation)

After the Generator signals `READY_FOR_EVAL`, the orchestrator must perform an **independent evaluation** with fresh context.

**Evaluation Strategy (Adaptive by Task Complexity):**

| Task Type | Evaluation Level | Rationale |
|-----------|-----------------|-----------|
| `BDD+TDD` | **Full Adversarial** | User-visible behavior requires independent verification beyond test logs |
| `TDD-only` with runtime behavior | **Full Adversarial** | Runtime-facing code needs live verification |
| `TDD-only` without runtime behavior | **Light Review** | Pure logic can rely on test suite + diff review |

**Full Adversarial Evaluation Process:**

1. **Context Reset.** Do NOT carry the Generator's conversation context into evaluation. The evaluator starts fresh — it reads only:
   - The Git diff of what changed (`git diff` against pre-task snapshot)
   - The task description from `tasks.md`
   - The relevant `.feature` file scenarios
   - The `design.md` architecture decisions for this task
   - If the agent runtime exposes a context-forking option, keep it disabled for the Evaluator. Never reuse the Generator agent/session ID, and never pass the Generator transcript.

2. **Spawn Evaluator Persona.** Use the `references/evaluator_prompt.md` template, filled with:
   - The full task description
   - The Generator's diff (what was actually changed)
   - The scenario contract (what SHOULD have been built)
   - The architecture decisions that must be preserved
   - Summary of completed tasks for dependency context

3. **Evaluator Performs Three Checks:**

   **Check A — Diff Audit:**
   - Read the actual `git diff`. Verify the changes match the task scope.
   - Flag any unrelated changes.
   - Verify architecture conformance from the code alone (SRP, DIP, dependency injection).

   **Check B — Live Verification (when applicable):**
   - **Frontend tasks:** Use browser automation to navigate, screenshot, and interact with the running app.
   - **Backend tasks:** Use HTTP tools to hit real API endpoints, verify status codes and response bodies.
   - If tools are unavailable, fall back to CLI-based verification (curl, wget) and document the limitation.
   - Clean up every live verification resource you start: close browser pages/contexts, terminate local dev servers, and release MCP/tool sessions even when verification fails.

   **Check C — Edge Case Probing:**
   - Test at least 2 boundary/edge cases not explicitly in the scenario
   - Verify error handling for invalid inputs
   - Check that no secrets, hardcoded values, or debug artifacts leaked into the code

   **Check D — BDD Evidence Verification (for BDD+TDD tasks ONLY):**
   - **RED Evidence:** Verify the Generator's output contains:
     - The exact BDD command run (e.g., `behave --tags=@login_success`)
     - The failing step(s) with error message
     - The scenario name that failed
   - **GREEN Evidence:** Verify the Generator's output contains:
     - The exact BDD command run (same as RED)
     - All steps passing
     - The scenario name that passed
   - **Independent Re-run:** Evaluator MUST independently run the scenario to verify it passes, plus related unit tests per the Incremental Test Strategy:

      ```text
      [BDD command] --tags@[scenario_tag]
      ```

   - If independent re-run FAILS, evaluation FAILS regardless of Generator's claims.

4. **Evaluator Reports Verdict.** The evaluator outputs one of:

   **PASS:**

   ```text
   ✅ EVALUATION PASS — Task X.Y: [Task Name]
   Diff Audit: [summary]
   BDD Evidence: [RED confirmed → GREEN confirmed → Independent re-run passed]
   Live Verification: [evidence]
   Edge Cases: [what was tested]
   Architecture: [conformance confirmed]
   Mark as DONE.
   ```

   **FAIL (returns to Generator):**

   ```text
   ❌ EVALUATION FAIL — Task X.Y: [Task Name]
   Issues Found:
   1. [Specific issue with file:line reference]
   Required Fix: [Concrete description]
   DCR Trigger: [Yes/No]
   ```

5. **Failure Loop:**
   - On FAIL: Pass evaluator feedback to a new Generator subagent (fresh context + failure hints).
   - Same retry budget applies (initial + 2 retries = 3 total).

**Light Review Process (for simple `TDD-only` tasks):**

1. Read the `git diff` to confirm scope.
2. Run affected tests only (follow Incremental Test Strategy).
3. Check for architecture violations in the diff.
4. If clean, emit PASS immediately.

#### 3e. Mark Task Completed (After Evaluator PASS)

A task is marked done **only after the Evaluator outputs PASS**. The Generator's own assessment does not determine completion.

After Evaluator PASS, update `tasks.md`:

- Change `- [ ]` to `- [x]` for every step in the completed task.
- Update the task's Status from `🟡 IN PROGRESS` to `🟢 DONE`.
- **Use precise editing:** Target the specific `### Task X.Y` block. Do NOT rewrite the entire `tasks.md` file.
- Do not move a task directly from `🔴 TODO` or legacy `TODO` to `🟢 DONE`; `🟢 DONE` is only reachable from `🟡 IN PROGRESS`.
- Mark `🟢 DONE` only when every required evidence checkbox is either `- [x]` or explicitly marked `N/A`.
- **Exact Match Required:** When updating the Status line, use the exact text and emoji `Status: 🟢 DONE`. Do not alter spacing, change the emoji, or reformat surrounding lines.
- Ensure you only update the `- [ ]` to `- [x]` for the checkboxes strictly within the current `### Task X.Y` block.

#### 3e-i. Post-Mark Verification (Mandatory)

After updating `tasks.md`, **verify the mark actually took effect** before proceeding to the next task.

1. **Re-read** the specific `### Task X.Y` block from `tasks.md`.
2. **Confirm** that:
   - The Status line shows `🟢 DONE`.
   - All `- [ ]` evidence checkboxes are now `- [x]`.
3. **If verification fails** — apply the mark immediately and re-verify.

> **⚠️ Context Reset:** After completing all tasks (or when context grows large), output: "Recommend starting a fresh session. Run `/pb-build <feature-name>` again to continue from where you left off."

### Step 4: Handle Failures (The Recovery Loop with Escalation)

> **Escalation Principle (from agent-sop):** Instead of blind retry with the same model, escalate to a stronger model after repeated failures. This prevents "stuck in a loop" syndrome and brings fresh reasoning to hard problems.

If a subagent fails:

1. **Analyze the diff:** Run `git diff` to see what the failed agent changed.
2. **Compute task-local change set:** Compare with the pre-task snapshot.
3. **Safe recovery (file-scoped):**
   - If pre-task workspace was clean: restore only task-local tracked files and remove newly created files.
   - If pre-task workspace was dirty: do NOT run workspace-wide restore. Report file-level cleanup and ask user.
4. **Report** the failure — which task, what went wrong, specific error output.
5. **Track consecutive failures per task.** Allowed budget: **3 consecutive failures total** (initial + 2 retries).

#### Escalation Protocol (Adaptive Model Routing)

| Failure Count | Action | Model Strategy |
|---------------|--------|----------------|
| 1 | **Retry** — new subagent, fresh context, pass previous error as hint | Same model |
| 2 | **Escalate** — automatically upgrade to stronger model for root-cause analysis | +1 tier (e.g., Haiku → Sonnet, Sonnet → Opus) |
| 3 | **DCR** — file Design Change Request, stop build | N/A |

**Escalation flow:**

- After **failure #2**, the orchestrator MUST:
  1. Capture the full failure context: code diff, terminal errors, task description
  2. Spawn a **reasoning-focused subagent** with a stronger model (explicitly set `model` parameter)
  3. Pass the failure context with an instruction: "Perform root-cause analysis. Do NOT implement fixes — diagnose the issue and propose a concrete solution."
  4. If the reasoning subagent identifies a fix, apply it and re-run the EvalRule
  5. If the reasoning subagent confirms the design is infeasible, file a DCR

6. **If failure count reaches 3**, suspend the task and stop the build loop. Output a standardized DCR packet:

   ```text
   🛑 Build Blocked — Task X.Y: [Task Name]
   Reason: 3 consecutive failed attempts (initial + 2 retries + 1 escalation)
   Loop Type: [BDD+TDD or TDD-only]
   Scenario Coverage: [Feature file + scenario name]

   What We Tried:
   - Attempt 1 (standard model): [summary]
   - Attempt 2 (standard model): [summary]
   - Escalation (reasoning model): [root-cause analysis summary]

   Failure Evidence:
   - [command] -> "[error excerpt]"
   Failing Step:
   - [Given/When/Then step text if applicable]

   Root Cause Analysis:
   - [Diagnosis from escalated reasoning model]

   Suggested Design Change:
   - [What should change in design.md/tasks.md]

   Impact:
   - [Which tasks are affected]

   Next Action:
   - Run /pb-refine <feature-name> with this block, then re-run /pb-build <feature-name>.
   ```

#### Design Change Requests (DCR)

If during implementation a subagent discovers that the design is **infeasible or incorrect**:

1. **Stop implementation.**
2. **File a DCR:**

   ```text
   🔄 Design Change Request — Task X.Y: [Task Name]
   Scenario Coverage: [Feature file + scenario name]

   Problem: [What is infeasible and why]
   What We Tried: [Attempt summaries]
   Failure Evidence: [Quoted errors]
   Failing Step: [Given/When/Then step text if applicable]
   Suggested Change: [What should change in design.md]
   Impact: [Which other tasks are affected]
   ```

3. The orchestrator pauses, reports the DCR to the user, and awaits a decision:
   - **Accept** — run `/pb-refine <feature-name>`, then retry.
   - **Override** — user provides alternative approach.
   - **Abort** — stop the build.

### Step 5: Final State Verification & Output Completion Summary

#### 5a. Full Test Suite Run (Mandatory)

After ALL tasks are `🟢 DONE`, run the full test suite ONCE to verify no regressions across the entire build:

```bash
# Run the project's full test suite
uv run pytest tests/ -v
```

If the full suite fails, investigate the failing tests and determine whether they are related to the tasks just completed or pre-existing failures. Only address failures caused by the build.

#### 5b. Final State Sweep (Mandatory)

Before outputting the summary, perform a **full reconciliation** of `tasks.md` against the build session's execution log.

1. Re-read the entire `tasks.md`.
2. Cross-check each `### Task X.Y:` block against the orchestrator's session record:
   - If a task was completed but `tasks.md` still shows `🔴 TODO` → auto-fix to `🟢 DONE`.
   - If a task was skipped but not marked → auto-fix to `⏭️ SKIPPED`.
   - If a task triggered a DCR but not marked → auto-fix to `🔄 DCR`.
3. Report any auto-fixes applied.

#### 5c. Output Completion Summary

```text
📊 pb-build Summary: specs/<spec-dir>/

Tasks: X/Y completed | Z skipped | W failed
Time: ~Xm

Completed:
  ✅ Task 1.1: [name]
  ✅ Task 1.2: [name]
  ⏭️ Task 2.2: [name] (skipped)

Files changed:
  - src/...
  - tests/...

Next steps:
  - Review changes: git diff
  - If tasks were skipped, fix and re-run: /pb-build <feature-name>
```

---

## Subagent Assignment Rules

1. **One subagent per task.** Never combine multiple tasks.
2. **Fresh context per subagent.** Only: task description, project context, architecture decisions, summary of completed tasks, files on disk.
3. **Sequential execution.** Tasks executed strictly in `tasks.md` order. No parallelism.
4. **Independence.** Cross-task state lives in files, not memory.
5. **Grounding first.** Every subagent verifies workspace state before writing code.
6. **Generator ↔ Evaluator isolation.** The Evaluator must never receive the Generator's conversation history.
7. **Verifiable closure.** A task closes only after the Evaluator's PASS verdict.

---

## Task State Tracking

| State | Marker | Meaning |
|-------|--------|---------|
| Pending | `🔴 TODO` | Not started; treat legacy `TODO` as this state |
| In Progress | `🟡 IN PROGRESS` | Active implementation |
| Done | `🟢 DONE` | Completed and verified after Evaluator PASS |
| Skipped | `⏭️ SKIPPED` | Skipped due to failure |
| Design Block | `🔄 DCR` | Blocked — awaiting design change |

Use `- [ ]` and `- [x]` inside the task block as evidence checkboxes, not as a substitute for the task Status line.

---

## Progress Display

```text
[2/8] ✅ Task 1.2: Define data models — 3 tests added, 2 files changed
[3/8] 🔄 Task 2.1: Implement core parser — in progress...
```

---

## Constraints

### NEVER

- **NEVER** implement tasks out of order.
- **NEVER** skip TDD steps (Red → Green → Refactor).
- **NEVER** combine test writing and implementation in the same step.
- **NEVER** let a subagent implement more than its assigned task.
- **NEVER** carry in-memory state between subagents.
- **NEVER** modify `design.md` — file a Design Change Request instead.
- **NEVER** modify, delete, or reformat `AGENTS.md` unless the user explicitly requests it.
- **NEVER** rewrite the entire `tasks.md` file — use targeted edits only.
- **NEVER** mark a task as done without the Evaluator's PASS verdict.
- **NEVER** skip adversarial evaluation for `BDD+TDD` tasks.
- **NEVER** claim tests passed without running them.
- **NEVER** exceed the retry budget (initial + 2 retries) for a single task.
- **NEVER** pass Generator conversation context to the Evaluator.

### ALWAYS

- **ALWAYS** mark completed tasks in `tasks.md` only after Evaluator PASS.
- **ALWAYS** capture a pre-task workspace snapshot before spawning a subagent.
- **ALWAYS** perform adversarial evaluation before marking any `BDD+TDD` task as done.
- **ALWAYS** run incremental tests (affected files only) after each task — see "Incremental Test Strategy" below.
- **ALWAYS** run runtime verification for runtime-facing tasks.
- **ALWAYS** report failures with retry/skip/abort options.
- **ALWAYS** apply the ponytail ladder — (1) Does this need to exist? (2) Stdlib? (3) Native? (4) Existing dep? (5) One line? (6) Minimum code. Never simplify away: validation, error handling, security.
- **ALWAYS** use existing project patterns and conventions.
- **ALWAYS** file a DCR if the design is infeasible.
- **ALWAYS** suspend after 3 consecutive failures and escalate with DCR packet.
- **ALWAYS** use fresh context for the Evaluator.

---

## Incremental Test Strategy

After each task, run ONLY tests affected by the task's changes. Full test suite is reserved for final verification after ALL tasks complete.

### How to Determine Affected Tests

1. **Identify changed source files:**
   ```bash
   git diff --name-only HEAD
   # or vs pre-task snapshot
   ```

2. **Find corresponding test files** using project conventions:
   - `src/foo/bar.py` → `tests/test_bar.py` or `tests/test_foo_bar.py`
   - `src/foo/bar.py` → `tests/foo/test_bar.py` (mirror layout)
   - Check `conftest.py` for shared fixtures used by the changed module

3. **Trace import dependencies** (for non-test source changes):
   - If `src/foo/bar.py` imports `src/foo/baz.py`, also run tests for `baz`
   - If `src/foo/bar.py` is imported by `src/foo/qux.py`, run tests for `qux` too
   - Use `grep -r "from.*bar import\|import.*bar" src/ tests/` to find dependents

4. **Run the affected test set:**
   ```bash
   # Specific test files
   uv run pytest tests/test_bar.py tests/test_baz.py -v

   # Or by keyword/module
   uv run pytest -v -k "bar or baz"

   # Or by test path pattern
   uv run pytest tests/ -v --co -q  # list collected tests first
   ```

### Rules

- **BDD+TDD tasks:** BDD scenarios already target specific scenarios — run those + related unit tests only.
- **TDD-only tasks:** Run the new test file + any test file that imports from the changed module.
- **Cross-module changes:** If a task touches 3+ modules, still run only affected tests — do not escalate to full suite.
- **Final verification:** After ALL tasks in `tasks.md` are `🟢 DONE`, run the full test suite once as the last step before marking the build complete.
- **Evaluator re-run:** The Evaluator independently runs the same affected tests — not the full suite.

---

## Anti-Pattern Quick Reference

The Evaluator should watch for these common agent mistakes:

| Anti-Pattern | Example | Correct Behavior |
|---|---|---|
| **Drive-by refactoring** | Fixing a bug but also reformatting adjacent code, adding type hints nobody asked for | Only change lines that fix the reported issue |
| **Over-abstraction** | Strategy pattern + ABC + config class for a single `calculate_discount()` function | One function until complexity is actually needed |
| **Silent assumptions** | Implementing "export users" without clarifying scope, format, fields | List assumptions, ask for clarification |
| **Speculative features** | Adding caching, validation, notifications to a "save preferences" request | Build only what was asked; add later when needed |
| **Vague success criteria** | "I'll review and improve the code" | "Write test for bug X → make it pass → verify no regressions" |
| **Style drift** | Changing quote style, whitespace, or return logic while adding logging | Match existing code style exactly |

---

## Key Principles

1. **Small, focused, sequential, independent.** Each task is self-contained.
2. **BDD+TDD is explicit.** `Scenario Coverage` and `Loop Type` define whether the double loop is used.
3. **TDD is non-negotiable.** Every task starts with a failing test.
4. **Fresh context prevents contamination.** Evaluator never inherits Generator context.
5. **Grounding before action.** Verify workspace state before writing code.
6. **Generator builds, Evaluator judges.** Roles are strictly separated.
7. **State lives on disk.** `tasks.md` checkboxes and committed code are the only persistent state.
8. **Fail fast, recover cleanly.** Task-local rollback, no workspace-wide resets.
9. **Context hygiene.** Pass minimal, relevant context to subagents.
10. **Evidence over assertion.** Status updates must map to actual command output.
11. **Escalate deterministically.** After 3 failures, route to `pb-refine` with DCR.
12. **Architecture decisions are binding.** `pb-build` executes the approved design.
13. **Adaptive evaluation.** Full adversarial for `BDD+TDD`, light review for simple `TDD-only`.
14. **ponytail ladder.** Before writing code, climb the 6-rung ladder: YAGNI → stdlib → native → existing dep → one-liner → minimum code. The Evaluator checks for over-engineering using the same ladder.
