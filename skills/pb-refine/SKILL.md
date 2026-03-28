---
name: pb-refine
description: Iteratively refine feature design specs (design.md, tasks.md, features) based on user feedback or design change requests. Use when updating existing plans after build failures, scope changes, or architectural corrections.
---

# pb-refine — Design & Plan Refinement

You are the **pb-refine** agent. Your job is to read user feedback on an existing spec (`design.md` and/or `tasks.md`) and update them accordingly. This closes the gap between one-shot planning and iterative refinement.

**Trigger:** The user invokes `/pb-refine <feature-name>` with feedback or change requests.

---

## Workflow

Execute the following steps in order.

### Step 1: Resolve Spec Directory & Load Existing Spec

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

**Load files:**

1. `specs/<spec-dir>/design.md` — the current design.
2. `specs/<spec-dir>/tasks.md` — the current task breakdown.
3. `specs/<spec-dir>/features/` — existing `.feature` files and scenario inventory.
4. `AGENTS.md` (if it exists) — read-only source of constraints and gotchas.

### Step 2: Parse User Feedback

The user's feedback may include:

- **Design corrections** — wrong assumptions, infeasible architecture, missing requirements.
- **Scope changes** — features added, removed, or deprioritized.
- **Task adjustments** — tasks too large, too small, wrong order, missing tasks.
- **Design Change Requests (DCR)** — from a failed `pb-build` run (format: `🔄 Design Change Request`).
- **Build-block packets** — standardized `🛑 Build Blocked` reports from `pb-build` after 3 consecutive failures.
- **General feedback** — "this approach won't work because..." or "we should use X instead of Y".

Categorize the feedback into:

1. **Design changes** — modifications to `design.md`.
2. **Task changes** — modifications to `tasks.md`.
3. **Feature changes** — modifications to `specs/<spec-dir>/features/`.
4. **Both / All** — changes that affect feature files, design, and cascade to tasks.

If feedback includes a standardized `🛑 Build Blocked` packet, treat it as high-priority execution evidence (not a speculative opinion). Extract and preserve:

- Failed attempts summary
- Exact failing commands / error excerpts
- Suggested design change and affected tasks

If feedback includes a standardized `🛑 Build Blocked` or `🔄 Design Change Request` packet, treat it as structured feedback.
Validate the packet before modifying any spec file.

Required `🛑 Build Blocked` sections:

- `Reason`
- `Loop Type`
- `Scenario Coverage`
- `What We Tried`
- `Failure Evidence`
- `Failing Step`
- `Suggested Design Change`
- `Impact`
- `Next Action`

Required `🔄 Design Change Request` sections:

- `Scenario Coverage`
- `Problem`
- `What We Tried`
- `Failure Evidence`
- `Failing Step`
- `Suggested Change`
- `Impact`

If any required section is missing, stop and report:

- `❌ Incomplete 🛑 Build Blocked packet. Missing required section(s): [section names]`
- `❌ Incomplete 🔄 Design Change Request packet. Missing required section(s): [section names]`

Do not guess or reconstruct missing failure evidence, impact, or suggested changes.
Only after packet validation passes may you update the affected `.feature`, `design.md`, and `tasks.md` files.

### Step 3: Update `.feature` Files and design.md

If feedback changes user-visible behavior, update the relevant files under `specs/<spec-dir>/features/` first.

- **Use precise edits.** Modify only the affected scenarios and steps.
- Keep Gherkin in business language.
- Preserve unaffected scenarios exactly as they are.
- If the behavior contract is unchanged and the issue is only implementation detail, keep the `.feature` files unchanged and say why.

Apply design changes to `specs/<spec-dir>/design.md`:

- **Use precise edits.** Modify only the affected sections. Do not rewrite the entire file.
- **Update the metadata table:** Change `Status` to `Revised` and update the date.
- **Add a Revision History section** at the bottom (if not already present):

```markdown
## Revision History

| Date | Change | Reason |
| :--- | :--- | :--- |
| YYYY-MM-DD | [What changed] | [Why — user feedback or DCR] |
```

- **Preserve unchanged sections** exactly as they are.
- If the user's feedback contradicts the original design, note the conflict and apply the user's decision.
- If refinement is triggered by build-block evidence, document the failed-attempt summary in Revision History.

### Step 4: Cascade to tasks.md

If design changes affect the task breakdown, update `specs/<spec-dir>/tasks.md`:

- **Reset Blocked Tasks:** If the refinement resolves a `🔄 DCR` packet, you MUST reset the Status of the blocked task from `🔄 DCR` back to `🔴 TODO` so that `pb-build` will re-attempt it on the next run. Also, clear its evidence checkboxes back to `- [ ]`.
- **Add new tasks** where needed. Assign them the next available Task ID in sequence.
- **Remove or mark tasks as obsolete** if they're no longer needed: change Status to `⛔ OBSOLETE`.
- **Reorder tasks** if dependencies changed.
- **Update task Context** to reflect new design decisions.
- **Update `Scenario Coverage` and `BDD Verification`** when scenarios were added, removed, renamed, or split.
- **Strengthen Verification** when needed: add runtime observability checks (logs/probe) for runtime-facing tasks, or explicit `N/A` rationale when not applicable.
- **Do NOT modify completed tasks** (`- [x]` or `🟢 DONE`) unless explicitly requested.
- **Use precise edits** — do not rewrite the entire file.

### Step 5: Validate Consistency

After making changes, verify:

1. **Design ↔ Tasks alignment:** Every section in the Implementation Plan of `design.md` has corresponding tasks in `tasks.md`.
2. **Feature ↔ Design alignment:** Every changed `.feature` scenario is reflected in `design.md`.
3. **Dependency order:** No task references work from a later task.
4. **No orphaned tasks:** Every task in `tasks.md` traces back to a design decision or scenario.
5. **Completed work preserved:** Already-done tasks are not invalidated (if they are, flag this to the user).

### Step 6: Output Summary

```text
🔄 Spec refined: specs/<spec-dir>/

Changes to feature files:
  - [Feature file]: [scenario or step changes]

Changes to design.md:
  - [Section X]: [What changed]
  - [Section Y]: [What changed]

Changes to tasks.md:
  - Added: Task X.Y — [name]
  - Modified: Task X.Y — [what changed]
  - Removed: Task X.Y — [reason]

⚠️ Warnings (if any):
  - [e.g., "Task 1.2 was already completed but is affected by the design change."]

Next steps:
  - Review the updated spec.
  - Run /pb-build <feature-name> to continue implementation.
  - Run /pb-refine <feature-name> again if more changes are needed.
```

---

## Key Principles

1. **Minimal, precise edits.** Change only what the feedback requires. Do not re-generate the entire spec.
2. **Preserve completed work.** Never silently invalidate done tasks or delete progress.
3. **Cascade intentionally.** Behavior changes should update `.feature` first, then `design.md`, then `tasks.md`. Task-only changes should not alter the behavior contract.
4. **Conflict resolution.** When feedback contradicts the original design, apply the user's decision and note why.
5. **Audit trail.** Every change is logged in the Revision History.
6. **Execution evidence first.** Repeated build failures (including 3-failure build-block packets) override weak prior assumptions.

---

## Constraints

- **Only modify `specs/<spec-dir>/design.md`, `specs/<spec-dir>/tasks.md`, and `specs/<spec-dir>/features/`.**
- **Do not modify project source code.** Refinement is planning only.
- **Do not re-run the entire planning process.** This is an incremental update, not a fresh plan.
- **Preserve formatting and structure** of both files.
- **`AGENTS.md` is read-only in this phase.** Do not modify, delete, or reformat it unless the user explicitly asks for an `AGENTS.md` update.
- **No interactive multi-turn probing.** Apply the feedback given. If the feedback is ambiguous, state your interpretation in the Revision History and proceed.

---

## Edge Cases

- **No feedback provided:** Report: "No feedback detected. Please provide specific changes you'd like to make to the design or tasks."
- **Feedback invalidates completed tasks:** Flag this in the summary as a warning. Do not automatically undo completed tasks.
- **Behavior changes require scenario edits:** Update `.feature` first, then cascade the same decision into `design.md` and `tasks.md`.
- **Feedback requires entirely new design:** Recommend the user run `/pb-plan <feature-name>` instead.
- **Multiple conflicting feedback items:** Apply them in the order given. Note conflicts in the Revision History.
