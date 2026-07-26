---
name: pb-build
description: Execute specs from specs/<spec-dir>/ via Generator/Evaluator dual-agent loop with Wave-Based parallel execution. Drives BDD+TDD inner loop. Escalates to DCR after 3 failures.
---

# pb-build

## Role

Execute the spec task-by-task. Spec is source of truth.

## Workflow

### 1. Load Spec & Resolve Task DAG

- Load `specs/<spec-dir>/design.md`, `tasks.md`, `features/*.feature`.
- Resolve `<spec-dir>` from actual directory names under `specs/`. Never guess.
- Parse `### Task X.Y:` blocks. Read 4 fields per task (see `docs/contract.md`).
- Build dependency graph from `DependsOn`. Detect cycles → STOP.
- Topologically sort. Group independent tasks into Waves by dependency depth.

### 2. Execute Wave (parallel subagents)

Per task in the Wave:

1. Dispatch **Generator** subagent with minimal context: task description, relevant design sections, `.feature` scenarios, `AGENTS.md`. No raw logs or full design.md.
2. Generator follows TDD inner loop (see I1). Outputs: code + fresh verification evidence.
3. Generator signals `READY_FOR_EVAL: Task X.Y`.
4. **Evaluator** subagent (fresh context, no Generator transcript) re-runs verification, inspects `git diff`, probes edge cases, re-runs BDD/tests.
5. Evaluator PASS → mark 🟢 DONE. Reject → Generator retries (see Step 3).

Wave isolation: tasks in same Wave are independent. A failure in one doesn't abort others. Next Wave starts only after all current Wave tasks DONE or exhausted retries.

### 3. Adaptive Model Routing

Per-task consecutive failure:

- **Failure 1:** Retry same model. Fresh context. Pass previous error as hint.
- **Failure 2:** Upgrade to stronger model. Spawn root-cause analysis subagent (no implementation), then retry.
- **Failure 3:** Emit 🛑 Build Blocked packet (see `docs/contract.md` for format). STOP. Hand off to `/pb-refine`.

### 4. Wave Completion & Handoff

After each task evaluation, append to `specs/<spec-dir>/progress.md`:
```
Task X.Y: complete (commits <base7>..<head7>, eval PASS)
```
Or on failure/DCR:
```
Task X.Y: FAILED (attempt N) — <one-line reason>
Task X.Y: DCR — <one-line reason>
```
- All tasks done → run full test suite once, emit Handoff Document (summary + evidence + next steps). Save to `$TMPDIR`. Redact secrets.
- More Waves remain → proceed to next Wave.
- On session resume/compaction: read the ledger first. Trust files over memory.

## Iron Laws

### I1: TDD

No production code without a failing test first. Write failing test → verify fail → implement → verify pass → refactor. For bug fixes, RED phase is the reproducer. If you wrote code before the test: delete it, start over.

### I2: Evidence Before Claims

No completion claims without fresh verification evidence. Run the FULL verification command in the current message, paste output, check exit code. "Should pass" / "looks correct" = lying. Previous-run evidence is stale.

### I3: Wave Isolation

Tasks in the same Wave are independent. A Generator sees only its assigned task + spec + already-merged DONE tasks. No shared mutable state. Same-file tasks must NOT be in the same Wave.

### I4: Spec Is Source of Truth

Never improvise beyond the spec. If ambiguous or wrong → emit DCR (see `docs/contract.md`). Do not silently "improve" the design.

## Block Packet Formats

See `docs/contract.md` for Build Blocked and DCR field requirements (3 fields each: Reason / Requested Change / Impact).

## Task States

| State | Marker |
|---|---|
| Pending | `🔴 TODO` |
| In Progress | `🟡 IN PROGRESS` |
| Done | `🟢 DONE` (only after Evaluator PASS) |
| Design Block | `🔄 DCR` |

## Constraints

- Only modify source code under project root. Never modify `specs/` directly — use DCR.
- Never commit/push unless explicitly asked.
- One subagent per task. Fresh context per subagent.
- Run incremental tests after each task; full suite only after ALL tasks complete.
- Match `AGENTS.md` conventions.

## Stopping Conditions

- 3 consecutive failures on same task → Build Blocked → hand off to `/pb-refine`.
- Spec ambiguity unresolvable from `design.md` → emit DCR, stop.
- User interrupts → persist progress to Ledger, summarize, stop.
- Dependency cycle detected → stop and report.

---

name: pb-build

## description: Execute specs from specs/<spec-dir>/ via Generator/Evaluator dual-agent loop with Wave-Based parallel execution. Drives BDD+TDD inner loop. Escalates to DCR after 3 failures
