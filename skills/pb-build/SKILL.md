---
name: pb-build
description: Execute a spec task-by-task via a strict TDD loop (Red → Green → Refactor → selective Mutate). Escalates to DCR after 3 failures on a task.
---

# pb-build

Execute the spec task-by-task. The spec is the source of truth.

## Workflow

### 1. Load spec and resolve tasks

- Resolve `<spec-dir>` from actual directory names under `specs/`. Never guess.
- Parse `### Task X.Y:` blocks (4 fields, schema in `docs/contract.md`), build the dependency graph from `DependsOn` (cycle → stop), and execute in dependency order. Independent tasks may run in parallel subagents; same-file tasks must not.

### 2. Per task — strict TDD loop

1. **Red:** write the failing test first (unit + property tests where applicable; for bug fixes the reproducer IS the red test) → verify it fails. If you wrote code before the test, delete it and start over.
2. **Green:** minimum implementation → verify pass.
3. **Refactor:** clean up → suite still green.
4. **Verify layers:** per the project testing principle, add integration/E2E/fuzz coverage the task's test matrix calls for — boundary and exception paths included. No production code without a failing test first; no completion claims without fresh evidence (run the command, paste output, check exit code — "should pass" is a lie).

### 3. Mutation testing — selective and scope-bounded

Mutation testing is very slow. Do NOT run it unconditionally:

- **Run it** when the task touches core logic with subtle correctness risk (parsers, state machines, gas/crypto/boundary math, concurrency), or when the spec's `TDD & Mutation Testing Strategy` marks it required.
- **Scope it strictly:** mutate only the files changed by this task — `pb-spec mutate --against <base>` or the project's diff-based script. Never whole-repo runs. Prefer targeted selection (e.g. `mutmut` path filters) to shrink the run further.
- **Skip it** for infra, config, docs, trivial getters/setters, and UI code.
- Surviving mutants on changed code are **test failures**: strengthen assertions until they are killed — or record a justified exemption in the task.

### 4. Failures and handoff

- Per-task failure retry: 1st → retry with the error as hint; 2nd → root-cause analysis before retrying; 3rd → emit a Build Blocked / DCR packet (3 fields: `Reason` / `Requested Change` / `Impact`) and stop, hand off to `/pb-refine`.
- After each task: flip its `Status:` to `🟢 DONE` in `tasks.md` and append a one-line result (task, commits, verdict) to the spec's progress notes.
- All tasks done → run the full suite once, emit a handoff summary (what shipped, evidence, next steps). On session resume, trust files over memory.

## Constraints

- Never improvise beyond the spec: ambiguity or defect → DCR packet, not silent "improvement".
- The only permitted edits under `specs/` are bookkeeping: flipping task `Status:` markers and
  appending progress notes. Any design/content change goes through a DCR packet instead.
- Never commit/push unless explicitly asked.
- Incremental tests after each task; full suite only at the end.
- Match `AGENTS.md` conventions.
