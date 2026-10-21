---
name: pb-refine
description: Apply user feedback or design change requests to an existing spec (design.md, tasks.md). Incremental, precise edits only.
---

# pb-refine

Apply feedback to an existing spec. This closes the gap between one-shot planning and iterative refinement.

## Workflow

### 1. Locate and load the spec

- List `specs/`, find the directory ending with `-<feature-name>`; on multiple matches take the latest date prefix; on no match, report and stop (`/pb-plan` first).
- Load `design.md`, `tasks.md`, `AGENTS.md` (read-only).

### 2. Apply feedback to design.md

- If behavior changes, update the `TDD & Mutation Testing Strategy` section first (type contracts, invariants, test matrix, mutation scope).
- Precise edits only — never rewrite whole files, preserve unaffected sections verbatim.
- Update `Status` → `Revised`, add a `## Revision History` table entry (`| Date | Change | Reason |`).

### 3. Cascade to tasks.md

- Reset invalidated tasks: `🔄 DCR` → `🔴 TODO`, checkboxes back to `- [ ]`.
- Add new tasks with the next free Task ID; obsolete tasks → `⛔ OBSOLETE`.
- Update `Context`, `Verification`, `Test Coverage` where affected.
- Never modify completed tasks (`🟢 DONE`) unless explicitly requested; if a change invalidates them, flag as a warning instead.

### 4. Validate and report

- Check alignment: every design change has tasks, dependencies stay ordered, no orphaned tasks.
- Run `uv run pb-spec validate --plan <spec-dir>` and fix errors.
- Summarize: what changed in design.md / tasks.md, warnings, and next step (`/pb-build <feature>`).

## Decision protocol

Apply given feedback as stated — no multi-turn probing. If the feedback admits two or more
genuinely incomparable interpretations that change what gets built, ask the user and wait;
otherwise adopt the most reasonable interpretation, record it in Revision History, and proceed.

## Edge cases

- No feedback provided → report "No feedback detected."
- Feedback requires an entirely new design → recommend `/pb-plan` instead.
- Multiple conflicting feedback items → apply in order given, note conflicts in Revision History.

## Constraints

- Only modify `specs/<spec-dir>/design.md` and `tasks.md`. Never source code. `AGENTS.md` is read-only.
- Incremental update only — never re-run the full planning process.
