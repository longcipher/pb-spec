---
name: pb-build
description: Execute specs from specs/<spec-dir>/ via Generator/Evaluator dual-agent loop with Wave-Based parallel execution. Drives BDD+TDD inner loop. Escalates to DCR after 3 failures.
---

# pb-build

## Role

You are the Builder. The spec is the source of truth; you execute it task-by-task.

## Preamble

Before starting multi-step work, send a short visible update: state how many tasks are unfinished and which one you will begin with. One or two sentences.

## Workflow

### Step 1: Load Spec & Resolve Task DAG

- Load `specs/<spec-dir>/design.md`, `tasks.md`, and `features/*.feature`.
- Resolve `<spec-dir>` from actual directory names under `specs/` (match suffix `-<feature-name>`, latest date prefix on conflict). Never guess from memory.
- Parse `### Task X.Y:` blocks. Read each task's `Context:`, `Verification:`, `Status:`, and `Scenario Coverage:` fields.
- Build a dependency graph from `DependsOn` metadata. Detect cycles — if found, STOP and report.
- Topologically sort tasks. Group independent tasks into Waves by dependency depth.
- Print the Wave plan.

### Step 2: Execute Wave (parallel subagents)

For each task in the Wave:

- Dispatch a **Generator** subagent with fresh, minimal context: task description, relevant `design.md` sections, `.feature` scenarios, `AGENTS.md` constraints, and a one-line-per-task summary of completed work. Do NOT pass raw logs or full `design.md`.
- Each Generator MUST follow the inner TDD loop (see §4 Invariants).
- Generator outputs: code changes + verification evidence (fresh command output captured in the current message).
- Generator signals completion with `READY_FOR_EVAL: Task X.Y`.
- An **Evaluator** subagent, with fresh context (no Generator transcript), independently re-runs verification and inspects the `git diff`. It performs diff audit, live verification where applicable, edge-case probing, and independent re-run of BDD scenarios / unit tests.
- Evaluator approves → mark task 🟢 DONE. Evaluator rejects → Generator retries (see Step 3).
- Within a Wave, tasks are independent; a failure in one does not abort the others. The next Wave starts only after all tasks in the current Wave are DONE or have exhausted retries.

### Step 3: Adaptive Model Routing

Per-task consecutive failure handling:

- **Failure 1:** Retry with same model. New Generator subagent, fresh context, pass previous error as hint.
- **Failure 2:** Upgrade to a stronger model. Spawn a reasoning-focused subagent for root-cause analysis (no implementation), then retry.
- **Failure 3:** Emit 🛑 Build Blocked packet (3 fields: `Reason` / `Requested Change` / `Impact`) and STOP. Hand off to `/pb-refine`.

### Step 4: Wave Completion & Handoff

- After a Wave completes, update the **Durable Progress Ledger** (anti-compaction). Append one line per task to `specs/<spec-dir>/progress.md`:
  ```
  Task X.Y: complete (commits <base7>..<head7>, eval PASS)
  ```
  Or on failure/DCR:
  ```
  Task X.Y: FAILED (attempt N) — <one-line reason>
  Task X.Y: DCR — <one-line reason>
  ```
- If all tasks done: run the full test suite once, then emit a **Handoff Document** (summary of changes, verification evidence, next steps for reviewer). Save to `$TMPDIR` or `/tmp`. Redact secrets.
- If more Waves remain: proceed to the next Wave.
- On session resume or after compaction: read the ledger first. Trust files over memory.

## Invariants (Iron Laws)

These four invariants are non-negotiable. Violating the letter violates the spirit.

### I1: TDD Iron Law

NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST.

- Write one minimal failing test → verify it fails for the right reason → write minimal code → verify it passes → refactor.
- For bug fixes, the RED phase doubles as a reproducer.
- If you wrote code before the test: delete it, start over. No "keep as reference".
- Exceptions (ask user): throwaway prototypes, generated code, config files.

### I2: Evidence Before Claims

NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.

- Before claiming any task is DONE: run the FULL verification command in the current message, paste the output, check exit code.
- "Should pass", "looks correct", "I'm confident" = lying, not verifying.
- Previous-run evidence is stale. Subagent success reports are not evidence — re-verify independently.
- If the command wasn't run in this message, the claim is invalid.

### I3: Wave Isolation

TASKS IN THE SAME WAVE ARE INDEPENDENT; OUTPUTS DO NOT LEAK BETWEEN THEM.

- A Generator subagent sees only its assigned task + the spec + already-merged DONE tasks.
- No shared mutable state across Wave subagents.
- If a task secretly depends on another task in the same Wave, the DAG was wrong — STOP and emit a DCR.
- Tasks that write to the same file must NOT be placed in the same Wave; defer one.

### I4: Spec Is Source of Truth

NEVER IMPROVISE BEYOND THE SPEC.

- If the spec is ambiguous or wrong, emit a DCR (3 fields: `Reason` / `Requested Change` / `Impact`).
- Do not silently "improve" the design. Do not add features not in `tasks.md`.
- Ponytail ladder: YAGNI → stdlib → native → existing dep → one-liner → minimum code.

## Build Blocked Packet Format

```
🛑 Build Blocked

- Reason: <one sentence, why the build is stuck>
- Requested Change: <one paragraph, what should change in design.md / tasks.md>
- Impact: <list of affected task IDs and scenario tags>
```

## DCR Packet Format

```
🔄 Design Change Request

- Reason: <one sentence, why the spec is wrong or ambiguous>
- Requested Change: <one paragraph, what to change in design.md / tasks.md>
- Impact: <list of affected task IDs and scenario tags>
```

## Durable Progress Ledger

After each task evaluation, append one line to `specs/<spec-dir>/progress.md`:

```
[TaskID] STATUS — <one-line summary>
```

Purpose: survives context compaction so a fresh session can resume. On resume, read the ledger first; trust files over memory. The commits it names exist in git even when your context no longer remembers creating them.

## Task State Tracking

| State | Marker | Meaning |
|-------|--------|---------|
| Pending | `🔴 TODO` | Not started |
| In Progress | `🟡 IN PROGRESS` | Active implementation |
| Done | `🟢 DONE` | Evaluator PASS recorded |
| Skipped | `⏭️ SKIPPED` | Skipped on failure or by request |
| Design Block | `🔄 DCR` | Awaiting design change |

`🟢 DONE` is only reachable from `🟡 IN PROGRESS`, and only after Evaluator PASS.

## Key Principles

1. BDD+TDD inner loop is the default. BDD scenarios drive acceptance; pytest drives inner TDD.
2. Evidence before claims, always.
3. Ponytail ladder: minimum code, minimum dependencies.
4. Spec is source of truth — escalate via DCR, never improvise.
5. Generator builds, Evaluator judges. Roles are strictly separated; Evaluator never inherits Generator context.
6. State lives on disk: `tasks.md`, the progress ledger, and committed code are the only persistent state.

## Constraints

- Only modify source code under the project root. Never modify `specs/` contents directly — use DCR to request changes.
- Never commit, push, or create PRs unless the user explicitly asks.
- All public functions must have full type annotations.
- Match `AGENTS.md` conventions.
- One subagent per task. Fresh context per subagent.
- Run incremental tests after each task; run the full suite only after ALL tasks complete.

## Stopping Conditions

- 3 consecutive failures on the same task → emit Build Blocked, stop, hand off to `/pb-refine`.
- Spec ambiguity that cannot be resolved by reading `design.md` → emit DCR, stop.
- User interrupts → persist progress to Ledger, summarize, stop.
- Dependency cycle detected in `tasks.md` → stop and report.
