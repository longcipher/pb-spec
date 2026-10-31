---
name: pb-build
description: Execute a spec task-by-task via a strict TDD loop (Red → Green → Refactor → off-by-default Mutate). Escalates to DCR after 3 failures on a task.
---

# pb-build

Execute the spec task-by-task. The spec is the source of truth.

## Workflow

### 1. Load spec and resolve tasks

- Resolve `<spec-dir>` from actual directory names under `specs/`. Never guess.
- Parse `### Task X.Y:` blocks (4 required fields plus optional `Mutation:`, schema in `docs/contract.md`), build the dependency graph from `DependsOn` (cycle → stop), and execute in dependency order. Independent tasks may run in parallel subagents; same-file tasks must not.

### 2. Per task — strict TDD loop

1. **Red:** write the failing test first (unit + property tests where applicable; for bug fixes the reproducer IS the red test) → verify it fails. If you wrote code before the test, delete it and start over.
2. **Green:** minimum implementation → verify pass.
3. **Refactor:** clean up → suite still green.
4. **Verify layers:** per the project testing principle, add integration/E2E/fuzz coverage the task's test matrix calls for — boundary and exception paths included. No production code without a failing test first; no completion claims without fresh evidence (run the command, paste output, check exit code — "should pass" is a lie).

### 3. Mutation testing — OFF by default

Mutation testing is the slowest gate. The default is **skip**. Run it only when all conditions hold:

1. The current task has `Mutation: <changed-source-glob>`; a task without the field is exempt.
   Never add the field "to be safe".
2. The files changed by this task match those globs.
3. The change touches core logic with subtle correctness risk — parser, state machine,
   boundary/money/crypto math, concurrency. Infra, config, docs, UI, glue, and trivial getters
   are never eligible.
4. The project already has the tool configured (`[tool.mutmut]`, `cargo-mutants`, or
   `stryker.conf.*`). If the tool is absent, skip; do not install or configure it for this task.
5. Tests are green and the scope is within budget: **≤3 changed files, ≤60 mutants, ≤300 s**.
6. Run once at the end of the task, never after every edit.

Define `<base>` as `git merge-base HEAD origin/main` (or the repo's main branch). Pre-check first,
then run. Stop and narrow the task's `Mutation:` globs (or split the task) when the count or
estimate exceeds the budget. Never raise the budget, and never fall back to a whole-repo run.

Rust:

```bash
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
DIFF=$(mktemp)
git diff "$BASE" -- <changed.rs> > "$DIFF"   # cargo-mutants --in-diff takes a diff file
cargo mutants --in-diff "$DIFF" --file <changed.rs> --list --no-times   # count first
cargo mutants --in-diff "$DIFF" --file <changed.rs> --timeout-multiplier 2 --no-times
```

Python:

```bash
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD main)
git diff --name-only "$BASE" -- '<src-glob>'   # confirm the changed file matches Mutation:
uv run mutmut print-time-estimates '<module>.*'   # count + estimated seconds first
uv run mutmut run '<module>.*' --max-children "$(getconf _NPROCESSORS_ONLN)"
```

`<module>.*` is file-level scoping (`src/pkg/parser.py` → `pkg.parser.*`). If the file exceeds
60 mutants or 300 s, stop; do not widen the scope.

Node/TypeScript:

```bash
npx stryker run --mutate <changed.ts,...> --since <base> --incremental --reporters clear-text,json
```

`--mutate` lists only the changed source files; `--since` limits to changed code. Stryker has no
dry-run mutant listing, so enforce the scope with the file cap and timeout, then abort if the
JSON report shows more than 60 mutants. Requires an existing Stryker config.

If the project ships `pb-spec`, `pb-spec mutate --against <base>` is an optional convenience that
applies the same gate. Without it, use the recipes above.

Surviving mutants on changed code are **test failures**: strengthen assertions until killed, or
record a justified exemption in the task. Paste the count/score in the task evidence.

### 4. Failures and handoff

- Per-task failure retry: 1st → retry with the error as hint; 2nd → root-cause analysis before retrying; 3rd → emit a Build Blocked / DCR packet (3 fields: `Reason` / `Requested Change` / `Impact`) and stop, hand off to `/pb-refine`.
- After each task: flip its `Status:` to `🟢 DONE` in `tasks.md` and append a one-line result (task, commits, verdict) to the spec's progress notes.
- All tasks done → run the full suite once, emit a handoff summary (what shipped, evidence, next steps). On session resume, trust files over memory.

## Constraints

- Never improvise beyond the spec: ambiguity or defect → DCR packet, not silent "improvement".
- The only permitted edits under `specs/` are bookkeeping: flipping task `Status:` markers and
  appending progress notes. Any design/content change goes through a DCR packet instead.
- Never commit/push unless explicitly asked.
- Mutation testing is OFF by default: only a task with `Mutation:` may trigger it, never in CI,
  and never as a generic completion check.
- Incremental tests after each task; full suite only at the end.
- Match `AGENTS.md` conventions.
