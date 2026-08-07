---
name: pb-refine
description: Iteratively refine feature design specs (design.md, tasks.md, features) based on user feedback or design change requests. Use when updating existing plans after build failures, scope changes, or architectural corrections.
---

# pb-refine

## Role

Apply user feedback to existing specs. This closes the gap between one-shot planning and iterative refinement.

## Workflow

### 1. Resolve spec directory & load existing spec

- List `specs/`, find directory ending with `-<feature-name>`.
- If multiple matches → most recent (latest date prefix).
- If no match → report: `❌ No spec directory found for feature "<feature-name>" in specs/. Run /pb-plan <requirement> first.`
- Load `design.md`, `tasks.md`, `AGENTS.md` (read-only).

### 2. Parse feedback & validate packets

Feedback may include: design corrections, scope changes, task adjustments, DCR packets, Build Blocked packets, general feedback.

If feedback includes structured packets (see `docs/contract.md` for 3-field schema: Reason / Requested Change / Impact), validate all fields present before modifying any file. If fields missing → report and stop. Do not guess or reconstruct missing fields.

### 3. Update design.md

If feedback changes behavior, update the `TDD & Mutation Testing Strategy` section first (type contracts, invariants, test matrix):

- Precise edits only. Preserve unaffected contract parts.
- If the behavior contract is unchanged, keep the section as-is, say why.

Apply design changes to `design.md`:

- Precise edits. Do not rewrite the entire file.
- Update metadata: `Status` → `Revised`, update date.
- Add Revision History at bottom:

```markdown
## Revision History

| Date | Change | Reason |
| :--- | :--- | :--- |
| YYYY-MM-DD | [What changed] | [user feedback or DCR] |
```

- Preserve unchanged sections exactly.
- If feedback contradicts original design, apply user's decision and note the conflict.

### 4. Cascade to tasks.md

If design changes affect task breakdown, update `tasks.md` (4-field schema, see `docs/contract.md`):

- Reset blocked tasks: `🔄 DCR` → `🔴 TODO`, clear checkboxes to `- [ ]`.
- Add new tasks with next available Task ID.
- Remove obsolete tasks: Status → `⛔ OBSOLETE`.
- Reorder if dependencies changed.
- Update Context, Verification, Test Coverage as needed.
- Do NOT modify completed tasks (`🟢 DONE` or `- [x]`) unless explicitly requested.
- Precise edits only.

### 5. Validate consistency

1. Design ↔ Tasks alignment: every design section has corresponding tasks.
2. Test matrix ↔ Design alignment: every changed contract reflected in the `TDD & Mutation Testing Strategy` section.
3. Dependency order: no task references later task work.
4. No orphaned tasks: every task traces to a design decision or test coverage entry.
5. Completed work preserved: if invalidated, flag to user.

### 6. Output summary

```text
🔄 Spec refined: specs/<spec-dir>/

Changes to design.md (TDD & Mutation Testing Strategy):
  - [Section X]: [test-matrix or contract changes]

Changes to design.md:
  - [Section X]: [What changed]

Changes to tasks.md:
  - Added: Task X.Y — [name]
  - Modified: Task X.Y — [what changed]
  - Removed: Task X.Y — [reason]

⚠️ Warnings (if any):
  - [e.g., "Task 1.2 was already completed but is affected by the design change."]

Next steps:
  - Review the updated spec.
  - Run /pb-build <feature-name> to continue implementation.
```

## Constraints

- Only modify `specs/<spec-dir>/design.md` and `tasks.md`. Do not modify source code.
- Do not re-run the entire planning process. Incremental update only.
- `AGENTS.md` is read-only.
- No interactive multi-turn probing. Apply given feedback. If ambiguous, state interpretation in Revision History and proceed.

## Edge Cases

- No feedback provided → report: "No feedback detected."
- Feedback invalidates completed tasks → flag as warning. Do not auto-undo.
- Behavior changes → update the `TDD & Mutation Testing Strategy` section (test matrix) first, then cascade.
- Feedback requires entirely new design → recommend `/pb-plan` instead.
- Multiple conflicting feedback items → apply in order given. Note conflicts in Revision History.

---

name: pb-refine

## description: Iteratively refine feature design specs (design.md, tasks.md, features) based on user feedback or design change requests. Use when updating existing plans after build failures, scope changes, or architectural corrections
